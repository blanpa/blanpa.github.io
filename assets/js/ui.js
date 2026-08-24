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

  /* Removed: animated count-up stats, the rotating hero keyword, and the
     two IntersectionObserver reveal passes. The numbers are baked into the
     HTML at build time and now simply render; the reveals hid real content
     behind a script for a decorative fade. See the MOTION note in
     custom.css for the reasoning. */

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

  /* Removed: the floating support button. Its links now live in the footer
     as plain text — see layouts/partials/extend-footer.html. */

  /* ---- Mermaid: lazy runtime + diagram lightbox --------------------- */
  function initMermaid() {
    var wrappers = document.querySelectorAll(".mermaid-wrapper");
    if (!wrappers.length) return;

    /* Pages whose diagrams are all build-time SVGs have no runtime work to
       do — only the lightbox below. Without this, the observer would still
       fetch 3.2 MB for a page that has nothing to render with it. */
    var needsRuntime = !!document.querySelector("pre.mermaid");

    /* -- Runtime ---------------------------------------------------- */
    /* The mermaid bundle is >3 MB — by far the heaviest asset here — so
       extend-footer.html only hands us its URL and we fetch it once a
       diagram is within a screen or so of the viewport. Blowfish's own
       eager <script> (vendor.html, shortcode pages only) wins if present. */
    var loader = document.getElementById("mermaid-loader");
    var pending = [];
    var state = "idle"; /* idle | loading | ready */

    function ensureRuntime(callback) {
      if (state === "ready" || window.mermaid) {
        state = "ready";
        if (callback) callback();
        return;
      }
      if (callback) pending.push(callback);
      if (state === "loading") return;

      /* Shortcode pages get Blowfish's own eager <script defer>; wait for
         that one rather than fetching three megabytes twice. */
      var themeScript = document.querySelector('script[src*="mermaid.bundle"]');
      if (themeScript) {
        state = "loading";
        themeScript.addEventListener("load", function () { onRuntimeReady(); });
        return;
      }
      if (!loader) return;

      state = "loading";
      var script = document.createElement("script");
      script.src = loader.getAttribute("data-src");
      var integrity = loader.getAttribute("data-integrity");
      if (integrity) script.integrity = integrity;
      script.onload = onRuntimeReady;
      script.onerror = function () {
        state = "idle";
        pending.length = 0;
      };
      document.head.appendChild(script);
    }

    function onRuntimeReady() {
      state = "ready";
      /* Blowfish's appearance.js owns mermaid's light/dark configuration and
         re-runs it on every theme switch. Its DOMContentLoaded call no-opped
         (mermaid was absent then), so trigger the first render here. */
      if (typeof window.updateMermaidTheme === "function") window.updateMermaidTheme();
      var queued = pending.slice();
      pending.length = 0;
      queued.forEach(function (fn) { fn(); });
    }

    if (needsRuntime) {
      if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            io.disconnect();
            ensureRuntime();
          });
        }, { rootMargin: "800px 0px" });
        Array.prototype.forEach.call(wrappers, function (w) { io.observe(w); });
      } else {
        ensureRuntime();
      }
    }

    /* -- Lightbox --------------------------------------------------- */
    /* A native <dialog>: focus trap, Escape, inert background, and focus
       restore on close all come from the platform. */
    var dialog = null;
    var stageHost = null;
    var zoom = 1;
    var minZoom = 0.5;
    var maxZoom = 5;
    var zoomStep = 0.25;

    function ensureDialog() {
      if (dialog) return dialog;
      dialog = document.createElement("dialog");
      dialog.className = "mermaid-lightbox";
      dialog.setAttribute("aria-label", "Zoomed diagram");
      dialog.innerHTML =
        '<button type="button" class="mermaid-lightbox__close" aria-label="Close">&times;</button>' +
        '<div class="mermaid-lightbox__inner"></div>' +
        '<div class="mermaid-lightbox__controls">' +
          '<button type="button" data-action="out" aria-label="Zoom out">&minus;</button>' +
          '<button type="button" data-action="reset" aria-label="Reset zoom">100%</button>' +
          '<button type="button" data-action="in" aria-label="Zoom in">+</button>' +
        '</div>';
      document.body.appendChild(dialog);
      stageHost = dialog.querySelector(".mermaid-lightbox__inner");

      /* Click outside the diagram (on the dialog's own padding) closes. */
      dialog.addEventListener("click", function (e) {
        if (e.target === dialog) dialog.close();
      });
      dialog.querySelector(".mermaid-lightbox__close").addEventListener("click", function () {
        dialog.close();
      });
      dialog.querySelectorAll(".mermaid-lightbox__controls button").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
          e.stopPropagation();
          var action = btn.getAttribute("data-action");
          if (action === "in") setZoom(zoom + zoomStep);
          else if (action === "out") setZoom(zoom - zoomStep);
          else setZoom(1);
        });
      });
      stageHost.addEventListener("wheel", function (e) {
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          setZoom(zoom + (e.deltaY < 0 ? zoomStep : -zoomStep));
        }
      }, { passive: false });
      dialog.addEventListener("close", function () {
        document.body.classList.remove("mermaid-lightbox-open");
        stageHost.innerHTML = "";
      });
      return dialog;
    }

    function setZoom(z) {
      zoom = Math.max(minZoom, Math.min(maxZoom, z));
      if (stageHost) stageHost.style.setProperty("--mermaid-zoom", zoom);
      if (dialog) {
        var resetBtn = dialog.querySelector('[data-action="reset"]');
        if (resetBtn) resetBtn.textContent = Math.round(zoom * 100) + "%";
      }
    }

    function open(wrapper) {
      /* Scoped to the diagram itself: the wrapper also holds the zoom-hint
         icon, and picking that up would zoom a magnifying glass. Two cases —
         a build-time SVG (take the variant currently shown, not the hidden
         one) or a runtime-rendered <pre class="mermaid">. */
      var svg;
      if (wrapper.classList.contains("mermaid-wrapper--static")) {
        var dark = document.documentElement.classList.contains("dark");
        svg = wrapper.querySelector(
          (dark ? ".mermaid-static--dark" : ".mermaid-static--light") + " svg"
        );
      } else {
        svg = wrapper.querySelector("pre.mermaid svg");
      }
      /* Clicked before the runtime arrived: load it, then open. Static
         diagrams never take this branch — their SVG is in the document. */
      if (!svg) {
        ensureRuntime(function () { open(wrapper); });
        return;
      }
      ensureDialog();
      stageHost.innerHTML = "";
      var stage = document.createElement("div");
      stage.className = "mermaid-lightbox__svg-stage";
      var clone = svg.cloneNode(true);
      clone.removeAttribute("style");
      clone.setAttribute("preserveAspectRatio", "xMidYMid meet");
      stage.appendChild(clone);
      stageHost.appendChild(stage);
      setZoom(1);
      document.body.classList.add("mermaid-lightbox-open");
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }

    Array.prototype.forEach.call(wrappers, function (w) {
      w.addEventListener("click", function () { open(w); });
      w.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open(w);
        }
      });
    });
  }

  /* ---- Blog list: tag filter chips --------------------------------- */
  function initBlogFilter() {
    var chips = document.querySelectorAll(".blog-filter-chip");
    if (!chips.length) return;
    var items = document.querySelectorAll("[data-tags]");
    var status = document.querySelector(".blog-filter-status");

    function known(filter) {
      for (var i = 0; i < chips.length; i++) {
        if (chips[i].getAttribute("data-filter") === filter) return true;
      }
      return false;
    }

    /* The filter lives in the URL, so a filtered view can be linked and the
       back button undoes it — the browser's own idea of "go back one step". */
    function fromURL() {
      var tag = new URL(window.location.href).searchParams.get("tag");
      return tag && known(tag) ? tag : "all";
    }

    function apply(filter, record) {
      var label = "";
      var shown = 0;

      chips.forEach(function (chip) {
        var active = chip.getAttribute("data-filter") === filter;
        chip.classList.toggle("is-active", active);
        chip.setAttribute("aria-pressed", active ? "true" : "false");
        if (active) label = (chip.firstChild && chip.firstChild.textContent || "").trim();
      });

      items.forEach(function (item) {
        var tags = (item.getAttribute("data-tags") || "").split(",");
        var match = filter === "all" || tags.indexOf(filter) !== -1;
        item.style.display = match ? "" : "none";
        if (match) shown++;
      });

      /* Screen readers get no signal from cards disappearing. */
      if (status) {
        status.textContent = shown + (shown === 1 ? " article" : " articles") +
          (filter === "all" ? "" : " tagged " + label);
      }

      if (record) {
        var url = new URL(window.location.href);
        if (filter === "all") url.searchParams.delete("tag");
        else url.searchParams.set("tag", filter);
        history.pushState({ tag: filter }, "", url);
      }
    }

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        apply(chip.getAttribute("data-filter"), true);
      });
    });

    window.addEventListener("popstate", function () { apply(fromURL(), false); });

    /* Restore a linked or bookmarked filter on load. */
    var initial = fromURL();
    if (initial !== "all") apply(initial, false);
  }

  /* ---- Giscus comments: follow the site's light/dark theme --------- */
  function initGiscusThemeSync() {
    if (!document.querySelector('script[src^="https://giscus.app"]')) return;
    var observer = new MutationObserver(function () {
      var isDark = document.documentElement.classList.contains("dark");
      var iframe = document.querySelector("iframe.giscus-frame");
      if (iframe) {
        iframe.contentWindow.postMessage(
          { giscus: { setConfig: { theme: isDark ? "noborder_dark" : "noborder_light" } } },
          "https://giscus.app"
        );
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  }

  function init() {
    initDialogs();
    initForms();
    initReadingProgress();
    initSearchHotkey();
    initMermaid();
    initBlogFilter();
    initGiscusThemeSync();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
