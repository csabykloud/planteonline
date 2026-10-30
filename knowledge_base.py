import os
import re
import json
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'catalog.db')
PLANTS_JSON = os.path.join(DATA_DIR, 'plants.json')
ARTICLES_JSON = os.path.join(DATA_DIR, 'articles.json')
PRODUCTS_JSON = os.path.join(DATA_DIR, 'products.json')

def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Articles table
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            category TEXT,
            date TEXT,
            views INTEGER,
            summary TEXT,
            content TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            brand TEXT,
            code TEXT,
            description TEXT,
            image_url TEXT,
            images TEXT,
            external_url TEXT
        )
    ''')

    # Plants table
    c.execute('''
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY,
            name TEXT,
            latin_name TEXT,
            category TEXT,
            origin TEXT,
            flowers TEXT,
            leaves TEXT,
            shape TEXT,
            care_guide TEXT,
            description TEXT,
            images TEXT,
            image_url TEXT,
            recommended_products TEXT,
            recommended_articles TEXT
        )
    ''')

    # Plant - Article Links table
    c.execute('''
        CREATE TABLE IF NOT EXISTS plant_article_links (
            plant_id INTEGER,
            article_id INTEGER,
            score INTEGER,
            reason TEXT,
            PRIMARY KEY (plant_id, article_id)
        )
    ''')

    conn.commit()
    conn.close()

def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    for s, d in [('ț', 't'), ('ș', 's'), ('ă', 'a'), ('â', 'a'), ('î', 'i')]:
        t = t.replace(s, d)
    return t

STOP_WORDS = {
    'planta', 'plante', 'decorativa', 'decorative', 'camera', 'apartament', 
    'gradina', 'ghiveci', 'ghivece', 'flori', 'tufa', 'frunze', 'arbust', 
    'arbore', 'arbori', 'arbusti', 'hibrid', 'hibrizi', 'specii', 'specie', 'soiuri',
    'culoare', 'verde', 'ingrijire', 'cultivare', 'dezvoltare', 'crestere',
    'japonez', 'japoneza', 'chinezesc', 'chinezeasca', 'comun', 'comuna',
    'alb', 'alba', 'rosu', 'rosie', 'galben', 'galbena', 'argintiu', 'argintie',
    'pitic', 'pitica', 'mare', 'mica', 'dulce', 'salbatic', 'salbatica',
    'european', 'europeana', 'american', 'americana', 'african', 'africana',
    'australian', 'australiana', 'peruvian', 'indian', 'indiana', 'regal', 'regala',
    'auriu', 'aurie', 'negru', 'neagra', 'albastru', 'albastra', 'ornamental',
    'ornamentala', 'peren', 'perena', 'toamna', 'vara', 'iarna', 'primavara',
    'munte', 'padure', 'balta', 'camp', 'floarea', 'floare', 'arborele'
}

def extract_plant_keywords(plant):
    keywords = set()
    name = normalize_text(plant.get('name', ''))
    # Clean name punctuation
    parts = re.split(r'[,;\(\)\-\/]', name)
    for part in parts:
        part = part.strip()
        words = part.split()
        if len(words) == 1 and len(part) >= 4 and part not in STOP_WORDS:
            keywords.add(part)
        elif len(words) > 1:
            for w in words:
                if len(w) >= 4 and w not in STOP_WORDS:
                    keywords.add(w)

    lat = normalize_text(plant.get('latin_name', ''))
    lat_parts = [w for w in lat.split() if len(w) >= 4 and w not in STOP_WORDS]
    if lat_parts:
        keywords.add(lat_parts[0]) # Genus
        if len(lat_parts) >= 2:
            keywords.add(f"{lat_parts[0]} {lat_parts[1]}") # Genus species

    return [k for k in keywords if len(k) >= 4]

def is_editorial_article(article):
    title = (article.get('title') or '').lower()
    if 'cod: 599' in title or 'gama florimo' in title:
        return False
    return True

def score_article_for_plant(article, plant_keywords):
    if not plant_keywords or not is_editorial_article(article):
        return 0, ''

    title = normalize_text(article.get('title', ''))
    summary = normalize_text(article.get('summary', ''))
    content = normalize_text(article.get('content', ''))

    score = 0
    matched_words = []

    for k in plant_keywords:
        # Regex word boundary match
        pattern = r'\b' + re.escape(k) + r'\b'
        if re.search(pattern, title):
            score += 100
            matched_words.append(f"titlu:{k}")
        elif k in title:
            score += 60
            matched_words.append(f"titlu_parțial:{k}")
        elif re.search(pattern, summary):
            score += 45
            matched_words.append(f"sumar:{k}")
        elif re.search(pattern, content):
            cnt = len(re.findall(pattern, content))
            if cnt >= 3:
                score += 30
                matched_words.append(f"conținut_frecvent:{k}({cnt})")
            elif cnt >= 1 and score > 0:
                score += 10

    return score, ', '.join(matched_words)

def sync_database_from_json():
    init_db()
    conn = get_connection()
    c = conn.cursor()

    # Load JSON files
    with open(ARTICLES_JSON, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
        products = json.load(f)
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    # 1. Sync Articles
    c.execute('DELETE FROM articles')
    for a in articles:
        c.execute('''
            INSERT INTO articles (id, title, category, date, views, summary, content, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            a.get('id'),
            a.get('title'),
            a.get('category'),
            a.get('date'),
            a.get('views', 0),
            a.get('summary'),
            a.get('content'),
            a.get('image_url')
        ))

    # 2. Sync Products
    c.execute('DELETE FROM products')
    for p in products:
        c.execute('''
            INSERT INTO products (id, name, brand, code, description, image_url, images, external_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p.get('id'),
            p.get('name'),
            p.get('brand'),
            p.get('code'),
            p.get('description'),
            p.get('image_url'),
            json.dumps(p.get('images', []), ensure_ascii=False),
            p.get('external_url')
        ))

    # 3. Match Articles to Plants & Update Links
    c.execute('DELETE FROM plant_article_links')
    
    plant_article_map = {}
    for p in plants:
        pid = p['id']
        keys = extract_plant_keywords(p)
        matched = []
        for a in articles:
            score, reason = score_article_for_plant(a, keys)
            if score >= 40: # High confidence that article is about this plant
                matched.append({
                    'score': score,
                    'reason': reason,
                    'article': {
                        'id': a['id'],
                        'title': a.get('title'),
                        'category': a.get('category'),
                        'date': a.get('date'),
                        'image_url': a.get('image_url'),
                        'summary': a.get('summary')
                    }
                })
        
        matched.sort(key=lambda x: -x['score'])
        # Top 3 articles
        top_articles = matched[:3]
        for m in top_articles:
            c.execute('''
                INSERT OR REPLACE INTO plant_article_links (plant_id, article_id, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (pid, m['article']['id'], m['score'], m['reason']))

        # Cache in plant dict
        rec_art_list = [m['article'] for m in top_articles]
        p['recommended_articles'] = rec_art_list
        plant_article_map[pid] = rec_art_list

    # 4. Sync Plants to DB
    c.execute('DELETE FROM plants')
    for p in plants:
        c.execute('''
            INSERT INTO plants (
                id, name, latin_name, category, origin, flowers, leaves, shape,
                care_guide, description, images, image_url, recommended_products, recommended_articles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            p.get('id'),
            p.get('name'),
            p.get('latin_name'),
            p.get('category'),
            p.get('origin'),
            p.get('flowers'),
            p.get('leaves'),
            p.get('shape'),
            json.dumps(p.get('care_guide', {}), ensure_ascii=False),
            p.get('description'),
            json.dumps(p.get('images', []), ensure_ascii=False),
            p.get('image_url'),
            json.dumps(p.get('recommended_products', []), ensure_ascii=False),
            json.dumps(p.get('recommended_articles', []), ensure_ascii=False)
        ))

    conn.commit()
    conn.close()

    # Save updated plants.json with recommended_articles
    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)

    print(f"Catalog DB successfully synchronized! Linked articles for {sum(1 for v in plant_article_map.values() if v)} plants.")

def get_recommended_articles_for_plant(plant):
    pid = plant.get('id') if isinstance(plant, dict) else plant
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT a.id, a.title, a.category, a.date, a.image_url, a.summary
        FROM plant_article_links l
        JOIN articles a ON l.article_id = a.id
        WHERE l.plant_id = ?
        ORDER BY l.score DESC
        LIMIT 3
    ''', (pid,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def on_article_saved(article_data):
    """
    Called when an article is created or updated in admin.
    Updates SQLite DB and re-indexes which plants mention this article.
    """
    init_db()
    conn = get_connection()
    c = conn.cursor()

    aid = article_data['id']
    c.execute('''
        INSERT OR REPLACE INTO articles (id, title, category, date, views, summary, content, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        aid,
        article_data.get('title'),
        article_data.get('category'),
        article_data.get('date'),
        article_data.get('views', 0),
        article_data.get('summary'),
        article_data.get('content'),
        article_data.get('image_url')
    ))

    # Remove old links for this article
    c.execute('DELETE FROM plant_article_links WHERE article_id = ?', (aid,))

    # Load plants and evaluate against this new/updated article
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    updated_plants = False
    for p in plants:
        keys = extract_plant_keywords(p)
        score, reason = score_article_for_plant(article_data, keys)
        if score >= 40:
            c.execute('''
                INSERT OR REPLACE INTO plant_article_links (plant_id, article_id, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (p['id'], aid, score, reason))

    conn.commit()
    conn.close()

    # Refresh cached recommended_articles for plants
    sync_plant_articles_cache()

def on_plant_saved(plant_data):
    """
    Called when a plant is created or updated in admin.
    Matches articles and updates SQLite DB.
    """
    init_db()
    conn = get_connection()
    c = conn.cursor()

    pid = plant_data['id']
    keys = extract_plant_keywords(plant_data)

    c.execute('DELETE FROM plant_article_links WHERE plant_id = ?', (pid,))
    c.execute('SELECT id, title, category, summary, content, date, image_url FROM articles')
    articles = [dict(r) for r in c.fetchall()]

    matched = []
    for a in articles:
        score, reason = score_article_for_plant(a, keys)
        if score >= 40:
            matched.append((score, a['id'], reason, a))

    matched.sort(key=lambda x: -x[0])
    top_matches = matched[:3]

    for score, aid, reason, _ in top_matches:
        c.execute('''
            INSERT OR REPLACE INTO plant_article_links (plant_id, article_id, score, reason)
            VALUES (?, ?, ?, ?)
        ''', (pid, aid, score, reason))

    rec_arts = [{
        'id': a['id'],
        'title': a['title'],
        'category': a['category'],
        'date': a['date'],
        'image_url': a['image_url'],
        'summary': a['summary']
    } for _, _, _, a in top_matches]

    plant_data['recommended_articles'] = rec_arts

    c.execute('''
        INSERT OR REPLACE INTO plants (
            id, name, latin_name, category, origin, flowers, leaves, shape,
            care_guide, description, images, image_url, recommended_products, recommended_articles
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pid,
        plant_data.get('name'),
        plant_data.get('latin_name'),
        plant_data.get('category'),
        plant_data.get('origin'),
        plant_data.get('flowers'),
        plant_data.get('leaves'),
        plant_data.get('shape'),
        json.dumps(plant_data.get('care_guide', {}), ensure_ascii=False),
        plant_data.get('description'),
        json.dumps(plant_data.get('images', []), ensure_ascii=False),
        plant_data.get('image_url'),
        json.dumps(plant_data.get('recommended_products', []), ensure_ascii=False),
        json.dumps(rec_arts, ensure_ascii=False)
    ))

    conn.commit()
    conn.close()

def sync_plant_articles_cache():
    conn = get_connection()
    c = conn.cursor()
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)

    for p in plants:
        pid = p['id']
        c.execute('''
            SELECT a.id, a.title, a.category, a.date, a.image_url, a.summary
            FROM plant_article_links l
            JOIN articles a ON l.article_id = a.id
            WHERE l.plant_id = ?
            ORDER BY l.score DESC
            LIMIT 3
        ''', (pid,))
        p['recommended_articles'] = [dict(r) for r in c.fetchall()]

    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)
    conn.close()

if __name__ == '__main__':
    sync_database_from_json()
