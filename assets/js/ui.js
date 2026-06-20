/* Shared site UI behaviours — loaded once, globally. No-ops when the
   relevant elements are absent, so it is safe on every page. */
(function () {
  "use strict";

  /* ---- Native <dialog> open/close wiring ---------------------------- */
  function initDialogs() {
    document.querySelectorAll("[data-open-dialog]").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        var dlg = document.getElementById(trigger.getAttribute("data-open-dialog"));
        if (dlg && typeof dlg.showModal === "function") dlg.showModal();
      });
    });

    document.querySelectorAll("dialog").forEach(function (dlg) {
      /* Close button(s) inside the dialog */
      dlg.querySelectorAll("[data-close-dialog]").forEach(function (btn) {
        btn.addEventListener("click", function () { dlg.close(); });
      });
      /* Click on the backdrop (the dialog element itself) closes it */
      dlg.addEventListener("click", function (e) {
        if (e.target === dlg) dlg.close();
      });
    });
  }

  /* ---- Formspree contact forms -------------------------------------- */
  function initForms() {
    document.querySelectorAll("form[data-formspree]").forEach(function (form) {
      form.addEventListener("submit", async function (e) {
        e.preventDefault();
        var endpoint = "https://formspree.io/f/" + form.getAttribute("data-formspree");
        var btn = form.querySelector(".contact-submit");
        var status = form.querySelector(".form-status");
        var original = btn ? btn.textContent : "";
        if (btn) { btn.disabled = true; btn.textContent = "Sending..."; }
        if (status) { status.textContent = ""; status.className = "form-status"; }
        try {
          var res = await fetch(endpoint, {
            method: "POST",
            body: new FormData(form),
            headers: { Accept: "application/json" }
          });
          if (status) {
            if (res.ok) {
              status.textContent = "Message sent successfully!";
              status.classList.add("form-status--success");
              form.reset();
            } else {
              status.textContent = "Something went wrong. Please try again.";
              status.classList.add("form-status--error");
            }
          }
        } catch (err) {
          if (status) {
            status.textContent = "Connection error. Please try again.";
            status.classList.add("form-status--error");
          }
        }
        if (btn) { btn.disabled = false; btn.textContent = original; }
      });
    });
  }

  /* ---- Reading progress bar (blog articles) ------------------------- */
  function initReadingProgress() {
    var bar = document.querySelector(".reading-progress > span");
    /* Only track long-form pages (blog posts, project write-ups). The bar
       markup is global but stays inert (width 0) elsewhere. */
    if (!bar || !document.querySelector(".article-content")) return;
    var ticking = false;
    function update() {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
      bar.style.width = pct + "%";
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  function init() {
    initDialogs();
    initForms();
    initReadingProgress();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
