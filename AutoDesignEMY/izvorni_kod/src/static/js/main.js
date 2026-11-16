/* Auto Design EMY – site behaviour (no dependencies) */
(function () {
  'use strict';
  var EMY = window.EMY || { root: '', lang: 'bs', labels: {} };
  var L = EMY.labels;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* When the site is opened straight from disk (file://), folder links need an explicit index.html */
  if (location.protocol === 'file:') {
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (/^(https?:|mailto:|tel:|viber:|#)/.test(h)) return;
      var parts = h.split('#');
      if (parts[0] === '' ) return;
      if (/\/$/.test(parts[0])) parts[0] += 'index.html';
      else if (/^(\.\.\/)*\.\.$|^\.$/.test(parts[0])) parts[0] += '/index.html';
      a.setAttribute('href', parts.join('#'));
    });
  }

  /* Header shadow on scroll */
  var header = document.querySelector('.site-header');
  function onScroll() { header && header.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* Mobile menu */
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('main-nav');
  function setMenu(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? toggle.dataset.labelClose : toggle.dataset.labelOpen);
    nav.classList.toggle('open', open);
    document.body.classList.toggle('nav-open', open);
  }
  if (toggle) {
    toggle.addEventListener('click', function () { setMenu(toggle.getAttribute('aria-expanded') !== 'true'); });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 960) setMenu(false); });
  }

  /* Language menu: close on outside click / Escape */
  var langMenu = document.querySelector('details.lang');
  document.addEventListener('click', function (e) { if (langMenu && langMenu.open && !langMenu.contains(e.target)) langMenu.open = false; });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (langMenu && langMenu.open) { langMenu.open = false; langMenu.querySelector('summary').focus(); }
    if (toggle && toggle.getAttribute('aria-expanded') === 'true') { setMenu(false); toggle.focus(); }
  });

  /* Reveal on scroll */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    reveals.forEach(function (el) { io.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add('in'); }); }

  /* Hero video: respect reduced motion, pause when off screen */
  var hv = document.querySelector('.hero-video');
  if (hv) {
    if (reduceMotion) { hv.removeAttribute('autoplay'); hv.pause(); }
    else if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) {
        en.forEach(function (x) { if (x.isIntersecting) { var p = hv.play(); if (p && p.catch) p.catch(function () {}); } else hv.pause(); });
      }).observe(hv);
    }
  }

  /* ---------- Gallery ---------- */
  var items = [];
  try { items = JSON.parse(document.getElementById('gallery-data').textContent || '[]'); } catch (e) { items = []; }
  var containers = document.querySelectorAll('[data-gallery]');

  function catLabel(c) { return (L.cats && L.cats[c]) || ''; }
  function caption(it) { return (it.caption && (it.caption[EMY.lang] || '')) || ''; }
  function altText(it) { return caption(it) || (catLabel(it.cat) + ' – Auto Design EMY'); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function listFor(kind) { return kind === 'featured' ? items.filter(function (i) { return i.featured; }).slice(0, 6) : items; }

  function tileHTML(it, idx) {
    var cap = caption(it);
    return '<button class="tile" type="button" data-index="' + idx + '" data-cat="' + esc(it.cat) + '" data-type="' + esc(it.type) + '" aria-label="' +
      esc(L.open + ': ' + altText(it) + (it.type === 'video' ? ' (' + L.video + ')' : '')) + '">' +
      '<img src="' + esc(EMY.root + it.thumb) + '" alt="" loading="lazy" decoding="async" width="' + (it.w || 720) + '" height="' + (it.h || 900) + '">' +
      (it.type === 'video' ? '<span class="tile-play" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="M3 1.5v13l11-6.5z"/></svg></span>' : '') +
      (cap ? '<span class="tile-cap" aria-hidden="true">' + esc(cap) + '</span>' : '') + '</button>';
  }
  function render() {
    containers.forEach(function (c) {
      c.innerHTML = listFor(c.dataset.gallery).map(tileHTML).join('');
    });
    applyFilter(currentFilter);
  }

  /* Filters */
  var currentFilter = 'all';
  var emptyMsg = document.querySelector('.empty');
  function matches(it, f) { return f === 'all' || (f === 'videos' ? it.type === 'video' : it.cat === f); }
  function applyFilter(f) {
    currentFilter = f;
    var grid = document.querySelector('[data-gallery="all"]');
    if (!grid) return;
    var shown = 0;
    grid.querySelectorAll('.tile').forEach(function (t) {
      var it = items[+t.dataset.index]; var ok = it && matches(it, f);
      t.hidden = !ok; if (ok) shown++;
    });
    if (emptyMsg) emptyMsg.hidden = shown > 0;
    document.querySelectorAll('.filter').forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.filter === f ? 'true' : 'false'); });
  }
  document.querySelectorAll('.filter').forEach(function (b) { b.addEventListener('click', function () { applyFilter(b.dataset.filter); }); });

  /* Fresh data (admin uploads) – falls back to the copy embedded in the page */
  if (containers.length && location.protocol !== 'file:' && window.fetch) {
    fetch(EMY.root + 'data/gallery.json?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) { if (Array.isArray(d)) { items = d; render(); } })
      .catch(function () {});
  }

  /* Lightbox */
  var lb = document.getElementById('lightbox');
  var lbList = [], lbIdx = 0, lastFocus = null, touchX = null;
  function lbShow(i) {
    if (!lbList.length) return;
    lbIdx = (i + lbList.length) % lbList.length;
    var it = lbList[lbIdx], stage = lb.querySelector('.lb-stage');
    stage.innerHTML = '';
    var el;
    if (it.type === 'video') {
      el = document.createElement('video');
      el.src = EMY.root + it.src; el.poster = EMY.root + it.thumb; el.controls = true; el.playsInline = true; el.autoplay = !reduceMotion; el.muted = false;
      el.setAttribute('playsinline', '');
    } else {
      el = document.createElement('img');
      el.src = EMY.root + (it.full || it.thumb); el.alt = altText(it);
      var nx = lbList[(lbIdx + 1) % lbList.length]; if (nx && nx.type !== 'video') { var pre = new Image(); pre.src = EMY.root + (nx.full || nx.thumb); }
    }
    stage.appendChild(el);
    lb.querySelector('.lb-cap').textContent = caption(it);
    lb.querySelector('.lb-count').textContent = (lbIdx + 1) + ' / ' + lbList.length;
  }
  function lbOpen(list, i) {
    if (!lb) return;
    lbList = list; lastFocus = document.activeElement;
    if (lb.showModal) lb.showModal(); else lb.setAttribute('open', '');
    document.body.style.overflow = 'hidden';
    lbShow(i);
    lb.querySelector('.lb-close').focus();
  }
  function lbClose() {
    var v = lb.querySelector('video'); if (v) v.pause();
    lb.querySelector('.lb-stage').innerHTML = '';
    if (lb.close) lb.close(); else lb.removeAttribute('open');
    document.body.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }
  if (lb) {
    document.addEventListener('click', function (e) {
      var t = e.target.closest('.tile'); if (!t) return;
      var c = t.closest('[data-gallery]');
      var list = listFor(c.dataset.gallery);
      if (c.dataset.gallery === 'all') {
        var visible = list.filter(function (it) { return matches(it, currentFilter); });
        lbOpen(visible, visible.indexOf(list[+t.dataset.index]));
      } else lbOpen(list, +t.dataset.index);
    });
    lb.querySelector('.lb-close').addEventListener('click', lbClose);
    lb.querySelector('.lb-prev').addEventListener('click', function () { lbShow(lbIdx - 1); });
    lb.querySelector('.lb-next').addEventListener('click', function () { lbShow(lbIdx + 1); });
    lb.addEventListener('cancel', function (e) { e.preventDefault(); lbClose(); });
    lb.addEventListener('keydown', function (e) {
      var rtl = document.documentElement.dir === 'rtl';
      if (e.key === 'ArrowRight') lbShow(lbIdx + (rtl ? -1 : 1));
      if (e.key === 'ArrowLeft') lbShow(lbIdx + (rtl ? 1 : -1));
    });
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.classList.contains('lb-stage')) lbClose(); });
    lb.addEventListener('touchstart', function (e) { touchX = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (touchX === null) return; var dx = e.changedTouches[0].clientX - touchX; touchX = null;
      if (Math.abs(dx) > 50) lbShow(lbIdx + (dx < 0 ? 1 : -1) * (document.documentElement.dir === 'rtl' ? -1 : 1));
    });
  }

  /* Map: loaded only on request (privacy + speed) */
  var mapBtn = document.querySelector('[data-map-src]');
  if (mapBtn) mapBtn.addEventListener('click', function () {
    var f = document.createElement('iframe');
    f.src = mapBtn.dataset.mapSrc; f.title = mapBtn.dataset.mapTitle; f.loading = 'lazy'; f.referrerPolicy = 'no-referrer-when-downgrade';
    var m = document.getElementById('map'); m.innerHTML = ''; m.appendChild(f);
  });

  /* Enquiry form -> WhatsApp / Viber */
  var form = document.getElementById('enquiry');
  if (form) {
    var status = form.querySelector('.form-status');
    function field(n) { return form.elements[n]; }
    function validate() {
      var ok = true;
      ['name', 'service'].forEach(function (n) {
        var el = field(n), bad = !el.value.trim(), err = document.getElementById('e-' + n);
        el.setAttribute('aria-invalid', bad ? 'true' : 'false'); err.hidden = !bad;
        if (bad && ok) { el.focus(); ok = false; }
      });
      return ok;
    }
    function message() {
      var lines = [L.msgHello, '', L.name + ': ' + field('name').value.trim()];
      if (field('vehicle').value.trim()) lines.push(L.vehicle + ': ' + field('vehicle').value.trim());
      lines.push(L.service + ': ' + field('service').value);
      if (field('message').value.trim()) lines.push('', field('message').value.trim());
      return lines.join('\n');
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault(); status.textContent = '';
      if (!validate()) return;
      window.open('https://wa.me/' + form.dataset.wa + '?text=' + encodeURIComponent(message()), '_blank', 'noopener');
    });
    document.getElementById('copy-viber').addEventListener('click', function () {
      if (!validate()) return;
      var txt = message();
      var done = function () { status.textContent = L.copied; setTimeout(function () { location.href = 'viber://chat?number=%2B' + form.dataset.wa; }, 600); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(txt).then(done, done);
      else { var ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (x) {} ta.remove(); done(); }
    });
    form.addEventListener('input', function (e) { if (e.target.getAttribute('aria-invalid') === 'true' && e.target.value.trim()) { e.target.setAttribute('aria-invalid', 'false'); var er = document.getElementById('e-' + e.target.name); if (er) er.hidden = true; } });
  }
})();
