import json

with open('data/articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

for a in articles:
    for k in ['title', 'summary', 'content']:
        if k in a and isinstance(a[k], str):
            a[k] = a[k].replace('\ufffd', '"').replace('', '"')

with open('data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print("Articles scrubbed of all replacement chars!")
