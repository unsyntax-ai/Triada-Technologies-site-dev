// Admin page: 6-digit PIN to open (checked on the server), email code as the backup, then drafting, publishing and job management.
(function () {
  var T = window.TRIADA;
  var $ = function (id) { return document.getElementById(id); };
  var session = null;     // admin session, kept in memory only: closing or reloading the page asks for the PIN again
  var unlocked = false;   // true only after the PIN was accepted on this visit (or a new PIN was just saved)
  var gate = 'pin';       // which sign-in panel shows: 'pin' | 'email' | 'reset' | 'done'
  var jobsLoaded = false; // the jobs list has been fetched for this sign-in
  var busy = false;
  var editing = null;      // job being edited, or null for a new one
  var jobs = [];
  var tab = 'published';   // jobs table tab: 'published' | 'draft' | 'archived'
  var page = 1;
  var searchAll = true;    // while searching, show matches from every tab
  var PER_PAGE = 5;
  var KEEP_DAYS = 365;     // archived jobs are deleted for good after this many days
  var resetEmail = '';
  var OBVIOUS = ['123456', '234567', '345678', '456789', '567890', '654321', '987654'];

  // ----- session -----
  function load() { return session; }
  function save(s) { session = s; }
  function now() { return Math.floor(Date.now() / 1000); }
  function signOut() {
    save(null); unlocked = false; jobsLoaded = false; gate = 'pin';
    ['a-pin', 'a-code', 'a-new-pin', 'a-confirm-pin'].forEach(function (id) { clearBoxes($(id)); });
    show();
  }

  // the email sign-in link (if used) lands here with the session in the address
  function takeHash() {
    if (!location.hash || location.hash.length < 2) return null;
    var p = new URLSearchParams(location.hash.slice(1));
    history.replaceState(null, '', location.pathname);
    if (p.get('error_description')) return { error: p.get('error_description').replace(/\+/g, ' ') };
    if (p.get('access_token')) {
      save({ access_token: p.get('access_token'), refresh_token: p.get('refresh_token'), expires_at: now() + (parseInt(p.get('expires_in'), 10) || 3600) });
      return { emailSignIn: true };
    }
    return null;
  }
  function handleHash(pr) {
    if (!pr) return;
    if (pr.emailSignIn) { gate = 'reset'; }
    else { gate = 'email'; msg('a-msg', pr.error + ' Request a new code.', 'bad'); }
  }

  function token() {
    var s = load();
    if (!s) return Promise.reject(new Error('Signed out'));
    if (s.expires_at - now() > 60) return Promise.resolve(s.access_token);
    return fetch(T.url + '/auth/v1/token?grant_type=refresh_token', {
      method: 'POST', headers: { apikey: T.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: s.refresh_token })
    }).then(function (r) { if (!r.ok) throw new Error('expired'); return r.json(); })
      .then(function (d) {
        save({ access_token: d.access_token, refresh_token: d.refresh_token, expires_at: now() + (d.expires_in || 3600) });
        return d.access_token;
      })
      .catch(function () { signOut(); throw new Error('Signed out'); });
  }

  function api(path, opts) {
    return token().then(function (t) {
      opts = opts || {};
      opts.headers = Object.assign({ apikey: T.key, Authorization: 'Bearer ' + t, 'Content-Type': 'application/json' }, opts.headers || {});
      return fetch(T.url + path, opts);
    }).then(function (r) {
      if (r.status === 401) { signOut(); throw new Error('Please sign in again.'); }
      return r.text().then(function (x) {
        var data = null;
        try { data = x ? JSON.parse(x) : null; } catch (e) { /* ignore */ }
        if (!r.ok) throw new Error((data && (data.error || data.message)) || 'Something went wrong (' + r.status + ').');
        return data;
      });
    });
  }

  function msg(id, text, kind) {
    var n = $(id);
    n.textContent = text || '';
    n.className = 'a-msg' + (kind ? ' ' + kind : '');
  }

  // ----- views -----
  function show() {
    var open = unlocked && !!load();
    $('a-signin').hidden = open;
    $('a-app').hidden = !open;
    $('a-out').hidden = !open;
    $('a-gate-pin').hidden = gate !== 'pin';
    $('a-gate-email').hidden = gate !== 'email';
    $('a-gate-reset').hidden = gate !== 'reset';
    $('a-gate-done').hidden = gate !== 'done';
    // after an email-link sign-in the code is already checked, so only the new PIN is asked for
    $('a-sect-code').hidden = !!load();
    if (open) { if (!jobsLoaded) refresh(); } else focusGate();
  }
  function focusGate() {
    if (gate === 'pin') focusFirst($('a-pin'));
    else if (gate === 'email') $('a-email').focus();
    else if (gate === 'reset') focusFirst(load() ? $('a-new-pin') : $('a-code'));
  }

  // six single-digit boxes: type, paste, backspace and arrows work; completing the sixth calls onComplete
  function boxes(root) { return Array.prototype.slice.call(root.querySelectorAll('input')); }
  function code(root) { return boxes(root).map(function (b) { return b.value; }).join(''); }
  function clearBoxes(root) { boxes(root).forEach(function (b) { b.value = ''; b.classList.remove('filled'); }); }
  function focusFirst(root) { var b = boxes(root)[0]; if (b) b.focus(); }
  // red boxes and a message directly below them; typing again clears both
  function setErr(root, msgId, text) {
    root.dataset.msg = msgId;
    root.classList.remove('bad');
    if (text) { void root.offsetWidth; root.classList.add('bad'); }   // restarts the shake on every wrong try
    msg(msgId, text, text ? 'bad' : '');
  }
  function wireBoxes(root, msgId, onComplete) {
    var all = boxes(root);
    root.dataset.msg = msgId;
    all.forEach(function (box, i) {
      box.addEventListener('input', function () {
        var v = box.value.replace(/\D/g, '');
        box.value = v.slice(-1);
        box.classList.toggle('filled', !!box.value);   // a typed digit turns its box light orange
        if (root.classList.contains('bad')) setErr(root, msgId, '');
        root.classList.remove('ok');
        if (v && i < all.length - 1) all[i + 1].focus();
        if (all.every(function (b) { return b.value; })) onComplete();
      });
      box.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !box.value && i > 0) { all[i - 1].focus(); all[i - 1].value = ''; all[i - 1].classList.remove('filled'); }
        else if (e.key === 'ArrowLeft' && i > 0) all[i - 1].focus();
        else if (e.key === 'ArrowRight' && i < all.length - 1) all[i + 1].focus();
        else if (e.key === 'Enter' && all.every(function (b) { return b.value; })) onComplete();
      });
      box.addEventListener('paste', function (e) {
        var t = ((e.clipboardData || window.clipboardData).getData('text') || '').replace(/\D/g, '').slice(0, 6);
        if (!t) return;
        e.preventDefault();
        if (root.classList.contains('bad')) setErr(root, msgId, '');
        t.split('').forEach(function (ch, k) { all[k].value = ch; all[k].classList.add('filled'); });
        all[Math.min(t.length, 5)].focus();
        if (t.length === 6) onComplete();
      });
      box.addEventListener('focus', function () { box.select(); });
    });
  }

  // opens the job page once its list is in; a round spinner shows only if that takes a moment
  function openApp() {
    refresh().then(function () { unlocked = true; show(); });
  }

  // The PIN check as one continuous animation: after the last digit the boxes slide together into an orange circle that
  // keeps turning while the server checks. A correct PIN turns it green and draws a tick; a wrong one opens it back
  // out into red boxes.
  function pinStage() {
    var root = $('a-pin'), gateEl = $('a-gate-pin'), bs = boxes(root), anims = [];
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var orb = document.createElement('div'); orb.className = 'pin-orb'; orb.setAttribute('aria-hidden', 'true');
    orb.innerHTML = '<svg viewBox="0 0 100 100"><circle class="ring-track" cx="50" cy="50" r="44"/><circle class="ring-arc" cx="50" cy="50" r="44"/><circle class="ring-full" cx="50" cy="50" r="44"/><path class="check" d="M32 52l12 12 24-26"/></svg>';
    gateEl.appendChild(orb);
    var g = gateEl.getBoundingClientRect(), f0 = bs[0].getBoundingClientRect(), l0 = bs[bs.length - 1].getBoundingClientRect();
    var cx = (f0.left + l0.right) / 2, cy = f0.top + f0.height / 2;   // the middle of the six boxes, not of the whole card
    orb.style.left = (cx - g.left) + 'px'; orb.style.top = (cy - g.top) + 'px';
    gateEl.classList.add('signing-in');
    var squeezed = bs.map(function (b) {
      var r = b.getBoundingClientRect();
      return { transform: 'translateX(' + (cx - (r.left + r.width / 2)) + 'px) scale(.6)', opacity: 0, borderRadius: '50%' };
    });
    var open = { transform: 'none', opacity: 1, borderRadius: '14px' };
    var stage = {
      merge: function () {
        if (reduce) { bs.forEach(function (b) { b.style.opacity = 0; }); orb.style.opacity = 1; return Promise.resolve(); }
        bs.forEach(function (b, i) {
          anims.push(b.animate([open, squeezed[i]], { duration: 400, easing: 'cubic-bezier(.65,0,.35,1)', fill: 'forwards' }));
        });
        anims.push(orb.animate([{ opacity: 0, transform: 'scale(.86)' }, { opacity: 1, transform: 'scale(1)' }],
          { duration: 300, delay: 160, easing: 'cubic-bezier(.32,.72,0,1)', fill: 'forwards' }));
        return wait(520);
      },
      // correct: the circle turns green and the tick draws
      success: function () {
        orb.style.setProperty('--tick', '.45s'); orb.style.setProperty('--tick-delay', '.28s');
        orb.classList.add('ok', 'done');
        if (!reduce) anims.push(orb.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.05)', offset: .5 }, { transform: 'scale(1)' }],
          { duration: 520, delay: 380, easing: 'cubic-bezier(.32,.72,0,1)', fill: 'forwards' }));
        return wait(reduce ? 300 : 1000);
      },
      // wrong: the circle opens back out into the six boxes
      reverse: function () {
        if (reduce) { stage.cleanup(); return Promise.resolve(); }
        anims.push(orb.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 160, fill: 'forwards' }));
        bs.forEach(function (b, i) {
          anims.push(b.animate([squeezed[i], open], { duration: 380, delay: 90, easing: 'cubic-bezier(.32,.72,0,1)', fill: 'forwards' }));
        });
        return wait(520).then(stage.cleanup);
      },
      cleanup: function () {
        anims.forEach(function (a) { try { a.cancel(); } catch (e) { /* ignore */ } });
        if (orb.parentNode) orb.parentNode.removeChild(orb);
        bs.forEach(function (b) { b.style.opacity = ''; b.readOnly = false; });
        root.classList.remove('checking'); gateEl.classList.remove('signing-in');
      }
    };
    return stage;
  }

  function goTo(next, text, kind) {
    gate = next;
    if (text) msg('a-msg', text, kind);
    show();
  }

  // ----- PIN -----
  // the PIN service runs next to the database (US East), not in the visitor's nearest region: its database trips are then quick
  var PIN_HEADERS = { apikey: T.key, 'Content-Type': 'application/json', 'x-region': 'us-east-1' };
  // wake the sign-in service and open the connection while the PIN is being typed
  fetch(T.url + '/functions/v1/admin-pin', { method: 'POST', headers: PIN_HEADERS, body: JSON.stringify({ action: 'ping' }) }).catch(function () { /* only a warm-up */ });
  function unlock() {
    var root = $('a-pin'), pin = code(root);
    if (busy || pin.length !== 6) return;
    busy = true;
    root.classList.add('checking');
    boxes(root).forEach(function (b) { b.readOnly = true; });
    var stage = pinStage();
    var merged = stage.merge();                    // the boxes start moving at once; the server answers meanwhile
    var answer = fetch(T.url + '/functions/v1/admin-pin', {
      method: 'POST', headers: PIN_HEADERS,
      body: JSON.stringify({ action: 'unlock', pin: pin })
    }).then(function (r) { return r.json().catch(function () { return {}; }); })
      .catch(function () { return { state: 'offline' }; });
    Promise.all([answer, merged]).then(function (x) {
      var d = x[0];
      if (d.state === 'ok' && d.session) {
        save({ access_token: d.session.access_token, refresh_token: d.session.refresh_token, expires_at: now() + (d.session.expires_in || 3600) });
        setErr(root, 'a-pin-msg', '');
        var loaded = refresh();                    // the job list loads while the tick draws
        return stage.success().then(function () { return loaded; }).then(function () {
          unlocked = true; show(); stage.cleanup(); clearBoxes(root);
        });
      }
      clearBoxes(root);
      if (d.state === 'locked') { stage.cleanup(); goTo('email', 'Too many wrong PINs. Request a code to set a new PIN.', 'bad'); return; }
      if (d.state === 'no_pin') { stage.cleanup(); goTo('email', '', ''); return; }
      setErr(root, 'a-pin-msg', d.state === 'wrong' ? 'Wrong PIN. Please try again.'
        : d.state === 'offline' ? 'Could not reach the sign-in service. Check your connection.'
        : 'Could not check the PIN. Check your connection and try again.');
      return stage.reverse().then(function () { if (gate === 'pin' && !unlocked) focusFirst(root); });
    }).then(function () { busy = false; });
  }
  wireBoxes($('a-pin'), 'a-pin-msg', unlock);
  $('a-forgot').addEventListener('click', function () { msg('a-msg', ''); goTo('email'); });

  // ----- email code, then the new PIN -----
  function sendCode() {
    var email = $('a-email').value.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { msg('a-msg', 'Enter a valid email address.', 'bad'); $('a-email').focus(); return; }
    $('a-send').disabled = true;
    msg('a-msg', '');
    fetch(T.url + '/auth/v1/otp?redirect_to=' + encodeURIComponent(location.origin + location.pathname), {
      method: 'POST', headers: { apikey: T.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, create_user: false })
    }).then(function (r) {
      if (r.status === 429) msg('a-msg', 'Too many requests. Please wait a minute and try again.', 'bad');
      else if (!r.ok) msg('a-msg', 'This email is not registered as an admin. Check it and try again.', 'bad');
      else { resetEmail = email; clearBoxes($('a-code')); goTo('reset'); }
    }).catch(function () { msg('a-msg', 'Could not reach the sign-in service. Check your connection.', 'bad'); })
      .then(function () { $('a-send').disabled = false; });
  }
  $('a-send').addEventListener('click', sendCode);
  $('a-email').addEventListener('keydown', function (e) { if (e.key === 'Enter') sendCode(); });
  function back() { save(null); msg('a-msg', ''); goTo('pin'); }
  $('a-back-pin').addEventListener('click', back);
  $('a-back-reset').addEventListener('click', back);

  function pinProblem(p) {
    return (/^(\d)\1{5}$/.test(p) || OBVIOUS.indexOf(p) >= 0) ? 'Choose a less obvious PIN.' : '';
  }
  function checkCode(entered) {
    return fetch(T.url + '/auth/v1/verify', {
      method: 'POST', headers: { apikey: T.key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'email', email: resetEmail, token: entered })
    }).then(function (r) { return r.json().then(function (d) { if (!r.ok || !d.access_token) throw new Error(); return d; }); })
      .then(function (d) { save({ access_token: d.access_token, refresh_token: d.refresh_token, expires_at: now() + (d.expires_in || 3600) }); })
      .catch(function () { var e = new Error('That code is incorrect or has expired.'); e.kind = 'code'; throw e; });
  }
  // runs when the last digit of the confirmation PIN is typed
  function finishReset() {
    if (busy) return;
    var cBox = $('a-code'), nBox = $('a-new-pin'), fBox = $('a-confirm-pin');
    var entered = code(cBox), a = code(nBox), b = code(fBox), needCode = !load();
    setErr(cBox, 'a-code-msg', ''); setErr(nBox, 'a-new-msg', ''); setErr(fBox, 'a-conf-msg', '');
    if (needCode && entered.length !== 6) { setErr(cBox, 'a-code-msg', 'Enter the 6-digit code from your email.'); focusFirst(cBox); return; }
    var bad = pinProblem(a);
    if (bad) { setErr(nBox, 'a-new-msg', bad); clearBoxes(nBox); clearBoxes(fBox); focusFirst(nBox); return; }
    if (a !== b) { setErr(fBox, 'a-conf-msg', 'The PINs do not match. Please try again.'); clearBoxes(fBox); focusFirst(fBox); return; }
    busy = true;
    (needCode ? checkCode(entered) : Promise.resolve())
      .then(function () { return api('/functions/v1/admin-pin', { method: 'POST', headers: { 'x-region': 'us-east-1' }, body: JSON.stringify({ action: 'set', pin: a }) }); })
      .then(function () {
        clearBoxes(cBox); clearBoxes(nBox); clearBoxes(fBox);
        gate = 'done'; show();
        setTimeout(openApp, 1900);
      })
      .catch(function (e) {
        if (e.kind === 'code') { setErr(cBox, 'a-code-msg', e.message); clearBoxes(cBox); focusFirst(cBox); return; }
        setErr(nBox, 'a-new-msg', e.message); clearBoxes(nBox); clearBoxes(fBox); focusFirst(nBox);
      })
      .then(function () { busy = false; });
  }
  wireBoxes($('a-code'), 'a-code-msg', function () {
    // after a wrong code was retyped, the PINs are still filled in: go straight on
    if (code($('a-new-pin')).length === 6 && code($('a-confirm-pin')).length === 6) finishReset();
    else focusFirst($('a-new-pin'));
  });
  wireBoxes($('a-new-pin'), 'a-new-msg', function () {
    var bad = pinProblem(code($('a-new-pin')));
    if (bad) { setErr($('a-new-pin'), 'a-new-msg', bad); clearBoxes($('a-new-pin')); focusFirst($('a-new-pin')); return; }
    focusFirst($('a-confirm-pin'));
  });
  wireBoxes($('a-confirm-pin'), 'a-conf-msg', finishReset);

  $('a-out').addEventListener('click', signOut);

  // on opening the page: an email sign-in link goes to choosing a PIN; otherwise the PIN screen shows
  handleHash(takeHash());

  // ----- AI draft -----
  $('a-draft').addEventListener('click', function () {
    var notes = $('a-notes').value.trim();
    if (notes.length < 20) { msg('a-draft-msg', 'Add a few more details about the role first.', 'bad'); return; }
    $('a-draft').disabled = true;
    msg('a-draft-msg', 'Drafting. This takes a few seconds.', '');
    token().then(function (t) {
      return fetch(T.url + '/functions/v1/draft-job', {
        method: 'POST', headers: { apikey: T.key, Authorization: 'Bearer ' + t, 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notes })
      });
    }).then(function (r) {
      return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || 'The draft failed.'); return d; });
    }).then(function (d) {
      fill(d);
      var c = $('f-confirm');
      c.textContent = '';
      if (d.confirm && d.confirm.length) {
        var h = document.createElement('strong'); h.textContent = 'Please check before publishing:'; c.appendChild(h);
        var ul = document.createElement('ul');
        d.confirm.forEach(function (t2) { var li = document.createElement('li'); li.textContent = t2; ul.appendChild(li); });
        c.appendChild(ul); c.hidden = false;
      } else { c.hidden = true; }
      msg('a-draft-msg', 'Draft ready below. Review and edit it, then publish.', 'ok');
      $('f-title').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }).catch(function (e) { msg('a-draft-msg', e.message, 'bad'); })
      .then(function () { $('a-draft').disabled = false; });
  });

  // ----- form -----
  function lines(v) { return v.split('\n').map(function (x) { return x.replace(/^[-•*\s]+/, '').trim(); }).filter(Boolean); }
  function fill(d) {
    $('f-title').value = d.title || '';
    $('f-location').value = d.location || '';
    $('f-type').value = d.employment_type || 'Contract';
    $('f-pay').value = d.pay || '';
    $('f-summary').value = d.summary || '';
    $('f-resp').value = (d.responsibilities || []).join('\n');
    $('f-req').value = (d.requirements || []).join('\n');
  }
  function localInput(iso) {
    var d = new Date(iso); d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  }
  function hasContent() {
    return !!editing || ['a-notes', 'f-title', 'f-pay', 'f-summary', 'f-resp', 'f-req'].some(function (id) { return $(id).value.trim(); });
  }
  function closePanels() { $('f-sched').hidden = true; $('f-clear-ask').hidden = true; }
  function clearForm() {
    editing = null;
    fill({});
    $('f-location').value = 'Remote (U.S.)';
    $('f-when').value = '';
    $('f-confirm').hidden = true;
    closePanels();
    msg('f-msg', '');
  }
  function clearAll() { clearForm(); $('a-notes').value = ''; msg('a-draft-msg', ''); }

  $('f-clear').addEventListener('click', function () {
    if (!hasContent()) { clearAll(); return; }
    $('f-clear-ask').hidden = false;
    $('f-clear-yes').focus();
  });
  $('f-clear-yes').addEventListener('click', clearAll);
  $('f-clear-no').addEventListener('click', function () { $('f-clear-ask').hidden = true; });

  function needsText() {
    if (!$('f-title').value.trim() || !$('f-summary').value.trim()) { msg('f-msg', 'A title and a summary are required.', 'bad'); return true; }
    return false;
  }
  $('f-schedule').addEventListener('click', function () {
    if (needsText()) return;
    $('f-clear-ask').hidden = true;
    msg('f-msg', '');
    openSched();
  });
  $('f-now').addEventListener('click', function () { submit('now'); });
  // ----- schedule pop-up: pick a date, then hour, minutes and AM/PM -----
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var sch = null;   // { y, m, date, h, min, ap } while the pop-up is open
  function two(n) { return (n < 10 ? '0' : '') + n; }
  function pickText() {
    if (!sch.date) return 'Pick a date';
    var d = sch.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    return d + ' · ' + (sch.h || '--') + ':' + (sch.min === null ? '--' : two(sch.min)) + ' ' + (sch.ap || '--');
  }
  function schedUpdate() {
    $('sched-pick').textContent = pickText();
    $('sched-go').disabled = !(sch.date && sch.h && sch.min !== null && sch.ap);
    msg('sched-msg', '');
  }
  function renderCal() {
    var first = new Date(sch.y, sch.m, 1), days = new Date(sch.y, sch.m + 1, 0).getDate();
    var today = new Date(); today.setHours(0, 0, 0, 0);
    $('cal-month').textContent = MONTHS[sch.m] + ' ' + sch.y;
    $('cal-prev').disabled = sch.y === today.getFullYear() && sch.m <= today.getMonth();
    var box = $('cal-days'); box.textContent = '';
    for (var i = 0; i < first.getDay(); i++) box.appendChild(document.createElement('span'));
    for (var d = 1; d <= days; d++) {
      (function (day) {
        var dt = new Date(sch.y, sch.m, day);
        var b = document.createElement('button'); b.type = 'button'; b.textContent = day;
        if (dt < today) b.disabled = true;
        if (dt.getTime() === today.getTime()) b.classList.add('today');
        if (sch.date && sch.date.getTime() === dt.getTime()) b.classList.add('on');
        b.addEventListener('click', function () { sch.date = dt; schedUpdate(); $('sched-date').hidden = true; $('sched-time').hidden = false; });
        box.appendChild(b);
      })(d);
    }
  }
  function timeCol(id, items, key) {
    var col = $(id); col.textContent = '';
    items.forEach(function (it) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = it.label;
      if (sch[key] === it.value) b.classList.add('on');
      b.addEventListener('click', function () {
        sch[key] = it.value; schedUpdate();
        Array.prototype.forEach.call(col.children, function (c) { c.classList.remove('on'); });
        b.classList.add('on');
      });
      col.appendChild(b);
    });
  }
  function renderTime() {
    var h = [], m = [];
    for (var i = 0; i < 12; i++) { var hv = (i + 5) % 12 + 1; h.push({ label: String(hv), value: hv }); }   // 6, 7 ... 12, 1 ... 5
    for (var j = 0; j < 12; j++) { var mv = (j * 5 + 15) % 60; m.push({ label: two(mv), value: mv }); }   // 15, 20 ... 55, 00, 05, 10
    timeCol('t-hour', h, 'h'); timeCol('t-min', m, 'min');
    timeCol('t-ap', [{ label: 'AM', value: 'AM' }, { label: 'PM', value: 'PM' }], 'ap');
  }
  function openSched() {
    var n = new Date();
    sch = { y: n.getFullYear(), m: n.getMonth(), date: null, h: 6, min: 15, ap: null };   // the time lists start at 6 and :15
    $('sched-date').hidden = false; $('sched-time').hidden = true;
    renderCal(); renderTime(); schedUpdate();
    $('f-sched').hidden = false;
    $('cal-days').querySelector('button:not(:disabled)').focus();
  }
  function closeSched() { $('f-sched').hidden = true; sch = null; }
  $('cal-prev').addEventListener('click', function () { sch.m--; if (sch.m < 0) { sch.m = 11; sch.y--; } renderCal(); });
  $('cal-next').addEventListener('click', function () { sch.m++; if (sch.m > 11) { sch.m = 0; sch.y++; } renderCal(); });
  $('sched-back').addEventListener('click', function () { $('sched-time').hidden = true; $('sched-date').hidden = false; renderCal(); });
  $('sched-close').addEventListener('click', closeSched);
  $('f-sched').addEventListener('click', function (e) { if (e.target === this) closeSched(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !$('f-sched').hidden) closeSched(); });
  $('sched-go').addEventListener('click', function () {
    var d = new Date(sch.date), h = sch.h % 12 + (sch.ap === 'PM' ? 12 : 0);
    d.setHours(h, sch.min, 0, 0);
    if (d <= Date.now()) { msg('sched-msg', 'Choose a time in the future.', 'bad'); return; }
    $('f-when').value = d.getFullYear() + '-' + two(d.getMonth() + 1) + '-' + two(d.getDate()) + 'T' + two(d.getHours()) + ':' + two(d.getMinutes());
    closeSched();
    submit('later');
  });
  $('f-draft').addEventListener('click', function () { submit('draft'); });

  function submit(when) {
    if (needsText()) return;
    var body = {
      title: $('f-title').value.trim(), location: $('f-location').value.trim() || 'Remote (U.S.)', employment_type: $('f-type').value,
      pay: $('f-pay').value.trim() || null, summary: $('f-summary').value.trim(),
      responsibilities: lines($('f-resp').value), requirements: lines($('f-req').value),
      updated_at: new Date().toISOString()
    };
    var start = null;
    if (when === 'draft') { body.status = 'draft'; body.publish_at = null; }
    else if (when === 'now') {
      body.status = 'published';
      // a job that is already live keeps its original start date
      if (editing && editing.status === 'published' && editing.publish_at && new Date(editing.publish_at) <= Date.now()) start = new Date(editing.publish_at);
      else start = new Date(Date.now() - 60000);
      body.publish_at = start.toISOString();
    } else {
      if (!$('f-when').value) { msg('f-msg', 'Choose the date and time to publish.', 'bad'); return; }
      start = new Date($('f-when').value);
      if (start <= Date.now()) { msg('f-msg', 'Choose a date and time in the future.', 'bad'); return; }
      body.status = 'published'; body.publish_at = start.toISOString();
    }
    var btns = ['f-now', 'f-schedule', 'f-draft'].map($);
    btns.forEach(function (b) { b.disabled = true; });
    var req = editing
      ? api('/rest/v1/jobs?id=eq.' + editing.id, { method: 'PATCH', body: JSON.stringify(body), headers: { Prefer: 'return=representation' } })
      : api('/rest/v1/jobs', { method: 'POST', body: JSON.stringify(body), headers: { Prefer: 'return=representation' } });
    req.then(function () {
      var label = when === 'draft' ? 'Saved as a draft.' : when === 'later' ? 'Scheduled. It will appear on the Jobs page at that time.' : 'Published. It is now on the Jobs page.';
      clearAll(); msg('f-msg', label, 'ok');
      tab = when === 'draft' ? 'draft' : 'published'; page = 1; refresh();
    }).catch(function (e) { msg('f-msg', e.message, 'bad'); })
      .then(function () { btns.forEach(function (b) { b.disabled = false; }); });
  }

  // ----- jobs table -----
  function state(j) {
    var n = Date.now();
    if (j.status === 'draft') return 'Draft';
    if (j.status === 'closed') return 'Archived';
    if (j.expires_at && new Date(j.expires_at) <= n) return 'Expired';
    if (new Date(j.publish_at) > n) return 'Scheduled';
    return 'Live';
  }
  function tabOf(j) { return j.status === 'draft' ? 'draft' : j.status === 'closed' ? 'archived' : 'published'; }
  function fmt(iso) { return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }); }

  function refresh() {
    var cutoff = new Date(Date.now() - KEEP_DAYS * 864e5).toISOString();
    // clearing out old archived jobs runs alongside loading the list, not before it
    api('/rest/v1/jobs?status=eq.closed&updated_at=lt.' + encodeURIComponent(cutoff), { method: 'DELETE' }).catch(function () { /* the next visit tries again */ });
    return api('/rest/v1/jobs?select=*&order=created_at.desc').then(function (rows) {
      jobs = rows; jobsLoaded = true; renderList();
    }).catch(function (e) { msg('a-jobs-msg', e.message, 'bad'); });
  }
  function button(label, cls, fn) {
    var b = document.createElement('button'); b.type = 'button'; b.className = cls; b.textContent = label;
    b.addEventListener('click', fn); return b;
  }
  function cell(label, node) {
    var td = document.createElement('td'); td.dataset.label = label;
    if (typeof node === 'string') td.textContent = node; else td.appendChild(node);
    return td;
  }
  function plural(n, w) { return n + ' ' + w + (n === 1 ? '' : 's'); }
  // "Just now", "1 hour ago", "23 hours ago", "2 days ago", "4 weeks ago"; a future start reads "In 2 days"
  function ago(iso) {
    var secs = (Date.now() - new Date(iso).getTime()) / 1000, future = secs < 0, v = Math.abs(secs), t;
    if (v < 3600) return future ? 'In under an hour' : 'Just now';
    if (v < 86400) t = plural(Math.floor(v / 3600), 'hour');
    else if (v < 7 * 86400) t = plural(Math.floor(v / 86400), 'day');
    else if (v < 30 * 86400) t = plural(Math.floor(v / (7 * 86400)), 'week');
    else if (v < 365 * 86400) t = plural(Math.floor(v / (30 * 86400)), 'month');
    else t = plural(Math.floor(v / (365 * 86400)), 'year');
    return future ? 'In ' + t : t + ' ago';
  }
  function posted(j) { return ago(j.status === 'published' ? j.publish_at : (j.updated_at || j.created_at)); }
  function haystack(j) {
    return [j.title, j.location, j.employment_type, j.pay, j.summary, (j.responsibilities || []).join(' '), (j.requirements || []).join(' '), state(j), posted(j)]
      .filter(Boolean).join(' ').toLowerCase();
  }
  var EMPTY = { published: 'No published jobs yet.', draft: 'No saved drafts.', archived: 'No archived jobs.', all: 'No jobs match your search.' };
  function renderList() {
    var q = $('a-search').value.trim().toLowerCase(), words = q ? q.split(/\s+/) : [];
    var found = words.length ? jobs.filter(function (j) { var h = haystack(j); return words.every(function (w) { return h.indexOf(w) >= 0; }); }) : jobs;
    var view = words.length && searchAll ? 'all' : tab;   // a search looks through every tab until a tab is chosen
    var counts = { published: 0, draft: 0, archived: 0 };
    found.forEach(function (j) { counts[tabOf(j)]++; });
    $('a-arch-note').hidden = view !== 'archived';
    document.querySelectorAll('.a-tab').forEach(function (t) {
      var on = t.dataset.tab === view;
      t.setAttribute('aria-selected', String(on));
      t.querySelector('.a-count').textContent = '(' + counts[t.dataset.tab] + ')';
    });
    var list = found.filter(function (j) { return view === 'all' || tabOf(j) === view; });
    var pages = Math.max(1, Math.ceil(list.length / PER_PAGE));
    if (page > pages) page = pages;
    var box = $('a-jobs'); box.textContent = '';
    msg('a-jobs-msg', list.length ? '' : EMPTY[words.length && view === 'all' ? 'all' : view], '');
    $('a-jobs').closest('.a-table-wrap').hidden = !list.length;
    list.slice((page - 1) * PER_PAGE, page * PER_PAGE).forEach(function (j) {
      var st = state(j);
      var tr = document.createElement('tr');
      var t = document.createElement('div');
      var h = document.createElement('strong'); h.textContent = j.title;
      var pill = document.createElement('span'); pill.className = 'pill pill-' + st.toLowerCase(); pill.textContent = st;
      t.appendChild(h); t.appendChild(pill);
      var acts = document.createElement('div'); acts.className = 'a-acts';
      acts.appendChild(button('Edit', 'btn btn-white btn-sm', function () { edit(j); }));
      if (j.status === 'published') acts.appendChild(button('Archive', 'btn btn-white btn-sm', function () { patch(j, { status: 'closed' }); }));
      if (j.status === 'closed') acts.appendChild(button('Restore', 'btn btn-white btn-sm', function () { patch(j, { status: 'published', publish_at: j.publish_at || new Date(Date.now() - 60000).toISOString() }); }));
      var del = button('Delete', 'btn btn-white btn-sm', function () {
        if (del.dataset.sure !== '1') { del.dataset.sure = '1'; del.textContent = 'Click again to delete'; setTimeout(function () { del.dataset.sure = ''; del.textContent = 'Delete'; }, 4000); return; }
        api('/rest/v1/jobs?id=eq.' + j.id, { method: 'DELETE' }).then(refresh).catch(function (e) { msg('a-jobs-msg', e.message, 'bad'); });
      });
      acts.appendChild(del);
      tr.appendChild(cell('Job', t));
      tr.appendChild(cell('Location', j.location || ''));
      tr.appendChild(cell('Type', j.employment_type || ''));
      tr.appendChild(cell('Posted', posted(j)));
      tr.appendChild(cell('', acts));
      box.appendChild(tr);
    });
    $('a-page').textContent = 'Page ' + page + ' of ' + pages;
    $('a-prev').disabled = page <= 1;
    $('a-next').disabled = page >= pages;
  }
  document.querySelectorAll('.a-tab').forEach(function (t) {
    t.addEventListener('click', function () { tab = t.dataset.tab; searchAll = false; page = 1; renderList(); });
  });
  $('a-search').addEventListener('input', function () { searchAll = true; page = 1; renderList(); });
  $('a-prev').addEventListener('click', function () { page--; renderList(); });
  $('a-next').addEventListener('click', function () { page++; renderList(); });

  function patch(j, fields) {
    fields.updated_at = new Date().toISOString();
    api('/rest/v1/jobs?id=eq.' + j.id, { method: 'PATCH', body: JSON.stringify(fields) }).then(refresh)
      .catch(function (e) { msg('a-jobs-msg', e.message, 'bad'); });
  }
  function edit(j) {
    editing = j;
    closePanels();
    fill(j);
    $('f-when').value = j.publish_at ? localInput(j.publish_at) : '';
    $('f-confirm').hidden = true;
    msg('f-msg', 'Editing "' + j.title + '". Publish Now, Schedule or Save as Draft will update this job.', '');
    $('form-title').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ----- start -----
  clearForm();
  show();
  window.addEventListener('hashchange', function () { handleHash(takeHash()); show(); });
})();
