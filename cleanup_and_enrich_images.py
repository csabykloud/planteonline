import os
import re
import json
import time
import urllib.request
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PLANTS_JSON = os.path.join(DATA_DIR, 'plants.json')
BACKUP_JSON = os.path.join(DATA_DIR, 'plants_backup_before_img_clean.json')

USER_AGENT = 'PlanteOnlineBotanicalCatalog/2.0 (contact@planteonline.ro; Educational Bot)'

KNOWN_PLACEHOLDERS = {
    'https://www.planteonline.ro/2/uploads/images/_12537743551.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12328767241.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537747261.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537746801.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12328766421.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537748731.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12328722451.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537740441.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537739441.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537735331.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537736611.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537741641.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537742841.jpg',
    'https://www.planteonline.ro/2/uploads/images/_12537737871.jpg'
}

LATIN_CORRECTIONS = {
    'Biedens ferulifolia': 'Bidens ferulifolia',
    'Bouganinvillea x buttiana': 'Bougainvillea buttiana',
    'Chaecyparis lawsoniana': 'Chamaecyparis lawsoniana',
    'Ciperus albostriatus': 'Cyperus albostriatus',
    'Ctenante oppenheimiana': 'Ctenanthe oppenheimiana',
    'Aeschyanthus radicans': 'Aeschynanthus radicans',
    'Gymnucalycium mihanovichii': 'Gymnocalycium mihanovichii',
    'Mandinilla x amoena \'\'Alice du Pont\'\'': 'Mandevilla amoena',
    'Molidul': 'Picea abies',
    'Paphiopedillum-hibrid': 'Paphiopedilum',
    'Sterlitzia reginae': 'Strelitzia reginae',
    'Strobilantes dyerianaus': 'Strobilanthes dyeriana',
    'Sparmania Africana': 'Sparrmannia africana',
    'Tradesantia zebrina': 'Tradescantia zebrina',
    'Camsis radicans': 'Campsis radicans'
}

def clean_latin_query(latin_name, common_name=''):
    if not latin_name:
        cn = re.split(r'[,;\(\)]', common_name)[0].strip()
        return cn

    if latin_name in LATIN_CORRECTIONS:
        return LATIN_CORRECTIONS[latin_name]

    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', latin_name)
    cleaned = re.sub(r'\b(hibrid|hybrid|var\.|subsp\.|sp\.|ssp\.|cv\.|cultivar)\b', '', cleaned, flags=re.I)
    cleaned = cleaned.replace(' x ', ' ').replace(' - ', ' ')
    cleaned = re.sub(r'[^a-zA-Z\s]', ' ', cleaned).strip()
    words = cleaned.split()
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    elif len(words) == 1:
        return words[0]
    return common_name

def fetch_additional_wiki_photos(latin_query, current_images, max_needed=3):
    needed = max_needed - len(current_images)
    if needed <= 0:
        return current_images

    found = []
    # 1. Lead page thumbnail if not already present
    url_lead = f'https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(latin_query)}&prop=pageimages&format=json&pithumbsize=960&redirects=1'
    try:
        req = urllib.request.Request(url_lead, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
            pages = d.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                thumb = p.get('thumbnail', {}).get('source')
                if thumb and thumb not in current_images and thumb not in found:
                    found.append(thumb)
                    if len(found) >= needed:
                        return current_images + found
    except Exception:
        pass

    # 2. Article images
    url_art = f'https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(latin_query)}&generator=images&gimlimit=12&prop=imageinfo&iiprop=url&iiurlwidth=960&format=json&redirects=1'
    try:
        req = urllib.request.Request(url_art, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
            pages = d.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                title = p.get('title', '').lower()
                if any(bad in title for bad in ['.svg', 'icon', 'logo', 'map', 'flag', 'commons-logo', 'crystal', 'distribution', 'stub']):
                    continue
                ii = p.get('imageinfo', [])
                if ii:
                    u = ii[0].get('thumburl') or ii[0].get('url')
                    if u and u not in current_images and u not in found:
                        found.append(u)
                        if len(found) >= needed:
                            return current_images + found
    except Exception:
        pass

    # 3. Wikimedia Commons search fallback if still needed
    if len(found) < needed:
        url_comm = f'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(latin_query)}&gsrlimit=6&prop=pageimages&pithumbsize=960&format=json'
        try:
            req = urllib.request.Request(url_comm, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as r:
                d = json.loads(r.read())
                pages = d.get('query', {}).get('pages', {})
                for pid, p in pages.items():
                    thumb = p.get('thumbnail', {}).get('source')
                    if thumb and not any(bad in thumb.lower() for bad in ['drawing', 'map', 'icon', 'logo', 'diagram', 'chart', 'distribution', 'stamp', 'specimen', 'herbarium']):
                        if thumb not in current_images and thumb not in found:
                            found.append(thumb)
                            if len(found) >= needed:
                                break
        except Exception:
            pass

    return (current_images + found)[:max_needed]

def main():
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    # Backup
    with open(BACKUP_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)
    print(f"Backed up plants to {BACKUP_JSON}")

    # Correct known Latin name typos
    for p in plants:
        orig_lat = p.get('latin_name', '')
        if orig_lat in LATIN_CORRECTIONS:
            p['latin_name'] = LATIN_CORRECTIONS[orig_lat]

    print("Step 1: Cleaning low-res thumbnails and duplicates...")
    plants_needing_enrichment = []

    for p in plants:
        orig = p.get('images', [])
        # Remove low-res thumbnails with '/_' and known placeholders
        cleaned = []
        for img in orig:
            if img in KNOWN_PLACEHOLDERS:
                continue
            if 'planteonline.ro' in img and '/_' in img:
                continue
            if img not in cleaned:
                cleaned.append(img)

        # Separate into HD wikimedia/unsplash vs old planteonline
        hd_images = [img for img in cleaned if 'wikimedia.org' in img or 'unsplash.com' in img]
        old_planteonline = [img for img in cleaned if 'planteonline.ro' in img]

        # If we have 2 or 3 HD images, we don't need old planteonline at all
        if len(hd_images) >= 3:
            p['images'] = hd_images[:3]
        elif len(hd_images) >= 1:
            p['images'] = hd_images
            plants_needing_enrichment.append(p)
        elif len(old_planteonline) > 0:
            # Plant has no HD image at all, must fetch!
            p['images'] = []
            plants_needing_enrichment.append(p)
        else:
            p['images'] = []
            plants_needing_enrichment.append(p)

    print(f"Cleaned images for {len(plants)} plants.")
    print(f"Plants with fewer than 3 HD photos: {len(plants_needing_enrichment)}")

    # Step 2: Fetch additional high-res photos for plants that have < 3 photos
    # To keep response fast, we query for plants needing photos
    for idx, p in enumerate(plants_needing_enrichment):
        lat = clean_latin_query(p.get('latin_name', ''), p.get('name', ''))
        current = p.get('images', [])
        if len(current) < 3:
            enriched = fetch_additional_wiki_photos(lat, current, max_needed=3)
            p['images'] = enriched

        if (idx + 1) % 25 == 0 or idx == len(plants_needing_enrichment) - 1:
            sys.stdout.write(f"\rEnriching photos: {idx + 1}/{len(plants_needing_enrichment)} done...")
            sys.stdout.flush()
        time.sleep(0.08)

    print("\nPhoto enrichment completed!")

    # Step 3: Verify and ensure max 3 images and valid fallback if any empty
    fallback_photos = [
        "https://images.unsplash.com/photo-1463936575829-25148e1db1b8?auto=format&fit=crop&w=960&q=80",
        "https://images.unsplash.com/photo-1545241047-6083a3684587?auto=format&fit=crop&w=960&q=80",
        "https://images.unsplash.com/photo-1512428813834-c702c7702b78?auto=format&fit=crop&w=960&q=80"
    ]
    for p in plants:
        imgs = p.get('images', [])
        if not imgs:
            imgs = [fallback_photos[p['id'] % len(fallback_photos)]]
        p['images'] = imgs[:3]
        p['image_url'] = p['images'][0]

    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)

    print("Saved all updated plant images to plants.json!")

if __name__ == '__main__':
    main()
