#!/usr/bin/env python3
"""Build the static site: python3 scripts/build_site.py.
Edit content/*.json, templates/home.html, and assets/site.css; generated HTML
is committed alongside sources and needs no server-side runtime.
"""
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONTACT_ICONS = (ROOT / 'templates/contact-icons.html').read_text().strip()
NAV = [('Home', ''), ('Publications', 'publications'), ('Projects', 'projects'),
       ('News', 'updates'), ('Jung Lab', 'junglab'), ('Data Sharing', 'data-sharing')]
def load(name):
    return json.loads((ROOT / 'content' / f'{name}.json').read_text())
def e(value):
    return escape(str(value), quote=True)
def author_line(authors):
    return e(authors).replace('Jae-Hyun Jung', '<strong>Jae-Hyun Jung</strong>')
def href(route, prefix):
    return prefix + (route + '/index.html' if route else 'index.html')
def local_url(url, prefix='../'):
    if url.startswith('data-sharing/files/'):
        return prefix + url
    parsed = urlparse(url)
    if parsed.netloc in ('www.jjunglab.com', 'jjunglab.com'):
        route = parsed.path.strip('/')
        if route in {path for _, path in NAV}:
            return href(route, prefix) + ('#' + parsed.fragment if parsed.fragment else '')
    return url
def link_list(items, prefix='../', label=None):
    links = []
    seen = set()
    for item in items:
        destination = local_url(item['url'], prefix)
        if destination in seen:
            continue
        seen.add(destination)
        links.append(f'<a href="{e(destination)}">{e(label or item["label"])} <span aria-hidden="true">↗</span></a>')
    return '<div class="resource-links">' + ''.join(links) + '</div>' if links else ''
def publication_details(paper, prefix='../', highlight_venue=False):
    venue = f'<strong>{e(paper["venue"])}</strong>' if highlight_venue else e(paper['venue'])
    venue_class = 'update-venue' if highlight_venue else 'paper-meta'
    return (f'<p class="authors">{author_line(paper["authors"])}</p>'
            f'<p class="{venue_class}">{venue}</p>' + link_list(paper['links'], prefix))
def date_label(date):
    if len(date) == 4: return date
    return datetime.strptime(date[:7], '%Y-%m').strftime('%b %Y')
def page(route, title, description, body):
    prefix = '../' if route else ''
    nav = '\n'.join(f'<a href="{href(path, prefix)}"' + (' aria-current="page"' if path == route else '') + f'>{label}</a>' for label, path in NAV)
    output = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(description)}">
  <title>{e(title)} — Jae-Hyun Jung</title>
  <link rel="stylesheet" href="{prefix}assets/site.css">
  <script src="{prefix}assets/site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header"><div class="shell masthead"><nav class="nav" aria-label="Primary navigation">{nav}</nav></div></header>
  <main class="shell" id="main">{body}</main>
  <footer><div class="shell footer-inner"><nav class="contact-links footer-links" aria-label="Footer contact and social profiles">{CONTACT_ICONS}</nav></div></footer>
</body>
</html>
'''
    dest = ROOT / route / 'index.html'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(output)
    if not route: (ROOT / 'proposed-layout.html').write_text(output)

def heading(title, summary, eyebrow=None):
    return f'<header class="page-intro">' + (f'<p class="eyebrow">{e(eyebrow)}</p>' if eyebrow else '') + f'<h1>{e(title)}</h1><p class="lead">{summary}</p></header>'

def teaser(item, prefix, destination):
    image_ids = item.get('teaser_ids', [item.get('teaser_id')])
    figures = []
    for image_id in image_ids:
        image = teasers.get(image_id)
        if image:
            figures.append(f'<figure class="teaser"><a class="teaser-link" href="{e(destination)}"><img src="{prefix}{e(image["src"])}" width="{image["width"]}" height="{image["height"]}" alt="{e(image["alt"])}" loading="lazy" decoding="async"></a></figure>')
    if len(figures) > 1:
        return '<div class="teaser-gallery">' + ''.join(figures) + '</div>'
    return ''.join(figures)

def record_meta(category, date):
    when = f'<time datetime="{e(date)}">{e(date_label(date))}</time>' if date[:4].isdigit() else f'<span>{e(date)}</span>'
    return f'<div class="record-meta"><span class="category">{e(category)}</span><span aria-hidden="true">·</span>{when}</div>'

def home_feed(publications, news, limit=5):
    entries = [dict(item, destination=f'updates/index.html#{item["id"]}') for item in news]
    for paper in publications:
        date = paper.get('date') or paper.get('year', '')
        # Keep the source precision; undated records cannot enter a chronological feed.
        if not date[:4].isdigit():
            continue
        entries.append(dict(paper, date=date, category=paper['type'],
                            destination=f'publications/index.html#{paper["id"]}'))
    return sorted(entries, key=lambda item: item['date'], reverse=True)[:limit]

def update_list(items, compact=False):
    rows=[]
    for n in items:
        destination = n.get('destination', f'updates/index.html#{n["id"]}') if compact else (local_url(n['links'][0]['url']) if n['links'] else '#' + n['id'])
        title = f'<a href="{e(destination)}">{e(n["title"])}</a>' if compact else e(n['title'])
        prefix = '' if compact else '../'
        details = (publication_details(n, prefix, highlight_venue=True) if 'authors' in n
                   else f'<p>{e(n["summary"])}</p>{link_list(n["links"], prefix)}')
        aliases = '' if compact else ''.join(f'<span id="{e(anchor)}" class="legacy-anchor" aria-hidden="true"></span>' for anchor in n.get('legacy_ids', []))
        visual = teaser(n, '' if compact else '../', destination)
        layout = 'record-content with-teaser' if visual else 'record-content'
        rows.append(f'<li id="{e(n["id"])}" data-category="{e(n["category"])}">{aliases}<div class="{layout}">{visual}<div class="record-text">{record_meta(n["category"], n["date"])}<h3>{title}</h3>{details}</div></div></li>')
    return '<ol class="updates-list'+(' compact' if compact else '')+'">'+''.join(rows)+'</ol>'

pubs = load('publications'); updates = sorted(load('updates'), key=lambda item: item['date'], reverse=True); projects = load('projects'); people = load('people'); datasets = load('datasets')
teasers = load('teasers')
# Home combines both archives without storing a second copy of publication records.
# Home and its editable-preview alias are generated from the same template.
recent = '<section class="section" aria-labelledby="updates-title"><div class="section-heading feed-heading"><h2 id="updates-title">Latest updates</h2><nav class="section-actions" aria-label="Browse news and publications"><a href="publications/index.html">Publications →</a><a href="updates/index.html">News →</a></nav></div>'+update_list(home_feed(pubs, updates), True)+'</section>'
home = (ROOT/'templates/home.html').read_text().replace('{{UPDATES}}', recent).replace('{{CONTACT_ICONS}}', CONTACT_ICONS)
page('', 'Home', 'Jae-Hyun Jung, PhD — human-inspired artificial intelligence, spatial intelligence, perception, and cognition at NVIDIA Research.', home)

body=heading('News','Press coverage, awards, funding, and news from the lab and beyond.')
body+='<div class="filter-bar" data-update-filters hidden><label for="update-category">Show</label><select id="update-category"><option value="">All news</option>'+''.join(f'<option>{e(c)}</option>' for c in sorted({n['category'] for n in updates}))+'</select><span class="result-count" id="update-count" aria-live="polite"></span></div>'
body+=update_list(updates)
page('updates','News','Press coverage, awards, funding, and milestones from Jae-Hyun Jung and the Jung Lab.',body)

body=heading('Publications','Papers, preprints, patents, and conference abstracts spanning human perception, spatial intelligence, displays, and vision rehabilitation.')
years=sorted({p['year'] for p in pubs}, key=lambda y: int(y) if y.isdigit() else 0, reverse=True)
body+='<div class="filter-bar" data-publication-filters hidden><label class="search-field" for="publication-search">Search publications<input id="publication-search" type="search" placeholder="Title, author, or keyword" autocomplete="off"></label><label for="publication-year">Year<select id="publication-year"><option value="">All years</option>'+''.join(f'<option>{y}</option>' for y in years)+'</select></label><label for="publication-type">Type<select id="publication-type"><option value="">All types</option>'+''.join(f'<option>{e(t)}</option>' for t in sorted({p['type'] for p in pubs}))+'</select></label><button type="button" id="clear-filters">Reset</button></div>'
body+=f'<p class="result-count" id="publication-count" aria-live="polite">{len(pubs)} research outputs</p>'
body+='<a class="publication-jump" href="#conference-abstracts" data-abstract-jump>Conference abstracts ↓</a>'
for abstracts, group_id in [(False, 'research-publications'), (True, 'conference-abstracts')]:
    group = [p for p in pubs if (p['type'] == 'Conference abstract') == abstracts]
    group_years = [y for y in years if any(p['year'] == y for p in group)]
    anchor_prefix = 'abstract-year' if abstracts else 'year'
    year_heading, item_heading = ('h3', 'h4') if abstracts else ('h2', 'h3')
    body+=f'<div class="publication-group" id="{group_id}">'
    if abstracts:
        body+='<h2>Conference abstracts</h2>'
    nav_label = 'Conference abstract years' if abstracts else 'Publication years'
    body+=f'<nav class="year-index" aria-label="{nav_label}">'+''.join(f'<a href="#{anchor_prefix}-{y}">{y}</a>' for y in group_years)+'</nav>'
    for y in group_years:
        body+=f'<section class="publication-year" id="{anchor_prefix}-{y}"><{year_heading} class="visually-hidden">{y}</{year_heading}><ol class="publication-list">'
        for p in sorted((p for p in group if p['year']==y), key=lambda p: p.get('date', p['year']), reverse=True):
            title=f'<a href="{e(p["links"][0]["url"])}">{e(p["title"])}</a>' if p['links'] else e(p['title'])
            visual=teaser(p, '../', local_url(p['links'][0]['url']) if p['links'] else '#' + p['id'])
            layout='record-content with-teaser' if visual else 'record-content'
            body+=f'<li id="{p["id"]}" data-year="{y}" data-type="{e(p["type"])}"><div class="{layout}">{visual}<div class="record-text">{record_meta(p["type"], p.get("date", y))}<{item_heading}>{title}</{item_heading}>{publication_details(p)}</div></div></li>'
        body+='</ol></section>'
    body+='</div>'
body+='<p id="no-publications" class="empty-state" hidden>No publications match these filters. Try another keyword or reset the filters.</p>'
page('publications','Publications','Publications, preprints, patents, and conference abstracts by Jae-Hyun Jung, searchable by year, author, and topic.',body)

body=heading('Projects','Spatial intelligence, immersive systems, and technologies that connect human vision with computation.')
body+='<section aria-labelledby="recent-projects"><h2 id="recent-projects">Recent work</h2><div class="project-grid">'
pubs_by_id = {p['id']: p for p in pubs}
recent_projects=[('Spatial-IQ','Hierarchical capability tests help pinpoint where multimodal models succeed or fail at spatial reasoning.','publication-1'),('Radiance fields on light field displays','Efficient rendering connects radiance field representations with interactive, glasses-free 3D displays.','publication-2'),('Natural walking in immersive VR','Studies of hemianopia and cerebral visual impairment measure pedestrian detection, avoidance, and visual scanning during natural walking.','publication-3')]
for title,summary,publication_id in recent_projects:
    paper=pubs_by_id[publication_id]
    ls=paper['links']
    if publication_id=='publication-3': ls=[{'label':'CVI preprint','url':paper['links'][0]['url']},{'label':'Hemianopia preprint','url':pubs_by_id['publication-4']['links'][0]['url']},{'label':'VR mobility project','url':'#vr-mobility'}]
    body+=f'<article class="project-card"><p class="eyebrow">{paper["year"]} · '+('VSS' if publication_id=='publication-5' else 'Research')+f'</p><h3>{e(title)}</h3><p>{e(summary)}</p>{link_list(ls)}</article>'
body+='</div></section><section class="section" aria-labelledby="lab-projects"><h2 id="lab-projects">Jung Lab research · 2015–2024</h2><p class="section-note">Research programs developed at Harvard Medical School and Mass Eye and Ear.</p>'
related=[[],['Field Expansion for Acquired Monocular','effect of visual rivalry'],['Develop then Rival','Binocular double vision'],['Active Confocal Imaging for Visual Prostheses','Comparing object recognition from binary'],['Real-time integral imaging system','Real-time capturing and 3D visualization']]
for i,p in enumerate(projects):
    imgs=''.join(f'<img src="../{im}" alt="{e(p["title"])} — research illustration {j+1}" loading="lazy">' for j,im in enumerate(p['images']))
    resources=p['links'][:]
    for fragment in related[i]:
        match=next((r for r in pubs if fragment.lower() in r['title'].lower()),None)
        if match: resources.append({'label':match['title'],'url':'../publications/index.html#'+match['id']})
    body+=f'<article class="project-detail" id="{p["id"]}"><div class="project-figures">{imgs}</div><div><h3>{e(p["title"])}</h3><p>{e(p["summary"])}</p>{link_list(resources)}<details class="funding"><summary>Funding &amp; support</summary><ul>'+''.join(f'<li>{e(g)}</li>' for g in p['grants'])+'</ul></details></div></article>'
body+='</section>'
page('projects','Projects','Research projects in spatial intelligence, VR mobility, field expansion, binocular vision, and computational imaging.',body)

body=heading('Jung Lab','A former research lab at Harvard Medical School and Mass Eye and Ear.','2015–2024')
body+='''<div class="lab-intro"><div><p>From 2015 to 2024, the Jung Lab at Schepens Eye Research Institute / Mass Eye and Ear, Harvard Medical School investigated the interface between electrical and optical systems and human vision. Research brought together visual perception, display engineering, computational photography, and vision rehabilitation.</p><p>Work included visual field expansion with multiplexing prisms, AR and see-through mobility aids, portable VR walking assessments, and light-field imaging for visual prostheses.</p><div class="resource-links"><a href="../projects/index.html">Explore lab projects →</a><a href="../data-sharing/index.html">Shared data →</a><a href="https://pelilab.partners.org/">Peli Lab ↗</a></div></div><aside class="archive-note"><strong>Lab archive · 2015–2024</strong><p>The Jung Lab concluded in 2024, when Jae-Hyun Jung joined NVIDIA Research. This page documents the former lab’s research and the people who contributed to it. Lab roles and dates are historical; current affiliations are listed below.</p></aside></div>'''
body+='<section class="section" aria-labelledby="former-members"><h2 id="former-members">Former members &amp; collaborators</h2><div class="people-grid">'
# One historical roster, ordered by joining year; collaborators without dates follow.
for p in sorted(people, key=lambda person: person['period'][:4], reverse=True):
    period=p['period'].replace('-', '–')
    image=f'<img src="../{p["images"][0]}" alt="{e(p["name"])}" loading="lazy" width="80" height="96">' if p['images'] else ''
    details=p['details'] if p['role']=='Co-Investigator' else 'Currently: '+p['details']
    dates=f'<p class="paper-meta">{e(period)}</p>' if period else ''
    body+=f'<article class="person">{image}<div><h3>{e(p["name"])}</h3><p class="person-role">{e(p["role"])}</p>{dates}<p class="person-detail">{e(details)}</p>{link_list(p["links"])}</div></article>'
body+='</div></section>'
page('junglab','Jung Lab (2015–2024)','The former Jung Lab at Harvard Medical School and Mass Eye and Ear, 2015–2024: research, former members, and collaborators.',body)

body=heading('Data Sharing','Study data and materials accompanying Jung Lab publications.')
body+='''<div class="data-note"><p>Data may be analyzed and cited in publications. Please cite the associated paper and follow any terms included with each dataset. Copyright remains with the authors or other rights holders; materials generally may not be reposted without their permission.</p></div><ol class="dataset-list">'''
for i,d in enumerate(datasets):
    ls=[{'label':'Download data (.xlsx)','url':l['url']} for l in d['links']]
    if 'publication_id' in d:ls.append({'label':'Publication','url':'../publications/index.html#'+d['publication_id']})
    note='' if d['links'] else '<p class="section-note">No download was listed for this study. <a href="mailto:Phd.Jaehyun.Jung@gmail.com?subject=Data%20request%3A%20binary%20and%20bipolar%20edge%20images">Contact Jae-Hyun Jung about data availability</a>.</p>'
    body+=f'<li id="dataset-{i+1}"><span class="paper-year">{e(d["year"])}</span><div><h2>{e(d["title"])}</h2><p class="authors">{author_line(d["authors"])}</p><p class="paper-meta">{e(d["venue"])}</p>{link_list(ls)}{note}</div></li>'
body+='</ol>'
page('data-sharing','Data Sharing','Download study data and materials for Jung Lab research in vision rehabilitation, field expansion, and visual prostheses.',body)
print(f'Built 6 pages + proposed-layout.html: {len(pubs)} publications, {len(updates)} updates, {len(projects)} lab projects, {len(people)} people, {len(datasets)} datasets.')
