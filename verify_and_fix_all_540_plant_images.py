import json
import re
import sys
import time
import urllib.request
import urllib.parse
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

USER_AGENT = 'PlanteOnlineBotanicalVerifier/3.0 (https://planteonline.ro; contact@planteonline.ro)'

# Synonym genera map so valid botanical synonyms are accepted in filenames
SYNONYM_GENERA = {
    "abutilon": ["abutilon"],
    "acalypha": ["acalypha"],
    "acanthus": ["acanthus", "acantus"],
    "acer": ["acer"],
    "achillea": ["achillea"],
    "achimenes": ["achimenes"],
    "aciphylla": ["aciphylla"],
    "adiantum": ["adiantum"],
    "aechmea": ["aechmea"],
    "aegopodium": ["aegopodium"],
    "aeonium": ["aeonium"],
    "aeschynanthus": ["aeschynanthus"],
    "aesculus": ["aesculus"],
    "agave": ["agave"],
    "aglaonema": ["aglaonema"],
    "ailanthus": ["ailanthus"],
    "ajuga": ["ajuga"],
    "albizia": ["albizia", "albizzia"],
    "allamanda": ["allamanda"],
    "alocasia": ["alocasia"],
    "aloe": ["aloe"],
    "alstroemeria": ["alstroemeria"],
    "amygdalus": ["amygdalus", "prunus"],
    "ananas": ["ananas"],
    "anemone": ["anemone", "eriocapitella"],
    "anthurium": ["anthurium"],
    "aphelandra": ["aphelandra"],
    "aporocactus": ["aporocactus", "disocactus"],
    "aquilegia": ["aquilegia"],
    "araucaria": ["araucaria"],
    "ardisia": ["ardisia"],
    "artemisia": ["artemisia"],
    "arundo": ["arundo"],
    "asparagus": ["asparagus"],
    "aspidistra": ["aspidistra"],
    "asplenium": ["asplenium"],
    "aster": ["aster", "symphyotrichum"],
    "astilbe": ["astilbe"],
    "begonia": ["begonia"],
    "berberis": ["berberis"],
    "bergenia": ["bergenia"],
    "betula": ["betula"],
    "bidens": ["bidens"],
    "billbergia": ["billbergia"],
    "blechnum": ["blechnum", "oceaniopteris"],
    "bougainvillea": ["bougainvillea"],
    "brassaia": ["brassaia", "schefflera", "heptapleurum"],
    "browallia": ["browallia"],
    "brunfelsia": ["brunfelsia"],
    "buddleia": ["buddleia", "buddleja"],
    "buxus": ["buxus"],
    "caladium": ["caladium"],
    "calathea": ["calathea", "goeppertia"],
    "calceolaria": ["calceolaria"],
    "calibrachoa": ["calibrachoa"],
    "callisia": ["callisia"],
    "camellia": ["camellia"],
    "campanula": ["campanula"],
    "campsis": ["campsis"],
    "capsicum": ["capsicum"],
    "carex": ["carex"],
    "carpinus": ["carpinus"],
    "caryopteris": ["caryopteris"],
    "caryota": ["caryota"],
    "castanea": ["castanea"],
    "catalpa": ["catalpa"],
    "catharanthus": ["catharanthus", "vinca"],
    "cedrus": ["cedrus"],
    "celosia": ["celosia"],
    "celtis": ["celtis"],
    "centaurea": ["centaurea", "psephellus"],
    "cerasus": ["cerasus", "prunus"],
    "cercis": ["cercis"],
    "ceropegia": ["ceropegia"],
    "chaenomeles": ["chaenomeles"],
    "chamaecyparis": ["chamaecyparis", "callitropsis", "xanthocyparis"],
    "chamaedorea": ["chamaedorea"],
    "chelidonium": ["chelidonium"],
    "chlorophytum": ["chlorophytum"],
    "chrysalidocarpus": ["chrysalidocarpus", "dypsis"],
    "chrysanthemum": ["chrysanthemum", "dendranthema"],
    "cissus": ["cissus"],
    "citrus": ["citrus"],
    "clematis": ["clematis"],
    "clerodendrum": ["clerodendrum"],
    "clivia": ["clivia"],
    "codiaeum": ["codiaeum", "croton"],
    "codonanthe": ["codonanthe", "codonanthopsis"],
    "convallaria": ["convallaria"],
    "cordyline": ["cordyline"],
    "cornus": ["cornus"],
    "cortaderia": ["cortaderia"],
    "corylus": ["corylus"],
    "corynocarpus": ["corynocarpus"],
    "cotinus": ["cotinus"],
    "cotoneaster": ["cotoneaster"],
    "crassula": ["crassula"],
    "cryptanthus": ["cryptanthus"],
    "ctenanthe": ["ctenanthe"],
    "cupressocyparis": ["cupressocyparis", "cuprocyparis", "cupressus"],
    "cupressus": ["cupressus", "hesperocyparis"],
    "cycas": ["cycas"],
    "cyclamen": ["cyclamen"],
    "cydonia": ["cydonia"],
    "cymbidium": ["cymbidium"],
    "cyperus": ["cyperus"],
    "cytisus": ["cytisus"],
    "davallia": ["davallia"],
    "delphinium": ["delphinium"],
    "deutzia": ["deutzia"],
    "dianthus": ["dianthus"],
    "dicentra": ["dicentra", "lamprocapnos"],
    "dieffenbachia": ["dieffenbachia"],
    "digitalis": ["digitalis"],
    "dionaea": ["dionaea"],
    "dizygotheca": ["dizygotheca", "schefflera", "plerandra"],
    "doronicum": ["doronicum"],
    "dracaena": ["dracaena"],
    "drosera": ["drosera"],
    "dryopteris": ["dryopteris"],
    "dypsis": ["dypsis", "chrysalidocarpus"],
    "echeveria": ["echeveria"],
    "echinacea": ["echinacea"],
    "echinopsis": ["echinopsis"],
    "elaeagnus": ["elaeagnus"],
    "epimedium": ["epimedium"],
    "epipremnum": ["epipremnum", "scindapsus"],
    "eremurus": ["eremurus"],
    "erica": ["erica"],
    "euonymus": ["euonymus"],
    "euphorbia": ["euphorbia", "poinsettia"],
    "exacum": ["exacum"],
    "fagus": ["fagus"],
    "fatshedera": ["fatshedera"],
    "fatsia": ["fatsia"],
    "faucaria": ["faucaria"],
    "ficus": ["ficus"],
    "filipendula": ["filipendula"],
    "fittonia": ["fittonia"],
    "foeniculum": ["foeniculum"],
    "forsythia": ["forsythia"],
    "fraxinus": ["fraxinus"],
    "freesia": ["freesia"],
    "fuchsia": ["fuchsia"],
    "gaillardia": ["gaillardia"],
    "gardenia": ["gardenia"],
    "gazania": ["gazania"],
    "gentiana": ["gentiana"],
    "geranium": ["geranium"],
    "gerbera": ["gerbera"],
    "geum": ["geum"],
    "ginkgo": ["ginkgo"],
    "gloriosa": ["gloriosa"],
    "glycyrrhiza": ["glycyrrhiza"],
    "grevillea": ["grevillea"],
    "guzmania": ["guzmania"],
    "gymnocalycium": ["gymnocalycium"],
    "gypsophila": ["gypsophila"],
    "haworthia": ["haworthia", "haworthiopsis", "tulista"],
    "hedera": ["hedera"],
    "helianthus": ["helianthus"],
    "helichrysum": ["helichrysum"],
    "helleborus": ["helleborus"],
    "hemerocallis": ["hemerocallis"],
    "hibiscus": ["hibiscus"],
    "hippeastrum": ["hippeastrum", "amaryllis"],
    "hippophae": ["hippophae"],
    "hosta": ["hosta", "funkia"],
    "howea": ["howea"],
    "hoya": ["hoya"],
    "hydrangea": ["hydrangea"],
    "hypericum": ["hypericum"],
    "hypoestes": ["hypoestes"],
    "ilex": ["ilex"],
    "impatiens": ["impatiens"],
    "iris": ["iris"],
    "ixora": ["ixora"],
    "jasminum": ["jasminum"],
    "juglans": ["juglans"],
    "juniperus": ["juniperus"],
    "justicia": ["justicia", "beloperone"],
    "kalanchoe": ["kalanchoe"],
    "kerria": ["kerria"],
    "kniphofia": ["kniphofia"],
    "koelreuteria": ["koelreuteria"],
    "lamium": ["lamium"],
    "lantana": ["lantana"],
    "larix": ["larix"],
    "lathyrus": ["lathyrus"],
    "lavandula": ["lavandula"],
    "liatris": ["liatris"],
    "ligustrum": ["ligustrum"],
    "lilium": ["lilium"],
    "liriodendron": ["liriodendron"],
    "lithops": ["lithops"],
    "livistona": ["livistona"],
    "lobelia": ["lobelia"],
    "lonicera": ["lonicera"],
    "lotus": ["lotus"],
    "lupinus": ["lupinus"],
    "lychnis": ["lychnis", "silene"],
    "lygodium": ["lygodium"],
    "lysimachia": ["lysimachia"],
    "magnolia": ["magnolia"],
    "mahonia": ["mahonia", "berberis"],
    "malva": ["malva"],
    "mammillaria": ["mammillaria"],
    "mandevilla": ["mandevilla", "dipladenia"],
    "maranta": ["maranta"],
    "melianthus": ["melianthus"],
    "mentha": ["mentha"],
    "metasequoia": ["metasequoia"],
    "microlepia": ["microlepia"],
    "mimulus": ["mimulus", "erythranthe"],
    "mirabilis": ["mirabilis"],
    "monstera": ["monstera"],
    "morus": ["morus"],
    "murraya": ["murraya"],
    "nematanthus": ["nematanthus", "hypocyrta"],
    "neoregelia": ["neoregelia"],
    "nepenthes": ["nepenthes"],
    "nephrolepis": ["nephrolepis"],
    "nerium": ["nerium"],
    "nertera": ["nertera"],
    "nicotiana": ["nicotiana"],
    "oenothera": ["oenothera"],
    "olea": ["olea"],
    "oncidium": ["oncidium"],
    "opuntia": ["opuntia"],
    "origanum": ["origanum"],
    "osteospermum": ["osteospermum", "dimorphotheca"],
    "oxalis": ["oxalis"],
    "pachysandra": ["pachysandra"],
    "pachystachys": ["pachystachys"],
    "paeonia": ["paeonia"],
    "pandanus": ["pandanus"],
    "pandorea": ["pandorea"],
    "paphiopedilum": ["paphiopedilum"],
    "parrotia": ["parrotia"],
    "parthenocissus": ["parthenocissus"],
    "passiflora": ["passiflora"],
    "paulownia": ["paulownia"],
    "pelargonium": ["pelargonium"],
    "pellaea": ["pellaea"],
    "penstemon": ["penstemon"],
    "pentas": ["pentas"],
    "peperomia": ["peperomia"],
    "petunia": ["petunia", "surfinia"],
    "phalaenopsis": ["phalaenopsis"],
    "philodendron": ["philodendron"],
    "phlox": ["phlox"],
    "phoenix": ["phoenix"],
    "physostegia": ["physostegia"],
    "picea": ["picea"],
    "pilea": ["pilea"],
    "pinus": ["pinus"],
    "piper": ["piper"],
    "platycerium": ["platycerium"],
    "platycladus": ["platycladus", "thuja", "biota"],
    "plectranthus": ["plectranthus", "coleus"],
    "plumbago": ["plumbago"],
    "polypodium": ["polypodium", "phlebodium"],
    "polyscias": ["polyscias"],
    "populus": ["populus"],
    "portulaca": ["portulaca"],
    "potentilla": ["potentilla", "dasiphora"],
    "primula": ["primula"],
    "prunus": ["prunus", "cerasus", "laurocerasus"],
    "pulmonaria": ["pulmonaria"],
    "punica": ["punica"],
    "pyracantha": ["pyracantha"],
    "quercus": ["quercus"],
    "ranunculus": ["ranunculus"],
    "rebutia": ["rebutia"],
    "rheum": ["rheum"],
    "rhipsalidopsis": ["rhipsalidopsis", "hatiora", "schlumbergera"],
    "rhipsalis": ["rhipsalis"],
    "rhododendron": ["rhododendron", "azalea"],
    "rhus": ["rhus"],
    "robinia": ["robinia"],
    "rosa": ["rosa", "rose"],
    "ruellia": ["ruellia"],
    "saintpaulia": ["saintpaulia", "streptocarpus"],
    "salix": ["salix"],
    "salvia": ["salvia"],
    "sansevieria": ["sansevieria", "dracaena"],
    "saxifraga": ["saxifraga"],
    "scabiosa": ["scabiosa"],
    "schefflera": ["schefflera", "heptapleurum"],
    "schizanthus": ["schizanthus"],
    "schlumbergera": ["schlumbergera", "zygocactus"],
    "scindapsus": ["scindapsus", "epipremnum"],
    "sedum": ["sedum", "hylotelephium"],
    "selaginella": ["selaginella"],
    "senecio": ["senecio", "pericallis", "cineraria"],
    "sinningia": ["sinningia", "gloxinia"],
    "skimmia": ["skimmia"],
    "solanum": ["solanum"],
    "soleirolia": ["soleirolia", "helxine"],
    "solidago": ["solidago"],
    "sophora": ["sophora", "styphnolobium"],
    "sorbus": ["sorbus"],
    "sparrmannia": ["sparrmannia"],
    "spathiphyllum": ["spathiphyllum"],
    "spiraea": ["spiraea"],
    "stachys": ["stachys"],
    "stapelia": ["stapelia", "orbea"],
    "stephanotis": ["stephanotis", "marsdenia"],
    "strelitzia": ["strelitzia"],
    "streptocarpus": ["streptocarpus"],
    "strobilanthes": ["strobilanthes"],
    "stromanthe": ["stromanthe"],
    "symphoricarpos": ["symphoricarpos"],
    "syringa": ["syringa"],
    "tamarix": ["tamarix"],
    "tanacetum": ["tanacetum", "chrysanthemum", "pyrethrum"],
    "taxodium": ["taxodium"],
    "taxus": ["taxus"],
    "thuja": ["thuja", "platycladus"],
    "tillandsia": ["tillandsia"],
    "tilia": ["tilia"],
    "torenia": ["torenia"],
    "tradescantia": ["tradescantia", "zebrina"],
    "tropaeolum": ["tropaeolum"],
    "tulipa": ["tulipa"],
    "ulmus": ["ulmus"],
    "valeriana": ["valeriana"],
    "verbascum": ["verbascum"],
    "verbena": ["verbena"],
    "viburnum": ["viburnum"],
    "vinca": ["vinca"],
    "vriesea": ["vriesea", "lutheria"],
    "washingtonia": ["washingtonia"],
    "weigela": ["weigela"],
    "wisteria": ["wisteria"],
    "yucca": ["yucca"],
    "zamioculcas": ["zamioculcas"],
}

BAD_KEYWORDS = [
    'illustration', 'botanical_magazine', 'botanical_register', 'curtis', 'edwards',
    'köhler', 'kohler', 'thomé', 'thome', 'lindman', 'herbarium', 'herbar', 'museum',
    'specimen', 'portrait', 'painting', 'van_dyck', 'brueghel', 'fantin', 'peeters',
    'mission_san_juan', 'lccn', 'stamp', 'postmark', 'coin', 'medal', 'coat_of_arms',
    'wappen', 'blason', 'map', 'range', 'distribution', 'locator', 'diagram', 'schema',
    'drawing', 'sketch', 'engraving', 'lithograph', 'plate', 'tafel', 'planche',
    'flora_', 'sowerby', 'redoute', 'redouté', 'bessa', 'hooker', 'martius', 'siebold',
    'blume', 'jacquin', 'weinmann', 'ehret', 'besler', 'fuchs', 'icones', '.tif',
    '.svg', '.pdf', '.djvu', '.gif', '.png', 'book', 'volume', 'page', 'title', 'text',
    'dried', 'pressed', 'seeds', 'seed', 'pollen', 'microscop', 'sem_', 'placa',
    'sign', 'label', 'tag', 'beic', 'eruditorum', 'historia', 'naturalis', 'systema',
    'genera', 'species_plantarum', 'bhl', 'biodiversity', 'library', 'holotype',
    'isotype', 'lectotype', 'syntype', 'neotype', 'epitype', 'type_specimen', 'mnhn',
    'kew', 'nybg', 'sheet', 'gravure', 'estampe', 'aquarelle', 'watercolor',
    'watercolour', 'etching', 'woodcut', 'chromolithograph', 'botanische', 'journal',
    'revue', 'illustrierte', 'blumen', 'etiquette', 'schild', 'icon', 'logo', 'flag',
    'king_edward', 'queen_', 'prince_of', 'princess_of', 'baroness_schroder',
    'shirley_temple', 'lord_butler', 'graf_zeppelin', 'charles_', 'carolus', 'linnaeus',
    '178', '179', '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
    '1900', '1901', '1902', '1903', '1904', '1905', '1906', '1907', '1908', '1909',
    '1910', '1911', '1912', '1913', '1914', '1915', 'mohl', 'kew_', 'anatomia',
    'root_cross', 'cross_section', 'wood_sample', 'xylarium', 'fossil', 'infection',
    'disease', 'rust_', 'gall_', 'larva', 'caterpillar', 'beetle', 'aphid', 'damage'
]

def extract_genus_and_species(latin_name):
    cleaned = re.sub(r'\(.*?\)', '', latin_name)
    cleaned = re.sub(r"'.*?'", '', cleaned)
    cleaned = re.sub(r'\b(var\.|subsp\.|ssp\.|f\.|cv\.|hibrid|hibrizi|hybrid|hybridum|sp\.)\b', ' ', cleaned, flags=re.I)
    cleaned = cleaned.replace(' x ', ' ').replace(' X ', ' ').replace('-', ' ')
    words = [w for w in re.findall(r'[A-Za-z]+', cleaned) if len(w) >= 2]
    genus = words[0].lower() if words else ''
    species = words[1].lower() if len(words) >= 2 else ''
    return genus, species

def extract_cultivar(latin_name):
    m = re.search(r"'([^']+)'", latin_name)
    if m:
        return m.group(1).strip()
    return ""

def is_url_clean_for_plant(url, genus):
    if not url:
        return False
    if 'unsplash.com' in url or 'planteonline.ro' in url:
        return False
    if url.startswith('/static/uploads/plants/'):
        return True
    decoded = unquote(url).lower()
    filename = decoded.split('/')[-1].split('?')[0]
    if any(k in decoded for k in BAD_KEYWORDS):
        return False
    if 'wikimedia.org' in decoded:
        allowed_genera = SYNONYM_GENERA.get(genus, [genus])
        if not any(g in filename for g in allowed_genera):
            return False
    return True

def extract_commons_filename(url):
    # From https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Filename.jpg/960px-Filename.jpg
    decoded = unquote(url.split('?')[0])
    m = re.search(r'/commons/thumb/[^/]+/[^/]+/([^/]+)/', decoded)
    if m:
        return "File:" + m.group(1).replace('_', ' ')
    m2 = re.search(r'/commons/[^/]+/[^/]+/([^/]+)$', decoded)
    if m2:
        return "File:" + m2.group(1).replace('_', ' ')
    return ""

def batch_verify_commons_categories(urls):
    """Returns a set of URLs that are flagged as illustrations/herbarium/bad on Commons."""
    file_to_urls = {}
    for u in urls:
        fn = extract_commons_filename(u)
        if fn:
            file_to_urls.setdefault(fn, []).append(u)

    bad_urls = set()
    all_files = list(file_to_urls.keys())
    bad_cat_words = [
        'illustration', 'drawing', 'painting', 'artwork', 'herbarium', 'specimen',
        'plate', 'engraving', 'lithograph', 'book', 'magazine', 'register', 'map',
        'stamp', 'coin', 'coat of arms', 'portrait', 'people', 'building', 'museum',
        'seed', 'pollen', 'microscopic', 'anatomy', 'wood', 'xylarium', 'fossil',
        'plaque', 'sign', 'label', 'botanical art', 'curtis', 'edwards', 'redout',
        'thomé', 'köhler', 'lindman', 'bhl', 'biodiversity heritage library', 'icons'
    ]

    for i in range(0, len(all_files), 45):
        batch = all_files[i:i+45]
        titles_param = "|".join(batch)
        api_url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(titles_param)}&prop=categories|imageinfo&cllimit=max&iiprop=mime&format=json"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                pages = data.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    title = pdata.get('title', '')
                    matched_urls = file_to_urls.get(title, [])
                    if 'missing' in pdata:
                        for mu in matched_urls:
                            bad_urls.add(mu)
                        continue
                    ii = pdata.get('imageinfo', [])
                    if ii and ii[0].get('mime') != 'image/jpeg':
                        for mu in matched_urls:
                            bad_urls.add(mu)
                        continue
                    cats = " ".join(c.get('title', '').lower() for c in pdata.get('categories', []))
                    if any(bc in cats for bc in bad_cat_words):
                        for mu in matched_urls:
                            bad_urls.add(mu)
        except Exception as e:
            pass
    return bad_urls

def search_commons_photos(query_str, genus, max_results=3, existing=None):
    if existing is None:
        existing = []
    results = []
    neg_filters = "-illustration -herbarium -plate -magazine -register -specimen -drawing -painting -portrait -map -stamp -book -tafel -planche -bhl -museum -pressed -dried -seed -seeds -label -sign -wood -fossil"
    full_query = f"{query_str} filetype:bitmap {neg_filters}"
    api_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
        f"&gsrsearch={urllib.parse.quote(full_query)}&gsrnamespace=6&gsrlimit=18"
        f"&prop=imageinfo|categories&cllimit=max&iiprop=url|mime|dimensions&iiurlwidth=960&format=json"
    )
    bad_cat_words = [
        'illustration', 'drawing', 'painting', 'artwork', 'herbarium', 'specimen',
        'plate', 'engraving', 'lithograph', 'book', 'magazine', 'register', 'map',
        'stamp', 'coin', 'coat of arms', 'portrait', 'people', 'building', 'museum',
        'seed', 'pollen', 'microscopic', 'anatomy', 'wood', 'xylarium', 'fossil',
        'plaque', 'sign', 'label', 'botanical art', 'curtis', 'edwards', 'redout',
        'thomé', 'köhler', 'lindman', 'bhl', 'biodiversity heritage library'
    ]
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            pages = data.get('query', {}).get('pages', {})
            # Sort pages by index if available
            sorted_pages = sorted(pages.values(), key=lambda x: x.get('index', 999))
            for pdata in sorted_pages:
                ii = pdata.get('imageinfo', [])
                if not ii:
                    continue
                info = ii[0]
                if info.get('mime') != 'image/jpeg':
                    continue
                if info.get('width', 0) < 450 or info.get('height', 0) < 350:
                    continue
                cats = " ".join(c.get('title', '').lower() for c in pdata.get('categories', []))
                if any(bc in cats for bc in bad_cat_words):
                    continue
                thumb = info.get('thumburl') or info.get('url')
                if not thumb:
                    continue
                # Strip query string for cleaner URLs
                thumb_clean = thumb.split('?')[0]
                if not is_url_clean_for_plant(thumb_clean, genus):
                    continue
                if thumb_clean not in existing and thumb_clean not in results:
                    results.append(thumb_clean)
                    if len(existing) + len(results) >= max_results:
                        break
    except Exception:
        pass
    return results

def search_inaturalist_photos(genus, species, max_results=3, existing=None):
    if existing is None:
        existing = []
    results = []
    q = f"{genus} {species}".strip()
    api_url = f"https://api.inaturalist.org/v1/taxa?q={urllib.parse.quote(q)}&per_page=3"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            for taxon in data.get('results', []):
                t_name = taxon.get('name', '').lower()
                allowed_genera = SYNONYM_GENERA.get(genus, [genus])
                if not any(t_name.startswith(g) for g in allowed_genera):
                    continue
                # 1. Default photo
                dp = taxon.get('default_photo') or {}
                m_url = dp.get('medium_url') or dp.get('url')
                if m_url and 'static.inaturalist.org' in m_url or 'inaturalist-open-data' in str(m_url):
                    large_url = m_url.replace('/square.', '/large.').replace('/medium.', '/large.')
                    if large_url not in existing and large_url not in results:
                        results.append(large_url)
                        if len(existing) + len(results) >= max_results:
                            return results
                # 2. Fetch taxon details for taxon_photos if still needed
                tid = taxon.get('id')
                if tid and len(existing) + len(results) < max_results:
                    t_url = f"https://api.inaturalist.org/v1/taxa/{tid}"
                    req2 = urllib.request.Request(t_url, headers={'User-Agent': USER_AGENT})
                    with urllib.request.urlopen(req2, timeout=8) as r2:
                        td = json.loads(r2.read())
                        for tp in td.get('results', [{}])[0].get('taxon_photos', []):
                            ph = tp.get('photo', {})
                            pu = ph.get('large_url') or ph.get('medium_url')
                            if pu and pu not in existing and pu not in results:
                                results.append(pu)
                                if len(existing) + len(results) >= max_results:
                                    return results
                break
    except Exception:
        pass
    return results

def fetch_verified_photos_for_plant(plant):
    latin = plant.get('latin_name', '')
    genus, species = extract_genus_and_species(latin)
    cultivar = extract_cultivar(latin)
    current = list(plant.get('images', []))

    if len(current) >= 3:
        return plant['id'], current[:3]

    # Try 1: Genus + species + cultivar in title
    if genus and species and cultivar:
        new_imgs = search_commons_photos(f'intitle:{genus} intitle:{species} "{cultivar}"', genus, 3, current)
        current.extend(new_imgs)

    # Try 2: Genus + species in title
    if len(current) < 3 and genus and species:
        new_imgs = search_commons_photos(f'intitle:{genus} intitle:{species}', genus, 3, current)
        current.extend(new_imgs)

    # Try 3: Synonym genus + species in title
    if len(current) < 3 and genus:
        for syn in SYNONYM_GENERA.get(genus, []):
            if syn != genus and species:
                new_imgs = search_commons_photos(f'intitle:{syn} intitle:{species}', genus, 3, current)
                current.extend(new_imgs)
                if len(current) >= 3:
                    break

    # Try 4: Genus + cultivar in title (for hybrid cultivars like Begonia 'Norah Bedson', Delphinium 'Lord Butler')
    if len(current) < 3 and genus and cultivar:
        new_imgs = search_commons_photos(f'intitle:{genus} "{cultivar}"', genus, 3, current)
        current.extend(new_imgs)

    # Try 5: iNaturalist Taxon photos for Genus + species (or Genus)
    if len(current) < 3 and genus:
        new_imgs = search_inaturalist_photos(genus, species, 3, current)
        current.extend(new_imgs)

    # Try 6: Genus in title on Commons
    if len(current) < 3 and genus:
        new_imgs = search_commons_photos(f'intitle:{genus}', genus, 3, current)
        current.extend(new_imgs)

    # Try 7: iNaturalist Genus fallback
    if len(current) < 3 and genus and species:
        new_imgs = search_inaturalist_photos(genus, "", 3, current)
        current.extend(new_imgs)

    return plant['id'], current[:3]

def main():
    with open('data/plants.json', 'r', encoding='utf-8') as f:
        plants = json.load(f)

    print("Step 1: Auditing all existing URLs by filename, extension, and genus match...")
    all_candidate_commons_urls = []
    for p in plants:
        genus, _ = extract_genus_and_species(p.get('latin_name', ''))
        valid = []
        for u in p.get('images', []):
            u_clean = u.split('?')[0] if 'wikimedia.org' in u else u
            if is_url_clean_for_plant(u_clean, genus):
                if u_clean not in valid:
                    valid.append(u_clean)
                    if 'wikimedia.org' in u_clean:
                        all_candidate_commons_urls.append(u_clean)
        p['images'] = valid

    print(f"Step 2: Batch-verifying {len(all_candidate_commons_urls)} Wikimedia Commons files for categories & MIME type...")
    bad_commons_urls = batch_verify_commons_categories(all_candidate_commons_urls)
    print(f"Flagged {len(bad_commons_urls)} Commons files via category/MIME inspection (illustrations, herbarium, non-JPEG, etc.)")

    needing_photos = []
    for p in plants:
        p['images'] = [u for u in p.get('images', []) if u not in bad_commons_urls]
        if len(p['images']) < 3:
            needing_photos.append(p)

    print(f"Step 3: Fetching verified real plant photos for {len(needing_photos)} plants needing enrichment...")
    id_to_plant = {p['id']: p for p in plants}

    completed = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_verified_photos_for_plant, p): p['id'] for p in needing_photos}
        for fut in as_completed(futures):
            pid, updated_imgs = fut.result()
            id_to_plant[pid]['images'] = updated_imgs
            if updated_imgs:
                id_to_plant[pid]['image_url'] = updated_imgs[0]
            completed += 1
            if completed % 25 == 0 or completed == len(needing_photos):
                print(f"  Progress: {completed}/{len(needing_photos)} plants enriched...")

    # Ensure image_url is synced for all plants
    empty_plants = 0
    for p in plants:
        p['images'] = p.get('images', [])[:3]
        if p['images']:
            p['image_url'] = p['images'][0]
        else:
            empty_plants += 1
            print(f"WARNING: Plant #{p['id']} ({p['latin_name']}) has 0 images!")

    with open('data/plants.json', 'w', encoding='utf-8') as f:
        json.dump(plants, f, ensure_ascii=False, indent=2)

    print(f"Done! Saved all 540 plants. Plants with 0 images: {empty_plants}")

if __name__ == '__main__':
    main()
