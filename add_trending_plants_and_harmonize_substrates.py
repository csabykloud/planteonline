import os
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PLANTS_JSON = os.path.join(DATA_DIR, 'plants.json')
PRODUCTS_JSON = os.path.join(DATA_DIR, 'products.json')

from recommendation_engine import recommend_products_for_plant

# 8 New Trending European & Romanian Plants
NEW_PLANTS = [
    {
        "id": 659,
        "name": "Zamioculcas, Planta ZZ, Planta smarald",
        "latin_name": "Zamioculcas zamiifolia",
        "category": "Plante de apartament",
        "origin": "Africa de Est (Kenya, Zanzibar, Tanzania, Africa de Sud)",
        "flowers": "Flori discrete sub formă de spadice mic alb-gălbui la baza plantei, rare în mediul de interior.",
        "leaves": "Frunze compuse penate, cărnoase, de un verde smarald intens, cu un luciu ceros natural spectaculos; stochează eficient rezerve de apă.",
        "shape": "Tufă erectă, sculpturală și elegantă, cu tije arcuite viguroase ce pornesc din tuberculi suculenți subterani.",
        "care_guide": {
            "lumina": "Foarte adaptabilă: preferă lumină medie indirectă, dar tolerează excelent spațiile mai umbroase; a se feri de soarele direct arzător.",
            "temperatura": "Optimă între 18°C și 26°C; nu tolerează temperaturi scăzute sub 15°C și curenții reci de aer.",
            "udare": "Udare redusă: se lasă substratul să se usuce complet între două udări; rezistă remarcabil la secetă datorită tuberculilor radiculari.",
            "sol": "Substrat fertil, foarte bine aerisit și drenat. Se recomandă utilizarea substratului specializat Nutrisol plante de camera (Nutrisol) amestecat cu puțin perlit.",
            "fertilizare": "Fertilizare lunară din primăvară până la începutul toamnei cu Vitaflora Solutie Nutritiva pt Plante decorative cu frunze."
        },
        "description": "Zamioculcas zamiifolia, denumită popular Planta ZZ sau Floarea de Smarald, este una dintre cele mai căutate și apreciate plante de apartament din România și întreaga Europă datorită esteticii sale arhitecturale moderne și robusteții desăvârșite. Originară din habitatele aride ale Africii de Est, planta este un veritabil 'supraviețuitor' urban, ideală atât pentru birouri moderne, cât și pentru locuințe contemporane. Tijele sale robuste susțin foliole suculente, lucioase, care reflectă lumina și aduc o notă luxuriantă oricărui decor interior, necesitând o îngrijire minimă chiar și pentru începători.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cf/Zamioculcas_zamiifolia_1.jpg/960px-Zamioculcas_zamiifolia_1.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/de/Raven_ZZ_Zamioculcas_Dowon.jpg/960px-Raven_ZZ_Zamioculcas_Dowon.jpg",
            "https://images.unsplash.com/photo-1632207691143-643e2a9a9361?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 660,
        "name": "Monstera Monkey Mask, Monstera perforată",
        "latin_name": "Monstera adansonii",
        "category": "Plante de apartament",
        "origin": "Pădurile tropicale din America Centrală și de Sud",
        "flowers": "Spadice alb-verzui tipic araceelor, rar apărut în condiții de apartament.",
        "leaves": "Frunze de un verde intens, cordate sau eliptice, prezentând perforații naturale spectaculoase (ferestre) pe toată suprafața limbului foliar.",
        "shape": "Plantă agățătoare sau curgătoare cu lăstari flexibili viguroși, ideală pentru ghivece suspendate sau ghidată pe tutori de mușchi.",
        "care_guide": {
            "lumina": "Lumină puternică, dar strict indirectă sau filtrată; soarele direct poate arde textura delicată a frunzelor perforate.",
            "temperatura": "Temperatură caldă constantă de 18–25°C; se evită curenții de aer rece și temperaturile sub 16°C.",
            "udare": "Udare moderată atunci când primii 2–3 cm de la suprafața substratului s-au uscat; apreciază pulverizarea regulată a frunzișului.",
            "sol": "Substrat bogat în humus, afânat și aerat. Se recomandă substratul Nutrisol plante de camera (Nutrisol) îmbogățit cu scoarță de pin și perlit.",
            "fertilizare": "Fertilizare la fiecare 2 săptămâni în perioada de vegetație activă cu Vitaflora Solutie Nutritiva pt Plante decorative cu frunze."
        },
        "description": "Monstera adansonii, cunoscută pretutindeni sub numele de Monstera 'Monkey Mask', este una dintre vedetele absolute ale curentului 'urban jungle' în România și Europa. Diferențiindu-se de ruda sa mai mare Monstera deliciosa prin frunzele compacte cu găuri închise ce nu ating marginea limbului, această liană tropicală impresionează prin ritmul rapid de creștere și versatilitate. Poate fi etalată în cascade spectaculoase pe etajere înalte sau palisată pe tutori naturali, aducând o veritabilă oază tropicală în orice cameră.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0c/Monstera_friedrichsthalii2.jpg/960px-Monstera_friedrichsthalii2.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f1/Monstera_friedrichsthalii1.jpg/960px-Monstera_friedrichsthalii1.jpg",
            "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 661,
        "name": "Petunie de grădină și balcon",
        "latin_name": "Petunia hybrida",
        "category": "Plante de balcon si terase",
        "origin": "America de Sud (hibrizi selecționați)",
        "flowers": "Flori infundibuliforme mari, extrem de numeroase, într-o paletă cromatică bogată (alb, roz, roșu, violet, bicolore, catifelate); înflorire continuă din mai până toamna târziu.",
        "leaves": "Frunze ovate, moi, ușor pubescente și lipicioase la atingere, de culoare verde crud.",
        "shape": "Tufă bogată, semidistinsă sau ușor pendulă, ramificată viguros de la bază.",
        "care_guide": {
            "lumina": "Iubitoare de soare plin; necesită minim 6 ore de soare direct zilnic pentru o înflorire bogată.",
            "temperatura": "Rezistentă la căldura verii; sensibilă la îngheț (se cultivă ca plantă anuală în climat temperat).",
            "udare": "Udare zilnică în zilele caniculare de vară, fără a uda direct florile delicate; solul se menține reavăn.",
            "sol": "Substrat fertil, bogat în materie organică și permeabil. Se recomandă Nutrisol Substrat Muscate (Nutrisol) pentru o înflorire exuberantă.",
            "fertilizare": "Fertilizare săptămânală cu Nutrisol Solutie Nutritiva pt Muscate si plante de balcon sau Florasol Soluție Nutritivă."
        },
        "description": "Petunia hybrida reprezintă una dintre cele mai populare și căutate flori de balcon și grădină din România și Europa. Cu o capacitate uimitoare de a produce flori spectaculoase pe tot parcursul verii, petuniile transformă jardinierele, ghivecele și bordurile florale într-un covor viu colorat. Îndepărtarea regulată a florilor ofilite stimulează formarea neîntreruptă a noilor boboci florali până la primele brume de toamnă.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4b/Petunia_hybrida.jpg/960px-Petunia_hybrida.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cf/Petunia_violacea.jpg/960px-Petunia_violacea.jpg",
            "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 662,
        "name": "Surfinia, Petunie curgătoare de balcon",
        "latin_name": "Petunia x hybrida 'Surfinia'",
        "category": "Plante de balcon si terase",
        "origin": "Hibrid creat în Japonia, consacrat pe scară largă în Europa",
        "flowers": "Cascade dense de flori în formă de trompetă, auto-curățătoare, în nuanțe strălucitoare de la roz, violet intens, alb pur până la purpuriu catifelat.",
        "leaves": "Frunziș verde intens, compact, ușor pubescent, rezistent la vânt moderat.",
        "shape": "Port pendul spectaculos, lăstari lungi ce pot atinge 80–120 cm formând veritabile perdele florale curgătoare.",
        "care_guide": {
            "lumina": "Plin soare sau lumină foarte puternică; are nevoie de multă energie solară pentru susținerea masei florale abundente.",
            "temperatura": "Tolerează foarte bine căldura estivală intensă; se adăpostește de vânturile puternice și grindină.",
            "udare": "Udare generoasă și frecventă în sezonul cald; substratul trebuie să fie reavăn, cu un drenaj excelent la fundul ghiveciului.",
            "sol": "Substrat dedicat plantelor de balcon cu consum mare de nutrienți. Se recomandă cu încredere Nutrisol Substrat Muscate (Nutrisol).",
            "fertilizare": "Fertilizare constantă de 1–2 ori pe săptămână cu Vitaflora Solutie Nutritiva Plante Curgatoare (cu conținut ridicat de fier Fe împotriva clorozei)."
        },
        "description": "Surfinia este campioana de necontestat a balcoanelor și teraselor suspendate din Europa. Spre deosebire de petuniile clasice, Surfinia dezvoltă lăstari curgători extrem de lungi și robuști, care produc o abundență copleșitoare de flori rezistente la intemperii. Aportul suplimentar de fier din fertilizatorii dedicați menține frunzișul de un verde crud și intens chiar și în lunile caniculare de iulie și august.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cd/Surfinia_violet.jpg/960px-Surfinia_violet.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b5/Surfinia_flowering.jpg/960px-Surfinia_flowering.jpg",
            "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 663,
        "name": "Dipladenia, Mandevilla, Iasomia braziliană",
        "latin_name": "Mandevilla sanderi (Dipladenia)",
        "category": "Plante de balcon si terase",
        "origin": "Regiunile tropicale din America de Sud (Brazilia)",
        "flowers": "Flori mari, elegante în formă de pâlnie, lucioase, în culori de la roșu aprins, ciclamen, roz pastel până la alb catifelat; înflorește neîntrerupt din mai până în noiembrie.",
        "leaves": "Frunze sempervirescente, ovale, groase, coriacee, de un verde smarald întunecat foarte lucios.",
        "shape": "Subarbust cățărător sau semipendul, cu lăstari viguroși ce pot fi palisați pe spaliere, arcade sau ghivece decorative de terasă.",
        "care_guide": {
            "lumina": "Locații foarte luminoase și călduroase; iubește soarele direct de dimineață și lumină filtrată la orele amiezii.",
            "temperatura": "Iubitoare de căldură (20–30°C); toamna târziu se retrage la interior într-un spațiu luminos și răcoros (10–14°C) pentru iernare.",
            "udare": "Udare moderată; rădăcinile tuberculoase stochează apă, astfel încât se preferă lăsarea stratului superior al solului să se usuce între udări.",
            "sol": "Substrat ușor, permeabil și fertil. Se recomandă Nutrisol Substrat Muscate (Nutrisol) sau Florasol Amestec turba Universal.",
            "fertilizare": "Fertilizare la fiecare 10–14 zile în perioada de creștere cu Vitaflora Solutie Nutritiva pt Plante decorative cu Flori."
        },
        "description": "Dipladenia (Mandevilla) este una dintre cele mai spectaculoase și rezistente plante floricole mediteraneene/tropicale apreciate în România și Europa pentru terase, curți și balcoane. Frunzișul său mereu verde și lucios completează armonios florile abundente cu textură catifelată, care nu se scutură ușor la ploaie sau vânt. Este planta ideală pentru un decor exterior de inspirație sud-europeană de lungă durată.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d4/Mandevilla_sanderi_02.jpg/960px-Mandevilla_sanderi_02.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c2/Mandevilla_sanderi_01.jpg/960px-Mandevilla_sanderi_01.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5e/Mandevilla_sanderi_flower.jpg/960px-Mandevilla_sanderi_flower.jpg"
        ]
    },
    {
        "id": 664,
        "name": "Măslin european decorativ",
        "latin_name": "Olea europaea",
        "category": "Arbori si arbusti ornamentali",
        "origin": "Bazinul Mediteranean",
        "flowers": "Flori mici, albe-crem, parfumate discret, grupate în raceme axilare primăvara.",
        "leaves": "Frunze persistente, lanceolate, argintii-cenușii pe dos și verde-măsliniu pe față, coriacee și rezistente la secetă.",
        "shape": "Arbore sau arbust mic cu coroană densă, trunchi sculptural sinuos și port nobil atemporal.",
        "care_guide": {
            "lumina": "Plin soare; necesită maximul de lumină solară posibil pe terasă, în curte sau lângă ferestre orientate spre sud.",
            "temperatura": "Rezistent la căldură toridă și secetă; iarna se protejează în încăperi răcoroase (5–10°C) ferite de înghețuri prelungite sub -5°C.",
            "udare": "Udare rară și profundă; se evită cu strictețe excesul de apă și stagnarea umidității la rădăcini.",
            "sol": "Substrat bine drenat, poros, calcaros sau nisipos. Se recomandă Nutrisol Straturi Inaltate (Nutrisol) combinat cu pietriș fin și perlit.",
            "fertilizare": "Fertilizare moderată lunară primăvara și vara cu Humiflor Solutie nutritiva plante de gradina sau Nutrisol."
        },
        "description": "Măslinul decorativ (Olea europaea) este simbolul prin excelență al longevității, păcii și rafinamentului mediteranean, devenind un element vedetă în designul teraselor și grădinilor din România și Europa. Cultivat în containere decorative mari de ceramică sau teracotă, măslinul oferă o prezență sculpturală impresionantă prin nuanțele sale argintii și trunchiul cu aspect nobil. Rezistența sa remarcabilă la secetă și căldură îl face perfect adaptat verilor toride contemporane.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/41/Olive_Trees_in_Greece.jpg/960px-Olive_Trees_in_Greece.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/69/Olea_europaea_leaves.jpg/960px-Olea_europaea_leaves.jpg",
            "https://images.unsplash.com/photo-1545241047-6083a3684587?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 665,
        "name": "Filodendron Pink Princess, Philodendron roz",
        "latin_name": "Philodendron erubescens 'Pink Princess'",
        "category": "Plante de apartament",
        "origin": "America de Sud (cultivar selecționat de colecție)",
        "flowers": "Inflorescențe rare în cultură de interior, protejate de spată maronie-purpurie.",
        "leaves": "Frunze spectaculoase cordate, de culoare verde-închis spre negru-bordeaux, decorate cu pete, marmorări și sectoare extinse de un roz aprins vibrant unic.",
        "shape": "Plantă semicățărătoare erectă, cu tije robuste de culoare vișinie, ideală pentru susținere pe tutori de cocos sau mușchi.",
        "care_guide": {
            "lumina": "Lumină indirectă puternică; lumina adecvată este esențială pentru menținerea și intensificarea variegării roz aprins a frunzelor.",
            "temperatura": "Mediu cald și constant între 18°C și 26°C, protejat de curenți de aer rece.",
            "udare": "Udare când primii centimetri ai substratului sunt uscați; necesită drenaj impecabil pentru a preveni putrezirea rădăcinilor epifite.",
            "sol": "Substrat de tip Aroid mix, poros și foarte aerisit. Se recomandă Nutrisol plante de camera (Nutrisol) combinat cu scoarță de pin și perlit.",
            "fertilizare": "Fertilizare bilunară din martie până în septembrie cu Vitaflora Solutie Nutritiva pt Plante decorative cu frunze diluată conform instrucțiunilor."
        },
        "description": "Philodendron 'Pink Princess' este considerat bijuteria colecționarilor de plante de interior din Europa și România, devenind un fenomen global datorită contrastului vizual electrizant dintre frunzișul de culoarea ciocolatei negre și stropii generoși de roz bombon. Fiecare frunză nouă care se desface este o surpriză unică de model și culoare. Este o plantă nobilă, spectaculoasă, care conferă o personalitate de neegalat oricărui spațiu de locuit modern.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/6f/Philodendron_erubescens_Pink_Princess.jpg/960px-Philodendron_erubescens_Pink_Princess.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a2/Philodendron_erubescens_leaves.jpg/960px-Philodendron_erubescens_leaves.jpg",
            "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?auto=format&fit=crop&w=960&q=80"
        ]
    },
    {
        "id": 666,
        "name": "Calibrachoa, Milioane de Clopoței, Million Bells",
        "latin_name": "Calibrachoa parviflora (Million Bells)",
        "category": "Plante de balcon si terase",
        "origin": "America de Sud",
        "flowers": "Sute de clopoței miniaturali asemănători petuniilor, extrem de denși, în culori vibrante (galben intens, portocaliu, roșu carmin, mov, roz aprins); înflorire neobosită până la îngheț.",
        "leaves": "Frunze mici, înguste, lanceolate, de un verde proaspăt, rezistente la vânt și ploaie.",
        "shape": "Globulară, semipendulă și compactă, acoperind integral vasul de cultură sub formă de cascadă de flori.",
        "care_guide": {
            "lumina": "Iubitoare pasionată de soare; preferă soare direct 6–8 ore pe zi pentru o explozie florală continuă.",
            "temperatura": "Rezistență excelentă la temperaturi ridicate; tolerează mai bine intemperiile de vară decât petuniile clasice.",
            "udare": "Udare regulată moderată; solul trebuie să rămână reavăn, evitând acumularea de apă la fundul ghiveciului.",
            "sol": "Substrat afânat, ușor acid și foarte bine drenat. Se recomandă Nutrisol Substrat Muscate (Nutrisol) pentru o înflorire continuă.",
            "fertilizare": "Fertilizare săptămânală cu Vitaflora Solutie Nutritiva Plante Curgatoare sau Nutrisol Solutie Nutritiva pt Muscate si balcon."
        },
        "description": "Calibrachoa, cunoscută și sub denumirea comercială de 'Million Bells' (Milioane de Clopoței), este una dintre cele mai populare și căutate alegeri floricole pentru ghivece suspendate și jardiniere din întreaga Europă. Producând literalmente sute de flori miniaturale care nu necesită curățare manuală (fiind auto-curățătoare), Calibrachoa creează adevărate globuri florale de o intensitate cromatică uluitoare de la începutul primăverii până toamna târziu.",
        "images": [
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a2/Calibrachoa_parviflora.jpg/960px-Calibrachoa_parviflora.jpg",
            "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d3/Calibrachoa_yellow_bells.jpg/960px-Calibrachoa_yellow_bells.jpg",
            "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?auto=format&fit=crop&w=960&q=80"
        ]
    }
]

def harmonize_care_guide(plant, products):
    rec = recommend_products_for_plant(plant, products)
    sub = rec['primary_substrate']
    fert = rec['primary_fertilizer']

    plant['recommended_products'] = rec['recommended_product_ids']

    cg = plant.setdefault('care_guide', {})
    existing_sol = cg.get('sol', '')

    # Determine base soil physical characteristics
    norm = (plant.get('name', '') + ' ' + plant.get('latin_name', '') + ' ' + plant.get('category', '')).lower()

    if any(k in norm for k in ['orhide', 'orchid', 'cymbidium', 'phalaenopsis']):
        base_sol = "Substrat afânat, aerat și foarte permeabil pe bază de scoarță de pin."
        recom_text = f"Se recomandă utilizarea substratului specializat {sub['name']} ({sub['brand']}) pentru aerisirea rădăcinilor și prevenirea mucegaiului."
    elif any(k in norm for k in ['muscat', 'pelargoni', 'balcon', 'petuni', 'surfinia', 'calibrachoa']):
        base_sol = "Substrat fertil, bogat în humus și permeabil."
        recom_text = f"Se recomandă utilizarea substratului dedicat {sub['name']} ({sub['brand']}) pentru o structură afânată și o înflorire spectaculoasă."
    elif any(k in norm for k in ['cactus', 'cactee', 'suculent', 'aloe', 'agave', 'crassula']):
        base_sol = "Substrat poros, nisipos și extrem de bine drenat."
        recom_text = f"Se recomandă utilizarea {sub['name']} ({sub['brand']}) combinat cu perlit și nisip fin pentru prevenirea excesului de umiditate."
    elif any(k in norm for k in ['apartament', 'camera', 'interior', 'ficus', 'monstera', 'palmier', 'zamioculcas', 'philodendron', 'calathea', 'spathiphyllum', 'anthurium']):
        base_sol = "Substrat fertil, aerat și bogat în nutrienți esențiali."
        recom_text = f"Se recomandă utilizarea substratului {sub['name']} ({sub['brand']}) pentru o creștere armonioasă și un frunziș viguros."
    elif any(k in norm for k in ['gradina', 'strat', 'arbust', 'trandafir', 'copac', 'conifer', 'legum']):
        base_sol = "Sol de grădină afânat, fertil și bine drenat."
        recom_text = f"Se recomandă utilizarea substratului {sub['name']} ({sub['brand']}) pentru îmbunătățirea calității solului și retenția apei."
    else:
        # Check if existing_sol has a good physical description before 'Se recomandă'
        if existing_sol and 'Se recomandă' in existing_sol:
            base_sol = existing_sol.split('Se recomandă')[0].strip()
        elif existing_sol and 'Recomandat' in existing_sol:
            base_sol = existing_sol.split('Recomandat')[0].strip()
        elif existing_sol:
            base_sol = existing_sol
        else:
            base_sol = "Sol bine structurat, fertil și permeabil."
        recom_text = f"Se recomandă utilizarea substratului de calitate {sub['name']} ({sub['brand']}) pentru o structură optimă a solului și o dezvoltare radiculară sănătoasă."

    cg['sol'] = f"{base_sol} {recom_text}"

    # Harmonize fertilizare
    existing_fert = cg.get('fertilizare', '')
    if 'Soluții Nutritive Florasol' in existing_fert or 'Florasol' in existing_fert:
        cg['fertilizare'] = f"Fertilizare periodică în perioada de vegetație cu {fert['name']} ({fert['brand']}) pentru o nutriție optimă; toamna târziu și iarna fertilizarea se reduce sau se suspendă."
    elif not existing_fert:
        cg['fertilizare'] = f"Fertilizare regulată în sezonul de creștere cu {fert['name']} ({fert['brand']}) conform instrucțiunilor de dozare."

    return plant

def main():
    with open(PLANTS_JSON, 'r', encoding='utf-8') as f:
        plants = json.load(f)
    with open(PRODUCTS_JSON, 'r', encoding='utf-8') as f:
        products = json.load(f)

    existing_ids = {p['id'] for p in plants}
    existing_latin = {(p.get('latin_name') or '').lower() for p in plants}

    # Add new plants if not existing
    added_count = 0
    for np in NEW_PLANTS:
        if np['id'] not in existing_ids and np['latin_name'].lower() not in existing_latin:
            np['image_url'] = np['images'][0]
            harmonize_care_guide(np, products)
            plants.append(np)
            added_count += 1
            existing_ids.add(np['id'])
            existing_latin.add(np['latin_name'].lower())

    print(f"Added {added_count} new trending plants to catalog!")

    # Harmonize care_guide.sol, recommended products, and deduplicate images for ALL plants
    print("Harmonizing care_guide.sol, recommended products and deduplicating images...")
    for p in plants:
        harmonize_care_guide(p, products)

        # Clean & deduplicate images by stripping URL query parameters
        raw_images = p.get('images', [])
        seen_bases = set()
        deduped = []
        for img in raw_images:
            base = img.split('?')[0].lower()
            if base not in seen_bases:
                seen_bases.add(base)
                deduped.append(img)
        p['images'] = deduped[:3] if deduped else raw_images[:3]
        if p['images']:
            p['image_url'] = p['images'][0]

    with open(PLANTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=2, ensure_ascii=False)

    print(f"Successfully updated and harmonized {len(plants)} plants in plants.json!")

if __name__ == '__main__':
    main()
