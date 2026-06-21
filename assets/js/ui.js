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

  /* ---- Homepage proof band: animated count-up stats ---------------- */
  /* Counts the package count and the live npm-download total up from
     zero the first time the band scrolls into view. The npm total is
     fetched async; whichever happens last (visibility or fetch) kicks
     off its animation. Respects prefers-reduced-motion. */
  function initProofCounters() {
    var band = document.querySelector("[data-npm-packages]");
    if (!band) return;

    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var pkgEl = band.querySelector("[data-count]");
    var npmEl = band.querySelector("[data-npm-total]");
    var npmTarget = null; // numeric target once fetched (null = pending)
    var visible = false;

    function countUp(el, target) {
      if (!el) return;
      if (reduce) { el.textContent = target.toLocaleString("en"); return; }
      var dur = 1200, from = 0, start = 0;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(from + (target - from) * eased).toLocaleString("en");
        if (p < 1) requestAnimationFrame(step);
        else el.textContent = target.toLocaleString("en");
      }
      requestAnimationFrame(step);
    }

    function runNpm() {
      if (!visible || npmTarget === null || npmTarget < 0 || !npmEl) return;
      if (npmTarget > 0) countUp(npmEl, npmTarget);
      else npmEl.textContent = "8+";
      npmTarget = -1; // mark consumed so it only runs once
    }

    // Fetch the live npm download totals.
    var pkgs = band.getAttribute("data-npm-packages").split(",").filter(Boolean);
    if (pkgs.length) {
      Promise.all(pkgs.map(function (p) {
        return fetch("https://api.npmjs.org/downloads/point/last-month/" + p)
          .then(function (r) { return r.json(); })
          .then(function (d) { return d.downloads || 0; })
          .catch(function () { return 0; });
      })).then(function (counts) {
        npmTarget = counts.reduce(function (a, b) { return a + b; }, 0);
        runNpm();
      });
    } else if (npmEl) {
      npmEl.textContent = "8+";
    }

    function start() {
      if (visible) return;
      visible = true;
      if (pkgEl) {
        var t = parseInt(pkgEl.textContent.replace(/[^\d]/g, ""), 10) || 0;
        countUp(pkgEl, t);
      }
      runNpm();
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { start(); io.disconnect(); }
        });
      }, { threshold: 0.35 });
      io.observe(band);
    } else {
      start();
    }
  }

  /* ---- Rotating keyword(s) in the tagline -------------------------- */
  function initRotors() {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.querySelectorAll("[data-rotor]").forEach(function (el) {
      var words = el.getAttribute("data-rotor").split("|").map(function (s) {
        return s.trim();
      }).filter(Boolean);
      if (words.length < 2 || reduce) return;

      // Reserve the width of the widest term so the line never reflows as
      // words cycle. Always reserved (even for a trailing rotor): a stable
      // footprint keeps the wrap position fixed. Measured live, font-correct.
      var maxW = 0;
      words.forEach(function (w) {
        el.textContent = w;
        if (el.offsetWidth > maxW) maxW = el.offsetWidth;
      });
      el.textContent = words[0];
      el.style.minWidth = maxW + "px";
      el.style.textAlign = "left";

      var i = 0;
      setInterval(function () {
        i = (i + 1) % words.length;
        el.style.opacity = "0";
        el.style.transform = "translateY(-4px)";
        setTimeout(function () {
          el.textContent = words[i];
          el.style.opacity = "1";
          el.style.transform = "translateY(0)";
        }, 280);
      }, 2400);
    });
  }

  /* ---- Scroll-reveal for the homepage recent-articles list -------- */
  function initScrollReveal() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;
    // Homepage only: the proof band exists nowhere else.
    if (!document.querySelector(".home-proof")) return;
    var items = document.querySelectorAll(".article-link--simple");
    if (!items.length) return;

    items.forEach(function (el, i) {
      el.classList.add("reveal-on-scroll");
      el.style.transitionDelay = (i % 5) * 0.08 + "s";
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ---- Generic staggered scroll-reveal --------------------------- */
  /* Reveals matching elements as they enter the viewport, then strips the
     helper classes so a pinned transform/opacity can't override the
     element's own hover styles (cards lift on hover). */
  function revealGroup(selector, step) {
    var items = document.querySelectorAll(selector);
    if (!items.length) return;
    items.forEach(function (el, i) {
      el.classList.add("reveal-on-scroll");
      // Stagger siblings, but cap so a long list doesn't crawl in.
      el.style.transitionDelay = (i % 6) * (step || 0.07) + "s";
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        io.unobserve(el);
        el.classList.add("is-visible");
        el.addEventListener("transitionend", function () {
          el.classList.remove("reveal-on-scroll", "is-visible");
          el.style.transitionDelay = "";
        }, { once: true });
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -8% 0px" });
    items.forEach(function (el) { io.observe(el); });
  }

  function initSectionReveal() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;
    // About page sections (no-op elsewhere — revealGroup self-guards).
    revealGroup(".about-stats");
    revealGroup(".skill-group");
    revealGroup(".tech-arch__layer");
    revealGroup(".timeline-item");
    revealGroup(".support-card");
    // Blog & projects list cards.
    revealGroup(".blog-featured");
    revealGroup(".blog-feed-item");
    revealGroup(".project-featured");
    revealGroup(".project-card");
  }

  /* ---- Cmd/Ctrl+K opens search (reuses Blowfish's own toggle) ----- */
  function initSearchHotkey() {
    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        var btn = document.getElementById("search-button")
               || document.getElementById("search-button-mobile");
        if (btn) {
          e.preventDefault();
          btn.click();
        }
      }
    });
  }

  function init() {
    initDialogs();
    initForms();
    initReadingProgress();
    initProofCounters();
    initRotors();
    initScrollReveal();
    initSectionReveal();
    initSearchHotkey();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
