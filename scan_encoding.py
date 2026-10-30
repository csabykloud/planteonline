import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

print(f"Total articles: {len(articles)}")

bad_chars = [chr(i) for i in range(32) if i not in (9, 10, 13)] + ['\ufffd']

corrupted = []
for a in articles:
    t = a.get('title', '')
    c = a.get('content', '')
    s = a.get('summary', '')
    
    has_bad = any(bc in t or bc in s or bc in c for bc in bad_chars)
    if has_bad or 'V remea' in t or 'Ă' in t:
        corrupted.append(a)

print(f"Articles with encoding issues: {len(corrupted)}")
for a in corrupted[:15]:
    print(f"ID {a['id']}: {repr(a['title'])}")
