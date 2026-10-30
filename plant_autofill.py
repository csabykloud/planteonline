# -*- coding: utf-8 -*-
"""
Automated Botanical Data & Image Fetcher from Internet Sources
(Wikipedia RO/EN, Wikidata, iNaturalist, GBIF, Wikimedia Commons)
for the PlanteOnline.ro Admin Panel.
"""
import json
import os
import re
import urllib.parse
import urllib.request

USER_AGENT = "PlanteOnlineBotanicalAssistant/2.0 (https://planteonline.ro; contact@planteonline.ro)"


def _http_get_json(url: str, timeout: int = 7):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _strip_accents(s: str) -> str:
    if not s:
        return ""
    repl = {
        "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t",
        "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ț": "T",
        "ş": "s", "ţ": "t", "Ş": "S", "Ţ": "T",
    }
    return "".join(repl.get(c, c) for c in s)


# Common Romanian <-> Latin dictionary for instant disambiguation when user types only Romanian common name
ROMANIAN_TO_LATIN_MAP = {
    "acant": ("Acanthus hungaricus", "Talpa-ursului (Acant)"),
    "acanthus hungaricus": ("Acanthus hungaricus", "Talpa-ursului (Matrună)"),
    "acanthus mollis": ("Acanthus mollis", "Talpa-ursului (Acant mediteranean)"),
    "talpa ursului": ("Acanthus hungaricus", "Talpa-ursului (Matrună)"),
    "lavanda": ("Lavandula angustifolia", "Lavanda (Levănțica)"),
    "levantica": ("Lavandula angustifolia", "Lavanda (Levănțica)"),
    "trandafir": ("Rosa", "Trandafirul"),
    "bujor": ("Paeonia officinalis", "Bujorul de grădină"),
    "lacramioare": ("Convallaria majalis", "Lăcrămioarele (Mărgăritărelul)"),
    "lacramioara": ("Convallaria majalis", "Lăcrămioarele (Mărgăritărelul)"),
    "ghiocel": ("Galanthus nivalis", "Ghiocelul"),
    "ghiocei": ("Galanthus nivalis", "Ghiocelul"),
    "lalea": ("Tulipa gesneriana", "Laleaua"),
    "lalele": ("Tulipa gesneriana", "Laleaua"),
    "zambila": ("Hyacinthus orientalis", "Zambila"),
    "narcisa": ("Narcissus pseudonarcissus", "Narcisa"),
    "brandusa": ("Crocus vernus", "Brândușa de primăvară"),
    "muscata": ("Pelargonium zonale", "Mușcata"),
    "petunie": ("Petunia × atkinsiana", "Petunia"),
    "surfinia": ("Petunia × atkinsiana 'Surfinia'", "Surfinia (Petunia curgătoare)"),
    "crinul pacii": ("Spathiphyllum wallisii", "Crinul păcii (Spatifilum)"),
    "spatifilum": ("Spathiphyllum wallisii", "Crinul păcii (Spatifilum)"),
    "limba soacrei": ("Sansevieria trifasciata", "Limba-soacrei (Planta-șarpe)"),
    "planta sarpe": ("Sansevieria trifasciata", "Limba-soacrei (Planta-șarpe)"),
    "monstera": ("Monstera deliciosa", "Monstera (Filodendronul cu frunze rupte)"),
    "ficus": ("Ficus elastica", "Ficusul de cauciuc"),
    "arborele de jad": ("Crassula ovata", "Arborele de jad (Planta banilor)"),
    "planta banilor": ("Crassula ovata", "Arborele de jad (Planta banilor)"),
    "zamioculcas": ("Zamioculcas zamiifolia", "Planta ZZ (Smaraldul Zanzibarului)"),
    "floarea pasiunii": ("Passiflora caerulea", "Floarea-pasiunii (Ceasornicul)"),
    "pasarea paradisului": ("Strelitzia reginae", "Pasărea-paradisului (Streliția)"),
    "strelitia": ("Strelitzia reginae", "Pasărea-paradisului (Streliția)"),
    "hortensie": ("Hydrangea macrophylla", "Hortensia de grădină"),
    "hortensia": ("Hydrangea macrophylla", "Hortensia de grădină"),
    "magnolie": ("Magnolia × soulangeana", "Magnolia"),
    "magnolia": ("Magnolia × soulangeana", "Magnolia"),
    "liliac": ("Syringa vulgaris", "Liliacul comun"),
    "iasomie": ("Philadelphus coronarius", "Iasomia falsă (Lămâița)"),
    "lamaita": ("Philadelphus coronarius", "Iasomia falsă (Lămâița)"),
    "leandru": ("Nerium oleander", "Leandrul"),
    "hibiscus": ("Hibiscus rosa-sinensis", "Trandafirul chinezesc (Hibiscus)"),
    "trandafir chinezesc": ("Hibiscus rosa-sinensis", "Trandafirul chinezesc (Hibiscus)"),
    "craciunita": ("Schlumbergera × buckleyi", "Crăciunița (Cactusul de Crăciun)"),
    "steaua craciunului": ("Euphorbia pulcherrima", "Steaua Crăciunului (Poinsettia)"),
    "poinsettia": ("Euphorbia pulcherrima", "Steaua Crăciunului (Poinsettia)"),
    "orhidee": ("Phalaenopsis Blume", "Orhideea fluture (Phalaenopsis)"),
    "violeta africana": ("Saintpaulia ionantha", "Violeta africană (Violeta de Usambara)"),
    "cercelus": ("Fuchsia × hybrida", "Cercelușul (Fuchsia)"),
    "aloe": ("Aloe vera", "Aloe vera"),
    "aloe vera": ("Aloe vera", "Aloe vera"),
    "agava": ("Agave americana", "Agava americană"),
    "iedera": ("Hedera helix", "Iedera comună"),
    "caprifoi": ("Lonicera japonica", "Caprifoiul (Mâna-Maicii-Domnului)"),
    "mana maicii domnului": ("Lonicera japonica", "Caprifoiul (Mâna-Maicii-Domnului)"),
    "glicina": ("Wisteria sinensis", "Glicina chinezească"),
    "clematita": ("Clematis × jackmanii", "Clematita"),
    "tuia": ("Thuja occidentalis", "Tuia occidentală (Arborele vieții)"),
    "molid": ("Picea abies", "Molidul"),
    "brad": ("Abies alba", "Bradul alb"),
    "pin": ("Pinus nigra", "Pinul negru"),
    "ienupar": ("Juniperus communis", "Ienupărul"),
    "rozmarin": ("Rosmarinus officinalis", "Rozmarinul"),
    "busuioc": ("Ocimum basilicum", "Busuiocul"),
    "menta": ("Mentha × piperita", "Menta (Izma bună)"),
    "cimbru": ("Thymus vulgaris", "Cimbrul de cultură"),
    "salvie": ("Salvia officinalis", "Salvia medicinală (Jaleșul)"),
    "galbenele": ("Calendula officinalis", "Gălbenelele (Filimica)"),
    "craite": ("Tagetes patula", "Crăițele"),
    "dalie": ("Dahlia pinnata", "Dalia (Gherghina)"),
    "gherghina": ("Dahlia pinnata", "Dalia (Gherghina)"),
    "gladiola": ("Gladiolus × hortulanus", "Gladiola (Săbiuța)"),
    "crizantema": ("Chrysanthemum × morifolium", "Crizantema (Tufănica)"),
    "tufanica": ("Chrysanthemum × morifolium", "Crizantema (Tufănica)"),
    "crin": ("Lilium candidum", "Crinul alb"),
    "crinul peruvian": ("Alstroemeria aurea", "Crinul peruvian (Crinul incaș)"),
}


# Origin region translation helper (English -> Romanian)
ORIGIN_TRANSLATIONS = [
    ("Balkan Peninsula", "Peninsula Balcanică"),
    ("Balkans", "Peninsula Balcanică"),
    ("Romania", "România"),
    ("Mediterranean", "Bazinul Mediteranean"),
    ("Southern Europe", "Europa de Sud"),
    ("Central Europe", "Europa Centrală"),
    ("Eastern Europe", "Europa de Est"),
    ("Europe", "Europa"),
    ("South America", "America de Sud"),
    ("Central America", "America Centrală"),
    ("North America", "America de Nord"),
    ("Mexico", "Mexic"),
    ("Brazil", "Brazilia"),
    ("Colombia", "Columbia"),
    ("Peru", "Peru"),
    ("Chile", "Chile"),
    ("Argentina", "Argentina"),
    ("South Africa", "Africa de Sud"),
    ("Madagascar", "Madagascar"),
    ("Tropical Africa", "Africa tropicală"),
    ("North Africa", "Africa de Nord"),
    ("Africa", "Africa"),
    ("East Asia", "Asia de Est"),
    ("Southeast Asia", "Asia de Sud-Est"),
    ("Tropical Asia", "Asia tropicală"),
    ("China", "China"),
    ("Japan", "Japonia"),
    ("Korea", "Coreea"),
    ("India", "India"),
    ("Himalayas", "Regiunea Himalayei"),
    ("Asia Minor", "Asia Mică"),
    ("Western Asia", "Asia de Vest"),
    ("Asia", "Asia"),
    ("Australia", "Australia"),
    ("New Zealand", "Noua Zeelandă"),
]


def _is_valid_plant_photo_url(url: str) -> bool:
    if not url:
        return False
    low = url.lower()
    bad_tokens = (
        ".svg", ".gif", ".tif", "map", "range", "distribution", "locator",
        "icon", "logo", "symbol", "herbarium", "drawing", "illustration",
        "stamp", "coat_of_arms", "diagram", "chart", "flag", "book", "page"
    )
    return not any(tok in low for tok in bad_tokens)


def _fetch_inaturalist_taxon(query: str):
    """Queries iNaturalist API for taxon scientific name, common names, family, and real photos."""
    q_enc = urllib.parse.quote(query)
    url = f"https://api.inaturalist.org/v1/taxa?q={q_enc}&per_page=5&locale=ro"
    data = _http_get_json(url)
    if not data or not data.get("results"):
        return None

    best = data["results"][0]
    sci_name = best.get("name", "")
    pref_common = best.get("preferred_common_name", "")
    iconic = best.get("iconic_taxon_name", "")
    if iconic and iconic not in ("Plantae", "Chromista"):
        # Filter to Plantae
        plant_hits = [r for r in data["results"] if r.get("iconic_taxon_name") == "Plantae"]
        if plant_hits:
            best = plant_hits[0]
            sci_name = best.get("name", "")
            pref_common = best.get("preferred_common_name", "")
        else:
            return None

    photos = []
    default_photo = best.get("default_photo") or {}
    if default_photo.get("medium_url"):
        large_url = default_photo["medium_url"].replace("/medium.", "/large.")
        if _is_valid_plant_photo_url(large_url):
            photos.append(large_url)

    # Also check taxon_photos if available
    taxon_id = best.get("id")
    if taxon_id:
        detail = _http_get_json(f"https://api.inaturalist.org/v1/taxa/{taxon_id}?locale=ro")
        if detail and detail.get("results"):
            d0 = detail["results"][0]
            if not pref_common and d0.get("preferred_common_name"):
                pref_common = d0.get("preferred_common_name")
            for tp in d0.get("taxon_photos", [])[:6]:
                ph = tp.get("photo") or {}
                u = ph.get("large_url") or ph.get("medium_url")
                if u and _is_valid_plant_photo_url(u) and u not in photos:
                    photos.append(u)
                    if len(photos) >= 3:
                        break

    return {
        "latin_name": sci_name,
        "ro_common_name": pref_common,
        "wikipedia_url": best.get("wikipedia_url", ""),
        "photos": photos[:3],
    }


def _fetch_wikipedia_summary(lang: str, query: str):
    """Searches Wikipedia in `lang` ('ro' or 'en') and returns title, extract, wikibase_item, and image."""
    q_enc = urllib.parse.quote(query)
    search_url = (
        f"https://{lang}.wikipedia.org/w/api.php?"
        f"action=query&list=search&srsearch={q_enc}&srlimit=3&format=json"
    )
    s_data = _http_get_json(search_url)
    if not s_data or not s_data.get("query", {}).get("search"):
        return None

    title = s_data["query"]["search"][0]["title"]
    t_enc = urllib.parse.quote(title)
    prop_url = (
        f"https://{lang}.wikipedia.org/w/api.php?"
        f"action=query&titles={t_enc}&prop=extracts|pageimages|pageprops|langlinks"
        f"&exintro=1&explaintext=1&piprop=original|thumbnail&pithumbsize=900"
        f"&lllang={'ro' if lang == 'en' else 'en'}&redirects=1&format=json"
    )
    p_data = _http_get_json(prop_url)
    if not p_data or not p_data.get("query", {}).get("pages"):
        return None

    pages = p_data["query"]["pages"]
    page = next(iter(pages.values()))
    if "missing" in page:
        return None

    extract = (page.get("extract") or "").strip()
    orig_img = (page.get("original") or {}).get("source", "")
    thumb_img = (page.get("thumbnail") or {}).get("source", "")
    img_url = orig_img if _is_valid_plant_photo_url(orig_img) else (thumb_img if _is_valid_plant_photo_url(thumb_img) else "")
    wikibase_item = (page.get("pageprops") or {}).get("wikibase_item", "")

    other_lang_title = ""
    for ll in page.get("langlinks", []):
        other_lang_title = ll.get("*", "")
        break

    return {
        "title": page.get("title", title),
        "extract": extract,
        "image_url": img_url,
        "wikibase_item": wikibase_item,
        "other_lang_title": other_lang_title,
    }


def _fetch_wikidata_labels(qid: str):
    """Fetches Romanian and Latin (P225 taxon name) from Wikidata item QID."""
    if not qid:
        return {}
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&props=labels|claims&languages=ro|en|la&format=json"
    data = _http_get_json(url)
    if not data or not data.get("entities", {}).get(qid):
        return {}
    ent = data["entities"][qid]
    labels = ent.get("labels", {})
    ro_label = (labels.get("ro") or {}).get("value", "")
    en_label = (labels.get("en") or {}).get("value", "")
    la_label = (labels.get("la") or {}).get("value", "")

    # Check P225 (taxon name)
    taxon_name = ""
    claims = ent.get("claims", {})
    if "P225" in claims:
        try:
            taxon_name = claims["P225"][0]["mainsnak"]["datavalue"]["value"]
        except Exception:
            pass

    return {
        "ro_label": ro_label,
        "en_label": en_label,
        "latin_name": taxon_name or la_label,
    }


def _extract_origin_from_text(ro_text: str, en_text: str) -> str:
    """Extracts geographic origin from Romanian or English Wikipedia text."""
    # 1. Try Romanian patterns
    for pat in [
        r"originar[ăa]?\s+din\s+([^.;(\n]{4,75})",
        r"răspândit[ăa]?\s+în\s+([^.;(\n]{4,75})",
        r"nativ[ăa]?\s+în\s+([^.;(\n]{4,75})",
        r"crește\s+spontan\s+în\s+([^.;(\n]{4,75})",
    ]:
        m = re.search(pat, ro_text, flags=re.IGNORECASE)
        if m:
            found = m.group(1).strip(" ,;:")
            return found[0].upper() + found[1:]

    # 2. Try English patterns and translate to Romanian
    if en_text:
        found_regions = []
        for en_reg, ro_reg in ORIGIN_TRANSLATIONS:
            if re.search(rf"\b{re.escape(en_reg)}\b", en_text, flags=re.IGNORECASE):
                if ro_reg not in found_regions:
                    found_regions.append(ro_reg)
        if found_regions:
            return ", ".join(found_regions[:4])

    return ""


def _synthesize_botanical_profile(
    latin_name: str,
    ro_name: str,
    ro_extract: str,
    en_extract: str,
    photos: list,
    existing_plant: dict = None,
):
    """
    Synthesizes a complete, accurate Romanian botanical profile for the admin form.
    Uses existing catalog data if available, enhanced with Wikipedia/iNaturalist data and botanical rules.
    """
    combined_text = f"{latin_name} {ro_name} {ro_extract} {en_extract}".lower()

    # Format display name ("Latin Name - Nume Românesc")
    clean_latin = latin_name.strip()
    clean_ro = ro_name.strip()

    if clean_latin and clean_ro:
        if clean_latin.lower() in clean_ro.lower():
            full_display_name = clean_ro
        else:
            full_display_name = f"{clean_latin} - {clean_ro}"
    elif clean_latin:
        full_display_name = clean_latin
    else:
        full_display_name = clean_ro

    # Determine Category & Ecological Profile based on taxonomic/botanical clues
    is_cactus_succ = any(w in combined_text for w in (
        "cactus", "cactaceae", "suculent", "succulent", "crassulaceae", "aloe", "agave",
        "echeveria", "sedum", "sempervivum", "kalanchoe", "haworthia", "opuntia", "mammillaria", "schlumbergera", "rhipsalis"
    ))
    is_orchid = any(w in combined_text for w in (
        "orchid", "orhidee", "phalaenopsis", "cymbidium", "dendrobium", "vanda", "cattleya", "oncidium", "miltonia", "paphiopedilum"
    ))
    is_conifer = any(w in combined_text for w in (
        "conifer", "pinaceae", "cupressaceae", "taxaceae", "picea", "abies", "pinus", "thuja", "juniperus", "chamaecyparis", "taxus", "cedrus", "rășinos"
    ))
    is_citrus_med = any(w in combined_text for w in (
        "citrus", "rutaceae", "fortunella", "poncirus", "oleander", "nerium", "bougainvillea", "olea ", "ficus carica", "punica", "mediteranean"
    ))
    is_acidophil = any(w in combined_text for w in (
        "rhododendron", "azalee", "azalea", "hydrangea", "hortensi", "camellia", "camelie", "ericaceae", "erica", "calluna", "gardenia", "vaccinium", "afin"
    ))
    is_palm = any(w in combined_text for w in (
        "arecaceae", "palmae", "palmier", "palm", "chamaedorea", "howea", "phoenix", "washingtonia", "trachycarpus", "cycas", "areca", "cocos"
    ))
    is_fern = any(w in combined_text for w in (
        "ferig", "fern", "polypodiopsida", "pteridophyta", "nephrolepis", "adiantum", "asplenium", "platycerium", "dryopteris"
    ))
    is_bulb = any(w in combined_text for w in (
        "bulb", "tubercul", "rizom", "tulipa", "lalea", "narcissus", "hyacinthus", "zambil", "crocus", "lilium", "crin", "gladiolus", "dahlia", "amaryllis", "hippeastrum", "iris", "galanthus", "convallaria", "alstroemeria", "freesia"
    ))
    is_climber = any(w in combined_text for w in (
        "cățărătoare", "urcătoare", "liană", "climbing", "vine", "liana", "hedera", "ieder", "clematis", "wisteria", "glicin", "campsis", "passiflora", "lonicera", "caprifoi", "parthenocissus", "ipomoea", "stephanotis", "hoya"
    ))
    is_shrub_tree = any(w in combined_text for w in (
        "arbust", "arbore", "shrub", "tree", "lemnos", "foios", "gard viu", "rosa", "trandafir", "syringa", "liliac", "magnolia", "hibiscus syriacus", "spiraea", "forsythia", "berberis", "buxus", "prunus", "acer", "betula", "tilia", "salix", "cornus", "viburnum", "philadelphus", "buddleja", "cotoneaster", "euonymus", "weigela", "deutzia"
    ))
    is_indoor_tropical = any(w in combined_text for w in (
        "apartament", "interior", "houseplant", "tropical", "epiphyte", "epifit", "araceae", "monstera", "philodendron", "ficus", "dracaena", "yucca", "schefflera", "dieffenbachia", "aglaonema", "calathea", "maranta", "stromanthe", "anthurium", "spathiphyllum", "zamioculcas", "sansevieria", "peperomia", "pilea", "begonia", "saintpaulia", "gloxinia", "sinningia", "cyclamen", "codiaeum", "croton", "syngonium", "pothos", "epipremnum", "tradescantia", "chlorophytum", "strelitzia", "bromeli", "guzmania", "vriesea", "aechmea", "tillandsia"
    ))
    is_annual_balcony = any(w in combined_text for w in (
        "anuală", "annual", "petunia", "surfinia", "pelargonium", "mușcat", "tagetes", "crăiț", "zinnia", "impatiens", "lobelia", "verbena", "gazania", "portulaca", "salvia splendens", "celosia", "antirrhinum", "begonia semperflorens", "viola", "panseluț"
    ))

    # 1. Category
    if existing_plant and existing_plant.get("category"):
        category = existing_plant["category"]
    elif is_cactus_succ:
        category = "Cactuși și suculente"
    elif is_orchid:
        category = "Plante de apartament"
    elif is_conifer:
        category = "Conifere"
    elif is_palm or is_indoor_tropical:
        category = "Plante de apartament"
    elif is_climber:
        category = "Plante cățărătoare"
    elif is_shrub_tree or is_acidophil:
        category = "Arbuști"
    elif is_bulb:
        category = "Bulboase"
    elif is_annual_balcony:
        category = "Plante anuale"
    else:
        category = "Perene"

    # 2. Origin
    origin = ""
    if existing_plant and existing_plant.get("origin"):
        origin = existing_plant["origin"]
    if not origin:
        origin = _extract_origin_from_text(ro_extract, en_extract)
    if not origin:
        if is_cactus_succ:
            origin = "Regiunile aride și semiaride din America și Africa"
        elif is_orchid or is_indoor_tropical or is_palm:
            origin = "Zonele tropicale și subtropicale din America, Asia și Africa"
        elif is_citrus_med:
            origin = "Bazinul Mediteranean și Asia de Sud-Est"
        else:
            origin = "Europa, Asia și zonele temperate ale emisferei nordice"

    # 3. Flowers, Leaves, Shape
    if existing_plant and existing_plant.get("flowers") and len(existing_plant["flowers"]) > 10:
        flowers = existing_plant["flowers"]
    else:
        if is_conifer or is_fern:
            flowers = "Plante fără flori (se reproduc prin conuri seminifere, respectiv spori); valoare decorativă asigurată de port și frunziș pe tot parcursul anului."
        elif is_orchid:
            flowers = "Flori spectaculoase, zigomorfe, dispuse în tije florale elegante; înflorire îndelungată (2–4 luni), în nuanțe variate de alb, roz, violet, galben sau pestriț."
        elif is_cactus_succ:
            flowers = "Flori solitare sau grupate, cu petale cu luciu mătăsos în tonuri vii (roz, roșu, galben, alb), care apar primăvara sau vara pe exemplarele mature."
        elif "acanthus" in combined_text:
            flowers = "Inflorescențe spiciforme înalte (până la 80–120 cm), cu flori labiate albe sau alb-roze protejate de bractee violaceu-purpurii; înfloresc în iunie–august."
        elif is_indoor_tropical:
            flowers = "Specie cultivată preponderent pentru frunzișul ornamental luxuriant; în condiții optime produce inflorescențe specifice familiei botanice în sezonul cald."
        else:
            flowers = "Flori decorative, bogat colorate, atractive pentru polenizatori, care se deschid eșalonat din primăvară până la sfârșitul verii."

    if existing_plant and existing_plant.get("leaves") and len(existing_plant["leaves"]) > 10:
        leaves = existing_plant["leaves"]
    else:
        if is_cactus_succ:
            leaves = "Frunze transformate în spini protectori (la cactuși) sau frunze cărnoase, suculente, acoperite cu pruină cerată pentru retenția apei."
        elif is_conifer:
            leaves = "Frunziș persistent (veșnic verde), acicular sau solzos, bogat în uleiuri eterice, de culoare verde-smarald, argintiu-albăstrui sau auriu."
        elif "acanthus" in combined_text:
            leaves = "Frunze mari, adânc penat-sectate, lucioase, de culoare verde-închis, dispuse într-o rozetă bazală bogată și arhitecturală."
        elif is_palm:
            leaves = "Frunze mari, penat-compuse sau palmat-sectate (în evantai), arcuite grațios, de culoare verde-intens și textură pieloasă."
        elif is_fern:
            leaves = "Fronde fin divizate (penat-sectate), dantelate sau întregi, de culoare verde-crud luminos, dispuse în rozetă bogată."
        else:
            leaves = "Frunziș sănătos și viguros, cu limb foliar bine conturat, de culoare verde-intens sau pestriț, care susține valoarea decorativă a plantei."

    if existing_plant and existing_plant.get("shape") and len(existing_plant["shape"]) > 10:
        shape = existing_plant["shape"]
    else:
        if is_climber:
            shape = "Plantă cățărătoare / volubilă cu lăstari lungi și flexibili, ideală pentru pergole, spaliere, garduri sau coșuri suspendate."
        elif is_shrub_tree or is_conifer:
            shape = "Port arbustiv sau arborescent ramificat armonios, cu coroană densă și structură lemnoasă viguroasă."
        elif is_cactus_succ:
            shape = "Port compact, globular, cilindric sau în rozetă densă, cu creștere lentă și arhitectură geometrică."
        else:
            shape = "Crește sub formă de tufă bogată, echilibrată și bine ramificată, cu port erect sau ușor arcuit."

    # 4. Ecological Care Guide (Lumină, Temperatură, Udare, Sol, Fertilizare)
    if existing_plant and existing_plant.get("care_guide"):
        cg = existing_plant["care_guide"]
        lumina = cg.get("lumina", "")
        temperatura = cg.get("temperatura", "")
        udare = cg.get("udare", "")
        sol = cg.get("sol", "")
        fertilizare = cg.get("fertilizare", "")
    else:
        if is_cactus_succ:
            lumina = "Locuri foarte luminoase și însorite (fereastră orientată spre sud, est sau vest; vara în grădină sau pe terasă însorită)."
            temperatura = "Optim 20–28 °C vara; iarna necesită repaus răcoros la 8–12 °C pentru stimularea înfloririi."
            udare = "Udare moderată primăvara și vara (numai după uscarea completă a substratului); iarna udarea se reduce drastic sau se suspendă."
            sol = "Substrat foarte permeabil, nisipos și bine drenat, care previne stagnarea apei la nivelul coletului."
            fertilizare = "Se fertilizează la 2–3 săptămâni în perioada aprilie–septembrie cu Vitaflora Soluție Nutritivă pentru Cactuși (NPK 3–5–7)."
        elif is_orchid:
            lumina = "Lumină intensă dar filtrată (ferestre de est sau vest), ferită de razele directe arzătoare ale soarelui de prânz."
            temperatura = "18–25 °C în timpul zilei și 15–18 °C noaptea; o diferență termică de 4–5 °C toamna stimulează emisia tijelor florale."
            udare = "Se udă prin scufundarea ghiveciului timp de 10–15 minute în apă dedurizată la temperatura camerei, o dată la 7–10 zile (când rădăcinile devin argintii)."
            sol = "Substrat special aerat din scoarță de pin calibrată și fibre de turbă – Florasol Substrat pentru Orhidee."
            fertilizare = "La fiecare a doua udare în perioada de creștere și înflorire cu Vitaflora Soluție Nutritivă pentru Orhidee și Bromelii."
        elif is_acidophil:
            lumina = "Semiumbră luminoasă sau soare de dimineață, în locuri adăpostite de vânturile uscate și de arșița amiezii."
            temperatura = "Temperaturi moderate (15–24 °C); speciile de grădină necesită mulcirea bazei peste iarnă cu scoarță și turbă acidă."
            udare = "Udări regulate cu apă dedurizată (fără calcar) sau apă de ploaie, menținând substratul constant reavăn."
            sol = "Substrat obligatoriu acid (pH 4,2–5,5), bogat în humus și bine drenat – Florasol Amestec de Turbă pentru Rhododendron."
            fertilizare = "Fertilizare din primăvară până în august cu soluții nutritive pentru plante acidofile și plante cu flori Vitaflora."
        elif is_citrus_med:
            lumina = "Plin soare și lumină directă abundentă; vara pe terasă sau în grădină, iar iarna în cel mai luminos spațiu disponibil."
            temperatura = "20–30 °C vara; iarna necesită iernare în spații luminoase și răcoroase la 5–12 °C, ferite de îngheț."
            udare = "Udare regulată și abundentă vara; iarna se udă moderat, doar cât să nu se usuce balotul de rădăcini."
            sol = "Substrat structurat, permeabil și bogat în fier – Florasol Substrat pentru Plante Mediteraneene și Citrice."
            fertilizare = "Săptămânal între martie și octombrie cu Vitaflora Soluție Nutritivă pentru Citrice (bogată în fier chelatat)."
        elif is_conifer:
            lumina = "Locuri însorite sau semiumbrite, bine aerisite, unde coroana primește lumină uniform pe toate laturile."
            temperatura = "Specie rustică, rezistentă la gerurile iernii (-20...-25 °C) și la oscilațiile climatului temperat-continental."
            udare = "Udare regulată în primii 2 ani de la plantare și în perioadele de secetă; toamna târziu se face o udare de aprovizionare înainte de îngheț."
            sol = "Sol profund, reavăn, ușor acid până la neutru, bine drenat, îmbogățit la plantare cu Amestec de turbă Florasol."
            fertilizare = "Din primăvară până în august cu Vitaflora Soluție Nutritivă pentru Conifere și Plante Sempervirescente (bogată în magneziu)."
        elif is_fern:
            lumina = "Semiumbră sau lumină difuză filtrată, ferită complet de razele directe ale soarelui."
            temperatura = "16–22 °C în apartament (sau rustică în grădină pentru speciile de exterior), cu umiditate atmosferică ridicată."
            udare = "Udare regulată cu apă dedurizată la temperatura camerei, menținând substratul permanent reavăn și pulverizând frunzișul."
            sol = "Substrat afânat, bogat în turbă fibroasă și humus de pădure – Florasol sau Humiflor Amestec de Turbă Universal."
            fertilizare = "La 2–3 săptămâni în sezonul cald cu o doză redusă la jumătate de Vitaflora Soluție Nutritivă pentru Plante Verzi."
        elif is_indoor_tropical or is_palm:
            lumina = "Lumină naturală intensă dar indirectă (filtrată), în apropierea unei ferestre orientate spre est sau vest."
            temperatura = "Temperatură optimă de apartament între 18–25 °C, ferită de curenții de aer rece și de temperaturi sub 13 °C."
            udare = "Udare moderată și regulată după zvântarea stratului superior de pământ, evitând stagnarea apei în farfurioară."
            sol = "Substrat bogat în humus, afânat și bine drenat – Florasol sau Humiflor Amestec de Turbă Universal."
            fertilizare = "La 1–2 săptămâni din martie până în septembrie cu Vitaflora Soluție Nutritivă pentru Plante Verzi și Palmieri sau Universală."
        elif is_annual_balcony:
            lumina = "Locuri însorite (minimum 5–6 ore de soare direct pe zi) sau semiumbră luminoasă pentru o înflorire continuă."
            temperatura = "Iubește căldura estivală (18–30 °C); se plantează afară după trecerea pericolului de brume târzii de primăvară."
            udare = "Udare zilnică în perioadele calde de vară (dimineața devreme sau seara), fără a lăsa apa să băltească."
            sol = "Substrat fertil cu retenție bună a apei – Nutrisol Substrat pentru Mușcate și Plante de Balcon sau Florasol Universal."
            fertilizare = "Săptămânal din mai până în septembrie cu Vitaflora Soluție Nutritivă pentru Mușcate și Plante de Balcon sau Plante cu Flori."
        else:
            # Perene / Arbuști / Bulboase / Cățărătoare de grădină
            lumina = "Locuri însorite sau semiumbrite în grădină, unde plantele beneficiază de minimum 4–6 ore de lumină zilnică."
            temperatura = "Specie rustică adaptată climatului din România, rezistentă la înghețurile iernii (-15...-25 °C)."
            udare = "Udare moderată și regulată, mai intensă după plantare, în perioada formării bobocilor și în verile secetoase."
            sol = "Sol fertil, profund și bine drenat, îmbogățit la plantare cu Florasol sau Humiflor Amestec de Turbă Universal."
            fertilizare = "Fertilizare fazială primăvara și în perioada de înflorire cu soluțiile nutritive Vitaflora și Plantasol."

    # 5. Full Morphological Description & Ecological Requirements
    if existing_plant and existing_plant.get("description") and len(existing_plant["description"]) > 60:
        description = existing_plant["description"]
    elif ro_extract and len(ro_extract) > 60:
        # Clean Wikipedia parenthetical clutter and combine with horticultural paragraph
        clean_ext = re.sub(r"\s+", " ", ro_extract).strip()
        if len(clean_ext) > 650:
            clean_ext = clean_ext[:650].rsplit(".", 1)[0] + "."
        description = (
            f"{clean_ext} "
            f"În horticultură și amenajări peisagistice, {full_display_name} se remarcă prin valoarea sa decorativă ridicată, "
            f"dezvoltându-se viguros atunci când îi sunt asigurate cerințele specifice de lumină, substrat bine drenat și nutriție echilibrată."
        )
    else:
        description = (
            f"{full_display_name} este o specie botanică valoroasă din categoria „{category}”, originară din {origin}. "
            f"{shape} {leaves} {flowers} "
            f"Pentru o dezvoltare armonioasă și o rezistență sporită, se recomandă amplasarea conform cerințelor de lumină ale speciei, "
            f"plantarea într-un substrat de calitate superioară și administrarea regulată a soluțiilor nutritive specifice în perioada de vegetație activă."
        )

    return {
        "name": full_display_name,
        "latin_name": clean_latin or full_display_name.split(" - ")[0].strip(),
        "category": category,
        "origin": origin,
        "flowers": flowers,
        "leaves": leaves,
        "shape": shape,
        "lumina": lumina,
        "temperatura": temperatura,
        "udare": udare,
        "sol": sol,
        "fertilizare": fertilizare,
        "description": description,
        "image_url": photos[0] if photos else "",
        "images": photos[:3],
    }


def find_existing_plant_in_catalog(name_input: str = "", latin_input: str = "", catalog_plants: list = None, exclude_id: int = None):
    """
    Checks if a plant already exists in `catalog_plants` by matching its Romanian name,
    Latin name, or any segment of 'Latin - Romanian (sau Synonym)'.
    Excludes `exclude_id` (when editing an existing plant).
    Returns the matching plant dict or None.
    """
    if not catalog_plants:
        return None

    candidates = set()
    for raw in (name_input, latin_input):
        if not raw:
            continue
        norm = _strip_accents(raw.lower()).strip()
        if len(norm) >= 2:
            candidates.add(norm)
        if " - " in norm:
            for part in norm.split(" - "):
                p_clean = part.strip()
                if len(p_clean) >= 2:
                    candidates.add(p_clean)
        if norm in ROMANIAN_TO_LATIN_MAP:
            m_lat, m_ro = ROMANIAN_TO_LATIN_MAP[norm]
            candidates.add(_strip_accents(m_lat.lower()).strip())
            candidates.add(_strip_accents(m_ro.lower()).strip())

    if not candidates:
        return None

    for p in catalog_plants:
        if exclude_id is not None and p.get("id") == exclude_id:
            continue
        p_name_norm = _strip_accents((p.get("name") or "").lower()).strip()
        p_lat_norm = _strip_accents((p.get("latin_name") or "").lower()).strip()

        plant_tokens = {p_name_norm, p_lat_norm}
        if " - " in p_name_norm:
            for seg in p_name_norm.split(" - "):
                seg_clean = seg.strip()
                if seg_clean:
                    plant_tokens.add(seg_clean)
                for sub in re.split(r"\bsau\b|,|/|\(|\)", seg_clean):
                    sub_clean = sub.strip()
                    if len(sub_clean) >= 3:
                        plant_tokens.add(sub_clean)

        plant_tokens.discard("")
        if candidates & plant_tokens:
            return p

    return None


def autofill_plant_info(name_input: str = "", latin_input: str = "", catalog_plants: list = None, catalog_products: list = None, exclude_id: int = None):
    """
    Main entry point called by `/api/plant/autofill`.
    Given either a Romanian name or a Latin scientific name (or both),
    fetches complete botanical data and images from the internet (Wikipedia RO/EN, Wikidata, iNaturalist)
    and existing catalog, returning all fields required by the Admin Plant Form.
    """
    raw_query = (latin_input or name_input or "").strip()
    if not raw_query:
        return {"success": False, "error": "Introduceți numele românesc sau numele latin al plantei."}

    # If input already has "Latin - Romanian" format, split it
    q_latin = latin_input.strip()
    q_ro = name_input.strip()
    if " - " in raw_query and not q_latin:
        parts = [p.strip() for p in raw_query.split(" - ", 1)]
        q_latin, q_ro = parts[0], parts[1]

    norm_q = _strip_accents(raw_query.lower()).strip()

    # 1. Check existing catalog (`plants.json`) for a match
    existing_match = find_existing_plant_in_catalog(name_input=name_input, latin_input=latin_input, catalog_plants=catalog_plants, exclude_id=exclude_id)
    if not existing_match and catalog_plants:
        for p in catalog_plants:
            if exclude_id is not None and p.get("id") == exclude_id:
                continue
            p_name_norm = _strip_accents((p.get("name") or "").lower())
            p_lat_norm = _strip_accents((p.get("latin_name") or "").lower())
            parts_norm = [x.strip() for x in p_name_norm.split(" - ")]
            if norm_q in parts_norm or (len(norm_q) >= 4 and (norm_q in p_lat_norm or norm_q in p_name_norm)):
                existing_match = p
                break

    # 2. Check Romanian-to-Latin dictionary
    mapped_latin, mapped_ro = "", ""
    if norm_q in ROMANIAN_TO_LATIN_MAP:
        mapped_latin, mapped_ro = ROMANIAN_TO_LATIN_MAP[norm_q]

    search_term_primary = mapped_latin or q_latin or q_ro or raw_query

    # 3. Query iNaturalist for scientific name, Romanian name, and verified real photos
    inat = _fetch_inaturalist_taxon(search_term_primary)
    if not inat and q_ro and q_ro != search_term_primary:
        inat = _fetch_inaturalist_taxon(q_ro)

    resolved_latin = (
        (existing_match.get("latin_name") if existing_match else "")
        or mapped_latin
        or (inat.get("latin_name") if inat else "")
        or q_latin
    )
    resolved_ro = (
        mapped_ro
        or (inat.get("ro_common_name") if inat else "")
        or q_ro
    )

    # 4. Query Romanian & English Wikipedia + Wikidata
    ro_wiki = _fetch_wikipedia_summary("ro", resolved_latin or search_term_primary)
    if not ro_wiki and q_ro:
        ro_wiki = _fetch_wikipedia_summary("ro", q_ro)

    en_wiki = _fetch_wikipedia_summary("en", resolved_latin or search_term_primary)

    qid = (ro_wiki.get("wikibase_item") if ro_wiki else "") or (en_wiki.get("wikibase_item") if en_wiki else "")
    wd_info = _fetch_wikidata_labels(qid) if qid else {}

    if not resolved_latin and wd_info.get("latin_name"):
        resolved_latin = wd_info["latin_name"]
    if not resolved_latin and en_wiki and en_wiki.get("title"):
        resolved_latin = en_wiki["title"]

    if not resolved_ro:
        if wd_info.get("ro_label") and wd_info["ro_label"].lower() != (resolved_latin or "").lower():
            resolved_ro = wd_info["ro_label"]
        elif ro_wiki and ro_wiki.get("title") and ro_wiki["title"].lower() != (resolved_latin or "").lower():
            resolved_ro = ro_wiki["title"]

    # Try to extract Romanian common name from first sentence of ro_wiki if still equal to latin
    if ro_wiki and ro_wiki.get("extract"):
        m_ro = re.search(r"^([A-ZĂÂÎȘȚ][a-zăâîșț\- ]{2,35})\s*\((?:<i>)?[A-Z][a-z]+", ro_wiki["extract"])
        if m_ro and not resolved_ro:
            resolved_ro = m_ro.group(1).strip()

    # If existing_match has "Latin - Romanian", extract Romanian part if needed
    if existing_match and " - " in existing_match.get("name", ""):
        ex_parts = existing_match["name"].split(" - ", 1)
        if not resolved_latin:
            resolved_latin = ex_parts[0].strip()
        if not resolved_ro or resolved_ro.lower() == resolved_latin.lower():
            resolved_ro = ex_parts[1].strip()

    # 5. Collect up to 3 verified photos
    photos = []
    if existing_match and existing_match.get("images"):
        for img in existing_match["images"]:
            if img and img not in photos:
                photos.append(img)
    if ro_wiki and ro_wiki.get("image_url") and ro_wiki["image_url"] not in photos:
        photos.append(ro_wiki["image_url"])
    if en_wiki and en_wiki.get("image_url") and en_wiki["image_url"] not in photos:
        photos.append(en_wiki["image_url"])
    if inat and inat.get("photos"):
        for img in inat["photos"]:
            if img and img not in photos:
                photos.append(img)
    photos = photos[:3]

    # 6. Synthesize profile fields
    profile = _synthesize_botanical_profile(
        latin_name=resolved_latin or raw_query,
        ro_name=resolved_ro or q_ro,
        ro_extract=ro_wiki.get("extract", "") if ro_wiki else "",
        en_extract=en_wiki.get("extract", "") if en_wiki else "",
        photos=photos,
        existing_plant=existing_match,
    )

    # Check if this species already exists in the catalog (excluding current edit ID)
    exact_dup = find_existing_plant_in_catalog(
        name_input=name_input or profile.get("name", ""),
        latin_input=latin_input or profile.get("latin_name", ""),
        catalog_plants=catalog_plants,
        exclude_id=exclude_id,
    )
    existing_summary = None
    if exact_dup:
        existing_summary = {
            "id": exact_dup.get("id"),
            "name": exact_dup.get("name"),
            "latin_name": exact_dup.get("latin_name"),
            "category": exact_dup.get("category"),
            "image_url": (exact_dup.get("images") or [""])[0],
        }

    return {
        "success": True,
        "plant": profile,
        "already_exists": bool(exact_dup),
        "existing_plant": existing_summary,
        "source": "Catalog + Wikipedia/iNaturalist/Wikidata" if existing_match else "Wikipedia + iNaturalist + Wikidata",
    }
