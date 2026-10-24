// Find a Job: a visitor uploads a resume, and it is read and matched against the open roles inside this page only.
// Nothing is uploaded, saved or shared: the resume and the results live in memory and disappear on refresh or leaving.
(function () {
  var T = window.TRIADA, J = window.TriadaJobs || {};
  var section = document.getElementById('find-section');
  if (!T || !section) return;

  var $ = function (id) { return document.getElementById(id); };
  var input = $('resume-file'), zone = $('dropzone'), chip = $('dz-file'), matchBtn = $('match-btn'), errorBox = $('find-error');
  var state = { file: null, busy: false };
  var MAX_BYTES = 5 * 1024 * 1024;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function problem(code) { var e = new Error(code); e.resume = code; return e; }

  // ----- steps: upload, checking, valid, matching, results, none -----
  function show(name) {
    Array.prototype.forEach.call(section.querySelectorAll('.find-step'), function (s) { s.hidden = s.getAttribute('data-step') !== name; });
    var head = section.querySelector('.find-step[data-step="' + name + '"] [data-focus]');
    if (head) head.focus({ preventScroll: true });
  }
  function showError(text) {
    errorBox.textContent = text || '';
    errorBox.hidden = !text;
  }
  function describe(file) {
    var kb = file.size / 1024;
    return kb < 1024 ? Math.max(1, Math.round(kb)) + ' KB' : (kb / 1024).toFixed(1) + ' MB';
  }
  function setFile(file) {
    state.file = file || null;
    if (!file) { input.value = ''; }
    chip.hidden = !file;
    zone.classList.toggle('has-file', !!file);
    if (file) {
      chip.querySelector('.dz-name').textContent = file.name;
      chip.querySelector('.dz-size').textContent = describe(file);
    }
    matchBtn.disabled = !file;
    showError('');
  }
  // forget everything: the file, the text read from it, the name and the results
  function reset() {
    state.busy = false;
    setFile(null);
    $('find-results').textContent = '';
    $('find-name').textContent = '';
    $('find-summary').textContent = '';
    $('find-none-name').textContent = '';
    show('upload');
  }
  function openPanel() {
    reset();
    section.hidden = false;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(function () { zone.focus({ preventScroll: true }); }, 350);
  }
  function closePanel() {
    reset();
    section.hidden = true;
  }

  // ----- choosing a file -----
  zone.addEventListener('click', function (e) { if (e.target.closest('.dz-remove')) return; input.click(); });
  zone.addEventListener('keydown', function (e) {
    if ((e.key === 'Enter' || e.key === ' ') && !e.target.closest('.dz-remove')) { e.preventDefault(); input.click(); }
  });
  input.addEventListener('change', function () { if (input.files && input.files[0]) setFile(input.files[0]); });
  ['dragenter', 'dragover'].forEach(function (t) {
    zone.addEventListener(t, function (e) { e.preventDefault(); zone.classList.add('is-over'); });
  });
  ['dragleave', 'dragend'].forEach(function (t) {
    zone.addEventListener(t, function () { zone.classList.remove('is-over'); });
  });
  zone.addEventListener('drop', function (e) {
    e.preventDefault();
    zone.classList.remove('is-over');
    var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  $('dz-remove').addEventListener('click', function (e) { e.stopPropagation(); setFile(null); zone.focus(); });

  // ----- reading the resume: PDF, Word (.docx) or plain text -----
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src; s.onload = resolve; s.onerror = function () { reject(problem('open')); };
      document.head.appendChild(s);
    });
  }
  var pdfReady = null;
  function pdfjs() {
    if (!pdfReady) {
      pdfReady = loadScript('assets/vendor/pdf.min.js').then(function () {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'assets/vendor/pdf.worker.min.js';
        return window.pdfjsLib;
      });
    }
    return pdfReady;
  }
  function readPdf(buffer) {
    return pdfjs().then(function (lib) {
      return lib.getDocument({ data: buffer, isEvalSupported: false }).promise.then(function (doc) {
        var pages = Math.min(doc.numPages, 8), text = '', chain = Promise.resolve();
        var one = function (n) {
          return doc.getPage(n).then(function (page) { return page.getTextContent(); }).then(function (content) {
            content.items.forEach(function (it) { text += it.str + (it.hasEOL ? '\n' : ' '); });
            text += '\n';
          });
        };
        for (var n = 1; n <= pages; n++) chain = chain.then(one.bind(null, n));
        return chain.then(function () { doc.destroy(); return text; });
      });
    }).catch(function (e) { throw e && e.resume ? e : problem('open'); });
  }
  // a .docx is a zip file; the text is in word/document.xml
  function readDocx(buffer) {
    var u8 = new Uint8Array(buffer), v = new DataView(buffer), end = -1, i;
    for (i = u8.length - 22; i >= Math.max(0, u8.length - 65557); i--) { if (v.getUint32(i, true) === 0x06054b50) { end = i; break; } }
    if (end < 0 || typeof DecompressionStream === 'undefined') return Promise.reject(problem('open'));
    var count = v.getUint16(end + 10, true), p = v.getUint32(end + 16, true), hit = null, k;
    for (k = 0; k < count; k++) {
      if (v.getUint32(p, true) !== 0x02014b50) break;
      var nlen = v.getUint16(p + 28, true), elen = v.getUint16(p + 30, true), clen = v.getUint16(p + 32, true);
      var name = new TextDecoder().decode(u8.subarray(p + 46, p + 46 + nlen));
      if (name === 'word/document.xml') { hit = { method: v.getUint16(p + 10, true), csize: v.getUint32(p + 20, true), usize: v.getUint32(p + 24, true), lho: v.getUint32(p + 42, true) }; break; }
      p += 46 + nlen + elen + clen;
    }
    if (!hit || hit.usize > 30 * 1024 * 1024) return Promise.reject(problem('open'));
    var at = hit.lho + 30 + v.getUint16(hit.lho + 26, true) + v.getUint16(hit.lho + 28, true);
    var data = u8.subarray(at, at + hit.csize);
    var inflate = hit.method === 0 ? Promise.resolve(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength))
      : new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer();
    return inflate.then(function (buf) {
      var xml = new DOMParser().parseFromString(new TextDecoder().decode(buf), 'application/xml');
      var out = [];
      Array.prototype.forEach.call(xml.getElementsByTagName('w:p'), function (para) {
        var line = '';
        Array.prototype.forEach.call(para.getElementsByTagName('*'), function (n) {
          if (n.nodeName === 'w:t') line += n.textContent;
          else if (n.nodeName === 'w:tab') line += ' ';
          else if (n.nodeName === 'w:br') line += '\n';
        });
        out.push(line);
      });
      return out.join('\n');
    }).catch(function () { throw problem('open'); });
  }
  function readResume(file) {
    var ext = (file.name.split('.').pop() || '').toLowerCase();
    if (['pdf', 'docx', 'txt'].indexOf(ext) < 0) return Promise.reject(problem('type'));
    if (file.size > MAX_BYTES) return Promise.reject(problem('size'));
    if (file.size === 0) return Promise.reject(problem('empty'));
    if (ext === 'txt') return file.text();
    return file.arrayBuffer().then(ext === 'pdf' ? readPdf : readDocx);
  }

  // does the text read like a resume? (readable, long enough, and shows the usual signs)
  function check(text) {
    var t = (text || '').replace(/\s+/g, ' ').trim();
    if (!t || t.split(' ').length < 40) return 'empty';
    var low = t.toLowerCase(), signs = 0;
    if (/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(t)) signs++;
    if (/\+?\d[\d\s().-]{8,}\d/.test(t)) signs++;
    var parts = ['experience', 'education', 'skills', 'summary', 'objective', 'profile', 'employment', 'projects', 'certification', 'achievements', 'work history', 'professional'];
    if (parts.filter(function (w) { return low.indexOf(w) >= 0; }).length >= 2) signs++;
    if ((low.match(/\b(19|20)\d{2}\b/g) || []).length >= 2) signs++;
    if (/\b(bachelor|master|b\.?s\.?|m\.?s\.?|ph\.?d|mba|university|college)\b/i.test(t)) signs++;
    return signs >= 2 ? '' : 'notresume';
  }

  // the candidate's name: usually the first line; else the email address; else the file name
  function titleCase(s) { return s.toLowerCase().replace(/(^|[\s'’-])([a-z])/g, function (m, a, b) { return a + b.toUpperCase(); }); }
  function findName(text, fileName) {
    var skip = /resume|curriculum|vitae|\bcv\b|profile|summary|objective|contact|experience|education|skills|email|phone|address|linkedin|github|www\.|@|\d|engineer|developer|manager|analyst|consultant|architect|specialist/i;
    var lines = text.split(/\n+/).map(function (l) { return l.trim(); }).filter(Boolean).slice(0, 12), i, name;
    for (i = 0; i < lines.length; i++) {
      var c = lines[i].replace(/[,|•·].*$/, '').trim(), w = c.split(/\s+/);
      if (c.length < 4 || c.length > 40 || skip.test(c) || w.length < 2 || w.length > 4) continue;
      if (!w.every(function (x) { return /^[A-Za-z][A-Za-z'’.-]*$/.test(x); })) continue;
      if (c === c.toUpperCase() || w.every(function (x) { return /^[A-Z]/.test(x); })) return titleCase(c);
    }
    var mail = /([a-z][a-z0-9]*)[._-]([a-z][a-z0-9]*)@/i.exec(text);
    if (mail) return titleCase(mail[1] + ' ' + mail[2]);
    name = fileName.replace(/\.[^.]+$/, '').replace(/[-_.\d]+/g, ' ').replace(/\b(resume|cv|curriculum|vitae|final|new|updated|copy)\b/gi, ' ').replace(/\s+/g, ' ').trim();
    return name && name.split(' ').length <= 3 ? titleCase(name) : '';
  }

  // ----- matching -----
  var STOP = {};
  ('a an the and or of to in on for with at by from as is are was were be been being this that these those it its you your we our they their i he she his her will would can could should may might must shall do does did have has had not no nor but if then than so such into over under about across per via etc using use used including include includes within without ' +
    'experience experienced years year work working worked role roles job position candidate candidates looking required requirement requirements require preferred strong excellent good great ability able skill skills knowledge team teams responsible responsibilities duties relevant related plus new best well also ensure help provide provides providing company business client clients').split(' ').forEach(function (w) { STOP[w] = 1; });
  var LEVEL = { senior: 1, lead: 1, junior: 1, sr: 1, jr: 1, principal: 1, staff: 1, associate: 1, ii: 1, iii: 1, iv: 1 };
  var ALIAS = { js: 'javascript', ts: 'typescript', k8s: 'kubernetes', nodejs: 'node', golang: 'go', postgres: 'postgresql', ml: 'machine', ai: 'ai' };
  function stem(w) {
    if (w.length > 5 && /ing$/.test(w)) return w.slice(0, -3);
    if (w.length > 4 && /(ed|es)$/.test(w)) return w.slice(0, -2);
    if (w.length > 3 && /s$/.test(w) && !/ss$/.test(w)) return w.slice(0, -1);
    return w;
  }
  function terms(text) {
    var t = String(text || '').toLowerCase().replace(/c\+\+/g, ' cpp ').replace(/c#/g, ' csharp ').replace(/\.net\b/g, ' dotnet ').replace(/node\.js/g, ' node ').replace(/ci\/cd/g, ' ci cd ');
    var out = {}, m = t.match(/[a-z][a-z0-9]+/g) || [];
    m.forEach(function (w) {
      w = ALIAS[w] || w;
      if (STOP[w] || w.length < 2) return;
      out[stem(w)] = 1;
    });
    return out;
  }
  function rank(resumeText, jobs) {
    var mine = terms(resumeText), n = jobs.length, df = {};
    var info = jobs.map(function (j) {
      var weights = {}, titleTerms = terms(j.title);
      var add = function (txt, w) { Object.keys(terms(txt)).forEach(function (t) { weights[t] = (weights[t] || 0) + w; }); };
      add(j.title, 3);
      add((j.requirements || []).join(' '), 2);
      add((j.responsibilities || []).join(' '), 1.5);
      add(j.summary, 1);
      Object.keys(weights).forEach(function (t) { df[t] = (df[t] || 0) + 1; });
      var core = Object.keys(titleTerms).filter(function (t) { return !LEVEL[t]; });
      return { job: j, weights: weights, title: core.length ? core : Object.keys(titleTerms) };
    });
    var idf = function (t) { return Math.max(0.35, Math.log((n + 1) / ((df[t] || 0) + 0.5))); };
    return info.map(function (x) {
      var have = 0, all = 0;
      Object.keys(x.weights).forEach(function (t) { var s = x.weights[t] * idf(t); all += s; if (mine[t]) have += s; });
      var tHave = 0, tAll = 0;
      x.title.forEach(function (t) { var s = idf(t); tAll += s; if (mine[t]) tHave += s; });
      var raw = 0.6 * (all ? have / all : 0) + 0.4 * (tAll ? tHave / tAll : 0);
      return { job: x.job, pct: Math.min(99, Math.round(100 * (1 - Math.exp(-3.4 * raw)))) };
    }).filter(function (r) { return r.pct >= 40; }).sort(function (a, b) {
      return b.pct - a.pct || new Date(b.job.publish_at) - new Date(a.job.publish_at);
    });
  }
  function getJobs() {
    return fetch(T.url + '/rest/v1/jobs?select=id,title,location,employment_type,summary,responsibilities,requirements,publish_at&order=publish_at.desc', { headers: { apikey: T.key } })
      .then(function (r) { if (!r.ok) throw new Error('jobs'); return r.json(); });
  }

  // ----- results, in the same table design as the job list -----
  function showResults(name, ranked) {
    $('find-name').textContent = name ? 'Matches for ' + name : 'Your matches';
    $('find-summary').textContent = ranked.length === 1 ? 'One opening fits your resume. Highest match first.' : ranked.length + ' openings fit your resume. Highest match first.';
    var list = $('find-results');
    list.textContent = '';
    ranked.forEach(function (r) {
      var j = r.job, row = el('article', 'job-row has-match'), href = 'job.html?id=' + encodeURIComponent(j.id);
      var h = el('h3', 'job-title'), a = el('a', null, j.title);
      a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
      h.appendChild(a);
      row.appendChild(h);
      row.appendChild(el('p', 'job-loc', j.location));
      var tp = el('p', 'job-type');
      tp.appendChild(el('span', 'type-pill', j.employment_type));
      row.appendChild(tp);
      row.appendChild(el('p', 'job-age', J.ago ? J.ago(j.publish_at) : ''));
      row.appendChild(el('p', 'job-match', r.pct + '% Match'));
      var view = el('a', 'btn btn-white btn-sm', 'View role');
      view.href = href; view.target = '_blank'; view.rel = 'noopener noreferrer';
      row.appendChild(view);
      list.appendChild(row);
    });
    show('results');
  }
  function showNone(name) {
    $('find-none-name').textContent = name ? 'Thank you, ' + name + '.' : 'Thank you.';
    show('none');
  }

  // ----- the flow -----
  var messages = {
    type: 'That file type is not supported. Please upload your resume again as a PDF, Word (.docx) or text file.',
    size: 'That file is larger than 5 MB. Please upload your resume again in a smaller file.',
    empty: 'We could not read any text in that file. Please upload your resume again as a PDF with selectable text, a Word document or a text file.',
    open: 'We could not open that file. Please upload your resume again, or try a different format.',
    notresume: 'That file does not look like a resume. Please upload the correct resume again, with your contact details, experience and skills.'
  };
  function run() {
    if (!state.file || state.busy) return;
    state.busy = true;
    show('checking');
    var started = 0;
    readResume(state.file).then(function (text) {
      var bad = check(text);
      if (bad) throw problem(bad);
      return { text: text, name: findName(text, state.file.name) };
    }).then(function (r) {
      show('valid');
      return wait(1500).then(function () { return r; });
    }).then(function (r) {
      show('matching');
      started = Date.now();
      return getJobs().then(function (jobs) {
        var ranked = rank(r.text, jobs);
        r.text = null;                                   // the resume text is not kept
        return wait(Math.max(0, 2800 - (Date.now() - started))).then(function () { return { name: r.name, ranked: ranked }; });
      });
    }).then(function (x) {
      setFile(null);                                     // the file is not kept either
      if (x.ranked.length) showResults(x.name, x.ranked); else showNone(x.name);
    }).catch(function (e) {
      show('upload');
      if (e && e.resume) {
        setFile(null);
        showError(messages[e.resume] || messages.open);
        zone.focus({ preventScroll: true });
      } else {
        showError('We could not load the current openings just now. Please check your connection and try again.');
      }
    }).then(function () { state.busy = false; });
  }
  matchBtn.addEventListener('click', run);

  $('find-open').addEventListener('click', openPanel);
  $('find-close').addEventListener('click', closePanel);
  Array.prototype.forEach.call(section.querySelectorAll('[data-again]'), function (b) { b.addEventListener('click', function () { reset(); zone.focus(); }); });
  Array.prototype.forEach.call(section.querySelectorAll('[data-browse]'), function (b) {
    b.addEventListener('click', function () { closePanel(); var board = $('jobs-board') || $('jobs-none'); if (board) board.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  });
  // leaving the page, or coming back to it from the back button, clears everything
  window.addEventListener('pagehide', reset);
  window.addEventListener('pageshow', function (e) { if (e.persisted) closePanel(); });
})();
