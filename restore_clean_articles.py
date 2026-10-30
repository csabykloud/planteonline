import json
import re
import sys
import ftfy

sys.stdout.reconfigure(encoding='utf-8')

# Load the clean backup from cleaned_articles.json
with open('cleaned_articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

print(f"Loaded {len(articles)} articles from cleaned_articles.json.")

# Curated, perfect titles for key articles
SPECIFIC_TITLES = {
    30: "Lucrări de primăvară: Transplantarea corectă a plantelor",
    31: "Fertilizarea livezilor de păr: doze și recomandări optime",
    32: "Cerințele plantelor ornamentale pentru elementele minerale și nutriție",
    34: "Înființarea și întreținerea livezilor de prun",
    36: "Legenda rozelor și simbolistica florilor în istorie",
    39: "Ghidul complet al substraturilor: ghivece, jardiniere și amestecuri de turbă",
    40: "Cum udăm și protejăm plantele în perioada concediului de vară",
    41: "Vremea umedă și ploioasă: protejarea plantelor din grădină și ghivece",
    42: "Cauzele îngălbenirii și ofilirii frunzelor la plantele de apartament",
    43: "Drenajul ghivecelor: rolul orificiilor de scurgere pentru rădăcini sănătoase",
    44: "Habitatul natural al plantelor și adaptarea la condițiile de apartament",
    45: "Pajiști superbe și amenajarea grădinilor rezidențiale",
    46: "Temperatura optimă și toleranța termică a plantelor de interior",
    47: "Umiditatea aerului și necesarul de apă pentru plantele exotice",
    48: "Amenajarea grădinilor moderne: arbori, arbuști și conifere",
    49: "Perioada de repaus vegetativ la plantele de apartament",
    51: "Protecția arborilor și coniferelor împotriva greutății zăpezii",
    52: "Viața plantei și rolul esențial al apei în țesuturile vegetale",
    53: "Toleranța termică și aerisirea spațiilor pentru florile de cameră",
    54: "Pregătirea grădinii pentru sezonul rece și îngrijirea de iarnă",
    120: "Semințe - dăruitori de viață: ghid complet pentru semănarea florilor",
    130: "Jardiniere și plante suspendate: decorațiuni florale pentru balcoane",
    184: "Pregătirea plantelor pentru iarnă & Culesul strugurilor"
}

MOJIBAKE_MAP = [
    ('Ă\x83', 'ă'),
    ('Ă\x82', 'â'),
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
    ('V remea', 'Vremea'),
    ('v remea', 'vremea'),
    ('v iața', 'viața'),
    ('V iața', 'Viața'),
    ('v iaţa', 'viața'),
    ('V iaţa', 'Viața'),
    ('cÎt', 'cât'),
    ('cît', 'cât'),
    ('rÎnd', 'rând'),
    ('rînd', 'rând'),
    ('Începind', 'Începând'),
    ('începind', 'începând'),
]

# Non-printable control characters
CTRLS = [chr(i) for i in range(32) if i not in (9, 10, 13)] + ['\ufffd']

def clean_text(text):
    if not text or not isinstance(text, str):
        return text

    res = text
    for cc in CTRLS:
        res = res.replace(cc, '')

    for bad, good in MOJIBAKE_MAP:
        res = res.replace(bad, good)

    res = ftfy.fix_text(res)

    res = re.sub(r'\bĂ\s*n\b', 'În', res)
    res = re.sub(r'\bĂ\s*n\s+', 'În ', res)

    # Clean double quotes repeats if any
    res = re.sub(r'"{2,}', '"', res)

    # Clean up spaces
    lines = res.splitlines()
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    return '\n'.join(cleaned_lines)

for a in articles:
    aid = a.get('id')
    
    # Clean content of calendar junk
    c = a.get('content', '')
    if 'Octombrie Octombrie Plante de Exterior' in c:
        c = c.split('Octombrie Octombrie Plante de Exterior')[0].strip()
    if 'Unelte Sapa, grebla' in c:
        c = c.split('Unelte Sapa, grebla')[0].strip()

    c = clean_text(c)
    a['content'] = c

    # Set clean title
    if aid in SPECIFIC_TITLES:
        t = SPECIFIC_TITLES[aid]
    else:
        t = clean_text(a.get('title', ''))
        # If title is excessively long or has sentence fragment, shorten
        if len(t) > 95 and '.' in t[:90]:
            t = t[:t.index('.')].strip()
        elif len(t) > 110:
            words = t.split()
            t = ' '.join(words[:12]) + '...'

    # Remove quotes around entire title if present
    t = t.strip(' "“„”\'')
    a['title'] = t

    # Clean summary
    s = clean_text(a.get('summary', ''))
    if 'Octombrie Octombrie' in s or len(s) < 20 or 'citeste mai mult' in s:
        s = c[:220].strip() + '...'
    s = s.strip(' "“„”\'')
    a['summary'] = s

with open('data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print("data/articles.json successfully updated with crystal clean Romanian titles and texts!")
