/* Repo status page (/status/) — open issues and pull requests across the
   user's public repositories, live from the GitHub search API.

   No token: the search API allows 10 unauthenticated requests a minute per
   IP and this page spends two per load (issues, then pull requests — one
   combined query would be cheaper, but GitHub is phasing out searches that
   leave the type open).

   "New" is relative to a timestamp in localStorage, set only by the
   "Mark all as seen" button, so reloading the page never swallows a badge.
   The same button records each package's Node-RED vote count, so a new
   rating shows up the same way. Storage can be unavailable (private mode,
   blocked site data); everything then still works, with the last 7 days
   standing in for "since last visit". */
(function () {
  "use strict";

  var root = document.querySelector(".repo-status[data-github-user]");
  if (!root) return;

  var USER = root.getAttribute("data-github-user");
  var API = "https://api.github.com/search/issues";
  var FALLBACK_DAYS = 7;
  var KEYS = {
    seen: "rs:lastSeen",
    votes: "rs:votes",
    cache: "rs:cache",
    hideBots: "rs:hideBots"
  };

  function load(key) {
    try { return JSON.parse(localStorage.getItem(key)); } catch (e) { return null; }
  }
  function save(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* no storage */ }
  }

  var state = {
    items: [],
    type: "all",
    repo: "all",
    hideBots: load(KEYS.hideBots) !== false,
    lastSeen: load(KEYS.seen),
    fetchedAt: null
  };

  var $ = function (sel) { return root.querySelector(sel); };
  var els = {
    meta: $("[data-rs-meta]"),
    list: $("[data-rs-list]"),
    repos: $("[data-rs-repos]"),
    botCount: $("[data-rs-bot-count]"),
    hideBots: $("[data-rs-hide-bots]"),
    refresh: $("[data-rs-refresh]"),
    seen: $("[data-rs-seen]")
  };

  /* ---- Time ------------------------------------------------------------ */
  function since() {
    return state.lastSeen
      ? new Date(state.lastSeen)
      : new Date(Date.now() - FALLBACK_DAYS * 864e5);
  }

  var rtf = typeof Intl !== "undefined" && Intl.RelativeTimeFormat
    ? new Intl.RelativeTimeFormat("en", { numeric: "auto" })
    : null;

  function ago(iso) {
    var secs = (new Date(iso) - Date.now()) / 1000;
    var steps = [[60, "second"], [60, "minute"], [24, "hour"], [7, "day"], [4.345, "week"], [12, "month"], [Infinity, "year"]];
    for (var i = 0; i < steps.length; i++) {
      if (Math.abs(secs) < steps[i][0]) {
        var n = Math.round(secs);
        return rtf ? rtf.format(n, steps[i][1]) : Math.abs(n) + " " + steps[i][1] + "s ago";
      }
      secs /= steps[i][0];
    }
    return "";
  }

  /* ---- Fetch ----------------------------------------------------------- */
  function search(kind) {
    var q = "user:" + USER + " is:open archived:false is:" + kind;
    var url = API + "?q=" + encodeURIComponent(q) + "&sort=updated&order=desc&per_page=100";
    return fetch(url, { headers: { Accept: "application/vnd.github+json" } }).then(function (res) {
      if (res.ok) return res.json();
      var reset = res.headers.get("x-ratelimit-reset");
      var err = new Error("GitHub answered " + res.status);
      if ((res.status === 403 || res.status === 429) && reset) {
        err.message = "GitHub rate limit reached — try again " + ago(new Date(reset * 1000).toISOString());
      }
      throw err;
    });
  }

  function normalise(raw, kind) {
    return {
      kind: kind,
      repo: raw.repository_url.split("/").pop(),
      number: raw.number,
      title: raw.title,
      url: raw.html_url,
      author: raw.user ? raw.user.login : "ghost",
      bot: !!raw.user && (raw.user.type === "Bot" || /\[bot\]$/.test(raw.user.login)),
      draft: !!raw.draft,
      comments: raw.comments,
      labels: (raw.labels || []).map(function (l) { return l.name; }),
      created: raw.created_at,
      updated: raw.updated_at
    };
  }

  function refresh() {
    els.refresh.disabled = true;
    els.meta.textContent = "Loading from GitHub…";
    Promise.all([search("issue"), search("pr")])
      .then(function (res) {
        var items = res[0].items.map(function (i) { return normalise(i, "issue"); })
          .concat(res[1].items.map(function (i) { return normalise(i, "pr"); }));
        var truncated = res[0].total_count > res[0].items.length || res[1].total_count > res[1].items.length;
        state.items = items;
        state.fetchedAt = new Date().toISOString();
        save(KEYS.cache, { items: items, fetchedAt: state.fetchedAt });
        render(truncated ? "Showing the 100 most recent of each type." : "");
      })
      .catch(function (err) {
        var cached = load(KEYS.cache);
        if (cached && cached.items) {
          state.items = cached.items;
          state.fetchedAt = cached.fetchedAt;
          render(err.message + ". Showing the copy from " + ago(cached.fetchedAt) + ".");
        } else {
          render(err.message + ".");
        }
      })
      .then(function () { els.refresh.disabled = false; });
  }

  /* ---- Render ---------------------------------------------------------- */
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function freshness(item) {
    var t = since();
    if (new Date(item.created) > t) return "new";
    if (new Date(item.updated) > t) return "updated";
    return "";
  }

  function render(note) {
    var pool = state.items.filter(function (i) { return !(state.hideBots && i.bot); });
    var bots = state.items.filter(function (i) { return i.bot; }).length;

    // Tiles follow the bot switch but not the type or repo filter: they
    // are the overview, the list below is the drill-down.
    var count = { new: 0, issue: 0, pr: 0 };
    pool.forEach(function (i) {
      count[i.kind]++;
      if (freshness(i)) count.new++;
    });
    Object.keys(count).forEach(function (k) {
      var node = root.querySelector('[data-rs-count="' + k + '"]');
      if (node) node.textContent = state.fetchedAt ? count[k] : "–";
    });
    els.botCount.textContent = bots ? "(" + bots + ")" : "";

    renderRepos(pool);

    var shown = pool.filter(function (i) {
      return (state.type === "all" || i.kind === state.type) &&
        (state.repo === "all" || i.repo === state.repo);
    }).sort(function (a, b) { return new Date(b.updated) - new Date(a.updated); });

    els.list.textContent = "";
    if (!shown.length && state.fetchedAt) {
      els.list.appendChild(el("li", "rs-empty", "Nothing open here."));
    }
    shown.forEach(function (i) { els.list.appendChild(row(i)); });

    var parts = [];
    if (state.fetchedAt) parts.push("Checked " + ago(state.fetchedAt) + ".");
    parts.push(state.lastSeen
      ? "Last marked as seen " + ago(state.lastSeen) + "."
      : "Nothing marked as seen in this browser yet — “new” means the last " + FALLBACK_DAYS + " days.");
    if (note) parts.push(note);
    els.meta.textContent = parts.join(" ");

    renderRatings();
  }

  function renderRepos(pool) {
    var counts = {};
    pool.forEach(function (i) {
      var c = counts[i.repo] || (counts[i.repo] = { total: 0, fresh: 0 });
      c.total++;
      if (freshness(i)) c.fresh++;
    });
    var names = Object.keys(counts).sort(function (a, b) {
      return counts[b].fresh - counts[a].fresh || counts[b].total - counts[a].total || a.localeCompare(b);
    });
    if (state.repo !== "all" && !counts[state.repo]) state.repo = "all";

    els.repos.textContent = "";
    [["all", pool.length, 0]].concat(names.map(function (n) {
      return [n, counts[n].total, counts[n].fresh];
    })).forEach(function (r) {
      var b = el("button", "rs-chip");
      b.type = "button";
      b.setAttribute("aria-pressed", String(state.repo === r[0]));
      b.appendChild(el("span", null, r[0] === "all" ? "All repos" : r[0].replace(/^node-red-contrib-/, "")));
      b.appendChild(el("span", "rs-chip__count", String(r[1])));
      if (r[2]) b.appendChild(el("span", "rs-chip__dot", null)).setAttribute("title", r[2] + " new or updated");
      b.addEventListener("click", function () { state.repo = r[0]; render(); });
      els.repos.appendChild(b);
    });
  }

  var ICONS = {
    issue: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"/><path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"/></svg>',
    pr: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"/></svg>'
  };

  function row(i) {
    var fresh = freshness(i);
    var li = el("li", "rs-item" + (fresh ? " rs-item--" + fresh : ""));

    var icon = el("span", "rs-item__icon rs-item__icon--" + i.kind);
    icon.innerHTML = ICONS[i.kind];
    icon.setAttribute("title", i.kind === "pr" ? "Pull request" : "Issue");
    li.appendChild(icon);

    var body = el("div", "rs-item__body");
    var head = el("div", "rs-item__head");
    var a = el("a", "rs-item__title", i.title);
    a.href = i.url;
    a.target = "_blank";
    a.rel = "noopener";
    head.appendChild(a);
    if (fresh) head.appendChild(el("span", "rs-badge rs-badge--" + fresh, fresh === "new" ? "New" : "Updated"));
    if (i.draft) head.appendChild(el("span", "rs-badge", "Draft"));
    i.labels.forEach(function (l) { head.appendChild(el("span", "rs-label", l)); });
    body.appendChild(head);

    var meta = el("div", "rs-item__meta");
    meta.appendChild(el("span", "rs-item__repo", i.repo.replace(/^node-red-contrib-/, "") + " #" + i.number));
    meta.appendChild(el("span", null, "by " + i.author));
    meta.appendChild(el("span", null, "opened " + ago(i.created)));
    if (i.updated !== i.created) meta.appendChild(el("span", null, "updated " + ago(i.updated)));
    if (i.comments) meta.appendChild(el("span", null, i.comments + " comment" + (i.comments === 1 ? "" : "s")));
    body.appendChild(meta);

    li.appendChild(body);
    return li;
  }

  /* Ratings are server-rendered; all that is left to do here is compare
     each vote count against the one recorded at the last "seen". */
  function renderRatings() {
    var seenVotes = load(KEYS.votes) || {};
    root.querySelectorAll("[data-rs-rating-pkg]").forEach(function (tr) {
      var pkg = tr.getAttribute("data-rs-rating-pkg");
      var now = Number(tr.getAttribute("data-rs-rating-count")) || 0;
      var before = seenVotes[pkg];
      var badge = tr.querySelector("[data-rs-rating-badge]");
      var diff = typeof before === "number" ? now - before : 0;
      badge.hidden = diff <= 0;
      badge.textContent = diff > 0 ? "+" + diff + " vote" + (diff === 1 ? "" : "s") : "";
    });
  }

  function currentVotes() {
    var votes = {};
    root.querySelectorAll("[data-rs-rating-pkg]").forEach(function (tr) {
      votes[tr.getAttribute("data-rs-rating-pkg")] = Number(tr.getAttribute("data-rs-rating-count")) || 0;
    });
    return votes;
  }

  function markSeen() {
    state.lastSeen = new Date().toISOString();
    save(KEYS.seen, state.lastSeen);
    save(KEYS.votes, currentVotes());
    render();
  }

  /* ---- Wiring ---------------------------------------------------------- */
  root.querySelectorAll("[data-rs-type]").forEach(function (b) {
    b.addEventListener("click", function () {
      state.type = b.getAttribute("data-rs-type");
      root.querySelectorAll("[data-rs-type]").forEach(function (o) {
        o.setAttribute("aria-pressed", String(o === b));
      });
      render();
    });
  });
  els.hideBots.checked = state.hideBots;
  els.hideBots.addEventListener("change", function () {
    state.hideBots = els.hideBots.checked;
    save(KEYS.hideBots, state.hideBots);
    render();
  });
  els.refresh.addEventListener("click", refresh);
  els.seen.addEventListener("click", markSeen);

  // First visit ever: start the vote baseline now, or no rating could ever
  // be reported as new without pressing the button first.
  if (load(KEYS.votes) === null && state.lastSeen === null) save(KEYS.votes, currentVotes());

  refresh();
})();
