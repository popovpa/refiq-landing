#!/usr/bin/env python3
"""Compress oversized landing images without changing width or height."""

from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

MAX_DEFAULT = 200_000
MAX_LOGO = 50_000
LOGO_NAMES = {"logo.png", "label.png"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
ASSET_DIRS = (Path("assets"), Path("design") / "assets", Path("src"))
TEXT_EXT = {".html", ".css", ".js", ".xml", ".txt"}
JPEG_QUALITIES = (90, 88, 85, 82, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30)
PNG_COLORS = (256, 224, 192, 160, 128, 96, 80, 64, 48, 32, 24, 16, 8)


def max_bytes_for(path: Path) -> int:
    if path.name.lower() in LOGO_NAMES:
        return MAX_LOGO
    return MAX_DEFAULT


def iter_images(root: Path) -> list[Path]:
    found: list[Path] = []
    for rel in ASSET_DIRS:
        folder = root / rel
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXT:
                found.append(path)
    return found


def has_transparency(img: Image.Image) -> bool:
    if img.mode in {"RGBA", "LA"}:
        return img.getchannel("A").getextrema()[0] < 255
    return img.mode == "P" and "transparency" in img.info


def flatten_rgb(img: Image.Image) -> Image.Image:
    if img.mode in {"RGBA", "LA"} or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


def encode_png(img: Image.Image, colors: int | None = None) -> bytes:
    work = img
    if colors is not None:
        if has_transparency(img) or img.mode in {"RGBA", "LA"}:
            work = img.convert("RGBA").quantize(
                colors=colors,
                method=Image.Quantize.FASTOCTREE,
            )
        else:
            work = flatten_rgb(img).quantize(
                colors=colors,
                method=Image.Quantize.MEDIANCUT,
            )
    elif img.mode not in {"RGB", "RGBA", "P", "L", "LA"}:
        work = img.convert("RGBA") if "A" in img.getbands() else img.convert("RGB")
    buf = BytesIO()
    work.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def encode_jpeg(img: Image.Image, quality: int) -> bytes:
    buf = BytesIO()
    flatten_rgb(img).save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
    )
    return buf.getvalue()


def encode_webp(img: Image.Image, quality: int) -> bytes:
    buf = BytesIO()
    work = img.convert("RGBA") if has_transparency(img) or img.mode in {"RGBA", "LA"} else flatten_rgb(img)
    work.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()


def best_under(candidates: list[bytes], limit: int) -> bytes | None:
    fitting = [data for data in candidates if len(data) <= limit]
    if not fitting:
        return None
    return max(fitting, key=len)


def compress_png(img: Image.Image, limit: int) -> tuple[bytes, str]:
    lossless = encode_png(img)
    if len(lossless) <= limit:
        return lossless, ".png"
    # Photos and UI screenshots cannot hit the cap as PNG without a resize.
    # Keep PNG only when transparency must be preserved; otherwise use JPEG.
    if has_transparency(img):
        quantized = [encode_png(img, colors) for colors in PNG_COLORS]
        png = best_under(quantized, limit)
        if png is not None:
            return png, ".png"
        return min([lossless, *quantized], key=len), ".png"
    jpegs = [encode_jpeg(img, quality) for quality in JPEG_QUALITIES]
    jpeg = best_under(jpegs, limit)
    if jpeg is not None:
        return jpeg, ".jpg"
    return min(jpegs, key=len), ".jpg"


def compress_jpeg(img: Image.Image, limit: int) -> bytes:
    candidates = [encode_jpeg(img, quality) for quality in JPEG_QUALITIES]
    chosen = best_under(candidates, limit)
    if chosen is not None:
        return chosen
    return min(candidates, key=len)


def compress_webp(img: Image.Image, limit: int) -> bytes:
    qualities = (90, 85, 80, 75, 70, 60, 50, 40, 30)
    candidates = [encode_webp(img, quality) for quality in qualities]
    chosen = best_under(candidates, limit)
    if chosen is not None:
        return chosen
    return min(candidates, key=len)


def write_image(path: Path, data: bytes, expected_size: tuple[int, int]) -> None:
    path.write_bytes(data)
    with Image.open(path) as written:
        if written.size != expected_size:
            raise RuntimeError(
                f"{path} changed dimensions {expected_size} -> {written.size}"
            )


def rewrite_refs(root: Path, replacements: list[tuple[str, str]]) -> list[Path]:
    if not replacements:
        return []
    changed: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXT:
            continue
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def compress_tree(root: Path) -> list[str]:
    reports: list[str] = []
    replacements: list[tuple[str, str]] = []

    print("compressing images (max 200KB; logo.png/label.png max 50KB)")

    for path in iter_images(root):
        limit = max_bytes_for(path)
        original_size = path.stat().st_size
        if original_size <= limit:
            continue

        with Image.open(path) as img:
            img.load()
            dimensions = img.size
            suffix = path.suffix.lower()
            if suffix == ".png":
                result = compress_png(img, limit)
            elif suffix in {".jpg", ".jpeg"}:
                result = (compress_jpeg(img, limit), suffix)
            else:
                result = (compress_webp(img, limit), suffix)

        if result is None:
            reports.append(f"  failed {path.relative_to(root)}")
            continue

        data, out_suffix = result
        dest = path if out_suffix == suffix else path.with_suffix(out_suffix)
        write_image(dest, data, dimensions)
        if dest != path:
            replacements.append(
                (path.relative_to(root).as_posix(), dest.relative_to(root).as_posix())
            )
            path.unlink()

        new_size = dest.stat().st_size
        rel = dest.relative_to(root).as_posix()
        note = "" if new_size <= limit else " (still over limit)"
        if dest != path:
            reports.append(
                f"  {path.relative_to(root).as_posix()} -> {rel} "
                f"{original_size} -> {new_size}{note}"
            )
        else:
            reports.append(f"  {rel} {original_size} -> {new_size}{note}")

    rewritten = rewrite_refs(root, replacements)
    for path in rewritten:
        reports.append(f"  updated refs in {path.relative_to(root)}")
    if not reports:
        print("  no images needed compression")
    else:
        for line in reports:
            print(line)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compress oversized images in assets without resizing."
    )
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    compress_tree(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
