// Public jobs: the list on jobs.html and the detail view on job.html. Reads only live jobs (the database enforces that).
(function () {
  var T = window.TRIADA;
  if (!T) return;

  function get(path) {
    return fetch(T.url + '/rest/v1/' + path, { headers: { apikey: T.key } }).then(function (r) {
      if (!r.ok) throw new Error('bad response');
      return r.json();
    });
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  // text with the searched words wrapped in <mark class="hit"> (brand orange); no HTML is ever inserted
  function mark(node, text, term) {
    var lower = text.toLowerCase(), at, i = 0;
    if (!term || lower.length !== text.length) { node.textContent = text; return node; }
    while ((at = lower.indexOf(term, i)) !== -1) {
      if (at > i) node.appendChild(document.createTextNode(text.slice(i, at)));
      var m = document.createElement('mark');
      m.className = 'hit';
      m.textContent = text.slice(at, at + term.length);
      node.appendChild(m);
      i = at + term.length;
    }
    node.appendChild(document.createTextNode(text.slice(i)));
    return node;
  }
  function pretty(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
  // "Just now", "5h ago", "1 day ago", "3 days ago", "1 week ago", "2 months ago": worked out from the real posting time
  function ago(iso) {
    var ms = Date.now() - new Date(iso).getTime();
    if (isNaN(ms)) return '';
    var hours = ms / 36e5, days = Math.floor(ms / 864e5), n;
    if (hours < 1) return 'Just now';
    if (hours < 24) return Math.floor(hours) + 'h ago';
    if (days < 7) return days === 1 ? '1 day ago' : days + ' days ago';
    if (days < 30) { n = Math.floor(days / 7); return n === 1 ? '1 week ago' : n + ' weeks ago'; }
    if (days < 365) { n = Math.floor(days / 30); return n === 1 ? '1 month ago' : n + ' months ago'; }
    n = Math.floor(days / 365);
    return n === 1 ? '1 year ago' : n + ' years ago';
  }
  window.TriadaJobs = { ago: ago };
  function applyLink(job) {
    return 'mailto:' + T.apply + '?subject=' + encodeURIComponent('Application: ' + job.title);
  }

  // ----- list -----
  var list = document.getElementById('jobs-list');
  if (list) {
    var all = [];
    var q = document.getElementById('jq');
    var ty = document.getElementById('jtype');
    var empty = document.getElementById('jobs-empty');
    var status = document.getElementById('jobs-status');

    var render = function () {
      var term = q.value.trim().toLowerCase();
      var type = ty.value;
      list.textContent = '';
      var shown = 0;
      all.forEach(function (j) {
        var hay = (j.title + ' ' + j.location + ' ' + j.summary).toLowerCase();
        if ((term && hay.indexOf(term) === -1) || (type && j.employment_type !== type)) return;
        shown++;
        var card = el('article', 'job-row');
        var href = 'job.html?id=' + encodeURIComponent(j.id);
        var h = el('h3', 'job-title');
        var a = mark(el('a'), j.title, term);
        a.href = href;
        h.appendChild(a);
        card.appendChild(h);
        card.appendChild(mark(el('p', 'job-loc'), j.location, term));
        var tp = el('p', 'job-type');
        tp.appendChild(el('span', 'type-pill', j.employment_type));
        card.appendChild(tp);
        card.appendChild(el('p', 'job-age', ago(j.publish_at)));
        var view = el('a', 'btn btn-white btn-sm', 'View role');
        view.href = href;
        card.appendChild(view);
        list.appendChild(card);
      });
      empty.hidden = shown !== 0 || all.length === 0;
    };

    get('jobs?select=id,title,location,employment_type,summary,publish_at&order=publish_at.desc')
      .then(function (rows) {
        all = rows;
        status.hidden = true;
        document.getElementById('jobs-board').hidden = all.length === 0;
        document.getElementById('jobs-none').hidden = all.length !== 0;
        render();
      })
      .catch(function () {
        status.textContent = 'We could not load the openings just now. Please refresh, or send us your resume and we will reach out.';
        document.getElementById('jobs-none').hidden = false;
      });
    q.addEventListener('input', render);
    ty.addEventListener('change', render);
  }

  // ----- detail -----
  var box = document.getElementById('job-detail');
  if (box) {
    var id = new URLSearchParams(location.search).get('id') || '';
    var notFound = function () {
      var m = document.createElement('meta');
      m.name = 'robots'; m.content = 'noindex, follow';
      document.head.appendChild(m);
      box.textContent = '';
      box.appendChild(el('h1', null, 'This role is no longer open.'));
      box.appendChild(el('p', 'lead', 'It may have been filled or closed. See our current openings, or send us your resume and we will contact you when a match opens.'));
      var back = el('a', 'btn btn-white', 'Back');
      back.href = 'jobs.html';
      box.appendChild(back);
    };
    if (!/^[0-9a-f-]{36}$/i.test(id)) { notFound(); return; }

    get('jobs?id=eq.' + id + '&select=*').then(function (rows) {
      if (!rows.length) { notFound(); return; }
      var j = rows[0];
      document.title = j.title + ' | Triada Technologies Jobs';
      var metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc) metaDesc.setAttribute('content', (j.title + ' (' + j.employment_type + ', ' + j.location + '). ' + j.summary).slice(0, 155));
      var canon = document.querySelector('link[rel="canonical"]');
      if (canon) canon.setAttribute('href', T.site + '/job.html?id=' + id);

      box.textContent = '';
      var crumb = el('p', 'eyebrow');
      var up = el('a', 'back-link');
      up.href = 'jobs.html';
      up.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg><span>Open roles</span>';
      crumb.appendChild(up);
      box.appendChild(crumb);
      box.appendChild(el('h1', null, j.title));
      box.appendChild(el('p', 'meta', [j.location, j.employment_type, j.pay ? j.pay : null, 'Posted ' + pretty(j.publish_at)].filter(Boolean).join(' · ')));
      box.appendChild(el('p', 'lead', j.summary));
      var section = function (title, items) {
        if (!items || !items.length) return;
        box.appendChild(el('h2', null, title));
        var ul = el('ul', 'job-list');
        items.forEach(function (t) { ul.appendChild(el('li', null, t)); });
        box.appendChild(ul);
      };
      section('What you will do', j.responsibilities);
      section('What we are looking for', j.requirements);
      var row = el('div', 'job-actions');
      var back = el('a', 'btn btn-white', 'Back');
      back.href = 'jobs.html';
      var share = el('button', 'btn btn-white share-btn');
      share.type = 'button';
      share.setAttribute('data-share', '');
      share.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg><span>Share</span>';
      row.appendChild(back); row.appendChild(share);
      box.appendChild(row);
      var contact = el('p', 'meta', 'Contact us: ');
      var mail = el('a', null, T.apply); mail.href = applyLink(j);
      var tel = el('a', null, T.phone); tel.href = T.phoneHref;
      contact.appendChild(mail); contact.appendChild(document.createTextNode(' · ')); contact.appendChild(tel);
      box.appendChild(contact);

      // Google job markup, added from the live data
      var remote = /remote/i.test(j.location);
      var ld = {
        '@context': 'https://schema.org', '@type': 'JobPosting', title: j.title,
        description: '<p>' + j.summary + '</p><h3>Responsibilities</h3><ul>' + (j.responsibilities || []).map(function (x) { return '<li>' + x.replace(/</g, '&lt;') + '</li>'; }).join('') +
          '</ul><h3>Requirements</h3><ul>' + (j.requirements || []).map(function (x) { return '<li>' + x.replace(/</g, '&lt;') + '</li>'; }).join('') + '</ul>',
        datePosted: j.publish_at, employmentType: ({ 'Contract': 'CONTRACTOR', 'Contract-to-hire': 'CONTRACTOR', 'Direct hire': 'FULL_TIME', 'Temporary': 'TEMPORARY' })[j.employment_type],
        hiringOrganization: { '@type': 'Organization', name: 'Triada Technologies', sameAs: T.site },
        directApply: false
      };
      if (j.expires_at) ld.validThrough = j.expires_at;
      if (remote) {
        ld.jobLocationType = 'TELECOMMUTE';
        ld.applicantLocationRequirements = { '@type': 'Country', name: 'USA' };
      } else {
        var m = /^(?:Hybrid,\s*)?([^,]+),\s*([A-Za-z]{2})\b/.exec(j.location);
        ld.jobLocation = { '@type': 'Place', address: { '@type': 'PostalAddress', addressLocality: m ? m[1].trim() : j.location, addressRegion: m ? m[2].toUpperCase() : undefined, addressCountry: 'US' } };
      }
      var s = document.createElement('script');
      s.type = 'application/ld+json';
      s.textContent = JSON.stringify(ld).replace(/</g, '\\u003c');
      document.head.appendChild(s);
    }).catch(function () {
      box.textContent = '';
      box.appendChild(el('p', 'lead', 'We could not load this role just now. Please refresh the page.'));
    });
  }
})();
