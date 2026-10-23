/* ==========================================================
   Solar AM Notes - 共通スクリプト
   ・ナビゲーション生成（ページ一覧はここで一元管理）
   ・目次の自動生成 / スクロール連動ハイライト
   ・読了プログレスバー / トップへ戻る / 表示アニメーション
   ・用語集の検索・カテゴリ絞り込み
   ========================================================== */
(function () {
  "use strict";

  // ---- ページ一覧（追加・並べ替えはここだけ編集すればOK） ----
  var PAGES = [
    { id: "news",        file: "notes/news.html",        label: "最新ニュース" },
    { id: "performance", file: "notes/performance.html", label: "発電性能" },
    { id: "om",          file: "notes/om.html",          label: "O&M" },
    { id: "policy",      file: "notes/policy.html",      label: "制度・市場" },
    { id: "finance",     file: "notes/finance.html",     label: "ファイナンス" },
    { id: "electrical",  file: "notes/electrical.html",  label: "電気設備" },
    { id: "legal",       file: "notes/legal.html",       label: "法令・契約" },
    { id: "glossary",    file: "notes/glossary.html",    label: "用語集" }
  ];

  var body = document.body;
  var root = body.getAttribute("data-root") || "";
  var current = body.getAttribute("data-page") || "home";

  // ---- ナビゲーション ----
  var nav = document.getElementById("site-nav");
  if (nav) {
    var html = '<a href="' + root + 'index.html"' + (current === "home" ? ' class="active"' : "") + ">ホーム</a>";
    PAGES.forEach(function (p) {
      html += '<a href="' + root + p.file + '"' + (current === p.id ? ' class="active" aria-current="page"' : "") + ">" + p.label + "</a>";
    });
    nav.innerHTML = html;
  }

  var toggle = document.getElementById("nav-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (nav) {
      nav.addEventListener("click", function (e) {
        if (e.target.tagName === "A") body.classList.remove("nav-open");
      });
    }
  }

  // ---- 前後ページのリンク ----
  var pager = document.getElementById("pager");
  if (pager) {
    var idx = -1;
    PAGES.forEach(function (p, i) { if (p.id === current) idx = i; });
    if (idx >= 0) {
      var out = "";
      if (idx > 0) {
        var pv = PAGES[idx - 1];
        out += '<a class="prev" href="' + root + pv.file + '"><small>← 前のノート</small>' + pv.label + "</a>";
      }
      if (idx < PAGES.length - 1) {
        var nx = PAGES[idx + 1];
        out += '<a class="next" href="' + root + nx.file + '"><small>次のノート →</small>' + nx.label + "</a>";
      }
      pager.innerHTML = out;
    }
  }

  // ---- 目次の自動生成 ----
  var tocList = document.getElementById("toc-list");
  var sections = document.querySelectorAll(".prose > section[id]");
  if (tocList && sections.length) {
    var t = "";
    sections.forEach(function (s) {
      var h = s.querySelector("h2");
      if (h) t += '<li><a href="#' + s.id + '">' + h.textContent + "</a></li>";
    });
    tocList.innerHTML = t;

    var toc = document.getElementById("toc");
    // スマホでは初期状態で閉じる
    if (toc && window.matchMedia("(max-width: 960px)").matches) toc.removeAttribute("open");
    tocList.addEventListener("click", function () {
      if (toc && window.matchMedia("(max-width: 960px)").matches) toc.removeAttribute("open");
    });

    if ("IntersectionObserver" in window) {
      var links = tocList.querySelectorAll("a");
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            links.forEach(function (a) {
              a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id);
            });
          }
        });
      }, { rootMargin: "-20% 0px -70% 0px" });
      sections.forEach(function (s) { spy.observe(s); });
    }
  }

  // ---- 読了プログレス / トップへ戻る ----
  var bar = document.getElementById("progress");
  var toTop = document.getElementById("to-top");
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = h.scrollTop || body.scrollTop;
    if (bar) bar.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
    if (toTop) toTop.classList.toggle("show", y > 600);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

  // ---- 表示アニメーション ----
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // ---- カードのマウス追従グロー ----
  document.querySelectorAll(".card").forEach(function (c) {
    c.addEventListener("pointermove", function (e) {
      var r = c.getBoundingClientRect();
      c.style.setProperty("--mx", (e.clientX - r.left) + "px");
      c.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  // ---- 表をスクロール可能なラッパーで包む ----
  document.querySelectorAll(".prose table").forEach(function (tb) {
    if (tb.parentElement.classList.contains("table-wrap")) return;
    var w = document.createElement("div");
    w.className = "table-wrap";
    tb.parentNode.insertBefore(w, tb);
    w.appendChild(tb);
  });

  // ---- 用語集：検索とカテゴリ絞り込み ----
  var q = document.getElementById("term-search");
  var terms = document.querySelectorAll(".term");
  if (q && terms.length) {
    var chips = document.querySelectorAll(".chip");
    var countEl = document.getElementById("term-count");
    var emptyEl = document.getElementById("term-empty");
    var cat = "all";

    function norm(s) {
      // 全角英数→半角、カタカナ→ひらがな、小文字化
      return s.replace(/[Ａ-Ｚａ-ｚ０-９]/g, function (ch) { return String.fromCharCode(ch.charCodeAt(0) - 0xFEE0); })
              .replace(/[\u30a1-\u30f6]/g, function (ch) { return String.fromCharCode(ch.charCodeAt(0) - 0x60); })
              .toLowerCase();
    }
    function apply() {
      var kw = norm(q.value.trim());
      var n = 0;
      terms.forEach(function (el) {
        var okCat = cat === "all" || el.getAttribute("data-cat") === cat;
        var okKw = !kw || norm(el.textContent).indexOf(kw) !== -1;
        var show = okCat && okKw;
        el.style.display = show ? "" : "none";
        if (show) n++;
      });
      if (countEl) countEl.textContent = n + " 件の用語";
      if (emptyEl) emptyEl.style.display = n ? "none" : "block";
    }
    q.addEventListener("input", apply);
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("active"); });
        c.classList.add("active");
        cat = c.getAttribute("data-filter");
        apply();
      });
    });
    apply();
  }

  // ---- 最新ニュース：非同期読み込み・検索・カテゴリ絞り込み ----
  var newsContainer = document.getElementById("news-cards");
  if (newsContainer) {
    var newsSearch = document.getElementById("news-search");
    var newsChips = document.querySelectorAll(".news-chip");
    var newsCount = document.getElementById("news-count");
    var newsUpdated = document.getElementById("news-updated");
    var newsEmpty = document.getElementById("news-empty");
    var newsItems = [];
    var currentNewsCat = "all";

    var catLabels = {
      meti: "経産省・エネ庁",
      policy: "制度・法改正・条例",
      market: "市場・出力制御・PPA",
      finance: "投資・ファイナンス",
      om_tech: "O&M・保安・事故",
      industry: "業界・技術"
    };

    function escapeHtml(s) {
      if (!s) return "";
      return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function renderNews() {
      var kw = newsSearch ? newsSearch.value.trim().toLowerCase() : "";
      var filtered = newsItems.filter(function (it) {
        var matchCat = currentNewsCat === "all" || it.category === currentNewsCat;
        var text = (it.title + " " + it.summary + " " + it.source).toLowerCase();
        var matchKw = !kw || text.indexOf(kw) !== -1;
        return matchCat && matchKw;
      });

      if (newsCount) newsCount.textContent = filtered.length + " 件の記事";
      if (newsEmpty) newsEmpty.style.display = filtered.length ? "none" : "block";

      var html = "";
      filtered.forEach(function (it) {
        var catName = catLabels[it.category] || "情報";
        var featTag = it.featured ? '<span class="news-featured-tag">★ 注目トピック</span>' : '';
        var linkTag = it.link
          ? '<a href="' + escapeHtml(it.link) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(it.title) +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg></a>'
          : escapeHtml(it.title);

        html += '<article class="news-card">' +
                  '<div class="news-meta-row">' +
                    featTag +
                    '<span class="news-cat cat-' + escapeHtml(it.category) + '">' + escapeHtml(catName) + '</span>' +
                    '<span class="news-source">' + escapeHtml(it.source) + '</span>' +
                    '<span class="news-date">' + escapeHtml(it.date) + '</span>' +
                  '</div>' +
                  '<h3 class="news-title">' + linkTag + '</h3>' +
                  (it.summary ? '<p class="news-summary">' + escapeHtml(it.summary) + '</p>' : '') +
                '</article>';
      });
      newsContainer.innerHTML = html;
    }

    fetch(root + "data/news.json")
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        if (data.updated_at && newsUpdated) {
          newsUpdated.textContent = "最終更新: " + data.updated_at;
        }
        newsItems = data.items || [];
        renderNews();
      })
      .catch(function (err) {
        console.warn("ニュース読み込みエラー:", err);
        newsContainer.innerHTML = '<p style="color:var(--text-sub);padding:20px;">最新ニュースの取得中またはオフラインです。上の公的機関リンク集から最新情報をご確認いただけます。</p>';
      });

    if (newsSearch) newsSearch.addEventListener("input", renderNews);
    newsChips.forEach(function (c) {
      c.addEventListener("click", function () {
        newsChips.forEach(function (x) { x.classList.remove("active"); });
        c.classList.add("active");
        currentNewsCat = c.getAttribute("data-filter");
        renderNews();
      });
    });
  }
})();
