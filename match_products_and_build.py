import os
import re
import json
import shutil
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_PATH = os.path.join(BASE_DIR, 'import_produse', 'documente_pdf', 'Descriere Produse.txt')
PROD_IMAGES_DIR = os.path.join(BASE_DIR, 'import_produse', 'produse_recomandate')
UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def strip_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_key(s):
    s = strip_accents(s.lower())
    s = s.replace('nutrislo', 'nutrisol')
    s = s.replace('soluite', 'solutie')
    # Remove volume suffixes like 0.1l, 500ml, 500 ml, 1l, 20l, 40l, 50l, 5l, 10l
    s = re.sub(r'\b(0[\.,]1\s*l|0[\.,]5\s*l|500\s*ml|1\s*l|5\s*l|10\s*l|20\s*l|40\s*l|50\s*l)\b', '', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def detect_brand(title):
    t_low = title.lower()
    if 'vitaflora' in t_low or 'vitaflóra' in t_low or 'baton' in t_low:
        return 'Vitaflora'
    if 'florasol' in t_low:
        return 'Florasol'
    if 'humiflor' in t_low:
        return 'Humiflor'
    if 'nutrisol' in t_low or 'nutrislo' in t_low:
        return 'Nutrisol'
    if 'plantasol' in t_low:
        return 'Plantasol'
    return 'Mont Rose'


def parse_descriere_produse(txt_path):
    """
    Parses numbered entries (1. Title - Description ... up to 26.) from Descriere Produse.txt
    """
    with open(txt_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Split by numbered item headers at start of line: e.g., "\t1. Title - " or "1. Title - "
    pattern = re.compile(r'(?:^|\n)\s*(\d+)\.\s+([^\n\-]+?)\s*-\s*', re.MULTILINE)
    matches = list(pattern.finditer(content))

    entries = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        raw_title = m.group(2).strip()
        start_pos = m.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start_pos:end_pos].strip()

        # Fix minor typo in entry 14 ("oluția" -> "Soluția")
        if body.startswith('oluția'):
            body = 'S' + body

        entries.append({
            'num': num,
            'title': raw_title,
            'norm_title': normalize_key(raw_title),
            'brand': detect_brand(raw_title),
            'description': body
        })
    return entries


# Extra fallback descriptions from Catalog Mont Rose 2026 (page 20) for products not in 1..26
EXTRA_CATALOG_PRODUCTS = {
    'baton_flori': {
        'title': 'Vitaflora Batoane fertilizante pentru plante cu flori',
        'brand': 'Vitaflora',
        'description': (
            'Batoanele fertilizante Vitaflora asigură plantelor decorative cu flori o nutriție completă, '
            'echilibrată și de lungă durată timp de 3 luni. Utilizarea preventivă și regulată a batoanelor '
            'nutritive contribuie la obținerea unor plante puternice, sănătoase și la o înflorire bogată.\n\n'
            'Utilizare: Pentru plante cu flori de apartament și balcon.\n'
            'Efect nutritiv: Asigură plantelor nutrienți timp de 3 luni.\n'
            'Ambalare: 30 buc / pachet'
        )
    },
    'baton_frunze': {
        'title': 'Vitaflora Batoane fertilizante pentru plante cu frunze',
        'brand': 'Vitaflora',
        'description': (
            'Batoanele fertilizante Vitaflora pentru plante decorative prin frunze asigură o hrănire '
            'continuă și echilibrată timp de 3 luni, stimulând dezvoltarea unui frunziș verde intens, '
            'viguros și sănătos.\n\n'
            'Utilizare: Pentru plante verzi și plante decorative cu frunze de interior.\n'
            'Efect nutritiv: Asigură plantelor nutrienți timp de 3 luni.\n'
            'Ambalare: 30 buc / pachet'
        )
    },
    'baton_orhidee': {
        'title': 'Vitaflora Batoane fertilizante pentru orhidee',
        'brand': 'Vitaflora',
        'description': (
            'Batoanele fertilizante Vitaflora special concepute pentru orhidee asigură eliberarea treptată '
            'a elementelor nutritive timp de 3 luni, susținând sănătatea rădăcinilor și înflorirea de lungă durată.\n\n'
            'Utilizare: Pentru toate speciile de orhidee cultivate în ghiveci.\n'
            'Efect nutritiv: Asigură plantelor nutrienți timp de 3 luni.\n'
            'Ambalare: 15 buc / pachet'
        )
    },
    'baton_balcon': {
        'title': 'Vitaflora Batoane fertilizante pentru plante de balcon',
        'brand': 'Vitaflora',
        'description': (
            'Batoanele fertilizante Vitaflora pentru plante de balcon și mușcate asigură plantelor '
            'nutrienții necesari timp de 3 luni, favorizând dezvoltarea viguroasă și înflorirea abundentă '
            'pe tot parcursul sezonului.\n\n'
            'Utilizare: Pentru mușcate și plante ornamentale de balcon în jardiniere sau ghivece.\n'
            'Efect nutritiv: Asigură plantelor nutrienți timp de 3 luni.\n'
            'Ambalare: 30 buc / pachet'
        )
    },
    'nutrisol_ecologic': {
        'title': 'Nutrisol Soluție de îngrijire ecologică a plantelor',
        'brand': 'Nutrisol',
        'description': (
            'Soluție de îngrijire ecologică a plantelor care are ca substanță activă oleat de potasiu (săpun K). '
            'Ajută la combaterea insectelor fitofage la toate tipurile de plante ornamentale în momentul apariției acestora, '
            'menținând plantele puternice și sănătoase.\n\n'
            'Substanță activă: Oleat de potasiu (săpun K).\n'
            'Utilizare: Pentru toate tipurile de plante ornamentale de interior și exterior.\n'
            'Ambalare: 0.5L (pulverizator)'
        )
    },
    'nutrisol_organic': {
        'title': 'Nutrisol Soluție de îngrijire organică a plantelor',
        'brand': 'Nutrisol',
        'description': (
            'Soluție de îngrijire organică a plantelor care are ca substanță activă extractul de urzică (Urtica). '
            'Ajută la combaterea insectelor fitofage și fortifică rezistența naturală la toate tipurile de plante ornamentale.\n\n'
            'Substanță activă: Urticaria (extract natural de urzică).\n'
            'Utilizare: Pentru toate tipurile de plante ornamentale de interior și exterior.\n'
            'Ambalare: 0.5L (pulverizator)'
        )
    }
}


def extract_volume_label(filename):
    """
    Extracts packaging size from the image filename if present (e.g. 0.1L, 0.5L / 500ml, 1L, 20L).
    """
    stem = filename.rsplit('.', 1)[0]
    m = re.search(r'\b(0[\.,]1\s*L|0[\.,]5\s*L|500\s*ml|1\s*L|5\s*L|10\s*L|20\s*L|40\s*L|50\s*L)\b', stem, re.I)
    if not m:
        return ''
    raw_vol = m.group(1).strip()
    low = raw_vol.lower().replace(' ', '')
    if low == '500ml':
        return '0.5L (500ml)'
    if low in ('0.1l', '0,1l'):
        return '0.1L'
    if low == '1l':
        return '1L'
    return raw_vol.upper()


def match_image_to_entry(filename, entries):
    stem = filename.rsplit('.', 1)[0].strip()
    norm_img = normalize_key(stem)
    vol_label = extract_volume_label(filename)

    # 1. Check direct/exact or high-overlap match with the 26 entries from Descriere Produse.txt
    best_entry = None
    best_score = 0

    for entry in entries:
        ne = entry['norm_title']
        if norm_img == ne:
            best_entry = entry
            best_score = 1000
            break

        # Token overlap score
        img_tokens = set(norm_img.split())
        entry_tokens = set(ne.split())
        # Must match brand (first token)
        if entry['norm_title'].split()[0] not in img_tokens:
            continue

        common = img_tokens & entry_tokens
        # Jaccard-like score weighted by exact coverage of entry tokens
        coverage = len(common) / max(len(entry_tokens), 1)
        precision = len(common) / max(len(img_tokens), 1)
        score = (coverage * 0.65) + (precision * 0.35)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry and best_score >= 0.65:
        display_name = best_entry['title']
        if vol_label:
            display_name = f"{display_name} - {vol_label}"
        return {
            'name': display_name,
            'brand': best_entry['brand'],
            'description': best_entry['description'],
            'matched_num': best_entry['num']
        }

    # 2. Check extra catalog items (Batoane fertilizante & Soluții de îngrijire ecologică/organică)
    if 'baton' in norm_img:
        if 'orhidee' in norm_img:
            info = EXTRA_CATALOG_PRODUCTS['baton_orhidee']
        elif 'frunze' in norm_img:
            info = EXTRA_CATALOG_PRODUCTS['baton_frunze']
        elif 'balcon' in norm_img:
            info = EXTRA_CATALOG_PRODUCTS['baton_balcon']
        else:
            info = EXTRA_CATALOG_PRODUCTS['baton_flori']
        return {
            'name': info['title'],
            'brand': info['brand'],
            'description': info['description'],
            'matched_num': 'Catalog'
        }

    if 'ecologica' in norm_img:
        info = EXTRA_CATALOG_PRODUCTS['nutrisol_ecologic']
        return {
            'name': info['title'],
            'brand': info['brand'],
            'description': info['description'],
            'matched_num': 'Catalog'
        }

    if 'organica' in norm_img:
        info = EXTRA_CATALOG_PRODUCTS['nutrisol_organic']
        return {
            'name': info['title'],
            'brand': info['brand'],
            'description': info['description'],
            'matched_num': 'Catalog'
        }

    # Fallback
    return {
        'name': stem,
        'brand': detect_brand(stem),
        'description': entries[0]['description'] if entries else '',
        'matched_num': 'Fallback'
    }


def build_products():
    entries = parse_descriere_produse(TXT_PATH)
    print(f"Loaded {len(entries)} product descriptions from 'Descriere Produse.txt'.")

    all_images = sorted([
        f for f in os.listdir(PROD_IMAGES_DIR)
        if f.rsplit('.', 1)[-1].lower() in {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    ])
    print(f"Found {len(all_images)} images in 'import_produse/produse_recomandate'.\n")

    # Clean up old prod_2026_ images in static/uploads
    for f in os.listdir(UPLOADS_DIR):
        if f.startswith('prod_2026_'):
            try:
                os.remove(os.path.join(UPLOADS_DIR, f))
            except Exception:
                pass

    processed_products = []
    for idx, img_name in enumerate(all_images):
        src_path = os.path.join(PROD_IMAGES_DIR, img_name)
        target_name = f"prod_2026_{img_name}"
        target_path = os.path.join(UPLOADS_DIR, target_name)
        shutil.copy2(src_path, target_path)

        image_url = f"/static/uploads/{target_name}"
        match_data = match_image_to_entry(img_name, entries)

        prod_id = idx + 1
        processed_products.append({
            'id': prod_id,
            'name': match_data['name'],
            'brand': match_data['brand'],
            'code': f"MR-{prod_id:03d}",
            'description': match_data['description'],
            'image_url': image_url,
            'images': [image_url],
            'external_url': "https://www.montrose.ro"
        })
        print(f"[{prod_id:2d}] Img: '{img_name}' -> [#{match_data['matched_num']}] '{match_data['name']}'")

    products_json_path = os.path.join(DATA_DIR, 'products.json')
    with open(products_json_path, 'w', encoding='utf-8') as f:
        json.dump(processed_products, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(processed_products)} products to {products_json_path}.")
    return processed_products


if __name__ == '__main__':
    build_products()
