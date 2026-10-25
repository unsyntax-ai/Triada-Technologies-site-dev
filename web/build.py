"""Generates the six Triada Technologies pages. Run: python3 build.py"""
import hashlib
import html
import json
import os
import re

NAV = [
    ("index.html", "Home"),
    ("services.html", "Services"),
    ("about.html", "About"),
    ("jobs.html", "Jobs"),
    ("insights.html", "Insights"),
    ("contact.html", "Contact"),
]

PHONE = "+1 469 396 2108"
PHONE_HREF = "tel:+14693962108"
POSTAL_CODE = "16502"          # shown on the contact page only; elsewhere the address is just city and state
EMAIL = "hr@triadatechnologies.com"
LINKEDIN = "https://www.linkedin.com/company/triada-technologies/"


SITE = "https://triadatechnologies.com"
OG_IMAGE = SITE + "/assets/og-image.jpg"            # the home picture, also the default
OG_BY_PAGE = {"services.html": "og-services.jpg", "about.html": "og-about.jpg", "jobs.html": "og-jobs.jpg", "job.html": "og-jobs.jpg",
              "contact.html": "og-contact.jpg", "insights.html": "og-insights.jpg", "insights-archive.html": "og-insights.jpg"}
LOGO_SQUARE = SITE + "/assets/favicon-512.png"        # Google shows the logo in a square, so it gets the square mark


def og_image(page_name):
    """The picture shown when this page is shared: its own one, the Insights one for every article, else the home one."""
    if page_name in OG_BY_PAGE:
        return SITE + "/assets/" + OG_BY_PAGE[page_name]
    if page_name.startswith("insight-"):
        return SITE + "/assets/og-insights.jpg"
    return OG_IMAGE
OG_ALT = "Triada Technologies, nationwide staffing based in Erie, PA"


def head(title, desc, page, schema="", og_type="website", noindex=False):
    url = SITE + "/" + ("" if page == "index.html" else page)
    e = html.escape
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large"
    og = og_image(page)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#FAFAFA">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Triada Technologies">
<meta property="og:locale" content="en_US">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{OG_ALT}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og}">
<link rel="icon" href="favicon.ico?v=2" sizes="48x48">
<link rel="icon" type="image/png" sizes="48x48" href="assets/favicon-48.png?v=2">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16.png?v=2">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png?v=2">
<link rel="icon" type="image/png" sizes="192x192" href="assets/favicon-192.png?v=2">
<link rel="icon" type="image/png" sizes="512x512" href="assets/favicon-512.png?v=2">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png?v=2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;500;600&family=Google+Sans+Flex:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/site.css">
{schema}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
'''


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def breadcrumb(*crumbs):
    """crumbs: (name, page) pairs after Home."""
    items = [("Home", "")] + [(n, p) for n, p in crumbs]
    return ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + "/" + p} for i, (n, p) in enumerate(items)]})


ORG_ID = SITE + "/#organization"


def org(with_phone=False):
    o = {"@type": ["Organization", "EmploymentAgency"], "@id": ORG_ID, "name": "Triada Technologies",
         "url": SITE + "/", "logo": {"@type": "ImageObject", "url": LOGO_SQUARE, "width": 512, "height": 512}, "image": OG_IMAGE,
         "description": "Nationwide staffing and recruitment partner headquartered in Erie, PA, providing temporary, contract, contract-to-hire, direct-hire, and executive search services across the United States.",
         "email": EMAIL, "sameAs": [LINKEDIN],
         "address": {"@type": "PostalAddress", "addressLocality": "Erie", "addressRegion": "PA", "addressCountry": "US"},
         "areaServed": {"@type": "Country", "name": "United States"},
         "knowsAbout": ["Contract staffing", "Contract-to-hire", "Direct hire placement", "Executive search", "Vendor management systems", "Technology hiring"]}
    if with_phone:                      # used on the contact page only, where the full address is shown
        o["telephone"] = PHONE
        o["address"]["postalCode"] = POSTAL_CODE
    return o


def header(active):
    if active.startswith("insight"):
        active = "insights.html"
    links = "\n".join(
        '        <li><a href="{}"{}>{}</a></li>'.format(
            href, ' aria-current="page"' if href == active else "", label)
        for href, label in NAV
    )
    return f'''<header class="site">
  <div class="wrap bar">
    <a class="brand" href="index.html" aria-label="Triada Technologies home"><img src="assets/logo.svg" width="116" height="34" alt="Triada Technologies"></a>
    <nav aria-label="Main">
      <ul>
{links}
      </ul>
    </nav>
    <div class="header-cta">
      <a class="btn btn-white" href="jobs.html">Find work</a>
      <a class="btn btn-white" href="contact.html">Hire talent</a>
    </div>
  </div>
</header>
'''


FOOTER = f'''<footer class="site-foot">
  <div class="wrap foot">
    <div>
      <img src="assets/logo.svg" width="116" height="34" alt="Triada Technologies">
      <p style="margin-top:13px">Nationwide staffing and recruitment, headquartered in Erie, PA.</p>
    </div>
    <div>
      <p>Headquartered in Erie, PA</p>
      <p><a href="mailto:{EMAIL}">{EMAIL}</a></p>
      <p><a href="contact.html">Contact page</a></p>
      <p><a href="{LINKEDIN}" target="_blank" rel="me noopener">Triada Technologies on LinkedIn</a></p>
    </div>
    <div>
      <p><a href="services.html">Services</a> · <a href="jobs.html">Jobs</a> · <a href="insights.html">Insights</a></p>
      <p><a href="about.html">About</a> · <a href="contact.html">Contact</a></p>
      <p class="copy">© 2026 Triada Technologies. All rights reserved.</p>
    </div>
  </div>
</footer>
'''


INTRO_HEAD = ('<script>(function(){var d=document.documentElement;'
              'if(window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches)return;'
              'var seen=false,nav=window.performance&&performance.getEntriesByType&&performance.getEntriesByType("navigation")[0];'
              'try{seen=sessionStorage.getItem("triada-intro")==="1"}catch(e){}'
              'if(seen&&!(nav&&nav.type==="reload"))return;'   # plays on the first visit of a browser session, and again on a reload
              'try{sessionStorage.setItem("triada-intro","1")}catch(e){}'
              'd.classList.add("intro-on");setTimeout(function(){d.classList.remove("intro-on")},9000)})()</script>\n')


def page(title, desc, page_name, body, script=False, schema="", og_type="website", noindex=False, extra=()):
    h = head(title, desc, page_name, schema, og_type, noindex)
    if page_name == "index.html":
        h = h.replace("</head>", INTRO_HEAD + "</head>", 1)
    s = (h + '<span class="top-bar-mark" aria-hidden="true"></span>\n' + header(page_name)
         + '\n<main id="main">\n' + body + '\n</main>\n\n' + FOOTER)
    if script:
        s += '\n<script src="assets/site.js"></script>\n'
    for src in extra:
        s += f'<script src="assets/{src}"></script>\n'
    return s + '</body>\n</html>\n'


SHARE_SVG = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/>'
             '<circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>')
SHARE_BTN = f'<button type="button" class="btn btn-white share-btn" data-share>{SHARE_SVG}<span>Share</span></button>'


def insights_cta(heading, text):
    """Closing call to action for the Insights pages: two clear next steps, in the same card style as the other pages."""
    return f'''

<section>
  <div class="wrap">
    <div class="cta-card">
      <div class="copy">
        <p class="eyebrow">Next step</p>
        <h2>{heading}</h2>
        <p>{text}</p>
      </div>
      <div class="cta-panel">
        <p class="label">Where would you like to start?</p>
        <a class="btn btn-solid" href="contact.html">Hire talent</a>
        <a class="btn btn-white" href="jobs.html">Find work</a>
      </div>
    </div>
  </div>
</section>
'''


def cta_card():
    return f'''<section>
  <div class="wrap">
    <div class="cta-card">
      <div class="copy">
        <p class="eyebrow">Next step</p>
        <h2>Your next great hire starts here.</h2>
        <p>Tell us about the role you need to fill, and we will find people who fit the work and your team. Share the job title, the main responsibilities, and your timeline, and a recruiter will reply during business hours with clear next steps.</p>
      </div>
      <div class="cta-panel">
        <p class="label">Email</p>
        <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
        <a class="btn btn-solid" href="contact.html">Contact us</a>
      </div>
    </div>
  </div>
</section>
'''


def ci(name, ext="jpg"):
    """Card photo. If the file has not been uploaded yet, the image removes itself so nothing looks broken."""
    return f'<img class="card-img{" art" if ext == "svg" else ""}" src="assets/cards/{name}.{ext}" alt="" width="800" height="500" loading="lazy" decoding="async" onerror="this.remove()">'


INDUSTRIES = [
    ("IT and Technology", "Software engineers, cloud and DevOps architects, cybersecurity analysts, database administrators, and system administrators for teams that depend on stable, secure systems."),
    ("Healthcare and Life Sciences", "Registered nurses, allied health professionals, medical administrators, and clinical research staff who meet strict credentialing and compliance standards."),
    ("Finance and Accounting", "CPAs, financial analysts, accounts payable and receivable specialists, internal auditors, and tax professionals for accurate, on-time financial operations."),
    ("Engineering and Construction", "Mechanical, electrical, and civil engineers, project managers, and technical drafters who keep complex projects moving within scope and schedule."),
    ("Administrative and Clerical", "Executive assistants, office coordinators, data entry specialists, and general office support that keeps daily operations organized and efficient."),
    ("Manufacturing and Industrial", "Production supervisors, quality control inspectors, CNC machinists, and assembly teams trained to your safety and production standards."),
    ("Logistics and Supply Chain", "Warehouse managers, inventory planners, logistics coordinators, and distribution specialists who keep goods moving from supplier to customer."),
    ("Telecommunications", "Network technicians, fiber installers, RF engineers, and telecom project coordinators for reliable connectivity and infrastructure build-outs."),
    ("Retail and Customer Support", "Call center agents, customer service representatives, retail managers, and customer experience specialists who represent your brand every day."),
]
industries_html = "\n".join(
    f'      <div class="card">{ci("industry-" + t.lower().replace(" and ", "-").replace(" ", "-"), "svg")}<h3>{t}</h3><p>{d}</p></div>' for t, d in INDUSTRIES)

STEPS = [
    ("Consultation", "We confirm the requirements, the technical skills, the team culture, the working schedule, and the timeline. A clear brief makes every later step faster."),
    ("Sourcing", "We search our local candidate database, industry networks, and referrals to find people who match the role, including those who are not actively looking."),
    ("Screening", "Each candidate completes skill reviews and behavioral interviews, and we verify background and credentials where the role requires it."),
    ("Presentation", "You receive a short list with each candidate's qualifications, experience, and fit for your team, summarized so you can decide quickly."),
    ("Placement", "We coordinate interviews, help with offer terms, and manage the paperwork and onboarding so the new hire starts on the right foot."),
    ("Follow-up", "We check in with you and the new hire during the first weeks, so any concern is addressed early and the placement succeeds."),
]
steps_html = "\n".join(
    f'      <li><h3>{t}</h3><p>{d}</p></li>' for t, d in STEPS)

# ---------- HOME ----------
HOME_SCHEMA = ld({"@context": "https://schema.org", "@graph": [
    org(),
    {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Triada Technologies",
     "inLanguage": "en-US", "publisher": {"@id": ORG_ID}},
]})

MARQUEE_ITEMS = [
    ("IT and technology", "industry-it-technology"), ("Healthcare", "industry-healthcare-life-sciences"),
    ("Finance and accounting", "industry-finance-accounting"), ("Engineering", "industry-engineering-construction"),
    ("Administrative", "industry-administrative-clerical"), ("Manufacturing", "industry-manufacturing-industrial"),
    ("Logistics", "industry-logistics-supply-chain"), ("Telecommunications", "industry-telecommunications"),
    ("Retail and support", "industry-retail-customer-support"),
]
MARQUEE = "".join(f'<span><img src="assets/icons/{icon}.svg" alt="" width="44" height="44" decoding="async"><b>{name}</b></span>'
                  for name, icon in MARQUEE_ITEMS)

home = f'''<div class="opening" id="opening" aria-hidden="true"><div class="opening-top"></div><div class="opening-bottom"></div><span class="opening-bar a"></span><span class="opening-bar b"></span></div>
<section class="hero-full hero-split" aria-label="Introduction">
  <div class="hero-center">
    <img class="hero-logo" src="assets/hero-logo.png" alt="Triada Technologies" width="1400" height="367">
    <h1>Creating value<br> for <span class="swap">everyone</span>.</h1>
    <p class="eyebrow">Nationwide staffing, based in Erie, PA</p>
  </div>
  <figure class="hero-photo">
    <img class="hero-img" src="assets/hero-city.jpg" alt="A smiling professional celebrating at her laptop" width="2200" height="1261" fetchpriority="high" decoding="async">
  </figure>
</section>

<section id="intro" class="intro">
  <div class="wrap hero-grid">
    <div>
      <p class="lead">Creating value for every side of the hiring journey. Triada Technologies connects clients, vendors, and candidates across the United States through temporary, contract, contract-to-hire, and direct-hire staffing. We keep the process clear, the screening careful, and every placement built to last.</p>
      <div class="hero-actions">
        <a class="btn btn-white" href="contact.html">Hire talent</a>
        <a class="btn btn-white" href="jobs.html">Find work</a>
      </div>
    </div>
    <aside class="hook" aria-label="Why hiring speed matters">
      <p class="eyebrow">The real cost of waiting</p>
      <strong>Every open seat slows down the work your team was hired to do.</strong>
      <p>Projects stall, deadlines slip, and the people already carrying the load start to feel the strain. We find candidates who match the role and the team, screen them with care, and bring them in ready to contribute. Once the seat is filled, your team can return to its best work, with the steady confidence that progress is moving again.</p>
    </aside>
  </div>
</section>

<div class="marquee" aria-hidden="true">
  <div class="marquee-track">
    {MARQUEE}
    {MARQUEE}
  </div>
</div>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Our approach</p>
      <h2>Clear requirements, <em>careful screening</em>, honest follow-up.</h2>
      <p class="lead">A good placement starts well before the first interview. We take the time to understand the role, so the candidates you see reflect what your team truly needs.</p>
    </div>
    <div class="values">
      <div class="card">{ci("values-requirements")}<h3>Clear requirements</h3><p>We confirm the skills, working environment, schedule, and the outcomes that define success for the role before we begin sourcing.</p></div>
      <div class="card">{ci("values-screening")}<h3>Careful screening</h3><p>Every candidate is reviewed for technical fit, communication, and reliability, so the shortlist you receive is ready for a decision.</p></div>
      <div class="card">{ci("values-followup")}<h3>Honest follow-up</h3><p>We stay in touch after the start date with you and the new hire, so small concerns are resolved early instead of becoming problems.</p></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Services</p>
      <h2>Four ways to bring talent <em>on board</em></h2>
      <p class="lead">Choose the arrangement that matches your hiring need, budget, and timeline. We will help you decide which one fits the role best.</p>
    </div>
    <div class="trio four">
      <div class="card">{ci("service-temporary")}<h3>Temporary and contract</h3><p>Short-term and project-based professionals who can start quickly and work to your schedule, for seasonal demand, special projects, and backfill coverage.</p></div>
      <div class="card">{ci("service-contract-to-hire")}<h3>Contract-to-hire</h3><p>Work with a candidate first, then decide whether to bring them on permanently. You see their work in your own environment before making a long-term commitment.</p></div>
      <div class="card">{ci("service-direct-hire")}<h3>Direct hire</h3><p>Permanent placements with a shortlist built around the role, your team, and your culture. We handle sourcing, screening, and coordination from first call to offer.</p></div>
      <div class="card">{ci("service-executive")}<h3>Executive search</h3><p>Senior search for leadership roles, with a shortlist built around the role, your team, and the level of responsibility it carries.</p></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Clients and candidates</p>
      <h2>Built for both sides of the <em>hiring journey</em></h2>
    </div>
    <div class="duo">
      <div class="card">
        {ci("for-clients")}
        <h3>For clients</h3>
        <p>Tell us what you need to staff. We will send a shortlist built around your team, your budget, your timeline, and the way your team works day to day. You stay in control of every decision, from interviews to offers.</p>
        <a class="btn btn-white" href="contact.html">Hire talent</a>
      </div>
      <div class="card">
        {ci("for-candidates")}
        <h3>For candidates</h3>
        <p>Share your resume and the roles you want. Our recruiters review your background, match you with openings that fit your skills, and keep you informed at every step. We will reach out when a matching opportunity comes up.</p>
        <a class="btn btn-white" href="jobs.html">Find work</a>
      </div>
    </div>
  </div>
</section>

{cta_card()}'''

# ---------- SERVICES ----------
SERVICES_SCHEMA = ""

FAQ_ITEMS = [
    ("What staffing services does Triada Technologies offer?",
     "Triada Technologies offers temporary, contract, contract-to-hire, direct-hire, and executive search placements, along with vendor management programs for ongoing workforce needs. Our primary focus is IT and technology staffing, and we also place professionals in healthcare, finance, engineering, administrative, manufacturing, logistics, telecommunications, and customer support roles."),
    ("What IT and technology roles does Triada Technologies place?",
     "We place software engineers, cloud and DevOps architects, cybersecurity analysts, database administrators, and system administrators, along with network technicians and telecom project coordinators. Each search starts with the technical skills, tools, and team environment the role requires, so the candidates we present match the work and not only the job title."),
    ("Which industries does Triada Technologies serve?",
     "IT and technology is our primary focus. We also serve healthcare and life sciences, finance and accounting, engineering and construction, administrative and clerical, manufacturing and industrial, logistics and supply chain, telecommunications, and retail and customer support. We tailor each search to the skills, credentials, and compliance standards of the industry."),
    ("What is the difference between contract, contract-to-hire, and direct-hire placement?",
     "Contract placement brings in a professional for a defined period or project, such as covering a skills gap or a spike in workload. Contract-to-hire starts as a contract and lets you evaluate the person in your own environment before offering a permanent role. Direct hire fills a permanent position from the first day. We help you choose the model that fits the role, your budget, and your timeline."),
    ("How does Triada Technologies screen candidates?",
     "Every candidate completes a skills review and a behavioral interview, and we verify background and credentials where the role requires it. For IT roles, the review covers the specific technical skills the position demands. We assess fit, communication, and reliability before presenting a short list, so you receive candidates who are ready for a hiring decision."),
    ("How long does it take to fill a role?",
     "The timeline depends on the seniority of the role, how specialized the skills are, the location, and how clearly the requirements are defined. Specialized technical roles, such as cybersecurity or cloud architecture, can take longer to source than general support roles. We confirm the requirements and the timeline in the first consultation, so you know what to expect before sourcing begins."),
    ("Does Triada Technologies work outside Pennsylvania?",
     "Yes. Triada Technologies is headquartered in Erie, Pennsylvania, and places talent for employers across the United States, with a focus on IT and technology roles. For every role, we confirm the working environment, schedule, and location expectations, such as onsite, hybrid, or remote work, before we begin sourcing."),
    ("How much do staffing services cost?",
     "Cost depends on the engagement model, the role, the skills required, and the location. In the staffing industry, contract and temporary work is commonly billed at an hourly rate, and direct hire is commonly billed as a fee tied to the placed candidate's compensation. We confirm terms for your specific role after the initial consultation. Contact us with the position you need to fill."),
    ("How do I start a search with Triada Technologies?",
     f'Share the job title, the main responsibilities, the skills and experience level the role needs, and your timeline. A recruiter reviews the details and replies during business hours with clear next steps. Use our <a href="contact.html">contact page</a> or email {EMAIL} to begin.'),
]
faq_html = "\n".join(
    f'      <details class="faq-item">\n        <summary><h3>{q}</h3><span class="faq-icon" aria-hidden="true"></span></summary>\n        <div class="faq-a"><p>{a}</p></div>\n      </details>' for q, a in FAQ_ITEMS)

services = f'''<section class="page-hero" style="border-top:0">
  <div class="wrap">
    <p class="eyebrow">Services</p>
    <h1>Staffing for <em>every stage</em> of hiring.</h1>
    <p class="lead">Temporary, contract, contract-to-hire, direct placement, and executive search, with vetted talent across nine industries, for employers nationwide. We shape each engagement around your schedule, your budget, and the level of responsibility the role carries.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Arrangements</p>
      <h2>Four ways to staff your team</h2>
      <p class="lead">Each arrangement balances speed, cost, and commitment differently. We will help you choose the one that fits your situation.</p>
    </div>
    <div class="quad">
      <div class="card">{ci("service-temporary")}<h3>Temporary and contract</h3><p>Short-term and project-based professionals who can start quickly and work to your schedule. Ideal for seasonal demand, special projects, and backfill coverage.</p></div>
      <div class="card">{ci("service-contract-to-hire")}<h3>Contract-to-hire</h3><p>Work with a candidate first, then decide whether to bring them on permanently. You see their work in your environment before making a long-term commitment.</p></div>
      <div class="card">{ci("service-direct-hire")}<h3>Direct hire</h3><p>Permanent placements with a shortlist built around the role, the team, and the culture. We manage sourcing, screening, and coordination from start to offer.</p></div>
      <div class="card">{ci("service-executive")}<h3>Executive search and VMS</h3><p>Senior search for leadership roles, plus vendor management programs that keep ongoing workforce needs organized, compliant, and cost-aware.</p></div>
    </div>
  </div>
</section>

<section id="industries">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Industries</p>
      <h2>Talent across the sectors we support</h2>
      <p class="lead">From technical specialists to administrative support, we place people who meet your industry's requirements, credentials, and standards.</p>
    </div>
    <div class="industries">
{industries_html}
    </div>
  </div>
</section>

<section id="process">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Process</p>
      <h2>How a placement works</h2>
      <p class="lead">Six clear steps, from the first conversation to a placement that keeps performing after the start date.</p>
    </div>
    <ol class="steps">
{steps_html}
    </ol>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Questions</p>
      <h2>Common questions about working with Triada Technologies</h2>
    </div>
    <div class="faq-list">
{faq_html}
    </div>
  </div>
</section>

{cta_card()}'''

# ---------- ABOUT ----------
about = f'''<section class="page-hero" style="border-top:0">
  <div class="wrap">
    <p class="eyebrow">About</p>
    <h1>Connecting clients, <em>vendors, and candidates.</em></h1>
    <p class="lead">Triada Technologies is a multi-industry staffing and workforce solutions partner headquartered in Erie, Pennsylvania, serving employers and professionals across the United States. We build smart, long-term relationships that help organizations grow and help professionals move their careers forward.</p>
  </div>
</section>

<section>
  <div class="wrap prose">
    <div>
      <p class="eyebrow">Who we are</p>
      <h2>A multi-industry staffing partner</h2>
    </div>
    <div>
      <p class="body">Triada Technologies is a multi-industry recruitment and workforce solutions partner headquartered in Erie, Pennsylvania. We connect organizations across the United States with skilled talent across technology, healthcare, finance, engineering, logistics, and more, with a focus on roles that are hard to fill and on teams that need dependable support.</p>
      <p class="body">We work to bridge the gap between candidates, vendors, and client goals. Every engagement begins with understanding the work itself, so that the people we place can succeed in their roles and the organizations we serve can keep their momentum.</p>
      <p class="body">Our team focuses on quality, reliability, and speed in every partnership. We would rather be precise and honest with you than promise more than the role can deliver.</p>
    </div>
  </div>
</section>

<section>
  <div class="wrap prose">
    <div>
      <p class="eyebrow">Mission</p>
      <h2>What we commit to</h2>
    </div>
    <div>
      <ul class="mission-list">
        <li>Build recruitment solutions that match our clients' business goals, culture, and timelines.</li>
        <li>Connect job seekers with opportunities that fit their skills and their long-term career goals.</li>
        <li>Work with vendors to build staffing programs that are efficient, compliant, and able to scale with demand.</li>
        <li>Hold every placement to a high standard of professionalism, speed, and accuracy.</li>
      </ul>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">Vision</p>
    <div class="prose prose-aligned">
      <h2>Where we are going</h2>
      <p class="body">To be the most trusted workforce solutions provider for employers and professionals across the United States, recognized for building high-performing teams and for fostering long-term relationships that outlast any single placement.</p>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Core values</p>
      <h2>How we work</h2>
      <p class="lead">Six principles guide our recruiters, from the first call to the final follow-up.</p>
    </div>
    <div class="values">
      <div class="card">{ci("about-integrity", "svg")}<h3>Integrity</h3><p>We are open, honest, and ethical in every business dealing, including when the answer is not the one someone hoped to hear.</p></div>
      <div class="card">{ci("about-collaboration", "svg")}<h3>Collaboration</h3><p>We work across teams to meet the needs of clients, candidates, and partners, and we keep everyone informed as the work moves forward.</p></div>
      <div class="card">{ci("about-excellence", "svg")}<h3>Excellence</h3><p>We hold every placement and every service to a high standard, and we check the details before we present a candidate or a proposal.</p></div>
      <div class="card">{ci("about-commitment", "svg")}<h3>Commitment</h3><p>We care about the long-term success of both the businesses we serve and the professionals we place, not only the first day of work.</p></div>
      <div class="card">{ci("about-people-first", "svg")}<h3>People first</h3><p>We put human connection and personal career goals ahead of transactions, because the right fit is the one that lasts.</p></div>
      <div class="card">{ci("about-innovation", "svg")}<h3>Innovation</h3><p>We use modern recruiting tools and practices to make staffing faster, clearer, and easier to measure for the teams we support.</p></div>
    </div>
  </div>
</section>'''

# ---------- JOBS ----------
jobs = '''<section class="page-hero" style="border-top:0">
  <div class="wrap">
    <div class="page-hero-row">
      <div>
        <p class="eyebrow">Jobs</p>
        <h1>Open <em>roles.</em></h1>
        <p class="lead">Your next opportunity could be here. Upload your resume and discover your matches, without searching listing by listing. Prefer to browse? Current openings with our clients are listed below, each with a clear description of the responsibilities, skills, and location. If nothing fits yet, send us your resume and we will contact you when a suitable role opens.</p>
      </div>
      <div class="jobs-cta">
        <button class="btn btn-solid" type="button" id="find-open">Find a Job</button>
        <div class="admin-slot">
          <a class="btn btn-solid" href="admin.html">Post a job</a>
          <small>Admin only</small>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="find" id="find-section" hidden>
  <div class="wrap">
    <div class="find-card" id="find-panel" aria-live="polite">
      <button type="button" class="link-btn find-close" id="find-close">Close</button>

      <div class="find-step" data-step="upload">
        <h2 tabindex="-1" data-focus>Find your best matches</h2>
        <p class="find-lead">Upload your resume and we will match you with the latest openings at Triada Technologies.</p>
        <div class="dropzone" id="dropzone" tabindex="0" role="button" aria-label="Upload your resume. Drag and drop a file here, or press Enter to choose one.">
          <input type="file" id="resume-file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" hidden>
          <svg class="dz-icon" viewBox="0 0 48 48" width="48" height="48" aria-hidden="true"><rect x="6" y="30" width="36" height="12" rx="6" fill="#1E3A8A"/><path d="M24 6v24" stroke="#14B8A6" stroke-width="5" stroke-linecap="round"/><path d="M14 16l10-10 10 10" fill="none" stroke="#14B8A6" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="37" cy="36" r="2.5" fill="#FF6A00"/></svg>
          <p class="dz-main">Drag and drop your resume here</p>
          <p class="dz-sub">or <span class="dz-link">choose a file</span>. PDF, Word (.docx) or text, up to 5 MB.</p>
          <div class="dz-file" id="dz-file" hidden>
            <span class="dz-name"></span><span class="dz-size"></span>
            <button type="button" class="link-btn dz-remove" id="dz-remove">Remove</button>
          </div>
        </div>
        <p class="find-privacy">Your privacy matters. Your resume is used only for this search session and is never stored. Close your browser or refresh the page, and your session data will be cleared.</p>
        <p class="find-error" id="find-error" role="alert" hidden></p>
        <button class="btn btn-solid" type="button" id="match-btn" disabled>Match My Resume</button>
      </div>

      <div class="find-step find-center" data-step="checking" hidden>
        <div class="spinner" aria-hidden="true"></div>
        <h2 tabindex="-1" data-focus>Checking your resume</h2>
        <p class="find-lead">This only takes a moment.</p>
      </div>

      <div class="find-step find-center" data-step="valid" hidden>
        <svg class="tick" viewBox="0 0 80 80" width="88" height="88" aria-hidden="true"><circle class="tick-ring" cx="40" cy="40" r="34"/><path class="tick-mark" d="M24 41l11 11 21-24"/></svg>
        <h2 tabindex="-1" data-focus>Your resume looks good</h2>
        <p class="find-lead">We could read it clearly.</p>
      </div>

      <div class="find-step find-center" data-step="matching" hidden>
        <div class="match-loader" aria-hidden="true"><i></i><i></i></div>
        <h2 tabindex="-1" data-focus>Finding Your Best Matches</h2>
        <p class="find-lead">Matching your profile with the latest opportunities at Triada Technologies.</p>
      </div>

      <div class="find-step" data-step="results" hidden>
        <h2 tabindex="-1" data-focus id="find-name"></h2>
        <p class="find-lead" id="find-summary"></p>
        <div class="job-row job-head has-match" aria-hidden="true"><span>Title</span><span>Location</span><span>Type</span><span>Posted</span><span>Match</span><span></span></div>
        <div id="find-results" class="jobs-rows"></div>
        <div class="find-actions"><button type="button" class="btn btn-white" data-again>Upload a different resume</button></div>
      </div>

      <div class="find-step find-center" data-step="none" hidden>
        <svg class="none-mark" viewBox="0 0 728 77" width="120" height="13" aria-hidden="true"><g fill="#FF6A00"><path transform="translate(18 0)" d="M30 0H710L696 29H0C0 12 12 0 30 0Z"/><path transform="translate(0 48)" d="M16 0H710V14C710 23 703 29 692 29H0Z"/></g></svg>
        <h2 tabindex="-1" data-focus id="find-none-name"></h2>
        <p class="find-lead">We do not have an opening that closely fits your resume today, but new roles are added often. You can browse every current opening, check back soon, or send us your resume and a recruiter will reach out when a suitable role opens.</p>
        <div class="find-actions">
          <button type="button" class="btn btn-solid" data-browse>Browse all openings</button>
          <a class="btn btn-white" href="contact.html">Send us your resume</a>
          <button type="button" class="btn btn-white" data-again>Try another resume</button>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="listing">
  <div class="wrap">
    <p id="jobs-status" class="archive-empty">Loading open roles...</p>
    <noscript><p class="archive-empty">Turn on JavaScript to see the current openings, or send us your resume and we will reach out.</p></noscript>
    <div id="jobs-board" hidden>
      <div class="toolbar toolbar-jobs">
        <label for="jq">Search
          <input id="jq" type="search" placeholder="Search by title or location" autocomplete="off">
        </label>
        <label for="jtype">Type
          <select id="jtype"><option value="">All types</option><option>Contract</option><option>Contract-to-hire</option><option>Direct hire</option><option>Temporary</option></select>
        </label>
      </div>
      <div class="job-row job-head" aria-hidden="true"><span>Title</span><span>Location</span><span>Type</span><span>Posted</span><span></span></div>
      <div id="jobs-list" class="jobs-rows"></div>
      <p id="jobs-empty" class="archive-empty" hidden>No roles match your search.</p>
    </div>
    <div id="jobs-none" hidden>
      <div class="section-head">
        <p class="eyebrow">Current openings</p>
        <h2>No openings listed right now</h2>
        <p class="lead">Our recruiters are always building their candidate pipeline. Send us your resume and the roles you are looking for, and we will reach out when a matching position opens.</p>
      </div>
    </div>
  </div>
</section>

<section class="recruiter-note">
  <div class="wrap">
    <h3>Contact the recruiter to discuss</h3>
    <p><a href="mailto:%%EMAIL%%">%%EMAIL%%</a> &middot; <a href="%%PHONE_HREF%%">%%PHONE%%</a></p>
  </div>
</section>'''.replace("%%EMAIL%%", EMAIL).replace("%%PHONE_HREF%%", PHONE_HREF).replace("%%PHONE%%", PHONE)

job_detail = '''<section class="page-hero hero-carded" style="border-top:0">
  <div class="wrap">
    <div class="hero-card" id="job-detail"><p class="lead">Loading role...</p></div>
  </div>
</section>'''

def otp_boxes(box_id, label, password=True, one_time=False):
    kind = 'type="password" ' if password else ""
    out = []
    for n in range(1, 7):
        extra = ' autocomplete="one-time-code"' if (one_time and n == 1) else ' autocomplete="off"'
        out.append(f'<input {kind}inputmode="numeric"{extra} maxlength="1" aria-label="{label} digit {n}">')
    return f'<div class="otp" id="{box_id}" role="group" aria-label="{label}">' + "".join(out) + "</div>"


TICK = ('<svg class="tick" viewBox="0 0 80 80" width="88" height="88" aria-hidden="true">'
        '<circle class="tick-ring" cx="40" cy="40" r="34"/><path class="tick-mark" d="M24 41l11 11 21-24"/></svg>')

CAL = ('<svg class="a-cal" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" '
       'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="3"/>'
       '<path d="M3 10h18M8 3v4M16 3v4"/></svg>')

admin_page = f'''<section class="page-hero hero-carded" style="border-top:0">
  <div class="wrap">
    <div class="hero-card admin-hero">
      <button class="btn btn-white btn-sm a-signout" type="button" id="a-out" hidden>Sign out</button>
      <p class="eyebrow">Admin</p>
      <h1>Post and manage jobs.</h1>
      <ul class="a-tips">
        <li>Paste the job description without contact details, then review the draft before it goes live.</li>
        <li>Schedule publishes a job automatically at the time you choose.</li>
        <li>Archive takes a job off the Jobs page. Delete removes it for good.</li>
      </ul>
    </div>
  </div>
</section>

<section class="listing" id="a-signin">
  <div class="wrap">
    <div class="card admin-card">

      <div id="a-gate-pin">
        <h2>Enter PIN</h2>
        {otp_boxes("a-pin", "PIN")}
        <div class="a-pin-slot">
          <p id="a-pin-msg" class="a-msg" role="alert"></p>
        </div>
        <p class="form-note"><button class="link-btn" type="button" id="a-forgot">Forgot PIN?</button></p>
      </div>

      <div id="a-gate-email" hidden>
        <label for="a-email" class="gate-title">Enter admin email address
          <input id="a-email" type="email" autocomplete="email" placeholder="you@example.com">
        </label>
        <p class="form-note">Don't have the admin email? Contact your administrator.</p>
        <button class="btn btn-solid" type="button" id="a-send">Send Code</button>
        <p id="a-msg" class="a-msg" role="alert"></p>
        <p class="form-note"><button class="link-btn" type="button" id="a-back-pin">Back</button></p>
      </div>

      <div id="a-gate-reset" hidden>
        <div class="a-sect" id="a-sect-code">
          <span class="otp-label gate-title">Enter 6-digit verification code</span>
          {otp_boxes("a-code", "Verification code", password=False, one_time=True)}
          <p id="a-code-msg" class="a-msg" role="alert"></p>
        </div>
        <div class="a-sect">
          <span class="otp-label gate-title">Enter new 6-digit PIN</span>
          {otp_boxes("a-new-pin", "New PIN")}
          <p id="a-new-msg" class="a-msg" role="alert"></p>
        </div>
        <div class="a-sect">
          <span class="otp-label gate-title">Confirm new PIN</span>
          {otp_boxes("a-confirm-pin", "Confirm new PIN")}
          <p id="a-conf-msg" class="a-msg" role="alert"></p>
        </div>
        <p class="form-note"><button class="link-btn" type="button" id="a-back-reset">Back</button></p>
      </div>

      <div id="a-gate-done" class="a-done" hidden role="status">
        {TICK}
        <h2>PIN changed successfully</h2>
      </div>

    </div>
  </div>
</section>

<div id="a-app" hidden>
  <section class="listing">
    <div class="wrap">

      <div class="card admin-card">
        <h2>Enter the Job Description</h2>
        <p>Paste the job description below without contact details.</p>
        <textarea id="a-notes" aria-label="Job description" placeholder="Paste the job description here"></textarea>
        <button class="btn btn-solid" type="button" id="a-draft">Draft Job Post</button>
        <p id="a-draft-msg" class="a-msg" role="status"></p>
      </div>

      <div class="card admin-card">
        <h2 id="form-title">Job Post Preview</h2>
        <p>Review and edit your job post before publishing.</p>
        <div id="f-confirm" class="a-confirm" hidden></div>
        <label for="f-title">Job title <input id="f-title" maxlength="120"></label>
        <div class="field-row">
          <label for="f-location">Location <input id="f-location" maxlength="120" placeholder="City, ST or Remote (U.S.)"></label>
          <label for="f-type">Type
            <select id="f-type"><option>Contract</option><option>Contract-to-hire</option><option>Direct hire</option><option>Temporary</option></select>
          </label>
        </div>
        <label for="f-pay">Pay (optional, shown to candidates) <input id="f-pay" maxlength="120" placeholder="Leave empty to hide"></label>
        <label for="f-summary">Summary <textarea id="f-summary" maxlength="6000"></textarea></label>
        <label for="f-resp">Responsibilities (one per line) <textarea id="f-resp"></textarea></label>
        <label for="f-req">Requirements (one per line) <textarea id="f-req"></textarea></label>
        <div class="a-acts a-publish">
          <button class="btn btn-solid" type="button" id="f-now">Publish Now</button>
          <button class="btn btn-white" type="button" id="f-schedule" aria-haspopup="dialog">{CAL}Schedule</button>
          <button class="btn btn-white" type="button" id="f-draft">Save as Draft</button>
          <button class="btn btn-white" type="button" id="f-clear">Clear</button>
        </div>
        <input id="f-when" type="hidden">
        <div id="f-clear-ask" class="a-confirm a-ask" hidden role="alert">
          <span>Clear everything you entered? Unsaved work will be lost.</span>
          <span class="a-acts">
            <button class="btn btn-solid btn-sm" type="button" id="f-clear-yes">Yes, clear</button>
            <button class="btn btn-white btn-sm" type="button" id="f-clear-no">Keep editing</button>
          </span>
        </div>
        <p id="f-msg" class="a-msg" role="status"></p>
      </div>

      <div class="card admin-card">
        <h2>Your jobs</h2>
        <input id="a-search" type="search" placeholder="Search all jobs" aria-label="Search all jobs" autocomplete="off">
        <div class="a-tabs" role="tablist" aria-label="Your jobs">
          <button type="button" role="tab" class="a-tab" data-tab="published" aria-selected="true">Published Jobs <span class="a-count"></span></button>
          <button type="button" role="tab" class="a-tab" data-tab="draft" aria-selected="false">Saved Drafts <span class="a-count"></span></button>
          <button type="button" role="tab" class="a-tab" data-tab="archived" aria-selected="false">Archived <span class="a-count"></span></button>
        </div>
        <p id="a-arch-note" class="form-note" hidden>Archived jobs are not shown on the website and are deleted permanently after 365 days.</p>
        <p id="a-jobs-msg" class="a-msg" role="status"></p>
        <div class="a-table-wrap">
          <table class="a-table">
            <thead><tr><th>Job</th><th>Location</th><th>Type</th><th>Posted</th><th><span class="sr-only">Actions</span></th></tr></thead>
            <tbody id="a-jobs"></tbody>
          </table>
        </div>
        <div class="a-pager">
          <button class="btn btn-white btn-sm" type="button" id="a-prev">Previous</button>
          <span id="a-page" aria-live="polite"></span>
          <button class="btn btn-white btn-sm" type="button" id="a-next">Next</button>
        </div>
      </div>
    </div>
  </section>
</div>
<div id="f-sched" class="sched-back" hidden>
  <div class="sched" role="dialog" aria-modal="true" aria-labelledby="sched-title">
    <button type="button" class="sched-x" id="sched-close" aria-label="Close">&times;</button>
    <h3 id="sched-title">Schedule job</h3>
    <p class="sched-pick" id="sched-pick" aria-live="polite"></p>
    <div id="sched-date">
      <div class="cal-head">
        <button type="button" class="cal-nav" id="cal-prev" aria-label="Previous month">&lsaquo;</button>
        <strong id="cal-month"></strong>
        <button type="button" class="cal-nav" id="cal-next" aria-label="Next month">&rsaquo;</button>
      </div>
      <div class="cal-grid cal-dow" aria-hidden="true"><span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span></div>
      <div class="cal-grid" id="cal-days"></div>
    </div>
    <div id="sched-time" hidden>
      <div class="time-cols">
        <div class="time-col" id="t-hour" role="group" aria-label="Hour"></div>
        <div class="time-col" id="t-min" role="group" aria-label="Minutes"></div>
        <div class="time-col" id="t-ap" role="group" aria-label="AM or PM"></div>
      </div>
      <button type="button" class="link-btn" id="sched-back">Change date</button>
    </div>
    <p id="sched-msg" class="a-msg bad" role="alert"></p>
    <button class="btn btn-solid" type="button" id="sched-go" disabled>Confirm Schedule</button>
  </div>
</div>
'''

# ---------- INSIGHTS ----------
import datetime as dt
import json
import os

SITE_URL = "https://triadatechnologies.com"
LIVE_DAYS = 30
BASE = os.path.dirname(os.path.abspath(__file__))


def build_date():
    v = os.environ.get("BUILD_DATE")
    return dt.date.fromisoformat(v) if v else dt.date.today()


def load_posts():
    d = os.path.join(BASE, "data", "insights")
    posts = []
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if n.endswith(".json"):
                with open(os.path.join(d, n), encoding="utf-8") as f:
                    posts.append(json.load(f))
    posts.sort(key=lambda p: p["published"], reverse=True)
    return posts


def pretty(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


def art_src(p):
    return f"assets/insights/{p['slug']}.svg" if p.get("has_art") else "assets/illustration.svg"


def post_card(p):
    url = f"insight-{p['slug']}.html"
    e = html.escape
    hay = e((p['title'] + ' ' + p['summary'] + ' ' + p['tag']).lower(), quote=True)
    return f'''      <article class="card post-card" data-item data-date="{p['published']}" data-text="{hay}">
        <a class="post-art pal-{e(p['palette'])}" href="{url}" aria-hidden="true" tabindex="-1"><img src="{art_src(p)}" alt="" width="485" height="300" loading="lazy"></a>
        <div class="post-text">
          <h3><a href="{url}">{e(p['title'])}</a></h3>
          <p class="meta">{pretty(p['published'])} · {e(p['tag'])}</p>
        </div>
      </article>'''


def archive_row(p):
    url = f"insight-{p['slug']}.html"
    e = html.escape
    hay = e((p['title'] + ' ' + p['summary'] + ' ' + p['tag']).lower(), quote=True)
    return (f'      <li class="archive-row" data-item data-date="{p["published"]}" data-text="{hay}">'
            f'<a href="{url}">{e(p["title"])}</a><span>{pretty(p["published"])} · {e(p["tag"])}</span></li>')


def toolbar(posts, archive_button):
    months = sorted({p["published"][:7] for p in posts}, reverse=True)
    opts = "".join(f'<option value="{m}">{dt.date.fromisoformat(m + "-01").strftime("%B %Y")}</option>' for m in months)
    btn = '\n      <a class="btn btn-white" href="insights-archive.html">Archive</a>' if archive_button else ""
    return f'''    <div class="toolbar{' toolbar-wide' if archive_button else ''}">
      <label for="q">Search
        <input id="q" type="search" placeholder="Search articles" autocomplete="off">
      </label>
      <label for="month">Date
        <select id="month"><option value="">All dates</option>{opts}</select>
      </label>
      <label for="sort">Sort
        <select id="sort"><option value="new">Latest first</option><option value="old">Oldest first</option></select>
      </label>{btn}
    </div>'''


def hero_card(eyebrow, title_html, lead):
    return f'''<section class="page-hero hero-carded" style="border-top:0">
  <div class="wrap">
    <div class="hero-card">
      <p class="eyebrow">{eyebrow}</p>
      <h1>{title_html}</h1>
      <p class="lead">{lead}</p>
    </div>
  </div>
</section>
'''


def build_insights(posts, today):
    live = [p for p in posts if (today - dt.date.fromisoformat(p["published"])).days <= LIVE_DAYS]
    old = [p for p in posts if p not in live]
    hero = hero_card("Insights", "Notes on <em>hiring</em> and the job market.",
                     "Short, sourced articles on U.S. technology hiring, in-demand skills, and workforce planning, for clients planning their teams and candidates planning their next role.")
    if not live and not old:
        return hero + '''
<section>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Coming soon</p>
      <h2>Our first articles are on the way</h2>
      <p class="lead">We will publish practical guidance on hiring trends, role requirements, and career moves in the industries we serve. Check back soon, or contact our team with a question you would like answered.</p>
    </div>
    <div class="card" style="max-width:610px">
      <h3>Ask a question</h3>
      <p>Tell us which hiring or career topic you would like us to cover, and our team will consider it for an upcoming article.</p>
      <a class="btn btn-white" href="contact.html">Ask a question</a>
    </div>
  </div>
</section>'''
    cards = chr(10).join(post_card(p) for p in live)
    return f'''
<section class="listing listing-first" data-page="9">
  <div class="wrap">
    <div class="plain-head">
      <p class="eyebrow">Insights</p>
      <h1>Notes on <em>hiring</em>.</h1>
      <p class="lead">Short, sourced articles on U.S. technology hiring, in-demand skills, and workforce planning, for clients planning their teams and candidates planning their next role.</p>
    </div>
{toolbar(live, True)}
    <div class="posts" id="items">
{cards}
    </div>
    <p id="empty" class="archive-empty" hidden>No articles match your search.</p>
    <div class="load-more"><button class="btn btn-white" type="button" id="more" hidden>Show more</button></div>
  </div>
</section>''' + insights_cta("Ready to act on what you read?",
                              "Whether you are building a team or planning your next role, we can help you turn these trends into a plan. Tell us what you are hiring for, or see the roles open now.")


def build_archive(posts, today):
    old = [p for p in posts if (today - dt.date.fromisoformat(p["published"])).days > LIVE_DAYS]
    hero = hero_card("Archive", "Earlier <em>articles.</em>",
                     "Articles older than 30 days are kept here for 12 months, as a simple list you can search and sort.")
    if not old:
        body = '''    <p class="archive-empty">No archived articles yet. Articles move here 30 days after they are published.</p>
    <p style="margin-top:20px"><a class="btn btn-white" href="insights.html">Back to Insights</a></p>'''
    else:
        body = f'''{toolbar(old, False)}
    <ul class="archive-list" id="items">
{chr(10).join(archive_row(p) for p in old)}
    </ul>
    <p id="empty" class="archive-empty" hidden>No articles match your search.</p>
    <div class="load-more"><button class="btn btn-white" type="button" id="more" hidden>Show more</button></div>
    <p style="margin-top:32px"><a class="btn btn-white" href="insights.html">Back to Insights</a></p>'''
    return hero + f'''
<section class="listing" data-page="20">
  <div class="wrap">
{body}
  </div>
</section>'''


def build_post(p):
    e = html.escape
    secs = "".join(
        f'<h2>{e(s["heading"])}</h2>' + "".join(f"<p>{e(t)}</p>" for t in s["paragraphs"])
        for s in p["sections"])
    take = "".join(f"<li>{e(t)}</li>" for t in p["takeaways"])
    srcs = "".join(f'<li><a href="{e(s["url"], quote=True)}" rel="noopener" target="_blank">{e(s["title"])}</a></li>' for s in p["sources"])
    return f'''<section class="page-hero hero-carded" style="border-top:0">
  <div class="wrap article-head">
    <div class="hero-card">
      <p class="eyebrow">{e(p['tag'])}</p>
      <h1>{e(p['title'])}</h1>
      <p class="lead">{e(p['summary'])}</p>
      <p class="meta">Published {pretty(p['published'])} · Updated {pretty(p['updated'])}</p>
    </div>
  </div>
</section>

<section>
  <div class="wrap article">
    <div class="post-art pal-{e(p['palette'])} post-art-lg"><img src="{art_src(p)}" alt="" width="485" height="300"></div>
    <div class="article-body">
      {secs}
      <div class="card takeaways"><h3>Key takeaways</h3><ul>{take}</ul></div>
      <h2>Sources</h2>
      <ul class="sources">{srcs}</ul>
      <p class="ai-note">This article was prepared with AI assistance from the sources listed above and published by Triada Technologies.</p>
      <p class="share-row">{SHARE_BTN}<a class="btn btn-white" href="insights.html">All insights</a></p>
    </div>
  </div>
</section>''' + insights_cta("Put this insight to work.",
                              "If this article raised questions about your own team or career, our recruiters are glad to talk it through. Share the role you are hiring for, or explore the roles open now.")


def post_schema(p):
    url = f"{SITE}/insight-{p['slug']}.html"
    words = sum(len(t.split()) for sec in p["sections"] for t in sec["paragraphs"])
    article = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": p["title"], "description": p["description"],
        "datePublished": p["published"], "dateModified": p["updated"],
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "articleSection": p["tag"], "inLanguage": "en-US", "wordCount": words,
        "image": OG_IMAGE,
        "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
        "isPartOf": {"@type": "WebSite", "@id": SITE + "/#website"},
        "citation": [s["url"] for s in p["sources"]],
    }
    return ld(article) + breadcrumb(("Insights", "insights.html"), (p["title"], f"insight-{p['slug']}.html"))


def plain(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


def page_schema(fname):
    if fname == "index.html":
        return HOME_SCHEMA
    if fname == "services.html":
        faq = ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in FAQ_ITEMS]})
        return breadcrumb(("Services", fname)) + faq
    if fname == "about.html":
        return breadcrumb(("About", fname)) + ld({"@context": "https://schema.org", "@type": "AboutPage",
                                                   "name": "About Triada Technologies", "url": f"{SITE}/{fname}", "about": {"@id": ORG_ID}})
    if fname == "jobs.html":
        return breadcrumb(("Jobs", fname))
    if fname == "insights.html":
        return breadcrumb(("Insights", fname)) + ld({"@context": "https://schema.org", "@type": "CollectionPage",
                                                      "name": "Insights on hiring and the job market", "url": f"{SITE}/{fname}",
                                                      "isPartOf": {"@id": SITE + "/#website"}, "publisher": {"@id": ORG_ID}})
    if fname == "insights-archive.html":
        return breadcrumb(("Insights", "insights.html"), ("Archive", fname))
    if fname == "contact.html":
        return breadcrumb(("Contact", fname)) + ld({"@context": "https://schema.org", "@type": "ContactPage",
                                                     "name": "Contact Triada Technologies", "url": f"{SITE}/{fname}",
                                                     "mainEntity": org(with_phone=True)})
    return ""


# real "last modified" dates: a page's date only moves when its content changes
LASTMOD_FILE = os.path.join(BASE, "data", "lastmod.json")


def lastmod_for(outputs, today):
    try:
        with open(LASTMOD_FILE, encoding="utf-8") as f:
            book = json.load(f)
    except Exception:
        book = {}
    for name, text in outputs.items():
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if book.get(name, {}).get("hash") != h:
            book[name] = {"hash": h, "date": today.isoformat()}
    with open(LASTMOD_FILE, "w", encoding="utf-8") as f:
        json.dump(book, f, indent=1, sort_keys=True)
    return {n: v["date"] for n, v in book.items()}


def seo_files(posts, today, dates):
    names = [n for n, _ in NAV] + ["insights-archive.html"] + [f"insight-{p['slug']}.html" for p in posts]
    items = "".join(
        f"  <url><loc>{SITE_URL}/{'' if n == 'index.html' else n}</loc><lastmod>{dates.get(n, today.isoformat())}</lastmod></url>\n"
        for n in names)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + "</urlset>\n")
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    lines = ["# Triada Technologies", "",
             "> Nationwide staffing and recruitment firm headquartered in Erie, PA, serving the United States. Temporary, contract, contract-to-hire, and direct-hire placement across IT, healthcare, finance, engineering, and more.", "",
             "## Pages", ""]
    lines += [f"- [{label}]({SITE_URL}/{'' if n == 'index.html' else n})" for n, label in NAV]
    if posts:
        lines += ["", "## Insights", ""]
        lines += [f"- [{p['title']}]({SITE_URL}/insight-{p['slug']}.html): {p['summary']} ({p['published']})" for p in posts]
    lines += ["", "## Frequently asked questions", ""]
    for q, a in FAQ_ITEMS:
        lines += [f"### {q}", plain(a), ""]
    with open("llms.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def retired_slugs():
    try:
        with open(os.path.join(BASE, "data", "retired.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def redirect_page(target):
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Moved | Triada Technologies</title>\n'
            f'<meta name="robots" content="noindex, follow">\n<link rel="canonical" href="{SITE}/{target}">\n'
            f'<meta http-equiv="refresh" content="0; url={target}"></head>\n'
            f'<body><p>This article has moved to the <a href="{target}">archive</a>.</p></body></html>\n')


POSTS = load_posts()
TODAY = build_date()
insights = build_insights(POSTS, TODAY)
archive_page = build_archive(POSTS, TODAY)

# ---------- CONTACT ----------
contact = f'''<section class="page-hero" style="border-top:0">
  <div class="wrap contact-grid">
    <div class="details">
      <p class="eyebrow">Contact</p>
      <h1>Get in <em>touch.</em></h1>
      <p class="lead">Tell us what you are hiring for or what you are looking for, and a member of our team will respond.</p>
      <span class="logo-bars" aria-hidden="true"></span>
      <dl>
        <div><dt>Phone</dt><dd><a href="{PHONE_HREF}">{PHONE}</a></dd></div>
        <div><dt>Email</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd></div>
        <div><dt>Address</dt><dd>Erie, PA {POSTAL_CODE}</dd></div>
        <div><dt>LinkedIn</dt><dd><a href="{LINKEDIN}" target="_blank" rel="me noopener">Triada Technologies</a></dd></div>
      </dl>
    </div>

    <form id="contact-form" class="contact-form" novalidate>
      <div class="field-row">
        <label for="name">Full name
          <input id="name" name="name" type="text" autocomplete="name" maxlength="80" required aria-required="true" aria-describedby="name-error">
          <span class="field-error" id="name-error" hidden></span>
        </label>
        <label for="company">Company (optional)
          <input id="company" name="company" type="text" autocomplete="organization" maxlength="100">
        </label>
      </div>
      <div class="field-row">
        <label for="email">Email
          <input id="email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="120" required aria-required="true" aria-describedby="email-error">
          <span class="field-error" id="email-error" hidden></span>
        </label>
        <label for="phone">Phone (optional)
          <input id="phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" maxlength="30" aria-describedby="phone-error">
          <span class="field-error" id="phone-error" hidden></span>
        </label>
      </div>
      <label for="reason">I am
        <select id="reason" name="reason">
          <option value="client">Hiring talent</option>
          <option value="candidate">Looking for work</option>
          <option value="vendor">A vendor or partner</option>
        </select>
      </label>
      <label for="message">Message
        <textarea id="message" name="message" maxlength="2000" required aria-required="true" aria-describedby="message-error"></textarea>
        <span class="field-error" id="message-error" hidden></span>
      </label>
      <div><button class="btn btn-solid" type="submit">Send message</button></div>
      <p class="form-note">This is a preview. The form is not connected yet, so nothing is sent.</p>
      <p id="form-status" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>
'''

pages = [
    ("index.html", "Triada Technologies | Staffing Services Across the USA",
     "Triada Technologies is a nationwide staffing firm based in Erie, PA, placing temporary, contract, contract-to-hire, and direct-hire talent across the USA.",
     home, True, HOME_SCHEMA),
    ("services.html", "Staffing Services | Triada Technologies",
     "Temporary, contract, contract-to-hire, direct hire, and executive search staffing across nine industries, nationwide, from Triada Technologies.",
     services, True, ""),
    ("about.html", "About Triada Technologies | Nationwide Staffing, Erie, PA",
     "About Triada Technologies, a multi-industry staffing partner based in Erie, PA, connecting clients, vendors, and candidates across the USA.",
     about, True, ""),
    ("jobs.html", "Open Jobs | Triada Technologies",
     "Current job openings with Triada Technologies clients across the USA, and how to submit your resume for temporary, contract, or direct-hire roles.",
     jobs, True, ""),
    ("insights.html", "Insights on Hiring | Triada Technologies",
     "Sourced articles on U.S. technology hiring, in-demand skills, and workforce planning from Triada Technologies, a nationwide staffing firm.",
     insights, True, ""),
    ("insights-archive.html", "Insights Archive | Triada Technologies",
     "Searchable list of earlier Triada Technologies articles on technology hiring, in-demand skills, and workforce planning, kept for 12 months.",
     archive_page, True, ""),
    ("contact.html", "Contact Triada Technologies | Nationwide Staffing",
     f"Contact Triada Technologies, based in Erie, PA and serving the USA. Call {PHONE} or email {EMAIL} to hire talent or submit your resume.",
     contact, True, ""),
]

if __name__ == "__main__":
    outputs = {}
    for fname, title, desc, body, script, schema in pages:
        extra = ("jobs-config.js", "jobs.js", "find.js") if fname == "jobs.html" else ()
        outputs[fname] = page(title, desc, fname, body, script=script, schema=page_schema(fname), extra=extra)
    outputs["job.html"] = page("Open role | Triada Technologies Jobs",
                               "A current job opening with Triada Technologies, a nationwide U.S. staffing firm.", "job.html",
                               job_detail, script=True, extra=("jobs-config.js", "jobs.js"))
    private = {"admin.html": page("Admin | Triada Technologies", "Private admin page.", "admin.html", admin_page,
                                  script=True, noindex=True, extra=("jobs-config.js", "admin.js"))}
    for p in POSTS:
        fname = f"insight-{p['slug']}.html"
        outputs[fname] = page(p["title"] + " | Triada Technologies Insights", p["description"], fname,
                              build_post(p), script=True, schema=post_schema(p), og_type="article")
    outputs["404.html"] = page("Page not found | Triada Technologies", "The page you are looking for does not exist.", "404.html",
                               hero_card("404", "Page not found.", "The page you are looking for has moved or does not exist.")
                               + '\n<section class="listing"><div class="wrap"><a class="btn btn-white" href="index.html">Go to home</a></div></section>',
                               script=True, noindex=True)
    for name, text in {**outputs, **private}.items():
        with open(name, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", name)
    for slug in retired_slugs():
        name = f"insight-{slug}.html"
        if name not in outputs:
            with open(name, "w", encoding="utf-8") as f:
                f.write(redirect_page("insights-archive.html"))
            print("redirect", name)
    dates = lastmod_for({k: v for k, v in outputs.items() if k not in ("404.html", "job.html")}, TODAY)
    seo_files(POSTS, TODAY, dates)
    print("wrote sitemap.xml, robots.txt, llms.txt")
