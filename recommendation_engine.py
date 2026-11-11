import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_products():
    path = os.path.join(DATA_DIR, 'products.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_plants():
    path = os.path.join(DATA_DIR, 'plants.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    for s, d in [('ț', 't'), ('ș', 's'), ('ţ', 't'), ('ş', 's'), ('ă', 'a'), ('â', 'a'), ('î', 'i')]:
        t = t.replace(s, d)
    return t

def has_word(text, words):
    pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def recommend_products_for_plant(plant, all_products=None):
    """
    Intelligent botanical recommendation tool:
    Based on plant characteristics (name, latin_name, category, leaves, flowers,
    shape, description), matches the optimal substrate and nutrient
    solutions from Florasol, Humiflor, Nutrisol, Vitaflora, and Plantasol.

    Rules:
    - If the plant is a tree or shrub (e.g., Salcam, Stejar, Tei, etc.) and not a bonsai or conifer:
      No liquid fertilizer is recommended, only substrate/soil.
    - If the plant is a conifer (e.g., Brad, Pin, Tuia): Vitaflora Solutie Nutritiva pt Conifere.
    - If the plant is a bonsai: Vitaflora Solutie Nutritiva Universal / Bonsai.
    """
    if all_products is None:
        all_products = load_products()

    prod_map = {p['id']: p for p in all_products}

    # Botanical fields only (avoid circular matches on existing care guide text)
    search_parts = [
        plant.get('name', ''),
        plant.get('latin_name', ''),
        plant.get('category', ''),
        plant.get('origin', ''),
        plant.get('leaves', ''),
        plant.get('flowers', ''),
        plant.get('shape', ''),
        plant.get('description', '')
    ]

    norm = normalize_text(' '.join(filter(None, search_parts)))
    cat_norm = normalize_text(plant.get('category', ''))
    name_norm = normalize_text(plant.get('name', ''))
    lat_norm = normalize_text(plant.get('latin_name', ''))

    # Helper match lists - match conifer strictly on category, name, or latin_name
    conifer_words = [
        'conifer', 'conifere', 'coniferelor', 'brad', 'bradul', 'brazi', 'abies',
        'molid', 'molidul', 'molizi', 'picea', 'pinul', 'pini', 'pinus',
        'tuia', 'thuja', 'ienupar', 'ienuparul', 'juniperus', 'juniper',
        'chamaecyparis', 'taxus', 'tisa', 'cupressus', 'cupressocyparis', 'chiparos', 'chiparosul',
        'cedru', 'cedrul', 'cedri', 'cedrus', 'araucaria', 'larix', 'larice', 'zada',
        'sequoia', 'metasequoia', 'cryptomeria', 'tsuga', 'taxodium', 'platycladus'
    ]
    is_conifer = (
        (('conifer' in cat_norm) or has_word(name_norm + ' ' + lat_norm, conifer_words))
        and 'pandanus' not in lat_norm and 'ginkgo' not in lat_norm and 'ginko' not in lat_norm
    )

    is_bonsai = ('bonsai' in cat_norm) or ('bonsai' in name_norm) or ('bonsai' in lat_norm)

    woody_words = [
        'salcam', 'robinia', 'stejar', 'quercus', 'tei', 'tilia', 'tillia', 'mesteacan', 'betula',
        'frasin', 'fraxin', 'fraxinus', 'fag', 'fagus', 'carpen', 'carpinus', 'acer',
        'paltin', 'artar', 'jugastru', 'ulm', 'ulmus', 'plop', 'populus', 'salcie', 'salix',
        'catalpa', 'platan', 'platanus', 'castan', 'aesculus', 'castanea', 'cornus',
        'spiraea', 'spirea', 'ligustrum', 'tamarix', 'cotoneaster', 'viburnum', 'forsythia',
        'berberis', 'dracila', 'mahonia', 'philadelphus', 'liliac', 'syringa', 'cercis',
        'ginkgo', 'ginko', 'albizia', 'corylus', 'coryllus', 'alun', 'ailanthus', 'cenuser',
        'celtis', 'sambovina', 'hippophae', 'catina', 'cotinus', 'cytisus', 'deutzia',
        'euonymus', 'salba', 'chaenomeles', 'cydonia', 'gutui', 'ilex', 'kerria', 'teisor',
        'koelreuteria', 'liriodendron', 'lonicera', 'magnolia', 'magnolie', 'morus', 'juglans',
        'rhus', 'otetar', 'parotia', 'parrotia', 'paulownia', 'paulovnia', 'parthenocissus',
        'potentilla', 'prunus', 'pyracantha', 'skimmia', 'sophora', 'sofora', 'sorbus', 'sorb',
        'symphoricarpos', 'weigela', 'wisteria', 'glicina', 'glicine', 'buxus', 'cimisir',
        'hibiscus syriacus', 'zamosita', 'olea', 'maslin', 'elagnus', 'eleagnus'
    ]
    # Note: Maranta, Strobilanthes, Saxifraga, Sansevieria, Solanum capsicastrum, Sparrmannia, Hoya, Ixora, Fuchsia, Gardenia, Hibiscus rosa-sinensis are potted/indoor plants even if tagged Arbusti
    indoor_override_genera = [
        'maranta', 'strobilanthes', 'saxifraga', 'sansevieria', 'solanum capsicastrum',
        'sparrmannia', 'hoya', 'ixora', 'fuchsia', 'gardenia', 'hibiscus rosa-sinensis',
        'clerodendrum', 'codiaeum', 'croton', 'schefflera', 'ficus benjamina', 'ficus elastica',
        'ficus elastia', 'ficus lyrata', 'ficus pumila', 'rhododendron simsii', 'azalee',
        'jasminum polyanthum', 'murraya', 'pachystachys', 'punica granatum var. nana',
        'citrus', 'lamai', 'lantana', 'nerium', 'leandru', 'washingtonia'
    ]
    is_indoor_override = any(g in (name_norm + ' ' + lat_norm) for g in indoor_override_genera)

    is_tree_or_shrub = (
        not is_indoor_override and (
            any(c in cat_norm for c in ['arbori', 'arbusti', 'arbust', 'arbore']) or
            has_word(name_norm + ' ' + lat_norm, woody_words)
        ) and not any(c in cat_norm for c in ['apartament', 'camera', 'balcon'])
    )

    # 1. Bonsai
    if is_bonsai:
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 23  # Vitaflora Solutie Nutritiva Universal / Bonsai
        alt_ids = [7, 18]

    # 2. Conifere & Rășinoase
    elif is_conifer:
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 26  # Vitaflora Solutie Nutritiva pt Conifere
        alt_ids = [19, 7, 20] # Substraturi: Nutrisol, Humiflor, Plantasol

    # 3. Arbori și Arbuști foioși / lemnoși (ex. Salcâm, Stejar, Tei) - STRICT FĂRĂ SOLUȚIE NUTRITIVĂ!
    elif is_tree_or_shrub:
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = None # NICIUN FERTILIZANT LICHID
        alt_ids = [19, 7, 20] # Substraturi alternative compatibile

    # 4. Mușcate & Plante de balcon
    elif has_word(name_norm + ' ' + lat_norm + ' ' + cat_norm, ['muscat', 'muscata', 'muscate', 'pelargonium', 'balcon', 'surfinia', 'petunie', 'petunia', 'calibrachoa', 'dipladenia', 'mandevilla', 'bidens']):
        primary_sub_id = 12   # Nutrisol Substrat Muscate
        primary_fert_id = 15  # Nutrisol Solutie Nutritiva pt Muscate si plante de balcon
        alt_ids = [5, 28, 8, 4]  # Florasol solutie muscate, Vitaflora solutie muscate, Humiflor solutie balcon, Florasol turba

    # 5. Orhidee
    elif has_word(name_norm + ' ' + lat_norm, ['orhidee', 'orhidei', 'orchid', 'orchidaceae', 'phalaenopsis', 'cymbidium', 'dendrobium', 'vanda', 'cattleya', 'oncidium', 'paphiopedilum']):
        primary_sub_id = 11   # Humiflor substrat orhidee
        primary_fert_id = 29  # Vitaflora Solutie Nutritiva pt Orhidee
        alt_ids = [1, 4]      # Vitaflora Batoane fertilizante orhidee, Florasol turba universal

    # 6. Cactuși & Suculente
    elif has_word(name_norm + ' ' + lat_norm + ' ' + norm, ['cactus', 'cactusi', 'cactee', 'suculent', 'suculente', 'aloe', 'agave', 'aeonium', 'aporocactus', 'sedum', 'sempervivum', 'crassula', 'mammillaria', 'mammilaria', 'opuntia', 'echinocactus', 'echinopsis', 'echeveria', 'eseveria', 'faucaria', 'gymnocalycium', 'gymnucalycium', 'haworthia', 'havortia', 'kalanchoe', 'kalancoe', 'lithops', 'rebutia', 'rhipsalidopsis', 'rhipsalis', 'schlumbergera', 'craciunita', 'stapelia']):
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 24  # Vitaflora Solutie Nutritiva pt Cactus
        alt_ids = [6, 7, 23]

    # 7. Curgătoare / Agățătoare / Suspendate
    elif has_word(name_norm + ' ' + lat_norm, ['hedera', 'iedera', 'clematis', 'pothos', 'potos', 'epipremnum', 'scindapsus', 'tradescantia', 'cissus', 'ceropegia', 'aeschynanthus', 'eschinantus', 'codonanthe', 'nematanthus', 'columnea', 'passiflora', 'pandorea', 'stephanotis', 'hoya', 'syngonium']):
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 22  # Vitaflora Solutie Nutritiva Plante Curgatoare
        alt_ids = [9, 13, 7]

    # 8. Gazon, Graminee decorative
    elif has_word(name_norm + ' ' + lat_norm, ['gazon', 'festuca', 'miscanthus', 'pennisetum', 'carex', 'stipa', 'cortaderia', 'arundo', 'imperata', 'graminee']):
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 27  # Vitaflora Solutie Nutritiva pt Gazon
        alt_ids = [14, 19]

    # 9. Căpșuni, Legume, Plante aromatice culinare
    elif has_word(lat_norm, ['fragaria', 'capsicum', 'mentha', 'origanum']) or has_word(name_norm, ['capsun', 'capsuni', 'legume', 'tomate']):
        primary_sub_id = 19   # Nutrisol Straturi Inaltate
        primary_fert_id = 25  # Vitaflora Solutie Nutritiva pt Capsuni si Legume
        alt_ids = [17, 16, 4]

    # 10. Plante de cameră / apartament cu frunze decorative
    elif has_word(name_norm + ' ' + lat_norm, ['ficus', 'monstera', 'palmier', 'chamaedorea', 'chamedora', 'chrysalidocarpus', 'howea', 'kentia', 'livistona', 'phoenix', 'caryota', 'washingtonia', 'cycas', 'cicas', 'feriga', 'adiantum', 'asplenium', 'blechnum', 'davallia', 'dryopteris', 'lygodium', 'microlepia', 'nephrolepis', 'pellaea', 'platycerium', 'polypodium', 'selaginella', 'selaginela', 'philodendron', 'filodendron', 'dracaena', 'dracena', 'cordyline', 'yucca', 'dieffenbachia', 'diefenbachia', 'diefenbahia', 'sansevieria', 'calathea', 'calatea', 'maranta', 'ctenanthe', 'ctenante', 'stromanthe', 'stromante', 'alocasia', 'alocasie', 'caladium', 'aglaonema', 'aspidistra', 'asparagus', 'schefflera', 'brassaia', 'dizygotheca', 'fatsia', 'fatshedera', 'polyscias', 'poliscias', 'fittonia', 'fitonia', 'hypoestes', 'hipoestes', 'peperomia', 'pilea', 'plectranthus', 'soleirolia', 'zamioculcas', 'codiaeum', 'croton', 'acalypha', 'acalifa', 'strombilanthes', 'strobilanthes', 'piper', 'pandanus', 'cyperus', 'ciperus', 'corynocarpus', 'araucaria', 'dionaea', 'dionea', 'drosera', 'nepenthes']):
        primary_sub_id = 18   # Nutrisol plante de camera
        primary_fert_id = 31  # Vitaflora Solutie Nutritiva pt Plante decorative cu frunze
        alt_ids = [4, 7, 13, 9, 3]

    # 11. Plante decorative cu Flori / Înflorire
    else:
        primary_sub_id = 4    # Florasol Amestec turba Universal
        primary_fert_id = 30  # Vitaflora Solutie Nutritiva pt Plante decorative cu Flori
        alt_ids = [32, 2, 6, 7, 10]

    primary_sub = prod_map.get(primary_sub_id, prod_map.get(4))
    primary_fert = prod_map.get(primary_fert_id) if primary_fert_id else None
    alts = [prod_map[aid] for aid in alt_ids if aid in prod_map]

    all_recommended_ids = [primary_sub['id']] + ([primary_fert['id']] if primary_fert else []) + [a['id'] for a in alts]
    seen = set()
    deduped_ids = []
    for pid in all_recommended_ids:
        if pid not in seen and pid in prod_map:
            seen.add(pid)
            deduped_ids.append(pid)

    return {
        'primary_substrate': primary_sub,
        'primary_fertilizer': primary_fert,
        'alternatives': alts,
        'recommended_product_ids': deduped_ids,
        'recommended_products_list': [
            {'id': pid, 'name': prod_map[pid]['name'], 'brand': prod_map[pid].get('brand', 'Florasol')}
            for pid in deduped_ids
        ]
    }


# =========================================================================
# ARTICLE RECOMMENDATIONS: Plants & Products for Articles & Guides
# =========================================================================

ARTICLE_BOTANICAL_CATEGORIES = {
    'cactusi': {
        'name': 'Cactuși și Plante Suculente',
        'priority': 10,
        'keywords': [
            'cactus', 'cactusi', 'cactusul', 'cactusului', 'cactusilor', 'cactee', 'suculent', 'suculenta', 'suculente', 'suculentelor',
            'aloe', 'agave', 'aeonium', 'aporocactus', 'sedum', 'crassula', 'mammillaria', 'mammilaria', 'opuntia', 'echinocactus', 
            'echinopsis', 'echeveria', 'haworthia', 'havortia', 'kalanchoe', 'kalancoe', 'lithops', 'rebutia', 'schlumbergera', 'craciunita'
        ],
        'products': [24, 4, 23, 6],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['cactus', 'cactusi', 'suculent', 'mammillar', 'opunti', 'echinopsis', 'crassula', 'sedum', 'aloe', 'agave', 'haworthi', 'havorti', 'kalancho', 'kalanco', 'schlumberger', 'craciunit', 'rebuti', 'lithops'])
    },
    'orhidee': {
        'name': 'Orhidee',
        'priority': 10,
        'keywords': [
            'orhidee', 'orhideea', 'orhideei', 'orhideele', 'orhideelor', 'orchid', 'orchidaceae',
            'phalaenopsis', 'cymbidium', 'dendrobium', 'vanda', 'cattleya', 'oncidium', 'paphiopedilum'
        ],
        'products': [11, 29, 1, 4],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['orhidee', 'orchid', 'phalaenopsis', 'cymbidium', 'dendrobium'])
    },
    'muscate_balcon': {
        'name': 'Mușcate și Flori de Balcon / Terasă',
        'priority': 9,
        'keywords': [
            'muscata', 'muscate', 'muscatele', 'muscatelor', 'muscatei', 'pelargonium', 'geranium',
            'petunie', 'petunia', 'petunii', 'petuniilor', 'surfinia', 'surfinie', 'calibrachoa', 'dipladenia',
            'jardiniera', 'jardiniere', 'jardinierelor', 'plante curgatoare', 'flori de balcon'
        ],
        'products': [12, 15, 5, 28, 22, 8],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['pelargonium', 'muscat', 'petuni', 'surfinia', 'verbena', 'fuchsia', 'calibrachoa']) or 'balcon' in cat
    },
    'conifere': {
        'name': 'Conifere și Rășinoase',
        'priority': 9,
        'keywords': [
            'conifer', 'conifere', 'coniferele', 'coniferelor', 'brad', 'bradul', 'brazi', 'molid', 'molidul', 'molizi',
            'pin', 'pinul', 'pini', 'tuia', 'thuja', 'ienupar', 'ienuparul', 'taxus', 'tisa', 'chiparos', 'cedru'
        ],
        'products': [26, 4, 19, 7],
        'plant_filter': lambda p_norm, cat: 'conifer' in cat or any(k in p_norm for k in ['conifer', 'brad', 'molid', 'pin', 'tuia', 'ienupar', 'taxus', 'chamaecyparis'])
    },
    'gazon': {
        'name': 'Gazon și Peluze',
        'priority': 9,
        'keywords': [
            'gazon', 'gazonul', 'gazonului', 'peluza', 'peluze', 'peluzei', 'peluzelor', 'insamantare gazon',
            'aerare gazon', 'tunderea gazonului', 'suprainsamantare', 'regenerare gazon', 'iarba de gazon'
        ],
        'products': [27, 4, 19, 14],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['gazon', 'festuca', 'graminee', 'iarba albastra', 'hosta', 'lavand', 'crizantem']) or 'perene' in cat
    },
    'trandafiri': {
        'name': 'Trandafiri',
        'priority': 9,
        'keywords': ['trandafir', 'trandafirul', 'trandafiri', 'trandafirii', 'trandafirilor', 'roze', 'rozelor', 'butasi de trandafir'],
        'products': [30, 4, 32, 6],
        'plant_filter': lambda p_norm, cat: 'rosa' in p_norm or 'trandafir' in p_norm
    },
    'citrice_mediteraneene': {
        'name': 'Citrice și Plante Mediteraneene',
        'priority': 9,
        'keywords': ['citrice', 'citricele', 'citricelor', 'citric', 'lamai', 'lamaiul', 'portocal', 'portocalul', 'mandarin', 'kumquat', 'maslin', 'leandru', 'olea', 'nerium'],
        'products': [23, 4, 18, 6],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['citrus', 'lamai', 'portocal', 'maslin', 'leandru', 'olea'])
    },
    'bonsai': {
        'name': 'Bonsai',
        'priority': 9,
        'keywords': ['bonsai', 'bonsaiul', 'bonsaii', 'arbori miniaturizati'],
        'products': [23, 4, 18, 6],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['ficus', 'ulmus', 'carmona', 'serissa', 'acer'])
    },
    'fructe_legume': {
        'name': 'Fructe, Căpșuni și Legume',
        'priority': 8,
        'keywords': [
            'capsun', 'capsuni', 'capsunii', 'capsunilor', 'capsuna', 'capsune', 'legume', 'legumelor', 'tomate', 'tomatele',
            'rosii', 'ardei', 'vinete', 'straturi inaltate', 'livada', 'livezilor', 'pomi fructiferi', 'prun', 'pruni',
            'mar', 'meri', 'cais', 'piersic', 'zmeur', 'zmeura', 'mur', 'mure', 'fructe de padure'
        ],
        'products': [25, 19, 4, 14],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['fragaria', 'capsun', 'legum', 'mentha', 'salvia', 'tomate', 'ardei', 'prun', 'mar', 'rubus', 'fruct', 'parotia'])
    },
    'daunatori_boli': {
        'name': 'Protecția Plantelor, Boli și Dăunători',
        'priority': 7,
        'keywords': [
            'insecticid', 'insecticide', 'afide', 'afidelor', 'acarieni', 'acarienilor', 'daunatori', 'daunatorilor',
            'ciuperci', 'ciupercilor', 'fungicid', 'fungicide', 'boli', 'bolilor', 'fainare', 'fainarea', 'rugina',
            'paduchi', 'omizi', 'ingalbenirea frunzelor', 'caderea frunzelor', 'igienizare', 'combaterea daunatorilor'
        ],
        'products': [33, 16, 17, 4],
        'plant_filter': None
    },
    'turba_sol_compost': {
        'name': 'Substraturi, Turbă și Sol',
        'priority': 6,
        'keywords': [
            'turba', 'turbei', 'turba eutrofa', 'turba oligotrofa', 'substrat', 'substraturi', 'substraturile',
            'pamant de flori', 'compost', 'composturi', 'pamant de telina', 'pamant de frunze', 'nisip', 'transplantare',
            'replantare', 'drenaj', 'drenajul'
        ],
        'products': [4, 7, 20, 18, 19],
        'plant_filter': None
    },
    'plante_camera_frunze': {
        'name': 'Plante de Cameră cu Frunze Decorative',
        'priority': 7,
        'keywords': [
            'plante de apartament', 'plante de interior', 'plante de camera', 'frunze decorative', 'plante verzi',
            'ficus', 'monstera', 'palmier', 'palmieri', 'dracaena', 'dracena', 'filodendron', 'philodendron',
            'dieffenbachia', 'sansevieria', 'calathea', 'feriga', 'ferigi', 'yucca', 'schefflera', 'zamioculcas',
            'aglaonema', 'croton', 'pothos', 'iedera', 'umiditatea aerului', 'curatarea frunzelor'
        ],
        'products': [18, 31, 9, 13, 3, 4],
        'plant_filter': lambda p_norm, cat: 'apartament' in cat and any(k in p_norm for k in ['ficus', 'monstera', 'palmier', 'dracaena', 'filodendron', 'sansevieria', 'calathea', 'feriga', 'yucca', 'schefflera', 'zamioculcas', 'croton', 'aglaonema', 'pothos'])
    },
    'plante_cu_flori': {
        'name': 'Plante cu Flori și Înflorire',
        'priority': 7,
        'keywords': [
            'flori', 'florile', 'florilor', 'inflorire', 'inflorirea', 'infloririi', 'inflorescenta', 'boboci', 'bobocilor',
            'stimularea infloririi', 'azalee', 'violeta', 'saintpaulia', 'ciclamen', 'cyclamen', 'anthurium', 'begonia',
            'hibiscus', 'zambile', 'lalele', 'narcise', 'flori de primavara', 'flori de toamna', 'crizanteme'
        ],
        'products': [30, 32, 2, 4, 10],
        'plant_filter': lambda p_norm, cat: any(k in p_norm for k in ['azalee', 'violeta', 'saintpaulia', 'cyclamen', 'anthurium', 'begonia', 'hibiscus', 'zambila', 'lalea', 'narcisa', 'crizantema', 'perene'])
    }
}

POPULAR_INDOOR_IDS = [206, 659, 135, 186, 173, 124, 89, 274, 278, 102]
POPULAR_OUTDOOR_IDS = [265, 328, 451, 471, 301, 308, 661, 574, 552]

def recommend_for_article(article, all_plants=None, all_products=None):
    """
    Intelligent botanical matching of related plants and recommended products
    for encyclopedia articles & practical guides.
    """
    if all_plants is None:
        all_plants = load_plants()
    if all_products is None:
        all_products = load_products()

    prod_map = {p['id']: p for p in all_products}

    # Pre-process plants
    plant_lookup = []
    for p in all_plants:
        p_name = p.get('name', '')
        p_lat = p.get('latin_name', '')
        p_cat = p.get('category', '')
        p_desc = p.get('description', '')
        
        raw_parts = p_name.split(' - ')
        common_part = raw_parts[0]
        subnames = [s.strip() for s in re.split(r'[,/]', common_part) if len(s.strip()) >= 4]
        genus = p_lat.split()[0].strip() if p_lat else ''
        p_norm_full = normalize_text(f"{p_name} {p_lat} {p_cat} {p_desc}")
        
        plant_lookup.append({
            'plant': p,
            'id': p['id'],
            'name': p_name,
            'category': p_cat,
            'subnames': [normalize_text(s) for s in subnames],
            'genus': normalize_text(genus),
            'full_norm': p_norm_full
        })

    title_norm = normalize_text(article.get('title', ''))
    summary_norm = normalize_text(article.get('summary', '') or '')
    content_norm = normalize_text((article.get('content', '') or '')[:4000])
    cat_norm = normalize_text(article.get('category', ''))

    # 1. Categorize Article Topic
    topic_scores = {}
    for t_key, t_info in ARTICLE_BOTANICAL_CATEGORIES.items():
        score = 0
        prio = t_info.get('priority', 5)
        for kw in t_info['keywords']:
            kw_norm = normalize_text(kw)
            if re.search(r'\b' + re.escape(kw_norm) + r'\b', title_norm, re.IGNORECASE):
                score += (20 * prio)
            elif re.search(r'\b' + re.escape(kw_norm) + r'\b', summary_norm, re.IGNORECASE):
                score += (6 * prio)
            elif re.search(r'\b' + re.escape(kw_norm) + r'\b', content_norm, re.IGNORECASE):
                score += (1 * prio)
        if score > 0:
            topic_scores[t_key] = score

    sorted_topics = sorted(topic_scores.items(), key=lambda x: -x[1])
    primary_topic = sorted_topics[0][0] if sorted_topics else None
    topic_data = ARTICLE_BOTANICAL_CATEGORIES.get(primary_topic)

    # Contextual environment detection (Strict)
    is_indoor = False
    is_outdoor = False

    if any(k in title_norm for k in ['apartament', 'camera', 'interior', 'ghivece', 'cactusi', 'orhidee']):
        is_indoor = True
    elif any(k in title_norm for k in ['gradina', 'balcon', 'gazon', 'curte', 'livada', 'pomi', 'arbori', 'arbusti', 'exterior', 'peluza']):
        is_outdoor = True
    elif 'interior' in cat_norm:
        is_indoor = True
    elif any(c in cat_norm for c in ['exterior', 'gradina', 'amenajari', 'fructe']):
        is_outdoor = True
    else:
        indoor_cues = len(re.findall(r'\b(apartament|camera|interior|ghiveci|locuinta)\b', content_norm))
        outdoor_cues = len(re.findall(r'\b(gradina|curte|livada|teren|peluza|rond)\b', content_norm))
        if indoor_cues > outdoor_cues:
            is_indoor = True
        else:
            is_outdoor = True

    # 2. Score Plants
    scored_plants = []
    seen_plant_ids = set()

    for pl in plant_lookup:
        p_score = 0
        p_cat_norm = normalize_text(pl['category'])
        is_p_indoor = ('apartament' in p_cat_norm or 'balcon' in p_cat_norm)

        # A) Explicit name in title/summary/content
        for sname in pl['subnames']:
            if sname and len(sname) >= 4:
                if re.search(r'\b' + re.escape(sname) + r'\b', title_norm, re.IGNORECASE):
                    p_score += 200
                elif re.search(r'\b' + re.escape(sname) + r'\b', summary_norm, re.IGNORECASE):
                    p_score += 50
                elif re.search(r'\b' + re.escape(sname) + r'\b', content_norm, re.IGNORECASE):
                    p_score += 15

        # B) Explicit genus
        if pl['genus'] and len(pl['genus']) >= 4:
            if re.search(r'\b' + re.escape(pl['genus']) + r'\b', title_norm, re.IGNORECASE):
                p_score += 150
            elif re.search(r'\b' + re.escape(pl['genus']) + r'\b', summary_norm, re.IGNORECASE):
                p_score += 40
            elif re.search(r'\b' + re.escape(pl['genus']) + r'\b', content_norm, re.IGNORECASE):
                p_score += 12

        # C) Specific Topic filter match
        if topic_data and topic_data.get('plant_filter'):
            if topic_data['plant_filter'](pl['full_norm'], p_cat_norm):
                p_score += 40
                if primary_topic == 'cactusi' and any(k in pl['full_norm'] for k in ['cactus', 'mammillar', 'opunti', 'echinopsis', 'schlumberger', 'craciunit']):
                    p_score += 45
                elif primary_topic == 'orhidee' and 'orhid' in pl['full_norm']:
                    p_score += 50
                elif primary_topic == 'conifere' and ('conifer' in p_cat_norm or any(k in pl['full_norm'] for k in ['brad', 'pin', 'molid', 'tuia', 'ienupar'])):
                    p_score += 35
                elif primary_topic == 'muscate_balcon' and ('muscat' in pl['full_norm'] or 'pelargon' in pl['full_norm'] or 'balcon' in p_cat_norm):
                    p_score += 40
                elif primary_topic == 'gazon' and any(k in pl['full_norm'] for k in ['hosta', 'lavand', 'iarba', 'festuca']):
                    p_score += 35
                elif primary_topic == 'plante_camera_frunze' and any(k in pl['full_norm'] for k in ['ficus', 'monstera', 'palmier', 'filodendron', 'sansevieria', 'zamioculcas']):
                    p_score += 40

        # Foliage cleaning or propagation cues in indoor articles
        if is_indoor:
            if any(k in title_norm for k in ['frunze', 'frunzelor', 'igienizare', 'curatare']):
                if any(k in pl['full_norm'] for k in ['ficus', 'monstera', 'filodendron', 'sansevieria', 'zamioculcas', 'dieffenbachia', 'calathea', 'palmier']):
                    p_score += 50
            if any(k in title_norm for k in ['butasi', 'inmultire', 'divizare']):
                if any(k in pl['full_norm'] for k in ['crassula', 'tradescantia', 'pothos', 'ficus', 'begonia', 'saintpaulia', 'pelargonium', 'sedum']):
                    p_score += 45

        # D) General Environment Context Affinity
        if is_indoor and is_p_indoor:
            p_score += 15
        elif is_outdoor and not is_p_indoor:
            p_score += 15

        if p_score > 0:
            scored_plants.append((p_score, pl['plant']))

    scored_plants.sort(key=lambda x: -x[0])

    # Pick top 4 unique plants (filtering environment when possible)
    matched_plants = []
    for sc, p in scored_plants:
        p_cat = normalize_text(p.get('category',''))
        p_is_indoor = ('apartament' in p_cat or 'balcon' in p_cat)
        if is_indoor and not p_is_indoor and sc < 100:
            continue
        if is_outdoor and p_is_indoor and sc < 100:
            continue

        if p['id'] not in seen_plant_ids:
            seen_plant_ids.add(p['id'])
            matched_plants.append(p)
            if len(matched_plants) >= 4:
                break

    # Fallback to popular curated plants for that environment
    fallback_pool = POPULAR_INDOOR_IDS if is_indoor else POPULAR_OUTDOOR_IDS
    for fid in fallback_pool:
        if len(matched_plants) >= 4:
            break
        if fid not in seen_plant_ids:
            pl_match = next((pl['plant'] for pl in plant_lookup if pl['id'] == fid), None)
            if pl_match:
                matched_plants.append(pl_match)
                seen_plant_ids.add(fid)

    # Absolute fallback
    if len(matched_plants) < 4:
        for pl in plant_lookup:
            p = pl['plant']
            if p['id'] not in seen_plant_ids:
                matched_plants.append(p)
                seen_plant_ids.add(p['id'])
            if len(matched_plants) >= 4:
                break

    # 3. Score Products
    if topic_data:
        prod_candidate_ids = list(topic_data['products'])
    else:
        prod_candidate_ids = [18, 31, 4] if is_indoor else [4, 19, 23]

    matched_products = []
    seen_prod_ids = set()
    for pid in prod_candidate_ids:
        if pid in prod_map and pid not in seen_prod_ids:
            seen_prod_ids.add(pid)
            matched_products.append(prod_map[pid])
            if len(matched_products) >= 3:
                break

    return matched_plants[:4], matched_products[:3]
