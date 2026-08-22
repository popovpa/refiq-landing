(function () {
  var jump = document.getElementById("docs-jump");
  var tocLinks = document.querySelectorAll(".docs-toc a");
  var sections = [];

  tocLinks.forEach(function (link) {
    var id = link.getAttribute("href").slice(1);
    var el = document.getElementById(id);
    if (el) sections.push({ id: id, el: el, link: link });
  });

  function setActive(id) {
    tocLinks.forEach(function (link) {
      var active = link.getAttribute("href") === "#" + id;
      link.classList.toggle("is-active", active);
    });
    if (jump) jump.value = "#" + id;
  }

  if (jump) {
    jump.addEventListener("change", function () {
      var target = document.querySelector(jump.value);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if ("IntersectionObserver" in window && sections.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        var visible = entries
          .filter(function (entry) { return entry.isIntersecting; })
          .sort(function (a, b) { return b.intersectionRatio - a.intersectionRatio; })[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-20% 0px -65% 0px", threshold: [0, 0.2, 0.6] }
    );
    sections.forEach(function (item) { observer.observe(item.el); });
  }

  function copyText(text, button) {
    function done() {
      var original = button.textContent;
      button.textContent = "Copied";
      button.classList.add("is-copied");
      setTimeout(function () {
        button.textContent = original;
        button.classList.remove("is-copied");
      }, 1200);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done);
      return;
    }

    var area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
    done();
  }

  document.querySelectorAll("[data-copy]").forEach(function (block) {
    var button = block.querySelector(".copy-btn");
    var code = block.querySelector("code");
    if (!button || !code) return;
    button.addEventListener("click", function () {
      copyText(code.textContent, button);
    });
  });

  document.querySelectorAll("[data-tabs]").forEach(function (tabs) {
    var buttons = tabs.querySelectorAll("[data-tab]");
    var panels = tabs.querySelectorAll("[data-panel]");

    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        var name = button.getAttribute("data-tab");
        buttons.forEach(function (item) {
          item.setAttribute("aria-selected", item === button ? "true" : "false");
        });
        panels.forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-panel") !== name;
        });
      });
    });
  });
})();
