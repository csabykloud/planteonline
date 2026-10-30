import os
import json
import shutil

os.makedirs('data', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/img', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Copy cleaned articles
with open('cleaned_articles.json', encoding='utf-8') as f:
    articles = json.load(f)
with open('data/articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

# Copy full plants database
with open('full_plants_database.json', encoding='utf-8') as f:
    plants = json.load(f)
with open('data/plants.json', 'w', encoding='utf-8') as f:
    json.dump(plants, f, indent=2, ensure_ascii=False)

# Copy products
with open('all_detailed_products.json', encoding='utf-8') as f:
    products = json.load(f)
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

# Copy calendar
with open('calendar_months.json', encoding='utf-8') as f:
    calendar = json.load(f)
with open('data/calendar.json', 'w', encoding='utf-8') as f:
    json.dump(calendar, f, indent=2, ensure_ascii=False)

# Create about.json
about_data = {
    "title": "Despre Noi - Portal Plante Online",
    "subtitle": "Pasiune pentru natură, grădinărit și îngrijirea plantelor încă din 2001",
    "company_name": "Societatea Mont Rose S.R.L.",
    "founded_year": 2001,
    "quality_standards": "Standarde Europene de Calitate",
    "description": "Societatea Mont Rose a fost înființată în anul 2001 cu scopul de a oferi pasionaților de plante și nu numai, soluțiile, precum și produsele necesare pentru întreținerea acestora.\n\nSocietatea noastră este producător și deținător al mărcii Florasol pentru pământ de flori și fertilizanți, respectiv distribuitor oficial al gamei de produse Humiflor, Nutrisol, Plantasol, Vitaflora și Florimo. Toate aceste produse sunt fabricate în Uniunea Europeană în concordanță cu cel mai exigent tip de calitate, cele mai exigente standarde europene de calitate.\n\nDatorită faptului că nu numai produsele de întreținere dar și cunoștințele necesare și materialul educațional lipsea de pe piață, ne-am hotărât să punem bazele unei culturi florale moderne, fundamentată pe cunoștințe tehnice și botanice solide.\n\nCa urmare, am realizat acest portal dedicat plantelor unde oricine să aibă acces facil și să poată obține informațiile de specialitate de care are nevoie. Website-ul conține o serie extinsă de informații utile legate de plante și de produsele profesionale de întreținere.",
    "mission": "Misiunea noastră este de a oferi comunității de iubitori de flori și grădinari din România informații botanice verificate, ghiduri practice sezoniere și cele mai eficiente produse pentru dezvoltarea armonioasă a plantelor de interior și exterior.",
    "values": [
        {"title": "Calitate Certificată", "desc": "Produse fabricate conform standardelor europene cele mai exigente standarde europene."},
        {"title": "Educație & Consiliere", "desc": "Articole, calendare sezoniere și sfaturi de specialitate pentru fiecare pasionat."},
        {"title": "Pasiune pentru Natură", "desc": "Peste două decenii de experiență dedicată frumuseții plantelor și spațiilor verzi."}
    ],
    "contact_email": "contact@planteonline.ro",
    "contact_phone": "+40 21 000 0000",
    "address": "București & Livrare în toată România"
}

with open('data/about.json', 'w', encoding='utf-8') as f:
    json.dump(about_data, f, indent=2, ensure_ascii=False)

print("Initialized data directory with articles, plants, products, calendar, and about!")
