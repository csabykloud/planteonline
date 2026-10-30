import json
import re

COMMON_WORDS = {
    'planta', 'plante', 'decorativa', 'decorative', 'camera', 'apartament', 
    'gradina', 'ghiveci', 'ghivece', 'flori', 'tufa', 'frunze', 'arbust', 
    'arbore', 'arbori', 'arbusti', 'hibrid', 'specii', 'specie', 'soiuri',
    'culoare', 'verde', 'ingrijire', 'cultivare', 'dezvoltare', 'crestere',
    'pana', 'vara', 'iarna', 'toamna', 'primavara', 'luna', 'zile', 'anul',
    'mult', 'putin', 'bine', 'nou', 'noi', 'tot', 'toate', 'toti', 'fel',
    'soi', 'aur', 'argint', 'lemn', 'apa', 'aer', 'sol', 'pamant', 'soare',
    'umbra', 'masa', 'casa', 'patria', 'loc', 'locuri', 'radacini', 'coada',
    'par', 'mar', 'stea', 'inima', 'ochi', 'alba', 'rosie', 'galbena',
    'negru', 'curat', 'ornamental', 'ornamentali', 'ornamentale', 'comun',
    'comuna', 'salbatic', 'peste', 'vulpe', 'crocodil', 'urs', 'maimuta',
    'munte', 'saracului'
}

def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    for s, d in [('ț', 't'), ('ș', 's'), ('ă', 'a'), ('â', 'a'), ('î', 'i')]:
        t = t.replace(s, d)
    return t

def get_stem(word):
    w = normalize_text(word)
    for suff in ['urilor', 'eelor', 'ilor', 'elor', 'ului', 'ele', 'uri', 'ea', 'ul', 'ei', 'ii', 'ula', 'e', 'i', 'a']:
        if w.endswith(suff) and len(w) - len(suff) >= 4:
            return w[:-len(suff)]
    return w

def extract_plant_keywords(p):
    keys = set()
    name = normalize_text(p.get('name', ''))
    raw_parts = [prt.strip() for prt in re.split(r'[,;\(\)\/]', name) if prt.strip()]
    for part in raw_parts:
        clean_part = re.sub(r'[^a-z0-9\s]', '', part).strip()
        words = clean_part.split()
        if len(words) == 1:
            if len(clean_part) >= 4 and clean_part not in COMMON_WORDS:
                keys.add(clean_part)
                stem = get_stem(clean_part)
                if len(stem) >= 4 and stem not in COMMON_WORDS:
                    keys.add(stem)
        elif len(words) > 1:
            keys.add(clean_part)
            for w in words:
                if len(w) >= 5 and w not in COMMON_WORDS:
                    keys.add(w)
                    stem = get_stem(w)
                    if len(stem) >= 4 and stem not in COMMON_WORDS:
                        keys.add(stem)

    lat = normalize_text(p.get('latin_name', ''))
    lat_clean = re.sub(r'[^a-z0-9\s]', '', lat).strip()
    lat_words = [w for w in lat_clean.split() if len(w) >= 4 and w not in COMMON_WORDS]
    if lat_words:
        genus = lat_words[0]
        keys.add(genus)
        genus_stem = get_stem(genus)
        if len(genus_stem) >= 4 and genus_stem not in COMMON_WORDS:
            keys.add(genus_stem)
        if len(lat_words) >= 2:
            keys.add(f'{lat_words[0]} {lat_words[1]}')

    # Specific well-known cross-mappings
    if any(k in keys for k in ['levendul', 'lavandula']):
        keys.add('lavand')
        keys.add('lavanda')
    if any(k in keys for k in ['orhide', 'orchid']):
        keys.add('orhid')
        keys.add('orhidee')

    return [k for k in keys if len(k) >= 4]

plants = json.load(open('data/plants.json', encoding='utf-8'))
articles = json.load(open('data/articles.json', encoding='utf-8'))

valid_articles = [
    a for a in articles 
    if a['id'] != 182 and not ('cod: 599' in a.get('title', '').lower() or 'gama florimo' in a.get('title', '').lower())
]

for test_name in ['Levendula', 'Orhidee', 'Tei', 'Trandafir', 'Salcam', 'Muscata', 'Bonsai']:
    matches = [p for p in plants if test_name.lower() in p['name'].lower()]
    if matches:
        p = matches[0]
        keys = extract_plant_keywords(p)
        matched = []
        for a in valid_articles:
            t = normalize_text(a.get('title', ''))
            s = normalize_text(a.get('summary', ''))
            c = normalize_text(a.get('content', ''))
            score = 0
            for k in keys:
                pat = r'\b' + re.escape(k) + r'\b'
                if re.search(pat, t):
                    score += 100
                elif re.search(pat, s):
                    score += 50
                elif len(re.findall(pat, c)) >= 2:
                    score += 25
            if score >= 50:
                matched.append((score, a['id'], a['title']))
        matched.sort(key=lambda x: -x[0])
        print(f"{p['name']} -> {len(matched)} articles:")
        for sc, aid, at in matched[:3]:
            print(f"   #{aid} (score {sc}): {at[:60]}")
