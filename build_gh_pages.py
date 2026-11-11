"""
Static site exporter for GitHub Pages (https://csabykloud.github.io/planteonline/).
Renders all Flask routes, category/letter views, legal pages,
API endpoints, and copies static & showcase assets.
"""
import os
import re
import json
import shutil
import urllib.parse
from pathlib import Path
import app as app_module
from app import app, load_json, PRODUCT_MENU_CATEGORIES, PLANT_CATEGORIES_META

BASE_PREFIX = "/planteonline"
OUT_DIR = Path("_gh_pages")

# Cache JSON loads in memory and disable analytics/view-count disk writes during static export
_JSON_CACHE = {}
_orig_load_json = app_module.load_json

def _cached_load_json(filename):
    if filename not in _JSON_CACHE:
        _JSON_CACHE[filename] = _orig_load_json(filename)
    return _JSON_CACHE[filename]

app_module.load_json = _cached_load_json
app_module.save_json = lambda *args, **kwargs: None
app_module.record_visit = lambda *args, **kwargs: None
app_module.record_product_interaction = lambda *args, **kwargs: None


def slugify(text: str) -> str:
    s = text.lower().strip()
    for a, b in [('ă', 'a'), ('â', 'a'), ('î', 'i'), ('ș', 's'), ('ț', 't'), ('ş', 's'), ('ţ', 't')]:
        s = s.replace(a, b)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'all'


import stat

def _remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def build_static_site():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR, onexc=_remove_readonly)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Touch .nojekyll so GitHub Pages serves all files and folders cleanly
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    plants = load_json("plants.json")
    articles = load_json("articles.json")
    products = load_json("products.json")

    article_categories = sorted({(a.get("category") or "").strip() for a in articles if (a.get("category") or "").strip()})
    letters = ["ALL"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]

    # Map of query-string URLs to static directory paths (relative to site root without BASE_PREFIX)
    query_url_map = {}

    # 1. Product categories
    for c in PRODUCT_MENU_CATEGORIES:
        slug = c["slug"]
        query_url_map[f"/produse?categorie={slug}"] = f"/produse/categorie/{slug}/"
    query_url_map["/produse?categorie=toate"] = "/produse/"

    # 2. Calendar months (on / and /calendar)
    for m in range(1, 13):
        query_url_map[f"/?luna={m}"] = f"/luna/{m}/"
        query_url_map[f"/calendar?luna={m}"] = f"/calendar/luna/{m}/"

    # 3. Article categories
    for acat in article_categories:
        aslug = slugify(acat)
        enc_plus = urllib.parse.quote_plus(acat)
        enc_pct = urllib.parse.quote(acat)
        query_url_map[f"/articole?categorie={enc_plus}"] = f"/articole/categorie/{aslug}/"
        query_url_map[f"/articole?categorie={enc_pct}"] = f"/articole/categorie/{aslug}/"
        query_url_map[f"/articole?categorie={acat}"] = f"/articole/categorie/{aslug}/"

    # 4. Plant A-Z letters & categories (support both ?l=, ?litera=, and clean paths)
    for l in letters:
        query_url_map[f"/plante-az?litera={l}"] = f"/plante-az/litera/{l}/"
        query_url_map[f"/plante-az?l={l}"] = f"/plante-az/litera/{l}/"
    for pc in PLANT_CATEGORIES_META:
        pslug = pc["slug"]
        pcat = pc["name"]
        enc_plus = urllib.parse.quote_plus(pcat)
        enc_pct = urllib.parse.quote(pcat)
        query_url_map[f"/plante-az?categorie={enc_plus}"] = f"/plante-az/categorie/{pslug}/"
        query_url_map[f"/plante-az?categorie={enc_pct}"] = f"/plante-az/categorie/{pslug}/"
        query_url_map[f"/plante-az?categorie={pcat}"] = f"/plante-az/categorie/{pslug}/"
        query_url_map[f"/plante-az?subtip={enc_plus}"] = f"/plante-az/categorie/{pslug}/"
        query_url_map[f"/plante-az?subtip={enc_pct}"] = f"/plante-az/categorie/{pslug}/"
        query_url_map[f"/plante-az?subtip={pcat}"] = f"/plante-az/categorie/{pslug}/"

    def rewrite_html(html: str) -> str:
        # First replace known query-string URLs (most specific first)
        for q_url, static_path in sorted(query_url_map.items(), key=lambda x: -len(x[0])):
            html = html.replace(f'href="{q_url}"', f'href="{BASE_PREFIX}{static_path}"')
            html = html.replace(f"href='{q_url}'", f"href='{BASE_PREFIX}{static_path}'")

        # Prefix root-relative href, src, action, data-*-url attributes with BASE_PREFIX
        def repl_attr(match):
            attr = match.group(1)
            quote = match.group(2)
            val = match.group(3)
            if val.startswith(("//", "http://", "https://", "mailto:", "tel:", "#", "javascript:", "data:", BASE_PREFIX)):
                return match.group(0)
            if val.startswith("/"):
                return f"{attr}={quote}{BASE_PREFIX}{val}{quote}"
            return match.group(0)

        html = re.sub(
            r'\b(href|src|action|data-url|data-base-url|data-plant-base-url|data-az-base-url|data-search-json-url)=(["\'])(/[^"\']*)\2',
            repl_attr,
            html,
        )

        # Also rewrite inline onclick="openShowcaseLightbox('/...')" or window.location.href='/...'
        html = re.sub(
            r"openShowcaseLightbox\('(/[^']+)'\)",
            lambda m: f"openShowcaseLightbox('{BASE_PREFIX}{m.group(1)}')",
            html,
        )
        html = re.sub(
            r"window\.location\.href='(/[^']+)'",
            lambda m: f"window.location.href='{BASE_PREFIX}{m.group(1)}'",
            html,
        )
        html = re.sub(
            r"switchMainImage\('(/[^']+)'",
            lambda m: f"switchMainImage('{BASE_PREFIX}{m.group(1)}'",
            html,
        )
        # Also rewrite JSON-embedded image paths on index.html
        html = html.replace('"/static/', f'"{BASE_PREFIX}/static/')

        # Inject window.PLANTEONLINE_BASE_PREFIX for client-side scripts
        base_script = f'<script>window.PLANTEONLINE_BASE_PREFIX = "{BASE_PREFIX}";</script>\n'
        html = html.replace("</head>", base_script + "</head>", 1)
        return html

    def save_route(client, flask_url: str, out_rel_path: str, is_html: bool = True):
        resp = client.get(flask_url)
        if resp.status_code != 200:
            print(f"WARN: {flask_url} returned {resp.status_code}")
            return
        target = OUT_DIR / out_rel_path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        if is_html:
            text = resp.data.decode("utf-8")
            text = rewrite_html(text)
            target.write_text(text, encoding="utf-8")
        else:
            target.write_bytes(resp.data)

    with app.test_client() as client:
        # Main pages
        save_route(client, "/", "index.html")
        save_route(client, "/plante-az", "plante-az/index.html")
        save_route(client, "/articole", "articole/index.html")
        save_route(client, "/produse", "produse/index.html")
        save_route(client, "/calendar", "calendar/index.html")
        save_route(client, "/despre-noi", "despre-noi/index.html")
        save_route(client, "/termeni-si-conditii", "termeni-si-conditii/index.html")
        save_route(client, "/politica-de-confidentialitate", "politica-de-confidentialitate/index.html")
        save_route(client, "/politica-cookies", "politica-cookies/index.html")
        save_route(client, "/robots.txt", "robots.txt", is_html=False)
        save_route(client, "/sitemap.xml", "sitemap.xml", is_html=False)
        save_route(client, "/llms.txt", "llms.txt", is_html=False)

        # Also write static robots.txt, sitemap.xml, and llms.txt to repo root with production domain
        prod_domain = "https://www.planteonline.ro"
        root_robots = client.get("/robots.txt").data.decode("utf-8").replace("http://localhost", prod_domain)
        Path("robots.txt").write_text(root_robots, encoding="utf-8")
        root_sitemap = client.get("/sitemap.xml").data.decode("utf-8").replace("http://localhost", prod_domain)
        Path("sitemap.xml").write_text(root_sitemap, encoding="utf-8")
        root_llms = client.get("/llms.txt").data.decode("utf-8").replace("http://localhost", prod_domain)
        Path("llms.txt").write_text(root_llms, encoding="utf-8")

        # Product category pages
        for c in PRODUCT_MENU_CATEGORIES:
            slug = c["slug"]
            save_route(client, f"/produse/categorie/{slug}", f"produse/categorie/{slug}/index.html")
        save_route(client, "/produse", "produse/categorie/toate/index.html")

        # Calendar month pages
        for m in range(1, 13):
            save_route(client, f"/?luna={m}", f"luna/{m}/index.html")
            save_route(client, f"/calendar?luna={m}", f"calendar/luna/{m}/index.html")

        # Article category pages
        for acat in article_categories:
            aslug = slugify(acat)
            save_route(client, f"/articole?categorie={urllib.parse.quote(acat)}", f"articole/categorie/{aslug}/index.html")

        # Plant A-Z letter and category pages
        for l in letters:
            save_route(client, f"/plante-az/litera/{l}", f"plante-az/litera/{l}/index.html")
        for pc in PLANT_CATEGORIES_META:
            pslug = pc["slug"]
            save_route(client, f"/plante-az/categorie/{pslug}", f"plante-az/categorie/{pslug}/index.html")

        # Individual Plant pages (468)
        for p in plants:
            pid = p["id"]
            save_route(client, f"/planta/{pid}", f"planta/{pid}/index.html")

        # Individual Article pages (166)
        for a in articles:
            aid = a["id"]
            save_route(client, f"/articol/{aid}", f"articol/{aid}/index.html")

        # Individual Product pages (32) + API JSON for modal
        for pr in products:
            pr_id = pr["id"]
            save_route(client, f"/produs/{pr_id}", f"produs/{pr_id}/index.html")
            resp = client.get(f"/api/product/{pr_id}")
            if resp.status_code == 200:
                pdata = json.loads(resp.data.decode("utf-8"))
                if pdata.get("image_url") and pdata["image_url"].startswith("/"):
                    pdata["image_url"] = BASE_PREFIX + pdata["image_url"]
                api_target = OUT_DIR / "api" / "product" / str(pr_id) / "index.html"
                api_target.parent.mkdir(parents=True, exist_ok=True)
                api_target.write_text(json.dumps(pdata, ensure_ascii=False), encoding="utf-8")

    # Save plants search JSON for client-side search & pagination on /plante-az
    search_data_dir = OUT_DIR / "data"
    search_data_dir.mkdir(parents=True, exist_ok=True)
    compact_plants = []
    for p in plants:
        raw_desc = (p.get("description") or p.get("requirements") or "Specie botanică decorativă.").strip()
        short_desc = (raw_desc[:115] + "...") if len(raw_desc) > 118 else raw_desc
        img_url = p.get("images", [""])[0] if p.get("images") else ""
        if img_url.startswith("/"):
            img_url = BASE_PREFIX + img_url
        compact_plants.append({
            "id": p["id"],
            "name": p.get("name", ""),
            "latin_name": p.get("latin_name", ""),
            "category": p.get("category", ""),
            "origin": p.get("origin", ""),
            "letter": p.get("letter", "A"),
            "image": img_url,
            "description": short_desc,
        })
    (search_data_dir / "plants_search.json").write_text(
        json.dumps(compact_plants, ensure_ascii=False), encoding="utf-8"
    )

    # Copy static/ folder
    shutil.copytree("static", OUT_DIR / "static", dirs_exist_ok=True)

    # Patch _gh_pages/static/js/app.js so BASE_PREFIX is respected for dynamic images/fetches
    js_path = OUT_DIR / "static" / "js" / "app.js"
    if js_path.exists():
        js_code = js_path.read_text(encoding="utf-8")
        js_code = js_code.replace(
            "fetch(`/api/product/${prodId}`)",
            "fetch(`${window.PLANTEONLINE_BASE_PREFIX || ''}/api/product/${prodId}/`)",
        )
        js_code = js_code.replace(
            "detailLinkEl.href = `/produs/${prod.id}`;",
            "detailLinkEl.href = `${window.PLANTEONLINE_BASE_PREFIX || ''}/produs/${prod.id}/`;",
        )
        js_code = js_code.replace(
            "href=\"/planta/${p.id}\"",
            "href=\"${window.PLANTEONLINE_BASE_PREFIX || ''}/planta/${p.id}/\"",
        )
        js_code = js_code.replace(
            "src=\"${imgSrc}\"",
            "src=\"${(imgSrc && imgSrc.startsWith('/') && window.PLANTEONLINE_BASE_PREFIX) ? (window.PLANTEONLINE_BASE_PREFIX + imgSrc) : imgSrc}\"",
        )
        js_path.write_text(js_code, encoding="utf-8")

    # Copy showcase images served by /showcase_img/<filename>
    showcase_src = Path("import_produse/termek_bemutato")
    if showcase_src.exists():
        showcase_dst = OUT_DIR / "showcase_img"
        showcase_dst.mkdir(parents=True, exist_ok=True)
        for item in showcase_src.iterdir():
            if item.is_file():
                shutil.copy2(item, showcase_dst / item.name)

    total_files = sum(1 for _ in OUT_DIR.rglob("*") if _.is_file())
    print(f"Static GitHub Pages build complete in {OUT_DIR}: {total_files} files generated.")


if __name__ == "__main__":
    build_static_site()
