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
UPLOADS_PLANTS = os.path.join(BASE_DIR, 'static', 'uploads', 'plants')
os.makedirs(UPLOADS_PLANTS, exist_ok=True)

USER_AGENT = 'PlanteOnlineBotanicalCatalog/2.0 (contact@planteonline.ro; Educational Botanical Project)'

def search_and_download_commons(query, local_prefix, count=3):
    url = f'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit={count*3}&prop=imageinfo&iiprop=url&iiurlwidth=960&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    saved_paths = []
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read())
            pages = d.get('query', {}).get('pages', {})
            idx = 1
            for pid, p in pages.items():
                title = p.get('title', '').lower()
                # Exclude non-photographs
                if any(bad in title for bad in ['.svg', 'logo', 'icon', 'map', 'chart', 'diagram', 'stamp', 'coin', 'drawing', 'illustration', 'specimen', 'herbarium', 'flag']):
                    continue
                ii = p.get('imageinfo', [])
                if ii:
                    thumb_url = ii[0].get('thumburl') or ii[0].get('url')
                    if not thumb_url:
                        continue
                    local_filename = f"{local_prefix}_{idx}.jpg"
                    dest = os.path.join(UPLOADS_PLANTS, local_filename)
                    try:
                        img_req = urllib.request.Request(thumb_url, headers={'User-Agent': USER_AGENT})
                        with urllib.request.urlopen(img_req, timeout=10) as resp:
                            with open(dest, 'wb') as out_f:
                                out_f.write(resp.read())
                        if os.path.getsize(dest) > 10000: # at least 10KB
                            saved_paths.append(f"/static/uploads/plants/{local_filename}")
                            print(f"✓ Saved {dest} ({os.path.getsize(dest)} bytes)")
                            idx += 1
                            if len(saved_paths) >= count:
                                break
                    except Exception as ex:
                        print(f"Error downloading {thumb_url}: {ex}")
    except Exception as e:
        print(f"Error searching {query}: {e}")
    return saved_paths

def main():
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    # 1. Download dedicated verified local photos for trending plants
    print("--- DOWNLOADING LOCAL VERIFIED PHOTOS FOR TOP TRENDING PLANTS ---")

    # Surfinia (ID 662)
    p662 = next((p for p in plants if p['id'] == 662), None)
    if p662:
        surf_imgs = [
            "/static/uploads/plants/surfinia_1.jpg",
            "/static/uploads/plants/surfinia_2.jpg",
            "/static/uploads/plants/surfinia_3.jpg"
        ]
        # Verify files exist on disk
        valid_surf = [img for img in surf_imgs if os.path.exists(os.path.join(BASE_DIR, img.lstrip('/')))]
        if len(valid_surf) < 3:
            fetched = search_and_download_commons("Petunia Surfinia balcony flower", "surfinia", 3)
            p662['images'] = fetched if fetched else valid_surf
        else:
            p662['images'] = valid_surf
        p662['image_url'] = p662['images'][0]
        print(f"Surfinia (662) images: {p662['images']}")

    # Petunia (ID 661)
    p661 = next((p for p in plants if p['id'] == 661), None)
    if p661:
        pet_imgs = search_and_download_commons("Petunia x hybrida flower garden", "petunia", 3)
        if pet_imgs:
            p661['images'] = pet_imgs
            p661['image_url'] = pet_imgs[0]
            print(f"Petunia (661) images: {p661['images']}")

    # Calibrachoa (ID 666)
    p666 = next((p for p in plants if p['id'] == 666), None)
    if p666:
        calib_imgs = search_and_download_commons("Calibrachoa flower", "calibrachoa", 3)
        if calib_imgs:
            p666['images'] = calib_imgs
            p666['image_url'] = calib_imgs[0]
            print(f"Calibrachoa (666) images: {p666['images']}")

    # Dipladenia (ID 663)
    p663 = next((p for p in plants if p['id'] == 663), None)
    if p663:
        dipla_imgs = search_and_download_commons("Mandevilla sanderi flower", "dipladenia", 3)
        if dipla_imgs:
            p663['images'] = dipla_imgs
            p663['image_url'] = dipla_imgs[0]
            print(f"Dipladenia (663) images: {p663['images']}")

    # Olea europaea (ID 664)
    p664 = next((p for p in plants if p['id'] == 664), None)
    if p664:
        olea_imgs = search_and_download_commons("Olea europaea tree garden", "olea", 3)
        if olea_imgs:
            p664['images'] = olea_imgs
            p664['image_url'] = olea_imgs[0]
            print(f"Olea europaea (664) images: {p664['images']}")

    # Zamioculcas (ID 659)
    p659 = next((p for p in plants if p['id'] == 659), None)
    if p659:
        zz_imgs = search_and_download_commons("Zamioculcas zamiifolia plant", "zamioculcas", 3)
        if zz_imgs:
            p659['images'] = zz_imgs
            p659['image_url'] = zz_imgs[0]
            print(f"Zamioculcas (659) images: {p659['images']}")

    # Monstera adansonii (ID 660)
    p660 = next((p for p in plants if p['id'] == 660), None)
    if p660:
        p660['images'] = [
            "/static/uploads/plants/monstera_adansonii_1.jpg",
            "/static/uploads/plants/monstera_adansonii_2.jpg",
            "/static/uploads/plants/monstera_adansonii_3.jpg"
        ]
        p660['image_url'] = p660['images'][0]
        print(f"Monstera adansonii (660) images: {p660['images']}")

    # Philodendron Pink Princess (ID 665)
    p665 = next((p for p in plants if p['id'] == 665), None)
    if p665:
        pp_imgs = search_and_download_commons("Philodendron erubescens Pink Princess", "pink_princess", 3)
        if not pp_imgs or len(pp_imgs) < 2:
            pp_imgs = search_and_download_commons("Philodendron erubescens", "pink_princess", 3)
        if pp_imgs:
            p665['images'] = pp_imgs
            p665['image_url'] = pp_imgs[0]
            print(f"Philodendron Pink Princess (665) images: {p665['images']}")

    # Muscata (ID 220)
    p220 = next((p for p in plants if p['id'] == 220), None)
    if p220:
        p220['images'] = [
            "/static/uploads/plants/muscata_1.jpg",
            "/static/uploads/plants/muscata_2.jpg",
            "/static/uploads/plants/muscata_3.jpg"
        ]
        p220['image_url'] = p220['images'][0]
        print(f"Muscata (220) images: {p220['images']}")

    # 2. General Catalog Sweep: Clean out broken raw upload.wikimedia.org URLs and sunflowers
    print("\n--- GENERAL CATALOG SWEEP ---")
    SUNFLOWER_UNSPLASH = "https://images.unsplash.com/photo-1597848212624-a19eb35e2651"
    MONSTERA_UNSPLASH = "https://images.unsplash.com/photo-1545241047-6083a3684587"

    cleaned_count = 0
    for p in plants:
        # Check images
        imgs = p.get('images', [])
        valid_imgs = []
        for u in imgs:
            # Drop unscaled upload.wikimedia.org which return 404
            if 'upload.wikimedia.org' in u:
                continue
            # Drop sunflower unsplash if not a sunflower plant
            if SUNFLOWER_UNSPLASH in u and 'floarea-soarelui' not in p.get('name', '').lower() and 'helianthus' not in p.get('latin_name', '').lower():
                continue
            # Drop monstera unsplash if not a monstera plant
            if MONSTERA_UNSPLASH in u and 'monstera' not in p.get('name', '').lower() and 'monstera' not in p.get('latin_name', '').lower():
                continue
            valid_imgs.append(u)

        if len(valid_imgs) != len(imgs):
            cleaned_count += 1
            # If all were removed, keep at least the first if thumb.wikimedia.org or local
            if not valid_imgs and imgs:
                # keep image 0 if it's thumb.wikimedia
                if 'thumb.wikimedia.org' in imgs[0] or imgs[0].startswith('/static/'):
                    valid_imgs = [imgs[0]]
            p['images'] = valid_imgs if valid_imgs else imgs[:1]
            p['image_url'] = p['images'][0]

    print(f"Cleaned broken URLs from {cleaned_count} plants.")

    # Save to data/plants.json
    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved updated catalog to {PLANTS_JSON}!")

if __name__ == '__main__':
    main()
