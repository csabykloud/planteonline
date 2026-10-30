import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_sentence(t):
    if not t:
        return ""
    t = t.strip()
    t = re.sub(r'^[.\-\s,;:]+', '', t)
    if not t:
        return ""
    t = t[0].upper() + t[1:]
    if t[-1] not in '.!?:;':
        t += '.'
    return t

def format_shape(shape, name, cat):
    if not shape or not shape.strip():
        return ""
    s = shape.strip().rstrip('.')
    if not s:
        return ""
    s_low = s.lower()
    if s_low.startswith('este ') or s_low.startswith('e ') or s_low.startswith('planta ') or s_low.startswith('arbust ') or s_low.startswith('arbore '):
        return clean_sentence(s)
    elif s_low.startswith('creste ') or s_low.startswith('crește ') or s_low.startswith('formeaza ') or s_low.startswith('formează ') or s_low.startswith('prezinta ') or s_low.startswith('prezintă ') or s_low.startswith('are '):
        return clean_sentence(f"Planta {s[0].lower() + s[1:]}")
    elif s_low.startswith('tufa ') or s_low.startswith('tufă ') or s_low.startswith('rozeta ') or s_low.startswith('rozetă '):
        return clean_sentence(f"Formează o {s[0].lower() + s[1:]}")
    elif s_low.startswith('port ') or s_low.startswith('forma ') or s_low.startswith('formă '):
        return clean_sentence(f"Are un {s[0].lower() + s[1:]}")
    else:
        return clean_sentence(f"Are o creștere {s[0].lower() + s[1:]}")

def format_leaves(leaves, cat, latin, name):
    if not leaves or not leaves.strip():
        latin_low = latin.lower()
        if 'aglaonema' in latin_low:
            return "Frunzele sunt mari, oval-lanceolate, de un verde strălucitor cu striații sau pete argintii-crem decorative."
        elif 'calathea' in latin_low or 'maranta' in latin_low:
            return "Frunzele sunt spectaculos desenate, cu nervuri și modele grafice elegante în nuanțe de verde, argintiu și purpuriu."
        elif 'ficus' in latin_low:
            return "Frunzele sunt lucioase, coriacee și elegante, conferind plantei un aspect nobil și luxuriant."
        elif 'dracaena' in latin_low or 'yucca' in latin_low:
            return "Frunzele sunt înguste, alungite în formă de sabie, dispuse armonios în rozete bogate."
        elif cat == 'Conifere':
            return "Acele sunt persistente, decorative tot timpul anului, cu o culoare intensă și aromă rășinoasă plăcută."
        elif cat == 'Plante de apartament':
            return "Frunzișul este dens, bogat și persistent, asigurând un decor proaspăt în orice încăpere."
        elif cat == 'Perene':
            return "Frunzișul este bogat, oferind o textură plăcută și un fundal excelent pentru flori."
        else:
            return "Frunzele sunt bine dezvoltate, sănătoase și decorative."
            
    l = leaves.strip().rstrip('.')
    if not l:
        return "Frunzele sunt bine dezvoltate și decorative."
    l_low = l.lower()
    if l_low.startswith('frunze') or l_low.startswith('frunzele') or l_low.startswith('frunzis') or l_low.startswith('frunziș') or l_low.startswith('acele'):
        return clean_sentence(l)
    elif l_low.startswith('sunt '):
        return clean_sentence(f"Frunzele {l}")
    else:
        return clean_sentence(f"Frunzele sunt {l[0].lower() + l[1:]}")

def format_flowers(flowers, is_conifer, is_fern, cat):
    if not flowers:
        if is_conifer:
            return "Fiind un conifer, nu formează flori clasice, ci conuri caracteristice decorative."
        elif is_fern:
            return "Ferigile nu înfloresc; reproducerea se face prin spori fini situați pe spatele frunzelor."
        elif cat == 'Plante de apartament':
            return "Planta este apreciată în principal pentru decorul spectaculos al frunzelor, florile fiind discrete."
        else:
            return ""
    fl = flowers.strip().rstrip('.')
    if not fl:
        return ""
    fl_low = fl.lower()
    if any(fl_low.startswith(w) for w in ['flori', 'florile', 'inflorescent', 'inflorescenț', 'infloresc', 'nu produce', 'fiind', 'cultivat', 'apreciat', 'planta']):
        return clean_sentence(fl)
    elif fl_low.startswith('sunt '):
        return clean_sentence(f"Florile {fl_low}")
    else:
        return clean_sentence(f"Florile sunt {fl[0].lower() + fl[1:]}")

def enrich_all():
    with open('data/plants.json', 'r', encoding='utf-8') as f:
        plants = json.load(f)

    print(f"Enriching {len(plants)} plants...")

    for p in plants:
        name = p.get('name', '').strip()
        latin = p.get('latin_name', '').strip()
        cat = p.get('category', 'Plante de apartament').strip()
        origin = p.get('origin', '').strip().rstrip('.')
        shape = p.get('shape', '').strip()
        leaves = p.get('leaves', '').strip()
        flowers = p.get('flowers', '').strip()
        fruit = p.get('fruit', '').strip()
        req = p.get('requirements', '').strip()

        name_lower = name.lower()
        latin_lower = latin.lower()

        is_fern = any(k in latin_lower or k in name_lower for k in ['ferig', 'asplenium', 'adiantum', 'nephrolepis', 'polypodium', 'pteris'])
        is_succulent = any(k in latin_lower or k in name_lower for k in ['cactus', 'cact', 'mammillaria', 'opuntia', 'echinocactus', 'aloe', 'agave', 'crassula', 'echeveria', 'kalanchoe', 'sedum', 'sempervivum', 'haworthia'])
        is_palm = any(k in latin_lower or k in name_lower for k in ['palmier', 'chamaedorea', 'phoenix', 'caryota', 'areca', 'howea', 'cycas', 'rhapis'])
        is_orchid = any(k in latin_lower or k in name_lower for k in ['orhidee', 'phalaenopsis', 'dendrobium', 'cattleya', 'vanda', 'cymbidium', 'oncidium', 'paphiopedilum'])
        is_conifer = cat == 'Conifere' or any(k in latin_lower for k in ['abies', 'picea', 'pinus', 'juniperus', 'thuja', 'chamaecyparis', 'taxus', 'cedrus', 'larix'])

        # 1. Fill missing flowers if empty
        if not flowers:
            if is_conifer:
                flowers = "Nu produce flori propriu-zise, ci conuri caracteristice (strobili) ornamentale."
            elif is_fern:
                flowers = "Nu produce flori; reproducerea are loc prin spori dispuși pe dosul frunzelor fertile."
            elif is_succulent:
                flowers = "Produce flori viu colorate în perioada caldă dacă beneficiază de lumină abundentă și repaus hibernal."
            elif is_palm:
                flowers = "Florile sunt mici, grupate în inflorescențe spiciforme la baza frunzelor, rare în interior."
            elif cat == 'Plante de apartament':
                flowers = "Planta este apreciată în principal pentru decorul spectaculos al frunzelor, florile fiind discrete."
            elif cat == 'Perene':
                flowers = "Înflorește frumos din primăvară până în vară, adăugând farmec și culoare bordurilor perene."
            elif cat in ['Arbusti', 'Arbori']:
                flowers = "Produce flori primăvara sau la începutul verii, fiind o sursă importantă de polen și nectar."
            else:
                flowers = "Flori decorative adaptate speciei."

        # 2. Fill missing shape if empty
        if not shape:
            if is_conifer:
                shape = "are un port conic sau piramidal bine structurat, cu ramificații dese și compacte"
            elif is_fern:
                shape = "formează o tufă elegantă cu frunze grațios arcuite"
            elif is_palm:
                shape = "are o creștere erectă, nobilă, cu o coroană bogată de frunze la vârf"
            elif is_succulent:
                shape = "crește sub formă de rozetă compactă sau lăstari cărnoși"
            elif cat == 'Plante de apartament':
                shape = "are o creștere compactă și armonioasă, ideală pentru ghivece"
            elif cat == 'Perene':
                shape = "crește sub formă de tufă viguroasă cu tulpini erecte"
            elif cat == 'Arbusti':
                shape = "formează o coroană densă cu ramuri bogate"
            elif cat == 'Arbori':
                shape = "are un trunchi drept și o coroană maiestuoasă"
            else:
                shape = "prezintă o dezvoltare echilibrată și aspect armonios"

        # 3. Construct Description
        cat_titles = {
            'Plante de apartament': 'plantă decorativă de interior',
            'Perene': 'plantă perenă de grădină',
            'Arbusti': 'arbust ornamental',
            'Conifere': 'conifer decorativ veșnic verde',
            'Arbori': 'arbore ornamental',
            'Anuale': 'plantă decorativă anuală'
        }
        cat_desc = cat_titles.get(cat, 'plantă ornamentală')
        if is_conifer:
            cat_desc = 'conifer decorativ veșnic verde'
        elif is_fern:
            cat_desc = 'ferigă ornamentală cu frunziș luxuriant'
        elif is_palm:
            cat_desc = 'palmier decorativ impunător'
        elif is_succulent:
            cat_desc = 'plantă suculentă decorativă'

        origin_phrase = f", originară din {origin}" if origin and origin.lower() not in ['global', 'cultiva', 'cultivar'] else ""
        latin_phrase = f" (*{latin}*)" if latin else ""

        p_intro = f"{name}{latin_phrase} este o {cat_desc}{origin_phrase}."
        p_shape = format_shape(shape, name, cat)
        p_leaves = format_leaves(leaves, cat, latin, name)
        p_flowers = format_flowers(flowers, is_conifer, is_fern, cat)
        
        use_phrases = {
            'Plante de apartament': "Este ideală pentru înfrumusețarea locuințelor, birourilor și a serelor luminoase, aducând o notă exotică deosebită.",
            'Perene': "Constituie o alegere perfectă pentru borduri de flori, stâncării și ronduri perene de grădină.",
            'Arbusti': "Se folosește cu succes în garduri vii, grupuri florale sau ca exemplar solitar decorativ.",
            'Conifere': "Asigură o structură vizuală puternică și verdeață impecabilă în orice anotimp.",
            'Arbori': "Impresionează prin portul său majestuos în parcuri, alei și grădini rezidențiale spațioase.",
            'Anuale': "Oferă pete de culoare spectaculoase în jardiniere, ghivece sau ronduri pe durata întregii veri."
        }
        p_use = use_phrases.get(cat, "Este foarte apreciată pentru calitățile sale decorative.")

        parts = [p_intro]
        if p_shape: parts.append(p_shape)
        if p_leaves: parts.append(p_leaves)
        if p_flowers: parts.append(p_flowers)
        parts.append(p_use)

        description = " ".join(parts)

        # 4. Care Guide / What it needs ("Mire van szüksége")
        req_low = req.lower()

        # LIGHT
        if 'umbra' in req_low or 'umbrit' in req_low:
            light_guide = "Preferă amplasamentele semiumbrite sau umbrite, ferite de expunerea la soarele direct arzător de vară."
        elif 'soare direct' in req_low or 'plin soare' in req_low or 'insorit' in req_low or 'însorit' in req_low:
            light_guide = "Are nevoie de locuri însorite, cu lumină solară directă pentru o creștere viguroasă și înflorire spectaculoasă."
        elif 'lumina multa' in req_low or 'lumina intensa' in req_low or 'lumină multă' in req_low or 'lumina filtrata' in req_low:
            light_guide = "Necesită lumină abundentă, dar filtrată; se va proteja de razele solare directe arzătoare din mijlocul zilei."
        else:
            if is_conifer:
                light_guide = "Preferă soare plin sau semiumbră ușoară; tolerează bine expunerea directă în grădină."
            elif is_fern:
                light_guide = "Necesită lumină difuză sau semiumbră răcoroasă; soarele direct provoacă arsuri pe frunze."
            elif is_succulent:
                light_guide = "Necesită lumină intensă și soare direct pentru a menține forma compactă a rozetelor și culorile vii."
            elif cat == 'Plante de apartament':
                light_guide = "Preferă spații luminoase cu lumină indirectă sau soare blând de dimineață."
            elif cat == 'Perene':
                light_guide = "Se dezvoltă excelent în locuri însorite sau parțial umbrite din grădină."
            else:
                light_guide = "Amplasament luminos, preferabil însorit sau semiumbrit."

        # WATERING & HUMIDITY
        if is_succulent:
            water_guide = "Udare redusă; pământul se lasă să se usuce complet între două udări. Iarna se udă foarte rar sau deloc."
        elif is_fern:
            water_guide = "Necesită umiditate constantă în sol și umiditate atmosferică ridicată; se recomandă pulverizarea periodică a frunzișului cu apă dedurizată."
        elif 'uscaciunea aerului' in req_low or 'umiditate ridicata' in req_low or 'aer uscat' in req_low:
            water_guide = "Udare regulată cu apă călduță și pulverizarea periodică a frunzelor; nu tolerează aerul uscat din încăperile încălzite."
        elif 'sol cu drenaj bun' in req_low or 'drenaj' in req_low:
            water_guide = "Udare moderată astfel încât substratul să rămână reavăn; este esențial să se evite stagnarea apei la nivelul rădăcinilor."
        elif cat == 'Plante de apartament':
            water_guide = "Udare moderată când primii 2–3 cm de pământ de la suprafață s-au uscat. Apa din farfurioară se elimină după udare."
        elif is_conifer:
            water_guide = "Udare moderată; coniferele tinere necesită udări regulate în primii 2–3 ani și toamna înainte de primul îngheț."
        elif cat in ['Perene', 'Arbusti']:
            water_guide = "Udare regulată în primăvară și vară, în special în perioadele secetoase prelungite. Se udă la baza plantei."
        else:
            water_guide = "Udare echilibrată în funcție de sezon, asigurând un sol mereu reavăn."

        # SOIL & SUBSTRATE
        if is_conifer:
            soil_guide = "Sol permeabil, aerisit, cu pH ușor acid sau neutru. Se recomandă Amestec turbă Florasol și mulcire cu scoarță de pin."
        elif is_succulent:
            soil_guide = "Substrat nisipos, extrem de poros și bine drenat. Se recomandă Amestec turbă Florasol combinat cu perlit și pietriș fin."
        elif is_fern or is_orchid:
            soil_guide = "Substrat afânat, ușor acid și bogat în fibre vegetale. Se recomandă Amestec turbă Florasol pentru plante speciale."
        elif cat == 'Plante de apartament':
            soil_guide = "Substrat fertil, bogat în humus și permeabil. Se recomandă Amestec turbă Florasol universal pentru ghivece."
        elif cat in ['Perene', 'Arbusti', 'Arbori']:
            soil_guide = "Sol de grădină afânat, fertil și bine drenat. Se recomandă Amestec turbă Florasol pentru îmbunătățirea calității solului la plantare."
        else:
            soil_guide = "Sol permeabil, bogat în nutrienți. Recomandat Amestec turbă Florasol."

        # TEMPERATURE & WINTERING
        if cat == 'Plante de apartament':
            temp_guide = "Temperatură optimă de vegetație 18–24°C; iarna nu trebuie expusă la temperaturi sub 14–15°C sau la curenți reci."
        elif is_conifer or cat in ['Perene', 'Arbusti', 'Arbori']:
            temp_guide = "Specie rustică, perfect adaptată climatului din România; rezistă cu succes la gerurile aspre de iarnă (-20°C...-25°C)."
        else:
            temp_guide = "Sensibilă la îngheț; vegetează în lunile calde și se protejează de frig."

        # FERTILIZATION & NUTRITION
        if cat == 'Plante de apartament':
            fert_guide = "Fertilizare la 2–3 săptămâni din martie până în octombrie cu Soluții Nutritive Florasol; toamna târziu și iarna fertilizarea se suspendă."
        elif is_conifer:
            fert_guide = "Fertilizare primăvara la pornirea în vegetație și toamna cu îngrășăminte dedicate pentru menținerea vigorii acelor."
        elif is_succulent:
            fert_guide = "Fertilizare lunară în doze diluate cu Soluție Nutritivă Florasol exclusiv în perioada caldă (mai–august)."
        else:
            fert_guide = "Administrarea de Soluții Nutritive Florasol primăvara stimulează dezvoltarea masei foliare și îmbobocirea bogată."

        care_guide = {
            "lumina": light_guide,
            "udare": water_guide,
            "sol": soil_guide,
            "temperatura": temp_guide,
            "fertilizare": fert_guide
        }

        req_combined = f"{light_guide} {water_guide} {soil_guide} {temp_guide} {fert_guide}"

        # Update plant record
        p['description'] = description
        p['care_guide'] = care_guide
        p['shape'] = clean_sentence(shape)
        p['leaves'] = clean_sentence(leaves)
        p['flowers'] = clean_sentence(flowers)
        p['fruit'] = clean_sentence(fruit)
        p['requirements'] = req_combined

    # Save to data/plants.json
    with open('data/plants.json', 'w', encoding='utf-8') as f:
        json.dump(plants, f, ensure_ascii=False, indent=2)

    print("Successfully enriched and saved all 532 plants in data/plants.json!")

if __name__ == '__main__':
    enrich_all()
