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

def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    for s, d in [('ț', 't'), ('ș', 's'), ('ă', 'a'), ('â', 'a'), ('î', 'i')]:
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
