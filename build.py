#!/usr/bin/env python3
"""Copy public landing files and stamp local static URLs with ?nocache=<checksum>."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

SITE_ORIGIN = "https://refiq.ru"
ASSET_EXT = {
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".svg",
    ".woff",
    ".woff2",
}
PUBLIC_FILES = (
    "index.html",
    "404.html",
    "styles.css",
    "script.js",
    "robots.txt",
    "sitemap.xml",
)
PUBLIC_DIRS = ("assets", "design", "src", "howto", "docs")
SKIP_NAMES = {".DS_Store"}
DIGEST_LEN = 12

HTML_ATTR_RE = re.compile(
    r"""((?:href|src|content)\s*=\s*)(["'])([^"']+)\2""",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(
    r"""(url\(\s*)(["']?)([^"')]+)\2(\s*\))""",
    re.IGNORECASE,
)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()[:DIGEST_LEN]


def split_url(url: str) -> tuple[str, str, str]:
    fragment = ""
    rest = url
    if "#" in rest:
        rest, fragment = rest.split("#", 1)
        fragment = "#" + fragment
    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)
        query = "?" + query
    return rest, query, fragment


def with_nocache(url: str, digest: str) -> str:
    path, query, fragment = split_url(url)
    params = []
    if query:
        for part in query[1:].split("&"):
            if not part or part.startswith("nocache="):
                continue
            params.append(part)
    params.append(f"nocache={digest}")
    return f"{path}?{'&'.join(params)}{fragment}"


def resolve_local(base_file: Path, url: str, root: Path) -> Path | None:
    path, _, _ = split_url(url.strip())
    if not path or path.startswith(("data:", "mailto:", "tel:", "//")):
        return None
    if Path(path).suffix.lower() not in ASSET_EXT:
        return None

    root = root.resolve()
    if path.startswith(("http://", "https://")):
        origin = SITE_ORIGIN.rstrip("/")
        if path == origin or path == origin + "/":
            return None
        if not path.startswith(origin + "/"):
            return None
        candidate = root / path[len(origin) + 1 :]
    elif path.startswith("/"):
        candidate = root / path.lstrip("/")
    else:
        candidate = base_file.parent / path

    try:
        candidate = candidate.resolve()
        candidate.relative_to(root)
        if candidate.is_file():
            return candidate
    except (OSError, ValueError):
        return None
    return None


def stamp_text(text: str, base_file: Path, root: Path, pattern: re.Pattern[str], url_group: int) -> str:
    cache: dict[Path, str] = {}

    def repl(match: re.Match[str]) -> str:
        url = match.group(url_group)
        local = resolve_local(base_file, url, root)
        if local is None:
            return match.group(0)
        digest = cache.setdefault(local, file_digest(local))
        stamped = with_nocache(url, digest)
        full = match.group(0)
        # Rebuild from original so unmatched prefix/suffix stay intact.
        start = match.start(url_group) - match.start()
        end = match.end(url_group) - match.start()
        return full[:start] + stamped + full[end:]

    return pattern.sub(repl, text)


def copy_public(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for name in PUBLIC_FILES:
        source = src / name
        if source.is_file():
            shutil.copy2(source, dest / name)

    for name in PUBLIC_DIRS:
        source = src / name
        if not source.is_dir():
            continue
        shutil.copytree(
            source,
            dest / name,
            ignore=shutil.ignore_patterns(*SKIP_NAMES),
        )


def stamp_tree(root: Path) -> list[Path]:
    changed: list[Path] = []
    css_files = sorted(path for path in root.rglob("*.css") if path.is_file())
    html_files = sorted(path for path in root.rglob("*.html") if path.is_file())

    for path in css_files:
        original = path.read_text(encoding="utf-8")
        updated = stamp_text(original, path, root, CSS_URL_RE, 3)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)

    for path in html_files:
        original = path.read_text(encoding="utf-8")
        updated = stamp_text(original, path, root, HTML_ATTR_RE, 3)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Stamp static URLs with ?nocache=<checksum>.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    src = args.root.resolve()
    dest = args.out.resolve()
    if dest == src:
        print("refusing to stamp in-place; pass a separate --out directory", file=sys.stderr)
        return 1

    copy_public(src, dest)
    required = ("robots.txt", "sitemap.xml")
    missing = [name for name in required if not (dest / name).is_file()]
    if missing:
        print("missing public files: " + ", ".join(missing), file=sys.stderr)
        return 1
    changed = stamp_tree(dest)
    print(f"built {dest}")
    for path in changed:
        print(f"  stamped {path.relative_to(dest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
