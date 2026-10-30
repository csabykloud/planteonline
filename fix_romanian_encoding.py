import json
import re
import sys
import ftfy

sys.stdout.reconfigure(encoding='utf-8')

# Known Romanian mojibake mappings
MOJIBAKE_REPLACEMENTS = [
    # Double-encoded Romanian characters
    ('Ă\x83', 'ă'),
    ('Ă\x82', 'â'),
    ('Ă\x8e', 'Î'),
    ('Ă\x8ee', 'În'),
    ('Ă\x8e', 'Î'),
    ('Ă®', 'î'),
    ('ĂŽ', 'Î'),
    ('Ĺ\x9f', 'ș'),
    ('Ĺ\x9e', 'Ș'),
    ('Ĺ\xa3', 'ț'),
    ('Ĺ\xa2', 'Ț'),
    ('È\x99', 'ș'),
    ('È\x98', 'Ș'),
    ('È\x9b', 'ț'),
    ('È\x9a', 'Ț'),
    ('Ã\x83', 'ă'),
    ('Ã\xa2', 'â'),
    ('Ã®', 'î'),
    ('Ã\x8e', 'Î'),
    ('Ã®', 'î'),
    ('Ä\x83', 'ă'),
    ('Ä\x82', 'Ă'),
    ('â\x80\x93', '–'),
    ('â\x80\x94', '—'),
    ('â\x80\x9c', '„'),
    ('â\x80\x9d', '”'),
    ('â\x80\x98', '‘'),
    ('â\x80\x99', '’'),
    ('â\x80\xa6', '…'),
    ('Â\xa0', ' '),
    ('\xa0', ' '),
    # Common broken words where initial letter was spaced
    ('V remea', 'Vremea'),
    ('v remea', 'vremea'),
    ('v iața', 'viața'),
    ('V iața', 'Viața'),
    ('v iaţa', 'viața'),
    ('V iaţa', 'Viața'),
    # Old orthography or typos
    ('cÎt', 'cât'),
    ('cît', 'cât'),
    ('rÎnd', 'rând'),
    ('rînd', 'rând'),
    ('Începind', 'Începând'),
    ('începind', 'începând'),
    ('sĂ\x83', 'să'),
    ('cĂ\x83', 'că'),
    ('plouĂ\x83', 'plouă'),
    ('grĂ\x83din', 'grădin'),
    ('Însemnate', 'însemnate'),
]

# Control characters to strip
CONTROL_CHARS = [chr(i) for i in range(32) if i not in (9, 10, 13)]

def clean_romanian_text(text):
    if not text or not isinstance(text, str):
        return text

    res = text

    # Remove non-printable control characters
    for cc in CONTROL_CHARS:
        res = res.replace(cc, '')

    # Apply specific mojibake replacements
    for bad, good in MOJIBAKE_REPLACEMENTS:
        res = res.replace(bad, good)

    # In case of remaining ftfy fixes
    res = ftfy.fix_text(res)

    # Post-cleanup: if there's any remaining "Ă " at word start where "În" was intended
    res = re.sub(r'\bĂ\s*n\b', 'În', res)
    res = re.sub(r'\bĂ\s*n\s+', 'În ', res)

    # Normalize multiple spaces (preserving newlines)
    lines = res.splitlines()
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    res = '\n'.join(cleaned_lines)

    return res

def clean_articles():
    with open('data/articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"Cleaning {len(articles)} articles...")
    fixed_count = 0
    for a in articles:
        orig_t = a.get('title', '')
        orig_s = a.get('summary', '')
        orig_c = a.get('content', '')

        new_t = clean_romanian_text(orig_t)
        new_s = clean_romanian_text(orig_s)
        new_c = clean_romanian_text(orig_c)

        if (new_t, new_s, new_c) != (orig_t, orig_s, orig_c):
            fixed_count += 1
            a['title'] = new_t
            a['summary'] = new_s
            a['content'] = new_c

    with open('data/articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Fixed {fixed_count} articles in data/articles.json!")

def clean_plants():
    with open('data/plants.json', 'r', encoding='utf-8') as f:
        plants = json.load(f)

    print(f"Cleaning {len(plants)} plants...")
    fixed_count = 0
    text_fields = ['name', 'shape', 'leaves', 'flowers', 'fruit', 'requirements', 'origin']
    for p in plants:
        changed = False
        for f in text_fields:
            if f in p and isinstance(p[f], str):
                new_val = clean_romanian_text(p[f])
                if new_val != p[f]:
                    p[f] = new_val
                    changed = True
        if changed:
            fixed_count += 1

    with open('data/plants.json', 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)
    print(f"Fixed {fixed_count} plants in data/plants.json!")

if __name__ == '__main__':
    clean_articles()
    clean_plants()
