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
BACKUP_JSON = os.path.join(DATA_DIR, 'plants_backup_before_hd_fetch.json')

USER_AGENT = 'PlanteOnlineBotanicalCatalog/2.0 (contact@planteonline.ro; Educational Bot)'

# Known placeholder images on the old planteonline.ro website (flower icon, broken icon, etc.)
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

def clean_latin_query(latin_name, common_name=''):
    if not latin_name:
        # Fallback to common name cleaning
        cn = re.split(r'[,;\(\)]', common_name)[0].strip()
        return cn

    # Remove text in parentheses, e.g. (planta de apartament)
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', latin_name)
    # Remove 'hibrid', 'var.', 'subsp.', 'sp.', 'x ', 'cv.'
    cleaned = re.sub(r'\b(hibrid|hybrid|var\.|subsp\.|sp\.|ssp\.|cv\.|cultivar)\b', '', cleaned, flags=re.I)
    cleaned = cleaned.replace(' x ', ' ').replace(' - ', ' ')
    cleaned = re.sub(r'[^a-zA-Z\s]', ' ', cleaned).strip()
    words = cleaned.split()
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    elif len(words) == 1:
        return words[0]
    return common_name

def fetch_wikipedia_batch(titles_list):
    """
    Fetches thumbnails for a batch of page titles from English Wikipedia.
    """
    if not titles_list:
        return {}
    
    titles_str = '|'.join([t.replace(' ', '_') for t in titles_list])
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(titles_str)}&prop=pageimages&format=json&pithumbsize=960&redirects=1"
    
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            pages = data.get('query', {}).get('pages', {})
            results = {}
            # Handle normalized titles
            norm_map = {}
            for n in data.get('query', {}).get('normalized', []):
                norm_map[n['to']] = n['from']
            # Handle redirects
            red_map = {}
            for red in data.get('query', {}).get('redirects', []):
                red_map[red['to']] = red['from']

            for pid, pinfo in pages.items():
                title = pinfo.get('title')
                thumb = pinfo.get('thumbnail', {}).get('source')
                if thumb and title:
                    results[title] = thumb
                    # Also map back to original query if normalized/redirected
                    if title in red_map:
                        results[red_map[title]] = thumb
                    if title in norm_map:
                        results[norm_map[title]] = thumb
            return results
    except Exception as e:
        print(f"Error querying Wikipedia batch: {e}")
        return {}

def search_wikimedia_commons(query):
    """
    Searches Wikimedia Commons for high-quality botanical photography.
    """
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrlimit=3&prop=pageimages&pithumbsize=960&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                thumb = p.get('thumbnail', {}).get('source')
                if thumb and not any(bad in thumb.lower() for bad in ['drawing', 'map', 'distribution', 'icon', 'logo', 'diagram']):
                    return thumb
    except Exception:
        pass
    return None

def search_wikipedia_fallback(query):
    """
    Performs full text search on English Wikipedia and fetches page thumbnail.
    """
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&srlimit=2&format=json"
    req = urllib.request.Request(search_url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            search_res = data.get('query', {}).get('search', [])
            if search_res:
                top_title = search_res[0]['title']
                batch_res = fetch_wikipedia_batch([top_title])
                return batch_res.get(top_title)
    except Exception:
        pass
    return None

def main():
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    # Save backup first
    if not os.path.exists(BACKUP_JSON):
        with open(BACKUP_JSON, 'w', encoding='utf-8') as f:
            json.dump(plants, f, indent=2, ensure_ascii=False)
        print(f"Created backup at {BACKUP_JSON}")

    print(f"Processing {len(plants)} plants for HD photo enrichment...")

    # Step 1: Filter out placeholders from existing images
    cleaned_count = 0
    for p in plants:
        orig_imgs = p.get('images', [])
        valid_imgs = [img for img in orig_imgs if img not in KNOWN_PLACEHOLDERS]
        if len(valid_imgs) != len(orig_imgs):
            cleaned_count += 1
            p['images'] = valid_imgs

    print(f"Removed low-res placeholders from {cleaned_count} plants.")

    # Step 2: Batch Wikipedia query for all plants
    # Group in batches of 35
    BATCH_SIZE = 35
    plant_queries = []
    for p in plants:
        q = clean_latin_query(p.get('latin_name', ''), p.get('name', ''))
        plant_queries.append((p, q))

    print("\n--- BATCH 1: Primary Wikipedia Latin Name Resolution ---")
    all_matched = 0
    unmatched_plants = []

    for i in range(0, len(plant_queries), BATCH_SIZE):
        batch = plant_queries[i:i + BATCH_SIZE]
        titles = list(set([q for p, q in batch if q]))
        results = fetch_wikipedia_batch(titles)
        
        for p, q in batch:
            # Check if an exact match was found
            found_thumb = None
            if q in results:
                found_thumb = results[q]
            else:
                for k, v in results.items():
                    if k.lower() == q.lower() or q.lower() in k.lower():
                        found_thumb = v
                        break
            
            if found_thumb:
                # Add HD photo to front of list
                existing = p.get('images', [])
                if found_thumb not in existing:
                    p['images'] = [found_thumb] + [img for img in existing if img != found_thumb]
                all_matched += 1
            else:
                unmatched_plants.append((p, q))

        time.sleep(0.3)
        sys.stdout.write(f"\rProcessed {min(i + BATCH_SIZE, len(plant_queries))}/{len(plant_queries)} plants... (Matched: {all_matched})")
        sys.stdout.flush()

    print(f"\nBatch 1 completed! Found HD photos for {all_matched} plants.")
    print(f"Remaining plants to search via Commons/Search Fallback: {len(unmatched_plants)}")

    # Step 3: Targeted search on Wikimedia Commons & Wikipedia Search for remaining
    commons_matched = 0
    for idx, (p, q) in enumerate(unmatched_plants):
        found_img = None
        # Try genus only if species failed
        words = q.split()
        if len(words) >= 2:
            genus = words[0]
            # Try full query on Commons
            found_img = search_wikimedia_commons(q)
            if not found_img:
                found_img = search_wikipedia_fallback(q)
            if not found_img:
                # Try genus on Wikipedia
                g_res = fetch_wikipedia_batch([genus])
                found_img = g_res.get(genus) or g_res.get(genus.capitalize())
        else:
            found_img = search_wikimedia_commons(q) or search_wikipedia_fallback(q)

        if found_img:
            existing = p.get('images', [])
            if found_img not in existing:
                p['images'] = [found_img] + [img for img in existing if img != found_img]
            commons_matched += 1

        if (idx + 1) % 10 == 0 or idx == len(unmatched_plants) - 1:
            sys.stdout.write(f"\rFallback search: {idx + 1}/{len(unmatched_plants)}... (New matches: {commons_matched})")
            sys.stdout.flush()
        time.sleep(0.2)

    total_updated = all_matched + commons_matched
    print(f"\nTotal plants enriched with HD photos: {total_updated} / {len(plants)} ({(total_updated/len(plants))*100:.1f}%)")

    # Step 4: Ensure every single plant has at least 1 valid botanical photo
    default_botanic_photos = [
        "https://images.unsplash.com/photo-1463936575829-25148e1db1b8?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1545241047-6083a3684587?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1512428813834-c702c7702b78?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=900&q=80"
    ]
    missing_after = 0
    for p in plants:
        if not p.get('images') or len(p['images']) == 0:
            missing_after += 1
            cat = p.get('category', '')
            fallback = default_botanic_photos[p['id'] % len(default_botanic_photos)]
            p['images'] = [fallback]

    # Save to data/plants.json
    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved updated catalog to {PLANTS_JSON}!")
    print(f"Plants with HD images: {len(plants) - missing_after}, fallback-covered: {missing_after}")

if __name__ == '__main__':
    main()
