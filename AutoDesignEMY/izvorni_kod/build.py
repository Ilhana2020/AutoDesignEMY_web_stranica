#!/usr/bin/env python3
"""Static site generator for autodesignemy website.

Usage:  python3 build.py                 -> builds ./dist
        SITE_URL=https://www.example.ba python3 build.py   (adds canonical/hreflang URLs + sitemap)

The website content lives in src/i18n/<lang>.json, layouts in src/templates.
The gallery is managed on the live server through /admin (data/gallery.json);
src/gallery.seed.json is only used for the first deployment.
"""
import json, os, shutil, time, hashlib, datetime
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'dist')
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')

LANGS = ['bs', 'en', 'de', 'fr', 'tr', 'ar', 'it', 'sv', 'ru', 'sq', 'mk']
RTL = {'ar'}
OG_LOCALE = {'bs': 'bs_BA', 'en': 'en_GB', 'de': 'de_DE', 'fr': 'fr_FR', 'tr': 'tr_TR', 'ar': 'ar_AR',
             'it': 'it_IT', 'sv': 'sv_SE', 'ru': 'ru_RU', 'sq': 'sq_AL', 'mk': 'mk_MK'}
PAGES = {'home': '', 'services': 'usluge/', 'gallery': 'galerija/', 'about': 'o-nama/', 'contact': 'kontakt/'}
NAV = ['home', 'services', 'gallery', 'about', 'contact']

# ---- Verified business data (do not add anything that is not confirmed) ----
PHONE_INTL = '38761938601'
PHONE_LOCAL = '061 938 601'
PHONE_PRETTY = '+387 61 938 601'
ADDRESS = 'Rosulje 6, br. 1, Vogošća'
MAPS_QUERY = quote('Rosulje 6, Vogošća, Bosna i Hercegovina')
SOCIALS = [
    {'name': 'Instagram', 'icon': 'instagram', 'handle': '@autodesignemy', 'url': 'https://www.instagram.com/autodesignemy/'},
    {'name': 'Facebook', 'icon': 'facebook', 'handle': 'Auto Design EMY', 'url': 'https://www.facebook.com/profile.php?id=100075993196938'},
    {'name': 'TikTok', 'icon': 'tiktok', 'handle': '@autodesignemy', 'url': 'https://www.tiktok.com/@autodesignemy'},
]
FOLLOWERS = {'en': '2,200+', 'ar': '2,200+', 'fr': '2 200+', 'sv': '2 200+', 'ru': '2 200+', 'sq': '2 200+', 'mk': '2 200+'}

# ---- Icons ----
BRAND = json.load(open(os.path.join(SRC, 'icons.json')))
ICONS = {k: f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="{v}"/></svg>' for k, v in BRAND.items()}
ICONS.update({
    'phone': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    'phone-line': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    'globe': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/></svg>',
    'pin': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    'clock': '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
})

# ---- Gallery seed (first deployment only) ----
CAT_LABEL = {'wheels': 'wheels', 'seats': 'seats', 'interior': 'interior'}
PHOTO_ITEMS = [
    ('volan-vw-alcantara-koza', 'wheels', 'VW volan – alcantara i perforirana koža, crvena oznaka', 'VW steering wheel – Alcantara and perforated leather, red centre marker', False),
    ('volan-mercedes-amg-tirkiz', 'wheels', 'Mercedes-AMG volan – koža i tirkizni detalji', 'Mercedes-AMG steering wheel – leather with turquoise details', True),
    ('volan-bmw-m-alcantara', 'wheels', 'BMW M volan – alcantara, trobojni šav', 'BMW M steering wheel – Alcantara with tricolour stitching', True),
    ('volan-mercedes-koza', 'wheels', 'Volan – glatka i perforirana koža', 'Steering wheel – smooth and perforated leather', False),
    ('volan-audi-alcantara', 'wheels', 'Audi volan – alcantara, crvena oznaka', 'Audi steering wheel – Alcantara, red centre marker', False),
    ('volan-bmw-plava-oznaka', 'wheels', 'BMW volan – koža, plava oznaka', 'BMW steering wheel – leather, blue centre marker', True),
    ('volan-bmw-u-vozilu', 'wheels', 'BMW volan ugrađen u vozilo', 'BMW steering wheel fitted in the car', False),
]
VIDEO_ITEMS = [
    ('01_volan_vw_alcantara_koza', 'wheels', 'VW volan – alcantara i perforirana koža', 'VW steering wheel – Alcantara and perforated leather', True),
    ('13_sjedista_romb_crveni_konac', 'seats', 'Sjedišta – prošivanje u obliku romba, crveni konac', 'Seats – diamond stitching, red thread', True),
    ('16_enterijer_sjedista_vrata', 'interior', 'Sjedišta i tapacir vrata – šav u obliku saća', 'Seats and door panels – honeycomb stitching', False),
    ('17_tapacir_vrata', 'interior', 'Tapacir vrata – šav u obliku saća', 'Door panel – honeycomb stitching', False),
    ('02_volan_bmw_m', 'wheels', 'Presvučen volan', 'Re-covered steering wheel', False),
    ('03_volan_vw', 'wheels', 'Presvučen volan', 'Re-covered steering wheel', False),
    ('04_volan_audi', 'wheels', 'Presvučen volan', 'Re-covered steering wheel', False),
    ('05_volan_mercedes_amg', 'wheels', 'Presvučen volan', 'Re-covered steering wheel', False),
    ('06_volan_mercedes', 'wheels', 'Volan – iz radionice u vozilo', 'Steering wheel – from the workshop to the car', False),
    ('07_volan_audi_radionica_vozilo', 'wheels', 'Audi volan – iz radionice u vozilo', 'Audi steering wheel – from the workshop to the car', True),
    ('08_volan_bmw_u_vozilu', 'wheels', 'BMW volan ugrađen u vozilo', 'BMW steering wheel fitted in the car', False),
    ('09_volan_mercedes_g_u_vozilu', 'wheels', 'Mercedes G – volan ugrađen u vozilo', 'Mercedes G – steering wheel fitted in the car', False),
    ('10_volan_audi_u_vozilu', 'wheels', 'Audi volan ugrađen u vozilo', 'Audi steering wheel fitted in the car', False),
    ('11_volan_i_mjenjac_audi', 'wheels', 'Audi – volan i mjenjač', 'Audi – steering wheel and gear shifter', False),
    ('12_mjenjac_audi', 'interior', 'Presvučena ručica mjenjača', 'Re-covered gear knob', False),
    ('14_sjedista_romb', 'seats', 'Sjedišta – prošivanje u obliku romba', 'Seats – diamond stitching', False),
    ('15_sjedista', 'seats', 'Presvučena sjedišta', 'Re-covered seats', False),
]


def seed_gallery(images):
    photos, videos = [], []
    for name, cat, bs, en, feat in PHOTO_ITEMS:
        im = images[name]
        webp = dict((w, f) for f, w in im['webp'])
        thumb = webp.get(480) or im['webp'][0][0]
        full = webp.get(1440) or webp.get(960) or im['webp'][-1][0]
        photos.append({'id': name, 'type': 'image', 'cat': cat, 'thumb': 'assets/img/' + thumb, 'full': 'assets/img/' + full,
                       'w': im['w'], 'h': im['h'], 'caption': {'bs': bs, 'en': en}, 'featured': feat})
    for name, cat, bs, en, feat in VIDEO_ITEMS:
        landscape = name.startswith(('12_', '13_', '14_'))
        videos.append({'id': name, 'type': 'video', 'cat': cat, 'thumb': f'media/gallery/{name}.webp', 'src': f'media/gallery/{name}.mp4',
                       'w': 1280 if landscape else 720, 'h': 720 if landscape else 1280, 'caption': {'bs': bs, 'en': en}, 'featured': feat})
    # interleave photos and videos for a varied grid
    out = []
    while photos or videos:
        if videos: out.append(videos.pop(0))
        if photos: out.append(photos.pop(0))
    return out


def main():
    t0 = time.time()
    images = json.load(open(os.path.join(SRC, 'images.json')))
    seed_path = os.path.join(SRC, 'gallery.seed.json')
    gallery = seed_gallery(images)
    json.dump(gallery, open(seed_path, 'w'), ensure_ascii=False, indent=1)

    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree(os.path.join(SRC, 'static', 'css'), os.path.join(DIST, 'assets', 'css'))
    shutil.copytree(os.path.join(SRC, 'static', 'js'), os.path.join(DIST, 'assets', 'js'))
    shutil.copytree(os.path.join(SRC, 'static', 'fonts'), os.path.join(DIST, 'assets', 'fonts'))
    shutil.copytree(os.path.join(SRC, 'static', 'img'), os.path.join(DIST, 'assets', 'img'))
    shutil.copytree(os.path.join(SRC, 'static', 'media'), os.path.join(DIST, 'media'))
    os.makedirs(os.path.join(DIST, 'media', 'uploads'), exist_ok=True)
    open(os.path.join(DIST, 'media', 'uploads', '.htaccess'), 'w').write(
        '# Uploaded files are never executed\nphp_flag engine off\nRemoveHandler .php .phtml .php5 .php7 .phar\n'
        '<FilesMatch "\\.(php|phtml|php\\d|phar|cgi|pl|py|sh)$">\n  Require all denied\n</FilesMatch>\n')
    os.makedirs(os.path.join(DIST, 'data'), exist_ok=True)
    shutil.copy(seed_path, os.path.join(DIST, 'data', 'gallery.json'))
    shutil.copytree(os.path.join(ROOT, 'admin'), os.path.join(DIST, 'admin'))
    for f in os.listdir(os.path.join(SRC, 'root')):
        shutil.copy(os.path.join(SRC, 'root', f), os.path.join(DIST, f))

    version = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    env = Environment(loader=FileSystemLoader(os.path.join(SRC, 'templates')), autoescape=select_autoescape(['html']),
                      trim_blocks=True, lstrip_blocks=True)
    tr = {l: json.load(open(os.path.join(SRC, 'i18n', f'{l}.json'))) for l in LANGS}
    langs = [{'code': l, 'name': tr[l]['lang_name']} for l in LANGS]

    def prefix(l): return '' if l == 'bs' else l + '/'
    def abs_path(l, p): return '/' + prefix(l) + PAGES[p]

    count = 0
    for lang in LANGS:
        t = tr[lang]
        for page, tpl in [('home', 'home.html'), ('services', 'services.html'), ('gallery', 'gallery.html'),
                          ('about', 'about.html'), ('contact', 'contact.html')] + ([('404', '404.html')] if lang == 'bs' else []):
            depth = (lang != 'bs') + (page not in ('home', '404'))
            root = '/' if page == '404' else '../' * depth   # 404 can be served at any depth -> absolute paths

            def url(l, p, _root=root):
                u = _root + prefix(l) + PAGES.get(p, '')
                return u or './'
            wa = f'https://wa.me/{PHONE_INTL}'
            cats = {'wheels': t['gallery']['wheels'], 'seats': t['gallery']['seats'], 'interior': t['gallery']['interior']}

            def item_cap(it, _l=lang): return it.get('caption', {}).get(_l, '')
            def item_alt(it, _l=lang, _c=cats): return item_cap(it, _l) or f"{_c[it['cat']]} – Auto Design EMY"

            seo_key = 'home' if page == '404' else page
            title = t['notfound']['title'] + ' | Auto Design EMY' if page == '404' else t['seo'][seo_key + '_title']
            description = t['seo'][seo_key + '_desc']
            jsonld = {
                '@context': 'https://schema.org', '@type': 'AutomotiveBusiness', 'name': 'Auto Design EMY',
                'description': t['seo']['home_desc'], 'telephone': '+' + PHONE_INTL,
                'address': {'@type': 'PostalAddress', 'streetAddress': 'Rosulje 6, br. 1', 'addressLocality': 'Vogošća', 'addressCountry': 'BA'},
                'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification',
                                               'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                                               'opens': '09:00', 'closes': '17:00'}],
                'sameAs': [s['url'] for s in SOCIALS],
            }
            if SITE_URL:
                jsonld['url'] = SITE_URL + abs_path('bs', 'home')
                jsonld['image'] = SITE_URL + '/assets/img/og-image.jpg'
            labels = {'open': t['gallery']['open'], 'video': t['gallery']['video'], 'cats': cats,
                      'msgHello': t['contact']['msg_hello'], 'name': t['contact']['name'], 'vehicle': t['contact']['vehicle'],
                      'service': t['contact']['service'], 'copied': t['contact']['copied']}
            ctx = dict(
                lang=lang, dir='rtl' if lang in RTL else 'ltr', page=page, t=t, langs=langs, root=root, url=url,
                abs_path=lambda l, p: abs_path(l, 'home' if p == '404' else p), site_url=SITE_URL, nav_pages=NAV,
                title=title, description=description, og_locale=OG_LOCALE[lang], version=version,
                icon=lambda n: Markup(ICONS[n]), tel=f'tel:+{PHONE_INTL}', wa=wa, wa_number=PHONE_INTL,
                viber=f'viber://chat?number=%2B{PHONE_INTL}',
                wa_text=lambda txt: wa + '?text=' + quote(txt),
                phone_display=PHONE_LOCAL if lang == 'bs' else PHONE_PRETTY,
                address=ADDRESS, maps_query=MAPS_QUERY, maps_url='https://www.google.com/maps/search/?api=1&query=' + MAPS_QUERY,
                socials=SOCIALS, followers=FOLLOWERS.get(lang, '2.200+'), year=datetime.date.today().year,
                images=images, gallery=gallery, featured=[g for g in gallery if g['featured']][:6],
                item_cap=item_cap, item_alt=item_alt,
                needs_lightbox=page in ('home', 'gallery'),
                jsonld=Markup(json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/')),
                js_labels=Markup(json.dumps(labels, ensure_ascii=False).replace('</', '<\\/')),
                gallery_json=Markup(json.dumps(gallery if page in ('home', 'gallery') else [], ensure_ascii=False).replace('</', '<\\/')),
            )
            html = env.get_template(tpl).render(**ctx)
            if page == '404':
                out = os.path.join(DIST, '404.html')
            else:
                out = os.path.join(DIST, prefix(lang), PAGES[page], 'index.html')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(html)
            count += 1

    # robots + sitemap
    robots = 'User-agent: *\nDisallow: /admin/\n'
    if SITE_URL:
        robots += f'Sitemap: {SITE_URL}/sitemap.xml\n'
        urls = []
        for p in PAGES:
            for l in LANGS:
                alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{a}" href="{SITE_URL}{abs_path(a, p)}"/>' for a in LANGS)
                urls.append(f'<url><loc>{SITE_URL}{abs_path(l, p)}</loc>{alts}</url>')
        open(os.path.join(DIST, 'sitemap.xml'), 'w').write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + ''.join(urls) + '</urlset>\n')
    open(os.path.join(DIST, 'robots.txt'), 'w').write(robots)
    print(f'Built {count} pages in {time.time() - t0:.1f}s -> {DIST}' + ('' if SITE_URL else '  (SITE_URL not set: no canonical/sitemap)'))


if __name__ == '__main__':
    main()
