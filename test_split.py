import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

for a in articles:
    t = a['title']
    if re.search(r'\b[Vv]\s+[a-zA-Z]', t):
        print(f"ID {a['id']}: {repr(t)}")
