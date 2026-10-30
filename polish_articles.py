import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

for a in articles:
    # 1. Clean HTML junk and calendar append from content
    content = a.get('content', '')
    if 'Octombrie Octombrie Plante de Exterior' in content:
        content = content.split('Octombrie Octombrie Plante de Exterior')[0].strip()
    if 'Unelte Sapa, grebla' in content:
        content = content.split('Unelte Sapa, grebla')[0].strip()

    # 2. Fix specific title issues
    t = a.get('title', '').strip()
    
    # Remove leading/trailing quotes and strange characters
    t = t.replace('', '"').replace('dĂŠcor', 'decor').replace('atrăgăatoare', 'atrăgătoare')
    
    # Specific known titles that were mangled
    if a['id'] == 41:
        t = "Vremea urâtă și umiditatea ridicată: cum protejăm plantele din grădină și ghiveci"
    elif a['id'] == 42:
        t = "În timpul îngrijirii plantelor de apartament: cauzele îngălbenirii și ofilirii frunzelor"
    elif a['id'] == 43:
        t = "Drenajul optim al ghivecelor: importanța orificiilor de scurgere pentru sănătatea rădăcinilor"
    elif a['id'] == 44:
        t = "Habitatul natural al plantelor: cum reproducem spațiul optim de dezvoltare în apartament"
    elif a['id'] == 52:
        t = "Viața plantei și necesarul de apă în țesuturile vegetale"
    elif a['id'] == 120:
        t = "Semințe - dăruitori de viață: ghid complet pentru înmulțirea și semănarea florilor"
    elif a['id'] == 130:
        t = "Jardiniere și plante suspendate: amenajări spectaculoase pentru balcoane și terase"

    # If title is excessively long (more than 100 chars and contains sentence fragments), shorten cleanly
    if len(t) > 110 and '.' in t[:100]:
        t = t[:t.index('.')].strip()

    a['title'] = t
    a['content'] = content

    # Refresh summary
    summary = a.get('summary', '')
    if 'Octombrie Octombrie' in summary or 'citeste mai mult' in summary:
        summary = content[:220].strip() + '...'
    a['summary'] = summary

with open('data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print(f"Polished {len(articles)} articles!")
