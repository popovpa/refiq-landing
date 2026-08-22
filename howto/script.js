/* Логика страницы /howto. Шапка, меню и год — в общем ../script.js */

(function () {
  function highlightTarget() {
    var hash = window.location.hash;
    if (hash !== "#business" && hash !== "#agent") return;
    var section = document.querySelector(hash);
    if (!section) return;
    section.classList.add("is-highlighted");
    setTimeout(function () {
      section.classList.remove("is-highlighted");
    }, 1200);
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

  window.addEventListener("hashchange", highlightTarget);
  highlightTarget();
})();
