"""Build the German and Italian pages from the English ones.

Run from the repository root:  python3 i18n/build.py
English pages (index.html, privacy.html) are the source. Edit them, then rerun.
"""
import html
import json
import re
import sys

T = json.load(open('i18n/translations.json', encoding='utf-8'))
PAGES = {'index.html': {'de': 'de.html', 'it': 'it.html', 'hr': 'hr.html'},
         'privacy.html': {'de': 'privacy-de.html', 'it': 'privacy-it.html', 'hr': 'privacy-hr.html'}}
missing = set()


def tr(s, d):
    key = html.unescape(s.strip())
    if key in d:
        return d[key]
    return None


def translate(src, lang):
    d = T[lang]
    # protect style/script blocks
    blocks = []

    def keep(m):
        blocks.append(m.group(0))
        return f'\x00{len(blocks) - 1}\x00'
    out = re.sub(r'<(style|script)\b.*?</\1>', keep, src, flags=re.S)

    def text(m):
        lead, body, trail = m.group(1), m.group(2), m.group(3)
        t = tr(body, d)
        if t is None:
            k = html.unescape(body.strip())
            if re.search(r'[A-Za-z]{3}', k) and k not in KEEP:
                missing.add(k)
            return m.group(0)
        return lead + html.escape(t, quote=False) + trail
    out = re.sub(r'(>\s*)([^<>\x00]*?[^\s<>\x00][^<>\x00]*?)(\s*<)', text, out)

    def attr(m):
        t = tr(m.group(2), d)
        return m.group(0) if t is None else m.group(1) + html.escape(t, quote=True) + m.group(3)
    out = re.sub(r'(\b(?:alt|aria-label|title|content)=")([^"]*)(")', attr, out)

    # scripts: gallery group names and aria label
    def script(s):
        s = re.sub(r'\["([^"]+)",\[', lambda m: '["' + d.get(m.group(1), m.group(1)) + '",[', s)
        s = s.replace("'Open photo'", "'" + d['Open photo'].replace("'", "\\'") + "'")
        return s
    blocks2 = [script(b) if b.startswith('<script') else b for b in blocks]
    out = re.sub(r'\x00(\d+)\x00', lambda m: blocks2[int(m.group(1))], out)
    return out


KEEP = {'Villa Vaho', 'Novi Vinodolski', 'Lana Haynes Hodžić', 'Adriagate', 'Booking.com', 'Airbnb',
        'OpenStreetMap', 'azop.hr', '30 min', 'info@villavaho.com', 'info@adriagate.com'}

for src_name, targets in PAGES.items():
    src = open(src_name, encoding='utf-8').read()
    for lang, dst in targets.items():
        out = translate(src, lang)
        out = out.replace('<html lang="en">', f'<html lang="{lang}">', 1)
        # links to the other language versions of pages
        out = out.replace('href="privacy.html"', f'href="privacy-{lang}.html"')
        if src_name == 'privacy.html':
            out = out.replace('href="index.html">Villa Vaho', f'href="{lang}.html">Villa Vaho')
            out = re.sub(r'class="back" href="index.html"', f'class="back" href="{lang}.html"', out)
            out = out.replace('<a href="privacy-' + lang + '.html" class="on">EN</a>', '<a href="privacy.html">EN</a>')
        else:
            out = out.replace('img/th/villaroute2.jpg', f'img/th/villaroute2-{lang}.jpg')
            out = out.replace('"villaroute2"', f'"villaroute2-{lang}"')
        # language switcher state
        out = re.sub(r'(<a href="[^"]*" (?:hreflang="en" lang="en" )?)class="on">EN</a>', r'\1>EN</a>', out)
        out = out.replace('>EN</a>', '>EN</a>')
        out = re.sub(r'(<a href="[^"]*"[^>]*?)>(' + lang.upper() + r')</a>', r'\1 class="on">\2</a>', out)
        out = out.replace(' >EN</a>', '>EN</a>')
        if lang == 'it':
            out = out.replace("Una villa affacciata sull' <em>", "Una villa affacciata sull'<em>")
        open(dst, 'w', encoding='utf-8').write(out)
        print('wrote', dst)

if missing:
    print('UNTRANSLATED:', *sorted(missing), sep='\n  ')
    sys.exit(1)
