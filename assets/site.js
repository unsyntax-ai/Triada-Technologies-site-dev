(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // Top bar: frosted and transparent once the page is scrolled
  var header = document.querySelector('header.site');
  function onScroll() {
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Fade sections and cards in as they enter the screen
  var targets = document.querySelectorAll('main section > .wrap, main .hero-grid, main .page-hero .wrap, main .card, main .marquee');
  targets.forEach(function (el, i) { el.classList.add('reveal'); el.style.transitionDelay = ((i % 3) * 90) + 'ms'; });
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    targets.forEach(function (el) { io.observe(el); });
  } else {
    targets.forEach(function (el) { el.classList.add('in'); });
  }


  // Share buttons (insight articles, job pages): the phone's share sheet where there is one, otherwise copy the link
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('[data-share]') : null;
    if (!b) return;
    e.preventDefault();
    var canon = document.querySelector('link[rel="canonical"]');
    var url = (canon && canon.href) || location.href, label = b.querySelector('span');
    var said = function (t) {
      if (!label) return;
      var was = label.getAttribute('data-was') || label.textContent;
      label.setAttribute('data-was', was); label.textContent = t;
      setTimeout(function () { label.textContent = was; }, 1800);
    };
    if (navigator.share) { navigator.share({ title: document.title, url: url }).catch(function () { /* cancelled */ }); return; }
    var fallback = function () {
      var t = document.createElement('textarea'); t.value = url; t.style.position = 'fixed'; t.style.opacity = '0';
      document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); said('Link copied'); } catch (err) { said('Copy the page address'); }
      t.remove();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { said('Link copied'); }, fallback);
    else fallback();
  });

  // Home opening sequence: plain background, two full-width logo bars slide in from opposite sides, part vertically to
  // reveal the page, the hero settles in, and the upper bar thins to a line that stays at the top.
  // Only transform and opacity are animated, and it waits for the page to finish loading so frames do not drop.
  var intro = document.getElementById('opening');
  if (intro && root.classList.contains('intro-on') && intro.animate) {
    var barA = intro.querySelector('.opening-bar.a'), barB = intro.querySelector('.opening-bar.b');
    var panelTop = intro.querySelector('.opening-top'), panelBottom = intro.querySelector('.opening-bottom');
    var W = intro.clientWidth, H = intro.clientHeight;
    var BW = Math.round(W * 1.1), off = -Math.round(W * 0.05);   // a little wider than the screen so the bars' slanted ends sit off-screen
    barA.style.width = barB.style.width = BW + 'px';
    barA.style.left = barB.style.left = off + 'px';
    var T = barA.offsetHeight;
    var gap = Math.round(T * 0.66);              // the gap between the two bars in the logo
    barA.style.top = Math.round(H / 2 - gap / 2 - T) + 'px';
    barB.style.top = Math.round(H / 2 + gap / 2) + 'px';
    var running = [], ended = false;
    var move = function (el, from, to, opts) {
      var a = el.animate([from, to], Object.assign({ fill: 'both' }, opts));
      running.push(a);
      return a.finished;
    };
    var pause = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var frame = function () { return new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); }); };
    var xy = function (x, y) { return { transform: 'translate3d(' + x + 'px,' + y + 'px,0)' }; };
    var finish = function () {
      if (ended) return;
      ended = true;
      running.forEach(function (a) { try { a.cancel(); } catch (e) { /* ignore */ } });
      root.classList.remove('intro-on');          // the hero is shown, and the permanent top line takes the bar's place
      intro.remove();
    };
    intro.addEventListener('click', finish);
    window.addEventListener('keydown', finish, { once: true });

    var slide = 'cubic-bezier(.65,0,.35,1)', part = 'cubic-bezier(.45,0,.15,1)';
    var loaded = new Promise(function (r) { if (document.readyState === 'complete') r(); else window.addEventListener('load', r, { once: true }); });
    Promise.race([loaded, pause(2500)]).then(frame).then(function () {
      if (ended) return;
      return Promise.all([
        move(barA, xy(-BW, 0), xy(0, 0), { duration: 650, easing: slide }),
        move(barB, xy(BW, 0), xy(0, 0), { duration: 650, easing: slide })
      ]);
    }).then(function () {
      return pause(100);
    }).then(function () {
      if (ended) return;
      var up = -Math.round(H / 2 - gap / 2 - T);     // the upper bar rises until it touches the top edge
      var down = Math.round(H / 2 + gap / 2 + T) + 6;  // the lower bar leaves through the bottom
      setTimeout(function () { root.classList.add('intro-reveal'); }, 250);
      return Promise.all([
        move(barA, xy(0, 0), xy(0, up), { duration: 750, easing: part }),
        move(panelTop, xy(0, 0), xy(0, -Math.round(H / 2) - 6), { duration: 750, easing: part }),
        move(barB, xy(0, 0), xy(0, down), { duration: 750, easing: part }),
        move(panelBottom, xy(0, 0), xy(0, Math.round(H / 2) + 6), { duration: 750, easing: part })
      ]);
    }).then(function () {
      if (ended) return;
      var thin = 1 / T;                               // the upper bar thins to the permanent 1px line
      return move(barA, { transform: 'translate3d(0,' + up2() + 'px,0) scaleY(1)' }, { transform: 'translate3d(0,' + up2() + 'px,0) scaleY(' + thin + ')' }, { duration: 400, easing: 'cubic-bezier(.4,0,.2,1)' });
    }).then(function () {
      return pause(80);
    }).then(finish);
    var up2 = function () { return -Math.round(H / 2 - gap / 2 - T); };
  }

  // Home page only: scroll-linked motion (parallax hero, stagger)
  var hero = document.querySelector('.hero-full');
  if (hero && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    root.classList.add('home-motion');
    document.body.classList.add('home-motion');
    var ticking = false;
    var step = function () {
      var y = window.scrollY, h = hero.offsetHeight || 1;
      var p = Math.min(1, Math.max(0, y / h));
      hero.style.setProperty('--p', p.toFixed(3));
      ticking = false;
    };
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(step); } }, { passive: true });
    window.addEventListener('resize', step);
    step();
    // cards in a row arrive one after another
    document.querySelectorAll('.values, .trio, .industries, .steps').forEach(function (g) {
      Array.prototype.forEach.call(g.querySelectorAll('.card'), function (c, i) { c.style.transitionDelay = (i * 140) + 'ms'; });
    });
  }

  // FAQ accordion: a row opens downward and closes upward with a smooth height change
  Array.prototype.forEach.call(document.querySelectorAll('.faq-item'), function (d) {
    var sum = d.querySelector('summary'), body = d.querySelector('.faq-a'), anim = null;
    sum.addEventListener('click', function (e) {
      if (!d.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;   // plain open/close
      e.preventDefault();
      if (anim) anim.cancel();
      var edge = d.offsetHeight - d.clientHeight, from = d.offsetHeight, opening = !d.open;
      if (opening) d.open = true;
      var to = sum.offsetHeight + (opening ? body.offsetHeight : 0) + edge;
      d.style.overflow = 'hidden';
      anim = d.animate({ height: [from + 'px', to + 'px'] }, { duration: 360, easing: 'cubic-bezier(.2,.7,.2,1)' });
      anim.onfinish = function () { if (!opening) d.open = false; anim = null; d.style.overflow = ''; };
      anim.oncancel = function () { d.style.overflow = ''; };
    });
  });

  // Insights lists: search, date filter, sort, load more
  var list = document.getElementById('items');
  if (list) {
    var q = document.getElementById('q');
    var mo = document.getElementById('month');
    var so = document.getElementById('sort');
    var more = document.getElementById('more');
    var empty = document.getElementById('empty');
    var pageSize = parseInt(list.closest('.listing').getAttribute('data-page'), 10) || 9;
    var items = Array.prototype.slice.call(list.querySelectorAll('[data-item]'));
    var shown = pageSize;
    // the words a reader can see on each row, kept so they can be re-marked on every search
    var marks = items.map(function (el) {
      var t = Array.prototype.slice.call(el.querySelectorAll('h3 a, .meta'));
      if (!t.length) t = Array.prototype.slice.call(el.querySelectorAll('a, span'));
      return t.map(function (n) { return [n, n.textContent]; });
    });
    var mark = function (node, text, term) {
      node.textContent = '';
      var lower = text.toLowerCase(), at, i = 0;
      if (!term || lower.length !== text.length) { node.textContent = text; return; }
      while ((at = lower.indexOf(term, i)) !== -1) {
        if (at > i) node.appendChild(document.createTextNode(text.slice(i, at)));
        var m = document.createElement('mark');
        m.className = 'hit';
        m.textContent = text.slice(at, at + term.length);
        node.appendChild(m);
        i = at + term.length;
      }
      node.appendChild(document.createTextNode(text.slice(i)));
    };
    var render = function () {
      var term = q.value.trim().toLowerCase();
      var month = mo.value;
      var oldest = so.value === 'old';
      items.forEach(function (el, k) {
        marks[k].forEach(function (p) { mark(p[0], p[1], term); });
      });
      items.sort(function (a, b) {
        var x = a.getAttribute('data-date'), y = b.getAttribute('data-date');
        return oldest ? (x < y ? -1 : x > y ? 1 : 0) : (x < y ? 1 : x > y ? -1 : 0);
      });
      var match = 0;
      items.forEach(function (el) {
        list.appendChild(el);
        var ok = (!month || el.getAttribute('data-date').slice(0, 7) === month) &&
                 (!term || el.getAttribute('data-text').indexOf(term) !== -1);
        if (ok) { match++; el.hidden = match > shown; } else { el.hidden = true; }
      });
      empty.hidden = match !== 0;
      more.hidden = match <= shown;
    };
    [q, mo, so].forEach(function (c) {
      c.addEventListener(c === q ? 'input' : 'change', function () { shown = pageSize; render(); });
    });
    more.addEventListener('click', function () { shown += pageSize; render(); });
    render();
  }

  // Contact form: tells the visitor exactly which entry is missing or not valid, right beside the field
  var form = document.getElementById('contact-form');
  if (form) {
    var status = document.getElementById('form-status');
    var rules = {
      name: function (v) {
        if (!v) return 'Enter your full name.';
        if (v.length < 2) return 'That name looks too short. Enter your full name.';
        if (!/[A-Za-zÀ-ɏ]/.test(v)) return 'Your name should include letters.';
        return '';
      },
      email: function (v) {
        if (!v) return 'Enter your email address.';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return 'Enter a valid email address, like name@company.com.';
        return '';
      },
      phone: function (v) {
        if (!v) return '';   // optional
        if (!/^\+?[\d\s().-]+$/.test(v)) return 'Use digits, spaces and + ( ) - only, for example (814) 555-0123.';
        var d = v.replace(/\D/g, '');
        if (d.length < 10 || d.length > 15) return 'Enter the full phone number with area code, or leave this empty.';
        return '';
      },
      message: function (v) {
        if (!v) return 'Write a short message so we know how to help.';
        if (v.length < 10) return 'Add a little more detail (at least 10 characters).';
        if (v.length > 2000) return 'Shorten your message to 2000 characters or fewer.';
        return '';
      }
    };
    var show = function (field, text) {
      var input = form.elements[field], err = document.getElementById(field + '-error');
      if (text) { input.setAttribute('aria-invalid', 'true'); err.textContent = text; err.hidden = false; }
      else { input.removeAttribute('aria-invalid'); err.textContent = ''; err.hidden = true; }
      return !text;
    };
    var check = function (field) { return show(field, rules[field](form.elements[field].value.trim())); };
    Object.keys(rules).forEach(function (field) {
      var input = form.elements[field];
      input.addEventListener('blur', function () { if (input.value.trim() || input.getAttribute('aria-invalid')) check(field); });
      input.addEventListener('input', function () {
        if (input.getAttribute('aria-invalid')) check(field);   // clears the message as soon as the entry is fixed
        status.textContent = ''; status.className = '';
      });
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var bad = Object.keys(rules).filter(function (field) { return !check(field); });
      if (bad.length) {
        status.className = 'is-error';
        status.textContent = bad.length === 1 ? 'Please fix the entry marked below.' : 'Please fix the ' + bad.length + ' entries marked below.';
        form.elements[bad[0]].focus();
        return;
      }
      status.className = 'is-ok';
      status.textContent = 'Preview only. The form is not connected yet, so nothing was sent.';
    });
  }
})();
