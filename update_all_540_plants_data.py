import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

from recommendation_engine import recommend_products_for_plant, load_products

# Exact Latin name typo corrections and standardizations
LATIN_FIXES = {
    99: "Aeonium arboreum",
    305: "Albizia julibrissin",
    315: "Corylus colurna",
    78: "Araucaria heterophylla",
    521: "Bidens ferulifolia",
    72: "Calceolaria x herbeohybrida",
    143: "Calceolaria x herbeohybrida",
    161: "Dionaea muscipula",
    439: "Chamaecyparis lawsoniana",
    429: "Chamaecyparis pisifera 'Boulevard'",
    261: "Primula denticulata",
    135: "Cordyline fruticosa",
    142: "Chlorophytum comosum 'Variegatum'",
    406: "Spiraea betulifolia",
    159: "Dracaena deremensis 'Warneckii'",
    104: "Blechnum gibbum",
    174: "Ficus elastica",
    176: "Fittonia albivenis",
    320: "Ginkgo biloba",
    183: "Gloriosa superba 'Rothschildiana'",
    185: "Gymnocalycium mihanovichii",
    452: "Juniperus communis 'Repanda'",
    461: "Juniperus scopulorum",
    462: "Juniperus scopulorum 'Blue Arrow'",
    463: "Juniperus scopulorum 'Moonglow'",
    534: "Convallaria majalis",
    473: "Picea glauca",
    212: "Nematanthus gregarius",
    217: "Oxalis tetraphylla",
    117: "Chamaedorea elegans",
    49: "Dypsis lutescens (Chrysalidocarpus lutescens)",
    233: "Paphiopedilum hybridum",
    330: "Parrotia persica",
    482: "Pinus sylvestris",
    396: "Potentilla fruticosa 'Goldfinger'",
    397: "Potentilla fruticosa 'Goldstar'",
    395: "Potentilla fruticosa var. arbuscula",
    611: "Nicotiana alata",
    618: "Rheum palmatum 'Atrosanguineum'",
    363: "Euonymus fortunei 'Emerald 'n' Gold'",
    317: "Elaeagnus angustifolia",
    341: "Tilia cordata",
    494: "Platycladus orientalis 'Aurea' (Thuja orientalis)",
}

# Comprehensive Genus -> (Romanian Popular Name, Default Geographical Origin)
GENUS_DATA = {
    "Abies": ("Brad", "Emisfera Nordică (zonele montane din Europa, Asia și America de Nord)"),
    "Abutilon": ("Pristolnic sau Arțar de cameră", "Regiunile tropicale și subtropicale din America de Sud"),
    "Acalypha": ("Acalifă sau Coada-pisicii / Coada-vulpii", "Insulele Pacificului și regiunile tropicale din Asia și America"),
    "Acanthus": ("Talpa-ursului", "Bazinul Mediteranean și sud-estul Europei (Balcani, România)"),
    "Acer": ("Arțar sau Paltin", "Europa, Asia și America de Nord"),
    "Achillea": ("Coada-șoricelului ornamentală", "Europa, Asia de Vest și Caucaz"),
    "Achimenes": ("Achimenes sau Floarea-magică", "America Centrală și Mexic"),
    "Aciphylla": ("Iarba-spadă neozeelandeză (Spaniard Grass)", "Noua Zeelandă și Australia (zonele alpine)"),
    "Adiantum": ("Feriga Părul-Maicii-Domnului (Părul-fetei)", "Regiunile tropicale și subtropicale din America de Sud (Brazilia)"),
    "Aechmea": ("Ecmea sau Vaza-de-argint", "Pădurile tropicale din America de Sud (Brazilia)"),
    "Aegopodium": ("Piciorul-caprei pestriț", "Europa și Asia temperată"),
    "Aeonium": ("Aeonium sau Rozeta-arborescentă", "Insulele Canare, Madeira și nordul Africii"),
    "Aeschynanthus": ("Eschinantus sau Planta-ruj", "Pădurile tropicale din Asia de Sud-Est (Malaezia, Indonezia)"),
    "Aesculus": ("Castan porcesc sau Castan sălbatic ornamental", "Peninsula Balcanică și sud-estul Europei"),
    "Agave": ("Agavă sau Secolul-american", "Mexic și sud-vestul Americii de Nord"),
    "Aglaonema": ("Aglaonema sau Veșnic-verde chinezesc", "Pădurile tropicale umede din Asia de Sud-Est"),
    "Ailanthus": ("Cenușer sau Oțetar fals", "China de Nord și de Centru, Taiwan"),
    "Ajuga": ("Vineriță sau Costa-voinicului", "Europa, Caucaz și Asia de Vest"),
    "Albizia": ("Arborele de mătase", "Asia de Sud și de Est (din Iran până în China și Japonia)"),
    "Allamanda": ("Alamanda sau Trompeta-de-aur", "America de Sud tropicală (Brazilia)"),
    "Alocasia": ("Alocasie sau Urechea-elefantului", "Pădurile tropicale din Asia de Sud-Est și Insulele Borneo"),
    "Aloe": ("Aloe sau Sabur", "Peninsula Arabică, Africa de Nord și Insulele Canare"),
    "Alstroemeria": ("Crinul Peruvian sau Crinul Incas", "America de Sud (Anzii Cordilieri din Chile și Peru)"),
    "Amygdalus": ("Migdal decorativ", "Asia de Sud-Vest și Orientul Mijlociu"),
    "Ananas": ("Ananas ornamental", "America de Sud tropicală (Brazilia și Paraguay)"),
    "Anemone": ("Anemonă sau Floarea-vântului (Păștiță)", "Europa, China și Japonia (zonele împădurite și montane)"),
    "Anthurium": ("Flamingo sau Floarea-flamingo", "Pădurile tropicale din America Centrală și de Sud (Columbia, Ecuador)"),
    "Aphelandra": ("Afelandra sau Planta-zebră", "Pădurile tropicale atlantice din Brazilia"),
    "Aporocactus": ("Cactusul Coada-șobolanului", "Mexic (regiunile montane epifite)"),
    "Aquilegia": ("Căldărușă", "America de Nord, Europa și Asia temperată"),
    "Araucaria": ("Bradul de cameră (Pinul din Insula Norfolk)", "Insula Norfolk (Oceanul Pacific de Sud)"),
    "Ardisia": ("Ardisia sau Pomul de Crăciun cu bobițe", "Asia de Est și de Sud-Est (Japonia, China, Coreea)"),
    "Artemisia": ("Pelin argintiu decorativ", "America de Nord și Eurasia"),
    "Arundo": ("Trestie gigantă pestriță (Stuf ornamental)", "Bazinul Mediteranean și Asia de Sud-Vest"),
    "Asparagus": ("Asparagus sau Umbra-iepurelui", "Africa de Sud (regiunea Cape și Natal)"),
    "Aspidistra": ("Aspidistra sau Pana-cocoșului (Planta de fontă)", "Japonia, Taiwan și sudul Chinei"),
    "Asplenium": ("Feriga Cuib-de-pasăre sau Feriga de stâncă", "Regiunile tropicale din Asia, Australia și zonele stâncoase din Europa"),
    "Aster": ("Steluță de toamnă sau Ochiul-boului peren", "America de Nord (coasta de est a SUA și Canada)"),
    "Astilbe": ("Astilbe sau Spuma-mării", "Asia de Est (Japonia, China, Coreea)"),
    "Begonia": ("Begonie", "Regiunile tropicale și subtropicale din America de Sud, Africa și Asia"),
    "Berberis": ("Drăcilă ornamentală", "Europa, China și Japonia"),
    "Bergenia": ("Bergenia sau Floarea-de-piatră (Frunza-cizmarului)", "Asia Centrală și de Est (Siberia, Altai, Mongolia)"),
    "Betula": ("Mesteacăn alb", "Europa și Asia de Nord"),
    "Bidens": ("Bidens sau Roata-soarelui aurie", "America Centrală și Mexic"),
    "Billbergia": ("Billbergia sau Lacrimile-reginei", "America de Sud tropicală (Brazilia)"),
    "Blechnum": ("Feriga-palmier pitică (Scărița-muntelui)", "Noua Caledonie și insulele din Pacificul de Sud"),
    "Bougainvillea": ("Bughenvilea sau Floarea-de-hârtie", "America de Sud (Brazilia, Peru, Argentina)"),
    "Brassaia": ("Arborele-umbrelă (Schefflera)", "Australia de Nord-Est (Queensland) și Noua Guinee"),
    "Browallia": ("Brovalia sau Floarea-safir", "Pădurile tropicale din America de Sud (Columbia, Peru)"),
    "Brunfelsia": ("Brunfelsia sau Ieri-Azi-Mâine", "Brazilia și insulele tropicale din America"),
    "Buddleia": ("Liliacul de vară sau Arborele-fluturilor", "China Centrală și de Vest, Japonia"),
    "Buxus": ("Cimișir sau Merișor turcesc", "Europa de Sud, Africa de Nord și Asia de Vest"),
    "Caladium": ("Caladium sau Aripa-îngerului (Inima-lui-Iisus)", "Bazinul Amazonian din America de Sud (Brazilia)"),
    "Calathea": ("Calatea sau Planta-păun (Planta care se roagă)", "Pădurile tropicale din Brazilia și America Centrală"),
    "Calceolaria": ("Calceolaria sau Papucii-doamnei", "America de Sud (Anzii din Chile și Peru)"),
    "Calibrachoa": ("Milioane de Clopoței (Million Bells)", "America de Sud (Brazilia, Argentina, Uruguay)"),
    "Callisia": ("Calisia sau Răcorel târâtor", "America Centrală și de Sud"),
    "Camellia": ("Camelie sau Trandafirul japonez", "Asia de Est (Japonia, Coreea și China)"),
    "Campanula": ("Clopoței de grădină", "Europa (inclusiv Munții Carpați) și Asia temperată"),
    "Campsis": ("Trâmbița sau Luleaua-turcului", "America de Nord (sud-estul Statelor Unite)"),
    "Capsicum": ("Ardei decorativ în ghiveci", "America Centrală și de Sud"),
    "Carex": ("Rogoz ornamental pendul", "Europa, Africa de Nord și Asia de Vest"),
    "Carpinus": ("Carpen comun", "Europa Centrală și de Sud, Caucaz"),
    "Caryopteris": ("Barba-albastră (Spirea albastră)", "Asia de Est (China, Japonia și Coreea)"),
    "Caryota": ("Palmierul Coada-de-pește", "Asia de Sud-Est (India, Malaezia, Indonezia)"),
    "Castanea": ("Castan comestibil", "Europa de Sud, Bazinul Mediteranean și Asia Mică"),
    "Catalpa": ("Catalpă sau Arborele-de-trabuc", "America de Nord (sud-estul Statelor Unite)"),
    "Catharanthus": ("Saschiu de Madagascar (Vinca roz)", "Madagascar"),
    "Cedrus": ("Cedru", "Munții Atlas (Africa de Nord), Liban și Himalaya"),
    "Celosia": ("Creasta-cocoșului", "Regiunile tropicale din Asia și Africa"),
    "Celtis": ("Sâmbovină americană", "America de Nord"),
    "Centaurea": ("Albăstrea perenă roz", "Caucaz, Armenia și Turcia de Nord-Est"),
    "Cerasus": ("Cireș japonez ornamental", "Japonia, Coreea și China"),
    "Cercis": ("Arborele lui Iuda", "Bazinul Mediteranean și Europa de Sud-Est"),
    "Ceropegia": ("Ceropegia sau Șiragul-de-inimi", "Africa de Sud (Africa Australă, Zimbabwe)"),
    "Chaenomeles": ("Gutui japonez ornamental", "Japonia"),
    "Chamaecyparis": ("Chiparos fals (Chiparos de California / Sawara)", "America de Nord (Oregon, California) și Japonia"),
    "Chamaedorea": ("Palmierul de salon (Palmierul de cameră)", "Pădurile tropicale din Mexic și Guatemala"),
    "Chelidonium": ("Rostopască cu flori bătute", "Europa și Asia de Vest"),
    "Chlorophytum": ("Voalul-miresei sau Plăntuța-păianjen (Crinul verde)", "Africa de Sud"),
    "Chrysalidocarpus": ("Palmierul Areca sau Palmierul-fluture", "Madagascar"),
    "Chrysanthemum": ("Crizantemă sau Tufănică de toamnă", "Asia de Est (China și Japonia)"),
    "Cissus": ("Viță de apartament (Cissus)", "America Centrală și de Sud tropicală"),
    "Citrus": ("Lămâi ornamental de interior", "Asia de Sud și de Sud-Est (India, China)"),
    "Clematis": ("Clematită", "Europa, Asia de Est și America de Nord"),
    "Clerodendrum": ("Clerodendrum sau Lacrima-lui-Hristos", "Africa de Vest tropicală (din Nigeria până în Camerun)"),
    "Clivia": ("Clivia sau Crinul roșu de cameră", "Africa de Sud (regiunea Natal)"),
    "Codiaeum": ("Croton sau Mantaua-lui-Iosif", "Indonezia, Malaezia, Australia de Nord și Insulele Pacificului"),
    "Codonanthe": ("Codonante", "America Centrală și de Sud (pădurile tropicale)"),
    "Convallaria": ("Lăcrămioară sau Mărgăritar", "Europa și Asia temperată"),
    "Cordyline": ("Cordyline sau Palmierul-crin", "Asia de Sud-Est, Australia și Insulele Pacificului"),
    "Cornus": ("Sânger ornamental (Corn)", "Siberia, China de Nord și Coreea"),
    "Cortaderia": ("Iarba de Pampas", "America de Sud (Argentina, Brazilia, Uruguay)"),
    "Corylus": ("Alun turcesc", "Europa de Sud-Est (inclusiv România), Balcani și Asia Mică"),
    "Corynocarpus": ("Laurul din Noua Zeelandă (Karaka)", "Noua Zeelandă"),
    "Cotinus": ("Scumpie sau Arborele-de-fum", "Europa de Sud, Europa Centrală și Asia până în China"),
    "Cotoneaster": ("Bârcoace", "China de Vest și Himalaya"),
    "Crassula": ("Arborele de jad sau Planta banilor", "Africa de Sud și Mozambic"),
    "Cryptanthus": ("Criptantus sau Steaua-pământului", "Brazilia de Est"),
    "Ctenanthe": ("Ctenante", "Brazilia (pădurile tropicale atlantice)"),
    "Cupressocyparis": ("Chiparos Leyland", "Hibrid britanic între specii din America de Nord"),
    "Cupressus": ("Chiparos de Arizona", "Sud-vestul Americii de Nord (Arizona, New Mexico și nordul Mexicului)"),
    "Cycas": ("Cicas sau Palmierul-ferigă japonez", "Sudul Japoniei (Insulele Ryukyu) și sud-estul Chinei"),
    "Cyclamen": ("Ciclamen sau Pâinea-porcului", "Bazinul Mediteranean de Est, Grecia și Asia Mică"),
    "Cydonia": ("Gutui", "Caucaz, Persia și Asia de Sud-Vest"),
    "Cymbidium": ("Orhidee Cymbidium (Orhideea-barcă)", "Regiunile montane din Himalaya, China, Japonia și Australia"),
    "Cyperus": ("Papură de cameră sau Planta-umbrelă (Ciperus)", "Africa de Est și Madagascar"),
    "Cytisus": ("Drobiță sau Mătura-verde aurie", "Europa de Vest și Centrală"),
    "Davallia": ("Feriga Laba-iepurașului", "Insulele Fiji, Australia și Asia de Sud-Est"),
    "Delphinium": ("Nemțișor de grădină peren (Delphinium)", "Emisfera Nordică (Europa și Asia)"),
    "Deutzia": ("Deuție sau Floarea-miresei", "Japonia și China"),
    "Dianthus": ("Garofiță de grădină", "Europa și Bazinul Mediteranean"),
    "Dicentra": ("Cerceii-doamnei sau Inimă-sângerândă", "Asia de Est (Siberia, nordul Chinei, Coreea și Japonia)"),
    "Dieffenbachia": ("Diefenbachia", "America Centrală și de Sud tropicală (Brazilia, Columbia)"),
    "Digitalis": ("Degețel peren", "Europa de Vest și Centrală (hibrid stabilizat)"),
    "Dionaea": ("Capcana-muștei Venus", "America de Nord (mlaștinile din Carolina de Nord și de Sud, SUA)"),
    "Dizygotheca": ("Dizigoteca sau Aralia falsă", "Noua Caledonie (Oceanul Pacific)"),
    "Doronicum": ("Iarba-ciutei", "Europa de Vest și de Sud"),
    "Dracaena": ("Dracenă sau Arborele-dragonului", "Africa tropicală și Insulele Canare"),
    "Drosera": ("Roua-cerului (Plantă carnivoră)", "Asia de Sud-Est, Australia și Noua Zeelandă"),
    "Dryopteris": ("Ferigă comună de pădure", "Europa, Asia și America de Nord"),
    "Dypsis": ("Palmierul Areca sau Palmierul-fluture", "Madagascar"),
    "Echeveria": ("Eșeveria sau Trandafirul de piatră mexican", "Mexic și America Centrală"),
    "Echinacea": ("Echinacea", "America de Nord (prerii din estul și centrul SUA)"),
    "Echinopsis": ("Cactusul-arici de mare", "America de Sud (Argentina, sudul Braziliei, Uruguay)"),
    "Elaeagnus": ("Salcie mirositoare", "Asia Centrală și de Vest"),
    "Epimedium": ("Floarea-elfilor", "Japonia, Coreea și China"),
    "Epipremnum": ("Potos sau Iedera-diavolului", "Insulele Solomon (Polinezia Franceză)"),
    "Eremurus": ("Crinul-stepelor sau Coada-vulpii de grădină", "Asia Centrală (Himalaya, Pamir, Turkestan)"),
    "Erica": ("Iarbă-neagră de iarnă (Erica)", "Munții Alpi și Europa Centrală și de Sud"),
    "Euonymus": ("Salbă moale / Salbă târâtoare", "Japonia, Coreea și China"),
    "Euphorbia": ("Euforbie sau Laptele-câinelui (Steaua Crăciunului)", "Mexic (pentru Poinsettia) și Europa (pentru speciile perene)"),
    "Exacum": ("Violetă persană", "Insula Socotra (Oceanul Indian / Yemen)"),
    "Fagus": ("Fag european", "Europa Centrală, de Vest și de Sud-Est (inclusiv România)"),
    "Fatshedera": ("Fatsedera sau Iedera-arbore", "Hibrid horticol creat în Franța (Fatsia japonica × Hedera helix)"),
    "Fatsia": ("Fatsia sau Aralia japoneză", "Japonia de Sud și Coreea de Sud"),
    "Faucaria": ("Faucaria sau Fălcile-tigrului", "Africa de Sud (provincia Cape)"),
    "Ficus": ("Ficus sau Smochin", "Asia de Sud și de Sud-Est, Africa tropicală și Bazinul Mediteranean"),
    "Filipendula": ("Crețușcă roșie de preerie", "America de Nord (estul și centrul SUA)"),
    "Fittonia": ("Fitonia sau Planta-mozaic (Planta cu nervuri)", "Pădurile tropicale din America de Sud (Peru, Columbia)"),
    "Foeniculum": ("Fenicul decorativ bronz", "Bazinul Mediteranean"),
    "Forsythia": ("Forsiție sau Ploaia-de-aur", "Asia de Est (China și Balcani)"),
    "Fraxinus": ("Frasin comun", "Europa, Asia Mică și Caucaz"),
    "Freesia": ("Frezie parfumată", "Africa de Sud (provincia Cape)"),
    "Fuchsia": ("Cerceluș", "America Centrală și de Sud, Noua Zeelandă"),
    "Gaillardia": ("Fluturi de soare sau Gaillardia", "America de Nord"),
    "Gardenia": ("Gardenie sau Iasomie de Cape", "China de Sud, Japonia și Taiwan"),
    "Gazania": ("Gazania sau Floarea-comoară", "Africa de Sud"),
    "Gentiana": ("Ghințură sau Lumânărica-pământului", "Munții din Europa Centrală și de Sud-Est (inclusiv Carpați)"),
    "Geranium": ("Ciocul-berzei peren (Geranium de grădină)", "Europa și Munții Himalaya"),
    "Gerbera": ("Gerbera", "Africa de Sud (regiunea Transvaal)"),
    "Geum": ("Cerențel montan portocaliu", "Munții din Peninsula Balcanică și Bulgaria"),
    "Ginkgo": ("Arborele Ginkgo sau Arborele-pagodelor", "China de Sud-Est"),
    "Gloriosa": ("Crinul-flăcărilor sau Crinul cățărător", "Africa tropicală și Asia de Sud"),
    "Glycyrrhiza": ("Lemn-dulce", "Europa de Sud-Est, Bazinul Mediteranean și Asia de Vest"),
    "Grevillea": ("Stejarul de mătase australian", "Australia de Est (New South Wales și Queensland)"),
    "Guzmania": ("Guzmania", "Pădurile tropicale din America Centrală și de Sud"),
    "Gymnocalycium": ("Cactusul-rubin (Cactusul-lună)", "America de Sud (Paraguay și Argentina)"),
    "Gypsophila": ("Floarea-miresei", "Europa de Est, Caucaz și Siberia"),
    "Haworthia": ("Havortia sau Planta-perlată", "Africa de Sud"),
    "Hedera": ("Iederă", "Europa, Insulele Canare și Caucaz"),
    "Helianthus": ("Floarea-soarelui perenă", "America de Nord"),
    "Helichrysum": ("Imortelă perenă (Siminoc)", "Europa și Asia de Vest"),
    "Helleborus": ("Spânz sau Trandafirul Crăciunului", "Munții Alpi, Carpați, Balcani și Turcia"),
    "Hemerocallis": ("Crin de o zi", "Asia de Est (China, Coreea și Japonia)"),
    "Hibiscus": ("Trandafir chinezesc / Zămoșiță de grădină", "Asia de Est și de Sud-Est (China, India)"),
    "Hippeastrum": ("Crin de iarnă sau Amaryllis de apartament", "Regiunile tropicale și subtropicale din America de Sud"),
    "Hippophae": ("Cătină albă", "Europa și Asia temperată"),
    "Hosta": ("Hosta sau Crinul de toamnă (Funkia)", "Asia de Est (Japonia, China și Coreea)"),
    "Howea": ("Palmierul Kentia (Palmierul Paradisului)", "Insula Lord Howe (Australia)"),
    "Hoya": ("Floarea de ceară (Hoya)", "Asia de Sud-Est, India și Polinezia"),
    "Hydrangea": ("Hortensie", "America de Nord și Asia de Est (Japonia, China)"),
    "Hypericum": ("Pojarniță ornamentală (Sunătoare decorativă)", "Europa de Sud-Est și Asia Mică"),
    "Hypoestes": ("Hipoestes sau Planta cu pistrui", "Madagascar, Africa de Sud și Asia de Sud-Est"),
    "Ilex": ("Laur englezesc sau Ilice", "Europa de Vest și de Sud, Africa de Nord și Asia de Sud-Vest"),
    "Impatiens": ("Sporul-casei sau Balsamină", "Africa de Est (Zanzibar, Kenya) și Asia de Sud (Sri Lanka)"),
    "Iris": ("Stânjenel sau Iris", "Europa, Asia Centrală și America de Nord"),
    "Ixora": ("Ixora sau Flacăra-pădurii", "India de Sud și Sri Lanka"),
    "Jasminum": ("Iasomie", "China și Asia de Sud-Est"),
    "Juglans": ("Nuc negru american", "America de Nord (estul și centrul Statelor Unite)"),
    "Juniperus": ("Ienupăr", "Emisfera Nordică (Europa, Asia și America de Nord)"),
    "Justicia": ("Planta-crevete (Coroana regală)", "Mexic"),
    "Kalanchoe": ("Kalanchoe", "Madagascar"),
    "Kerria": ("Teișor sau Trandafirul galben japonez", "China, Japonia și Coreea"),
    "Kniphofia": ("Făclia-stepelor sau Crinul-torță", "Africa de Sud"),
    "Koelreuteria": ("Arborele de săpun (Oțetar galben)", "China de Nord și Coreea"),
    "Lamium": ("Urzică moartă pătată", "Europa și Asia de Vest"),
    "Lantana": ("Lantană", "Regiunile tropicale din America Centrală și de Sud"),
    "Larix": ("Larice sau Zadă", "Munții Alpi și Carpați (Europa Centrală)"),
    "Lathyrus": ("Măzăriche de primăvară (Săgeata-pădurii)", "Europa și Siberia"),
    "Lavandula": ("Lavandă sau Levănțică", "Bazinul Mediteranean"),
    "Liatris": ("Steaua-strălucitoare (Liatris)", "America de Nord (preriile din estul SUA)"),
    "Ligustrum": ("Lemn-câinesc", "Japonia, Coreea și Europa"),
    "Lilium": ("Crin", "Europa, Asia și America de Nord"),
    "Liriodendron": ("Arborele cu lalele (Tulipier)", "America de Nord (estul Statelor Unite)"),
    "Lithops": ("Pietre vii (Lithops)", "Deșerturile din Africa de Sud și Namibia"),
    "Livistona": ("Palmierul-evantai australian", "Australia de Sud-Est"),
    "Lobelia": ("Lobelia perenă stacojie", "America de Nord"),
    "Lonicera": ("Caprifoi sau Mâna-Maicii-Domnului", "China, Japonia și America de Nord"),
    "Lotus": ("Ghizdei din Canare (Ciocul-papagalului)", "Insulele Canare (Tenerife)"),
    "Lupinus": ("Lupin de grădină", "America de Nord (vestul SUA)"),
    "Lychnis": ("Curcubeu sau Floarea-lui-Jovis", "Europa de Sud-Est, Munții Alpi și Asia de Vest"),
    "Lygodium": ("Ferigă cățărătoare japoneză", "Asia de Est și tropicală (Japonia, China, India)"),
    "Lysimachia": ("Gălbenele de pădure (Iarba-boierului)", "Europa Centrală și de Sud-Est, Turcia"),
    "Magnolia": ("Magnolie", "Japonia și China"),
    "Mahonia": ("Mahonie", "America de Nord (coasta de vest, din Columbia Britanică până în California)"),
    "Malva": ("Nalbă moscata", "Europa și Asia de Sud-Vest"),
    "Mammillaria": ("Cactusul-pernă (Mammillaria)", "Mexic și sud-vestul Statelor Unite"),
    "Mandevilla": ("Dipladenia sau Iasomia braziliană (Mandevilla)", "America de Sud tropicală (Brazilia)"),
    "Maranta": ("Maranta sau Planta care se roagă", "Pădurile tropicale din Brazilia"),
    "Melianthus": ("Floarea-de-miere africană", "Africa de Sud"),
    "Mentha": ("Mentă aromată pestriță", "Europa de Sud și de Vest, Bazinul Mediteranean"),
    "Metasequoia": ("Metasequoia sau Arborele-mamut chinezesc", "China Centrală (provincia Sichuan și Hubei)"),
    "Microlepia": ("Ferigă dantelată (Microlepia)", "Regiunile tropicale din Asia și Polinezia"),
    "Mimulus": ("Crețișoară maimuță (Floarea-mim)", "America de Nord și de Sud (Anzii din Chile)"),
    "Mirabilis": ("Frumoasa-nopții (Noptiță)", "America tropicală (Peru și Mexic)"),
    "Monstera": ("Monstera sau Filodendron cu frunze rupte", "Pădurile tropicale din Mexic până în Panama și America de Sud"),
    "Morus": ("Dud alb", "China de Nord și Asia Centrală"),
    "Murraya": ("Iasomie portocalie (Murraya)", "Asia de Sud și de Sud-Est, Australia"),
    "Nematanthus": ("Planta-peștișor de aur (Nematanthus)", "Brazilia de Sud-Est"),
    "Neoregelia": ("Neoregelia sau Inima-înflăcărată", "Pădurile tropicale din Brazilia"),
    "Nepenthes": ("Planta-ulcior carnivoră (Nepenthes)", "Insula Borneo, Malaezia și Indonezia"),
    "Nephrolepis": ("Ferigă de cameră (Feriga sabie de Boston)", "Regiunile tropicale din America, Africa și Asia"),
    "Nerium": ("Leandru", "Bazinul Mediteranean și Asia de Sud"),
    "Nertera": ("Nertera sau Mărgeanul de pernă", "America de Sud (Anzii), Noua Zeelandă și Australia"),
    "Nicotiana": ("Regina-nopții", "America de Sud (sudul Braziliei, Argentina și Uruguay)"),
    "Oenothera": ("Luminița-zilei perenă", "America de Nord (estul SUA)"),
    "Olea": ("Măslin european", "Bazinul Mediteranean"),
    "Oncidium": ("Orhideea Dansatoare (Oncidium)", "America Centrală și de Sud tropicală"),
    "Opuntia": ("Limba-soacrei (Cactusul Ureche-de-iepure)", "Mexic Central și de Nord"),
    "Origanum": ("Șovârf sau Oregano ornamental", "Bazinul Mediteranean și Europa"),
    "Osteospermum": ("Margaretă africană", "Africa de Sud"),
    "Oxalis": ("Trifoiul cu patru foi (Măcrișul-norocos)", "Mexic"),
    "Pachysandra": ("Covorul-verde japonez (Pachysandra)", "Japonia și China"),
    "Pachystachys": ("Spicul-auriu sau Planta-acadea", "Peru și nordul Americii de Sud"),
    "Paeonia": ("Bujor", "Asia Centrală și de Est (China, Siberia) și Europa de Sud"),
    "Pandanus": ("Pandanus sau Pinul spiralat", "Insulele din Oceanul Pacific și Polinezia"),
    "Pandorea": ("Vița-Wonga sau Iasomia de Bower", "Australia de Est"),
    "Paphiopedilum": ("Orhideea Papucul-doamnei", "Asia de Sud-Est (Himalaya, China, Indonezia)"),
    "Parrotia": ("Arborele de fier persan (Parotia)", "Nordul Iranului și Caucaz (Marea Caspică)"),
    "Parthenocissus": ("Viță sălbatică de Canada (Viță decorativă)", "America de Nord (estul și centrul SUA și Canada)"),
    "Passiflora": ("Floarea-pasiunii (Ceasornicul)", "America de Sud (Brazilia, Argentina, Paraguay)"),
    "Paulownia": ("Arborele Prințesei (Paulovnia)", "China Centrală și de Vest"),
    "Pelargonium": ("Mușcată", "Africa de Sud"),
    "Pellaea": ("Feriga-nasture", "Noua Zeelandă și Australia"),
    "Penstemon": ("Penstemon sau Clopoței mexicani", "America de Nord și Mexic"),
    "Pentas": ("Steaua egipteană", "Africa de Est și Peninsula Arabică (Yemen)"),
    "Peperomia": ("Peperomia", "Pădurile tropicale din Brazilia"),
    "Petunia": ("Petunie", "America de Sud (Argentina și Brazilia)"),
    "Phalaenopsis": ("Orhideea-fluture (Phalaenopsis)", "Asia de Sud-Est, Filipine și Australia de Nord"),
    "Philodendron": ("Filodendron", "Pădurile tropicale din America de Sud și Caraibe"),
    "Phlox": ("Brumărele de vară (Phlox)", "America de Nord (estul și centrul Statelor Unite)"),
    "Phoenix": ("Curmalul din Insulele Canare", "Insulele Canare"),
    "Physostegia": ("Planta-ascultătoare (Vârf-de-săgeată)", "America de Nord"),
    "Picea": ("Molid", "Europa, America de Nord și Balcani"),
    "Pilea": ("Planta-aluminiu (Pilea)", "Vietnam și sudul Chinei"),
    "Pinus": ("Pin", "Europa, Asia (Himalaya) și America de Nord"),
    "Piper": ("Piper ornamental de Borneo", "Indonezia (Insula Sulawesi și Borneo)"),
    "Platycerium": ("Feriga Coarnele-cerbului", "Australia, Noua Guinee și Indonezia"),
    "Platycladus": ("Tuia orientală (Arborele-vieții)", "China, Coreea și Orientul Îndepărtat"),
    "Plectranthus": ("Iedera suedeză (Planta-tămâie)", "Africa de Sud și Australia"),
    "Plumbago": ("Floarea-amorului (Plumbago albastru)", "Africa de Sud"),
    "Polypodium": ("Feriguță dulce (Feriga-albastră)", "America tropicală și de Nord"),
    "Polyscias": ("Arborele-scut (Poliscias)", "Insulele Pacificului și Asia de Sud-Est"),
    "Populus": ("Plop negru", "Europa, Africa de Nord și Asia de Vest"),
    "Portulaca": ("Floarea de piatră (Iarbă grasă)", "America de Sud (Argentina, sudul Braziliei, Uruguay)"),
    "Potentilla": ("Cinci-degete arbustiv (Potentilla)", "Emisfera Nordică (Europa, Asia și America de Nord)"),
    "Primula": ("Ciuboțica-cucului sau Primulă", "Europa (Munții Alpi, Carpați) și Asia (China, Himalaya)"),
    "Prunus": ("Cireș / Laur-cireș / Migdal pitic", "Europa, Asia Mică și China"),
    "Pulmonaria": ("Mierea-ursului sau Plămânărică", "Europa (inclusiv România) și Caucaz"),
    "Punica": ("Rodiul pitic ornamental", "Iran, Caucaz și nordul Indiei"),
    "Pyracantha": ("Pyracantha sau Spinul-lui-Hristos (Cătină de foc)", "Europa de Sud-Est și Asia Mică"),
    "Quercus": ("Stejar pedunculat", "Europa, Caucaz și Asia Mică"),
    "Ranunculus": ("Piciorul-cocoșului cu flori bătute (Butonul de aur)", "Europa și Asia temperată"),
    "Rebutia": ("Cactusul-coroniță (Rebutia)", "America de Sud (Anzii din Argentina și Bolivia)"),
    "Rheum": ("Rubarbă ornamentală cu frunze roșii", "China de Vest și Tibet"),
    "Rhipsalidopsis": ("Cactusul de Paște", "Brazilia de Sud-Est"),
    "Rhipsalis": ("Cactusul-vâsc", "America Centrală și de Sud, Africa tropicală"),
    "Rhododendron": ("Rododendron sau Azalee", "Asia de Est (China, Japonia) și America de Nord"),
    "Rhus": ("Oțetar roșu (Sumac)", "America de Nord (estul Canadei și SUA)"),
    "Robinia": ("Salcâm alb", "America de Nord (Munții Appalachi)"),
    "Rosa": ("Trandafir", "Asia, Europa și America de Nord"),
    "Ruellia": ("Petunie sălbatică braziliană (Ruellia)", "Brazilia"),
    "Saintpaulia": ("Violetă africană (Violetă de Usambara)", "Africa de Est (Munții Usambara din Tanzania)"),
    "Salix": ("Salcie", "Europa, Asia (China) și Siberia"),
    "Salvia": ("Salvie decorativă", "Brazilia (pentru S. confertiflora)"),
    "Sansevieria": ("Limba-soacrei sau Sabia-Sfântului-Gheorghe", "Africa de Vest tropicală (din Nigeria până în Congo)"),
    "Saxifraga": ("Ochii-șoricelului (Iarba-surzilor)", "Asia de Est (China, Japonia și Coreea)"),
    "Scabiosa": ("Mușcata-dracului galbenă (Sipică)", "Europa Centrală și de Est, Balcani și Caucaz"),
    "Schefflera": ("Arborele-umbrelă pitic (Schefflera)", "Taiwan și Insula Hainan (China)"),
    "Schizanthus": ("Floarea-fluture sau Orhideea-săracului", "Chile (America de Sud)"),
    "Schlumbergera": ("Crăciuniță sau Cactusul Crăciunului", "Munții de coastă din sud-estul Braziliei"),
    "Scindapsus": ("Potos argintiu (Iedera-diavolului satinată)", "Asia de Sud-Est (Malaezia, Indonezia, Filipine)"),
    "Sedum": ("Iarbă grasă (Floarea de piatră / Coada-măgărușului)", "Mexic (pentru S. burrito) și China/Coreea (pentru S. spectabile)"),
    "Selaginella": ("Struțișor sau Mușchiul-club", "America tropicală și Africa de Sud"),
    "Senecio": ("Cineraria de ghiveci", "Insulele Canare"),
    "Sinningia": ("Gloxinie", "Brazilia"),
    "Skimmia": ("Skimmia japoneză", "Japonia, China și Asia de Sud-Est"),
    "Solanum": ("Mărul-dragostei sau Cireșul de Ierusalim", "America de Sud (Brazilia și Peru)"),
    "Soleirolia": ("Salțeluța sau Lacrimile-bebelușului", "Insulele Corsica și Sardinia (Bazinul Mediteranean)"),
    "Solidago": ("Splinuță de grădină (Sânziene de toamnă)", "America de Nord"),
    "Sophora": ("Soforă sau Salcâmul japonez", "China și Coreea"),
    "Sorbus": ("Scoruș de munte", "Europa și Asia de Nord"),
    "Sparrmannia": ("Teiul de cameră african", "Africa de Sud și Madagascar"),
    "Spathiphyllum": ("Crinul-păcii (Spatifilum)", "Pădurile tropicale din Columbia și Venezuela"),
    "Spiraea": ("Cununiță", "Asia de Est (China, Japonia) și America de Nord"),
    "Stachys": ("Urechea-iepurelui (Jaleș lânos)", "Turcia, Armenia, Caucaz și Iran"),
    "Stapelia": ("Floarea-stea africană (Stapelia)", "Africa de Sud"),
    "Stephanotis": ("Iasomie de Madagascar (Floarea-miresei parfumată)", "Madagascar"),
    "Strelitzia": ("Pasărea-Paradisului (Streliția)", "Africa de Sud"),
    "Streptocarpus": ("Primulă de Cape (Streptocarpus)", "Africa de Sud și Africa de Est (Kenya, Tanzania)"),
    "Strobilanthes": ("Scutul-persan (Strobilantes)", "Myanmar (Birmania)"),
    "Stromanthe": ("Stromante Tricolor", "Pădurile tropicale din Brazilia"),
    "Symphoricarpos": ("Hurmuz roz (Cârmâz)", "America de Nord"),
    "Syringa": ("Liliac comun", "Peninsula Balcanică și România (sud-estul Europei)"),
    "Tamarix": ("Cătină roșie", "Europa de Sud-Est și Asia Mică"),
    "Tanacetum": ("Piretru roz (Margarete colorate)", "Caucaz și Asia de Sud-Vest"),
    "Taxodium": ("Chiparos de baltă", "America de Nord (sud-estul Statelor Unite, Florida și Louisiana)"),
    "Taxus": ("Tisă", "Europa, Africa de Nord și Asia de Vest"),
    "Thuja": ("Tuia", "America de Nord și Asia de Est"),
    "Tillandsia": ("Tilandsia sau Pana-roz (Planta-aerului)", "Pădurile tropicale din Ecuador și Peru"),
    "Tilia": ("Tei pucios (Tei cu frunza mică)", "Europa și Caucaz"),
    "Torenia": ("Torenia sau Floarea-de-gând (Panseluța de vară)", "Asia de Sud-Est (Vietnam, Thailanda, Cambodgia)"),
    "Tradescantia": ("Telegraf sau Răcorel vărgat (Zebrină)", "Mexic și America Centrală"),
    "Tropaeolum": ("Condurași pereni galbeni", "Munții Anzi din Chile și Argentina"),
    "Tulipa": ("Lalea", "Asia Centrală, Turcia și Bazinul Mediteranean"),
    "Ulmus": ("Ulm de câmp", "Europa, Africa de Nord și Asia de Sud-Vest"),
    "Valeriana": ("Odolean sau Valeriană", "Europa și Asia temperată"),
    "Verbascum": ("Lumânărică neagră", "Europa și Asia de Vest"),
    "Verbena": ("Verbină de Buenos Aires", "America de Sud (Argentina, Brazilia, Chile)"),
    "Viburnum": ("Călin ornamental (Buldene)", "Europa, China și Coreea"),
    "Vinca": ("Saschiu mare pestriț", "Bazinul Mediteranean și Europa de Sud"),
    "Vriesea": ("Vriesea sau Sabia-înflăcărată", "Venezuela, Guyana și Trinidad"),
    "Washingtonia": ("Palmierul-evantai californian", "Sud-vestul Statelor Unite (California, Arizona) și nord-vestul Mexicului"),
    "Weigela": ("Veigela", "Asia de Est (Japonia, China și Coreea)"),
    "Wisteria": ("Glicină chinezească", "China"),
    "Yucca": ("Yucca sau Palmierul-crin", "Mexic, America Centrală și sud-estul Statelor Unite"),
    "Zamioculcas": ("Planta ZZ sau Floarea de Smarald", "Africa de Est (Kenya, Zanzibar, Tanzania)"),
}

# Specific species overrides for Romanian name & Origin where multiple species exist in the same genus
SPECIES_OVERRIDES = {
    502: ("Alstroemeria Ligtu hibrizi - Crinul Peruvian sau Crinul Incas", "America de Sud (Anzii Cordilieri din Chile și Peru)"),
    497: ("Acanthus hungaricus - Talpa-ursului balcanică", "Peninsula Balcanică și România (Banat, Oltenia)"),
    498: ("Achillea filipendulina - Coada-șoricelului aurie", "Caucaz, Asia Centrală și Turcia"),
    499: ("Aciphylla squarrosa - Iarba-spadă neozeelandeză", "Noua Zeelandă"),
    500: ("Aegopodium podagraria Variegatum - Piciorul-caprei pestriț", "Europa și Asia temperată"),
    501: ("Ajuga reptans Atropurpurea - Vinerița purpurie", "Europa, Caucaz și Asia de Vest"),
    503: ("Anemone nemorosa 'Allenii' - Floarea-Paștelui albastră (Păștiță)", "Europa (pădurile de foioase)"),
    504: ("Anemone nemorosa 'Robinsoniana' - Floarea-Paștelui bleu-lavandă (Păștiță)", "Europa (pădurile de foioase)"),
    505: ("Anemone hupehensis var. japonica 'Bressingham Glow' - Anemonă japoneză de toamnă", "China Centrală, naturalizată în Japonia"),
    506: ("Anthurium andreanum - Floarea-flamingo", "Pădurile tropicale din Columbia și Ecuador"),
    507: ("Aquilegia canadensis - Căldărușă canadiană roșie-aurie", "America de Nord (estul Canadei și SUA)"),
    78: ("Araucaria heterophylla - Bradul de cameră (Pinul din Norfolk)", "Insula Norfolk (Oceanul Pacific de Sud)"),
    496: ("Artemisia ludoviciana 'Silver Queen' - Pelin argintiu american", "America de Nord"),
    508: ("Arundo donax var. versicolor - Trestie gigantă pestriță", "Bazinul Mediteranean și Asia de Sud-Vest"),
    509: ("Asparagus densiflorus 'Sprengeri' - Asparagus curgător (Umbra-iepurelui)", "Africa de Sud"),
    510: ("Asparagus densiflorus 'Meyers' - Asparagus Coada-motanului", "Africa de Sud"),
    511: ("Cuib de pasăre - Asplenium nidus", "Regiunile tropicale din Asia de Sud-Est, Australia și Africa de Est"),
    512: ("Asplenium trichomanes - Strașnic (Ferigă de stâncă)", "Europa, Asia și America de Nord (zone stâncoase și montane)"),
    513: ("Aster novi-belgii 'White Swan' - Steluță de toamnă albă", "America de Nord"),
    514: ("Aster novi-belgii 'Fellowship' - Steluță de toamnă roz", "America de Nord"),
    515: ("Aster novi-belgii 'Marie Ballard' - Steluță de toamnă albastră", "America de Nord"),
    516: ("Astilbe 'Montgomery' - Astilbe roșie (Spuma-mării)", "Asia de Est (hibrid Arendsii)"),
    517: ("Astilbe 'Irrlicht' - Astilbe albă (Spuma-mării)", "Asia de Est (hibrid Arendsii)"),
    518: ("Begonia 'Norah Bedson' - Begonie decorativă prin frunze", "America Centrală și Mexic (hibrid Rhizomatous)"),
    519: ("Begonia masoniana - Begonia Crucea-de-Fier", "Sudul Chinei și nordul Vietnamului"),
    520: ("Bergenia 'Ballawley' - Bergenia (Floarea-de-piatră)", "Asia Centrală și Himalaya"),
    521: ("Bidens ferulifolia - Bidens sau Roata-soarelui aurie", "Mexic și sud-vestul Statelor Unite"),
    522: ("Calathea makoyana - Calatea-păun (Planta-fereastră)", "Brazilia (statul Espírito Santo)"),
    523: ("Campanula glomerata 'Superba' - Clopoței aglomerați violet", "Europa și Asia temperată"),
    524: ("Carex pendula - Rogoz pendul gigant", "Europa, Africa de Nord și Asia de Vest"),
    525: ("Centaurea pulcherrima - Albăstrea perenă roz-argintie", "Caucaz și Anatolia"),
    526: ("Chelidonium majus 'Flore Pleno' - Rostopască cu flori bătute", "Europa și Asia de Vest"),
    537: ("Cyperus involucratus - Papură de cameră (Planta-umbrelă)", "Africa de Est și Madagascar"),
    550: ("Drosera spathulata - Roua-cerului (Plantă carnivoră)", "Asia de Sud-Est, Australia și Noua Zeelandă"),
    556: ("Euphorbia palustris - Alior de baltă (Laptele-câinelui de mlaștină)", "Europa și Asia de Vest"),
    557: ("Euphorbia cyparissias - Alior sau Laptele-câinelui", "Europa și Bazinul Mediteranean"),
    558: ("Filipendula rubra - Crețușcă roz de preerie", "America de Nord (estul și centrul SUA)"),
    559: ("Foeniculum vulgare 'Purpureum' - Fenicul bronz ornamental", "Bazinul Mediteranean"),
    560: ("Gaillardia aristata - Fluturi de soare pereni", "America de Nord"),
    561: ("Gazania rigens var. uniflora - Gazania sau Floarea-comoară", "Africa de Sud și Mozambic"),
    562: ("Gentiana asclepiadea - Lumânărica-pământului (Ghințură de pădure)", "Munții din Europa Centrală și de Sud-Est (inclusiv Carpați)"),
    563: ("Geranium himalayense 'Gravetye' - Ciocul-berzei de Himalaya", "Munții Himalaya"),
    564: ("Geranium 'Johnson's Blue' - Ciocul-berzei albastru", "Europa și Asia (hibrid G. himalayense × G. pratense)"),
    565: ("Geum borisii - Cerențel montan portocaliu", "Munții din Peninsula Balcanică"),
    566: ("Glycyrrhiza glabra - Lemn-dulce", "Europa de Sud-Est și Asia de Sud-Vest"),
    567: ("Gypsophila 'Rosenschleier' - Floarea-miresei roz târâtoare", "Europa și Asia temperată"),
    571: ("Helleborus niger - Spânz alb (Trandafirul Crăciunului)", "Munții Alpi și Apenini (Europa Centrală și de Sud)"),
    572: ("Helleborus orientalis - Spânz oriental (Trandafirul Postului Mare)", "Grecia, Turcia și Caucaz"),
    581: ("Hypoestes phyllostachya - Hipoestes sau Planta cu pistrui", "Madagascar"),
    582: ("Impatiens repens - Sporul-casei târâtor galben", "Sri Lanka"),
    583: ("Iris confusa - Irisul-bambus", "China de Vest (provincia Sichuan și Yunnan)"),
    584: ("Iris afghanica - Iris afgan", "Munții Hindu Kush (Afganistan)"),
    587: ("Iris pseudacorus - Stânjenel de baltă galben", "Europa, Africa de Nord și Asia de Vest"),
    592: ("Lathyrus vernus 'Alboroseus' - Măzăriche de primăvară bicoloră", "Europa și Siberia"),
    593: ("Liatris spicata - Steaua-strălucitoare (Pana-indiană)", "America de Nord (estul SUA)"),
    598: ("Lychnis flos-jovis - Floarea-lui-Jovis", "Munții Alpi"),
    599: ("Lychnis coronaria - Curcubeu sau Floarea-cununii", "Europa de Sud-Est și Asia de Vest"),
    600: ("Lysimachia punctata - Gălbenele de pădure (Iarba-boierului)", "Europa Centrală și de Sud-Est"),
    601: ("Malva moschata - Nalbă moscata", "Europa și Asia de Sud-Vest"),
    602: ("Maranta leuconeura var. erythroneura - Maranta Tricolor (Planta care se roagă)", "Pădurile tropicale din Brazilia"),
    603: ("Maranta leuconeura var. kerchoveana - Maranta Laba-iepurelui (Planta care se roagă)", "Pădurile tropicale din Brazilia"),
    604: ("Melianthus major - Floarea-de-miere africană", "Africa de Sud"),
    605: ("Mentha suaveolens 'Variegata' - Mentă-măr pestriță (Mentă ananas)", "Europa de Sud și de Vest"),
    609: ("Nepenthes x hookeriana - Planta-ulcior carnivoră", "Insula Borneo, Malaezia și Indonezia"),
    612: ("Oenothera fruticosa 'Fyrverkeri' - Luminița-zilei galbenă", "America de Nord"),
    613: ("Origanum laevigatum 'Herrenhausen' - Șovârf ornamental purpuriu", "Cipru, Turcia și Siria"),
    614: ("Origanum vulgare 'Aureum' - Șovârf auriu (Oregano auriu)", "Europa și Bazinul Mediteranean"),
    615: ("Osteospermum 'Buttermilk' - Margaretă africană galben-pai", "Africa de Sud"),
    616: ("Ranunculus bulbosus 'Speciosus' - Piciorul-cocoșului bulbos cu flori bătute", "Europa"),
    617: ("Ranunculus acris 'Flore Pleno' - Piciorul-cocoșului cu flori bătute (Butonul de aur)", "Europa și Asia temperată"),
    618: ("Rheum palmatum 'Atrosanguineum' - Rubarbă ornamentală roșie", "China de Vest și Tibet"),
    619: ("Ruellia devosiana - Petunie sălbatică braziliană vărgată", "Brazilia"),
    620: ("Valeriana officinalis - Odolean sau Valeriană", "Europa și Asia temperată"),
    621: ("Verbascum nigrum - Lumânărică neagră", "Europa și Siberia"),
    622: ("Verbena bonariensis - Verbină de Buenos Aires", "America de Sud (Argentina, Brazilia, Chile)"),
    623: ("Tanacetum coccineum 'Brenda' - Piretru roz-carmin", "Caucaz și Asia de Sud-Vest"),
    624: ("Tropaeolum polyphyllum - Condurași pereni galbeni", "Munții Anzi din Chile și Argentina"),
    625: ("Salvia confertiflora - Salvie braziliană catifelată", "Brazilia"),
    626: ("Scabiosa ochroleuca - Sipică galbenă (Mușcata-dracului)", "Europa Centrală și de Est, Balcani"),
    628: ("Sedum spectabile 'Brilliant' - Iarbă grasă de toamnă (Verzișoară)", "China și Coreea"),
    629: ("Selaginella kraussiana - Struțișor târâtor", "Africa de Sud și Insulele Azore"),
    630: ("Solidago 'Goldenmosa' - Splinuță de grădină aurie", "America de Nord"),
    631: ("Stachys byzantina 'Silver Carpet' - Urechea-iepurelui argintie", "Turcia, Armenia și Caucaz"),
    632: ("Streptocarpus caulescens - Streptocarpus cu tulpină (Violetă-noduroasă)", "Africa de Est (Kenya și Tanzania)"),
    637: ("Paeonia officinalis 'Rubra Plena' - Bujor românesc de grădină roșu bătut", "Europa de Sud și de Sud-Est"),
    648: ("Physostegia virginiana subsp. speciosa 'Variegata' - Planta-ascultătoare pestriță", "America de Nord"),
    652: ("Polypodium glycyrrhiza - Feriga Lemn-dulce", "Coasta de vest a Americii de Nord (din Alaska până în California)"),
    654: ("Primula auricula 'Mark' - Urechea-ursului (Ciuboțica-cucului alpină)", "Munții Alpi și Carpați"),
    655: ("Primula elatior - Ciuboțica-cucului de munte", "Europa și Asia de Vest"),
    656: ("Primula veris - Ciuboțica-cucului medicinală", "Europa și Asia temperată"),
    657: ("Pulmonaria saccharata - Mierea-ursului pătată (Plămânărică)", "Europa (Franța și Italia)"),
    658: ("Pulmonaria angustifolia 'Mawson's Variety' - Plămânărică albastră cu frunza îngustă", "Europa Centrală și de Est"),
    472: ("Molid obișnuit - Picea abies", "Europa de Nord, Centrală și Munții Carpați"),
}

def get_genus(latin_name):
    cleaned = latin_name.replace("x ", "").replace("X ", "").strip()
    m = re.match(r"^([A-Za-z]+)", cleaned)
    return m.group(1).capitalize() if m else ""

def build_dual_name(plant, clean_latin, ro_popular):
    pid = plant['id']
    if pid in SPECIES_OVERRIDES:
        return SPECIES_OVERRIDES[pid][0]

    orig_name = plant.get('name', '').strip()
    # Fix encoding artifacts
    orig_name = orig_name.replace('â€™', "'").replace("''", "'").replace('"', "'")
    # Make idempotent if already contains ' - '
    if ' - ' in orig_name:
        orig_name = orig_name.split(' - ')[0].strip()
    # Strip any previously added ' (Latin name)' if orig_name was genus
    orig_name = re.sub(r'\s*\([A-Z][a-z]+.*?\)$', '', orig_name).strip()

    clean_latin_disp = clean_latin.replace("''", "'").replace('"', "'")

    # Determine if orig_name starts with the Latin genus
    genus = get_genus(clean_latin)
    orig_first_word = re.sub(r'[^A-Za-zĂÂÎȘȚăâîșț]', ' ', orig_name).split()[0] if orig_name else ''

    # If the original name is identical to the Latin name (like most #323-#658):
    if orig_name.lower().replace("'", "").replace('"', '') == clean_latin_disp.lower().replace("'", "").replace('"', ''):
        return f"{clean_latin_disp} - {ro_popular}"

    # If original name starts with Latin genus and has no Romanian translation yet
    if genus and orig_first_word.lower() == genus.lower():
        # If it's just the genus name (e.g., "Aeonium", "Begonia", "Faucaria", "Guzmania", "Peperomia", "Pilea")
        if orig_name.lower() == genus.lower():
            return f"{clean_latin_disp} - {ro_popular}"
        # If it already has a comma and Romanian explanation (e.g. "Acalifa, coada de vulpe")
        if ',' in orig_name:
            return f"{orig_name} - {clean_latin_disp}"
        # If it is a Latin species/cultivar name (e.g. "Chamaecyparis lawsoniana 'Alumigold'", "Hosta Krossa Regal")
        return f"{orig_name} - {ro_popular}"

    # Otherwise, original name starts with Romanian popular name (preserving its A-Z letter!)
    return f"{orig_name} - {clean_latin_disp}"

def fix_romanian_text(text):
    if not text:
        return ""
    t = text.strip()
    t = t.replace('â€™', "'").replace("''", "'")
    # Fix common typos from old scraped database
    replacements = [
        (r'\bPlanta\b', 'Plantă'),
        (r'\bplanta\b', 'plantă'),
        (r'\bInguste\b', 'Înguste'),
        (r'\binguste\b', 'înguste'),
        (r'\blanceolete\b', 'lanceolate'),
        (r'\btrompetifome\b', 'trompetiforme'),
        (r'\bSpectaculoasa\b', 'Spectaculoasă'),
        (r'\bspectaculoasa\b', 'spectaculoasă'),
        (r'\bInfloresc\b', 'Înfloresc'),
        (r'\binfloresc\b', 'înfloresc'),
        (r'\bInfloreste\b', 'Înflorește'),
        (r'\binfloreste\b', 'înflorește'),
        (r'\bvarf\b', 'vârf'),
        (r'\bVarf\b', 'Vârf'),
        (r'\bfrunze\b', 'frunze'),
        (r'\bcreste\b', 'crește'),
        (r'\bCreste\b', 'Crește'),
        (r'\btufa\b', 'tufă'),
        (r'\bTufa\b', 'Tufă'),
        (r'\brozeta\b', 'rozetă'),
        (r'\bRozeta\b', 'Rozetă'),
        (r'\binchis\b', 'închis'),
        (r'\bdeschis\b', 'deschis'),
        (r'\bcarnoase\b', 'cărnoase'),
        (r'\bCarnoase\b', 'Cărnoase'),
        (r'\bprimavara\b', 'primăvara'),
        (r'\bPrimavara\b', 'Primăvara'),
        (r'\bpana\b', 'până'),
        (r'\binaltime\b', 'înălțime'),
        (r'\bInaltime\b', 'Înălțime'),
        (r'\blasatari\b', 'lăstari'),
        (r'\blastari\b', 'lăstari'),
        (r'\btaratoare\b', 'târâtoare'),
        (r'\bcataratoare\b', 'cățărătoare'),
        (r'\bcurgatoare\b', 'curgătoare'),
        (r'\bradacini\b', 'rădăcini'),
        (r'\bimperecheate\b', 'împerecheate'),
        (r'\bmarginea\b', 'marginea'),
        (r'\bdintata\b', 'dințată'),
        (r'\bvariegata\b', 'variegată'),
        (r'\bnuante\b', 'nuanțe'),
        (r',\s*([a-zA-ZăâîșțĂÂÎȘȚ])', r', \1'),
    ]
    for pat, rep in replacements:
        t = re.sub(pat, rep, t)
    return t

def main():
    with open('data/plants.json', 'r', encoding='utf-8') as f:
        plants = json.load(f)
    products = load_products()

    # Tropical / Houseplant genera (even if tagged Perene or Arbusti in legacy DB)
    INDOOR_TROPICAL_GENERA = {
        "Abutilon", "Acalypha", "Achimenes", "Adiantum", "Aechmea", "Aeonium",
        "Aeschynanthus", "Agave", "Aglaonema", "Allamanda", "Alocasia", "Aloe",
        "Ananas", "Anthurium", "Aphelandra", "Aporocactus", "Araucaria", "Ardisia",
        "Asparagus", "Aspidistra", "Asplenium", "Begonia", "Billbergia", "Blechnum", "Bougainvillea",
        "Brassaia", "Browallia", "Brunfelsia", "Caladium", "Calathea", "Calceolaria",
        "Callisia", "Camellia", "Capsicum", "Caryota", "Catharanthus", "Ceropegia",
        "Chamaedorea", "Chlorophytum", "Chrysalidocarpus", "Cissus", "Citrus",
        "Clerodendrum", "Clivia", "Codiaeum", "Codonanthe", "Cordyline", "Corynocarpus",
        "Crassula", "Cryptanthus", "Ctenanthe", "Cycas", "Cyclamen", "Cymbidium",
        "Cyperus", "Davallia", "Dieffenbachia", "Dionaea", "Dizygotheca", "Dracaena",
        "Drosera", "Dypsis", "Echeveria", "Echinopsis", "Epipremnum", "Exacum",
        "Fatshedera", "Fatsia", "Faucaria", "Fittonia", "Fuchsia", "Gardenia",
        "Gerbera", "Grevillea", "Guzmania", "Gymnocalycium", "Haworthia", "Hippeastrum",
        "Howea", "Hoya", "Hypoestes", "Impatiens", "Ixora", "Justicia", "Kalanchoe",
        "Lantana", "Lithops", "Livistona", "Lotus", "Lygodium", "Mammillaria",
        "Mandevilla", "Maranta", "Microlepia", "Monstera", "Murraya", "Nematanthus",
        "Neoregelia", "Nepenthes", "Nephrolepis", "Nerium", "Nertera", "Oncidium",
        "Opuntia", "Oxalis", "Pachystachys", "Pandanus", "Pandorea", "Paphiopedilum",
        "Passiflora", "Pelargonium", "Pellaea", "Pentas", "Peperomia", "Phalaenopsis",
        "Philodendron", "Phoenix", "Pilea", "Piper", "Platycerium", "Plectranthus",
        "Plumbago", "Polypodium", "Polyscias", "Punica", "Rebutia", "Rhipsalidopsis", "Rhipsalis",
        "Ruellia", "Saintpaulia", "Sansevieria", "Schefflera", "Schlumbergera",
        "Scindapsus", "Senecio", "Sinningia", "Solanum", "Soleirolia", "Sparrmannia",
        "Spathiphyllum", "Stapelia", "Stephanotis", "Strelitzia", "Streptocarpus",
        "Strobilanthes", "Stromanthe", "Tillandsia", "Torenia", "Tradescantia",
        "Vriesea", "Washingtonia", "Yucca", "Zamioculcas"
    }

    # Half-hardy / Tender Perennials & Bulbs (need winter mulch or indoor tuber storage)
    TENDER_GARDEN_GENERA = {
        "Alstroemeria", "Arundo", "Bidens", "Calibrachoa", "Caryopteris", "Cortaderia", "Freesia",
        "Gazania", "Gloriosa", "Kniphofia", "Lobelia", "Melianthus", "Mimulus", "Mirabilis",
        "Nicotiana", "Osteospermum", "Petunia", "Portulaca", "Salvia", "Schizanthus",
        "Tropaeolum", "Verbena", "Olea"
    }

    updated_count = 0
    for p in plants:
        pid = p['id']
        # 1. Fix Latin Name
        if pid in LATIN_FIXES:
            p['latin_name'] = LATIN_FIXES[pid]
        else:
            p['latin_name'] = p.get('latin_name', '').replace('â€™', "'").replace("''", "'").strip()

        clean_latin = p['latin_name']
        genus = get_genus(clean_latin)

        ro_pop, default_origin = GENUS_DATA.get(genus, ("Plantă ornamentală", "Regiuni temperate și subtropicale"))
        if pid in SPECIES_OVERRIDES:
            _, default_origin = SPECIES_OVERRIDES[pid]

        # Specific species origin refinements
        lat_low = clean_latin.lower()
        if 'abies alba' in lat_low:
            default_origin = "Munții din Europa Centrală și de Sud (inclusiv Munții Carpați)"
        elif 'abies concolor' in lat_low:
            default_origin = "America de Nord (vestul Statelor Unite și nordul Mexicului)"
        elif 'abies koreana' in lat_low:
            default_origin = "Coreea de Sud (zonele montane înalte)"
        elif 'abies nordmanniana' in lat_low:
            default_origin = "Munții Caucaz și nord-estul Turciei"
        elif 'abies pinsapo' in lat_low:
            default_origin = "Sudul Spaniei (Andaluzia) și nordul Marocului"
        elif 'acer negundo' in lat_low or 'acer saccharinum' in lat_low:
            default_origin = "America de Nord"
        elif 'acer campestre' in lat_low or 'acer platanoides' in lat_low:
            default_origin = "Europa (inclusiv România) și Asia de Vest"
        elif 'asplenium nidus' in lat_low:
            default_origin = "Regiunile tropicale din Asia de Sud-Est, Australia și Africa de Est"
        elif 'chamaecyparis lawsoniana' in lat_low:
            default_origin = "America de Nord (sud-vestul statului Oregon și nord-vestul Californiei, SUA)"
        elif 'chamaecyparis pisifera' in lat_low:
            default_origin = "Japonia (insulele Honshu și Kyushu)"
        elif 'chamaecyparis nootkatensis' in lat_low:
            default_origin = "Coasta de nord-vest a Americii de Nord (din Alaska până în nordul Californiei)"
        elif 'ficus carica' in lat_low:
            default_origin = "Bazinul Mediteranean și Asia de Sud-Vest"
        elif 'ficus lyrata' in lat_low:
            default_origin = "Pădurile tropicale din Africa de Vest (din Camerun până în Sierra Leone)"
        elif 'ficus benjamina' in lat_low or 'ficus elastica' in lat_low:
            default_origin = "Asia de Sud și de Sud-Est (India, Malaezia, Indonezia)"
        elif 'ficus pumila' in lat_low:
            default_origin = "Asia de Est (China, Japonia și Vietnam)"
        elif 'hibiscus rosa-sinensis' in lat_low:
            default_origin = "Asia tropicală (sudul Chinei și Indiei)"
        elif 'hibiscus syriacus' in lat_low:
            default_origin = "China și India"
        elif 'juniperus chinensis' in lat_low:
            default_origin = "Asia de Est (China, Mongolia, Japonia și Coreea)"
        elif 'juniperus communis' in lat_low:
            default_origin = "Emisfera Nordică (Europa, Asia și America de Nord)"
        elif 'juniperus horizontalis' in lat_low or 'juniperus scopulorum' in lat_low:
            default_origin = "America de Nord (Canada și Statele Unite)"
        elif 'juniperus sabina' in lat_low:
            default_origin = "Munții din Europa Centrală și de Sud, Caucaz și Asia Centrală"
        elif 'juniperus squamata' in lat_low:
            default_origin = "Munții Himalaya și China de Sud-Vest"
        elif 'picea pungens' in lat_low:
            default_origin = "America de Nord (Munții Stâncoși din vestul SUA)"
        elif 'picea glauca' in lat_low:
            default_origin = "America de Nord (Canada și nordul Statelor Unite)"
        elif 'picea omorika' in lat_low or 'picea omorica' in lat_low:
            default_origin = "Peninsula Balcanică (Valea râului Drina din Serbia și Bosnia)"
        elif 'pinus mugo' in lat_low or 'pinus sylvestris' in lat_low or 'pinus silvestris' in lat_low:
            default_origin = "Europa (inclusiv Munții Carpați) și Asia de Nord"
        elif 'pinus strobus' in lat_low:
            default_origin = "America de Nord (estul Canadei și nord-estul SUA)"
        elif 'pinus wallichiana' in lat_low:
            default_origin = "Munții Himalaya (din Afganistan până în Nepal și Bhutan)"
        elif 'polypodium aureum' in lat_low:
            default_origin = "Regiunile tropicale și subtropicale din America"
        elif 'rhododendron simsii' in lat_low:
            default_origin = "China, Taiwan și Myanmar"
        elif 'rhododendron catawbiense' in lat_low:
            default_origin = "America de Nord (Munții Appalachi din estul SUA)"
        elif 'sedum burrito' in lat_low:
            default_origin = "Mexic de Sud"
        elif 'thuja occidentalis' in lat_low:
            default_origin = "America de Nord (estul Canadei și nord-estul Statelor Unite)"
        elif 'thuja plicata' in lat_low:
            default_origin = "America de Nord (coasta Pacificului, din Alaska până în California)"

        # 2. Update Name to include both Latin & Romanian names
        p['name'] = build_dual_name(p, clean_latin, ro_pop)

        # Ensure letter is populated
        if not p.get('letter') or not p['letter'].strip():
            first_ch = p['name'][0].upper()
            for s, d in [('Ă', 'A'), ('Â', 'A'), ('Î', 'I'), ('Ș', 'S'), ('Ț', 'T')]:
                first_ch = first_ch.replace(s, d)
            p['letter'] = first_ch

        # 3. Fix Origin if empty, short, or "Hibrid."/"Cultivar."
        cur_origin = p.get('origin', '').strip().rstrip('.,;')
        if len(cur_origin) < 5 or any(bad in cur_origin.lower() for bad in ['hibrid', 'cultiv', 'global', 'necunoscut']):
            p['origin'] = default_origin
        else:
            p['origin'] = fix_romanian_text(cur_origin)

        # 4. Special botanical morphology fixes for specific plants
        if pid == 502: # Alstroemeria Ligtu hibrizi
            p['shape'] = "Plantă perenă cu rădăcini tuberizate cărnoase și tulpini florifere erecte, viguroase, ce ating 60–100 cm înălțime."
            p['leaves'] = "Frunze liniar-lanceolate, de culoare verde-cenușiu, răsucite caracteristic cu 180° la bază (resupinate), astfel încât fața inferioară este orientată în sus."
            p['flowers'] = "Inflorescențe umbeliforme bogate cu flori spectaculoase în formă de pâlnie (asemănătoare crinilor miniaturali), în nuanțe vibrante de roz-somon, corai, portocaliu, galben și roșu, adesea pătate și striate fin pe petalele interioare; înflorește abundent în iunie– august."
        elif pid in (320, 321): # Ginkgo biloba
            p['category'] = "Arbori"
            p['shape'] = "Arbore foios relict (gimnosperm) de talie mare, cu port piramidal în tinerețe și coroană largă, maiestuoasă la maturitate, putând atinge 20–35 m înălțime."
            p['leaves'] = "Frunze caduce unice, pieloase, în formă de evantai bilobat cu nervuri dicotomice paralele, de culoare verde-crud vara și galben-auriu strălucitor toamna."
            p['flowers'] = "Specie dioică; nu produce flori tipice angiospermelor, ci conuri polinice subțiri (amentiforme) pe exemplarele masculine și ovule pedunculate pe cele feminine."

        p['shape'] = fix_romanian_text(p.get('shape', ''))
        p['leaves'] = fix_romanian_text(p.get('leaves', ''))
        p['flowers'] = fix_romanian_text(p.get('flowers', ''))

        # 5. Determine true ecological class for Temperature, Light, Watering, Soil & Fertilizer
        is_indoor = (
            p.get('category') == 'Plante de apartament' or
            (genus in INDOOR_TROPICAL_GENERA and 'ficus carica' not in lat_low and 'hibiscus syriacus' not in lat_low and 'rhododendron catawbiense' not in lat_low and 'sedum spectabile' not in lat_low and 'jasminum nudiflorum' not in lat_low and 'asplenium trichomanes' not in lat_low and 'polypodium glycyrrhiza' not in lat_low)
        )
        is_tender_garden = (genus in TENDER_GARDEN_GENERA)
        is_conifer = (p.get('category') == 'Conifere' and genus != 'Ginkgo')
        is_succulent = genus in {"Aeonium", "Agave", "Aloe", "Aporocactus", "Crassula", "Echeveria", "Echinopsis", "Faucaria", "Gymnocalycium", "Haworthia", "Kalanchoe", "Lithops", "Mammillaria", "Opuntia", "Rebutia", "Rhipsalidopsis", "Rhipsalis", "Schlumbergera", "Stapelia"} or 'sedum burrito' in lat_low
        is_fern = genus in {"Adiantum", "Asplenium", "Blechnum", "Davallia", "Dryopteris", "Lygodium", "Microlepia", "Nephrolepis", "Pellaea", "Platycerium", "Polypodium", "Selaginella"}
        is_carnivorous = genus in {"Dionaea", "Drosera", "Nepenthes"}

        cg = p.setdefault('care_guide', {})

        # Fix Temperature & Hardiness accurately
        if is_carnivorous:
            cg['temperatura'] = "Temperatură optimă 18–28°C în sezonul cald; iarna necesită protecție în interior luminos (10–18°C, sau 5–10°C repaus pentru Dionaea) și umiditate atmosferică ridicată."
        elif is_succulent and is_indoor:
            cg['temperatura'] = "Iubitoare de căldură (20–28°C vara); iarna preferă o perioadă de repaus răcoros și luminos la 10–14°C pentru stimularea înfloririi, ferită complet de îngheț."
        elif is_indoor:
            if genus in {"Camellia", "Citrus", "Cyclamen", "Fatshedera", "Fatsia", "Fuchsia", "Gardenia", "Grevillea", "Jasminum", "Lantana", "Nerium", "Passiflora", "Plumbago", "Punica", "Rhododendron", "Solanum", "Sparrmannia", "Washingtonia"}:
                cg['temperatura'] = "Plantă mediteraneană / subtropicală: vara se dezvoltă excelent la 18–26°C (inclusiv pe terase sau în grădină), iar iarna necesită adăpostire în spații luminoase și răcoroase (6–14°C), ferită de îngheț."
            else:
                cg['temperatura'] = "Plantă tropicală de interior: temperatură optimă constantă între 18°C și 25°C; nu tolerează înghețul, curenții reci de aer sau temperaturile sub 14–15°C."
        elif pid == 502: # Alstroemeria Ligtu hibrizi
            cg['temperatura'] = "Specie semirustică: rădăcinile tuberizate plantate adânc (15–20 cm) rezistă iarna până la -8°C...-10°C dacă solul este bine drenat și protejat cu un strat gros de mulci uscat (frunze, paie sau turbă); în zonele cu ierni geroase se protejează suplimentar sau se cultivă în containere adăpostite peste iarnă."
        elif is_tender_garden:
            if genus in {"Freesia", "Gloriosa", "Mirabilis"}:
                cg['temperatura'] = "Sensibilă la îngheț: vegetează și înflorește spectaculos în sezonul cald (18–28°C); toamna, înainte de primul îngheț, bulbotuberii sau rădăcinile tuberizate se scot din pământ și se păstrează peste iarnă în spații uscate și răcoroase (8–12°C)."
            elif genus in {"Arundo", "Cortaderia", "Kniphofia", "Verbena", "Tropaeolum"}:
                cg['temperatura'] = "Specie semirustică (rezistentă până la -10°C...-12°C): în climatul din România necesită amplasare în locuri adăpostite de vânturile reci și protejarea bazei tufei toamna cu un strat consistent de mulci și frunze uscate."
            elif genus == "Olea":
                cg['temperatura'] = "Rezistent la căldură toridă și secetă; iarna tolerează înghețuri scurte până la -5°C...-7°C, fiind recomandată adăpostirea în spații luminoase și răcoroase (5–10°C) în perioadele cu ger sever."
            else:
                cg['temperatura'] = "Iubitoare de căldură estivală (18–30°C) și sensibilă la îngheț; în climatul din România se cultivă în sezonul cald în grădină sau jardiniere, ori se iernează în spații luminoase ferite de îngheț (8–12°C)."
        else:
            # Hardy outdoor Perene, Arbusti, Arbori, Conifere
            cg['temperatura'] = "Specie rustică, foarte bine adaptată climatului temperat-continental din România; rezistă cu succes în grădină la gerurile de iarnă (-20°C...-25°C)."

        # Fix Carnivorous watering/soil special case
        if is_carnivorous:
            cg['udare'] = "Se udă exclusiv cu apă de ploaie, apă distilată sau demineralizată (nu tolerează calcarul și sărurile din apa de la robinet); substratul se menține permanent umed."
            cg['sol'] = "Substrat special acid, sărac în săruri minerale, pe bază de turbă blondă (Sphagnum) și perlit; nu se folosesc substraturi fertilizate standard."
            cg['fertilizare'] = "Nu se aplică îngrășăminte chimice în sol (rădăcinile sunt extrem de sensibile la săruri); planta își extrage nutrienții în mod natural din insectele capturate."
            p['recommended_products'] = [4]
        else:
            # Harmonize substrate & fertilizer using fixed recommendation_engine
            rec = recommend_products_for_plant(p, products)
            sub = rec['primary_substrate']
            fert = rec['primary_fertilizer']
            p['recommended_products'] = rec['recommended_product_ids']

            # Soil text
            if sub['id'] == 11: # Orhidee
                cg['sol'] = f"Substrat epifit extrem de aerat și permeabil, pe bază de scoarță de pin calibrată. Se recomandă utilizarea substratului specializat {sub['name']} ({sub['brand']}) pentru oxigenarea optimă a rădăcinilor."
            elif sub['id'] == 12: # Muscate & balcon
                cg['sol'] = f"Substrat bogat în humus, fertil și bine drenat, capabil să susțină o înflorire abundentă. Se recomandă utilizarea substratului dedicat {sub['name']} ({sub['brand']})."
            elif sub['id'] == 18: # Plante de camera
                cg['sol'] = f"Substrat fertil, afânat și permeabil, cu retenție echilibrată a umidității. Se recomandă utilizarea substratului {sub['name']} ({sub['brand']}) pentru o dezvoltare foliară viguroasă."
            elif sub['id'] == 19: # Straturi inaltate (legume / aromatice)
                cg['sol'] = f"Sol bogat în materie organică, afânat și foarte bine drenat. Se recomandă utilizarea substratului {sub['name']} ({sub['brand']}) pentru o creștere sănătoasă și aromată."
            elif is_succulent:
                cg['sol'] = f"Substrat poros, nisipos și extrem de bine drenat pentru prevenirea putrezirii rădăcinilor. Se recomandă {sub['name']} ({sub['brand']}) amestecat cu perlit și nisip cuartos."
            elif is_conifer:
                cg['sol'] = f"Sol permeabil, reavăn, cu reacție ușor acidă până la neutră. Se recomandă {sub['name']} ({sub['brand']}) la plantare și mulcirea bazei cu scoarță decorativă."
            else:
                cg['sol'] = f"Sol de grădină fertil, bine structurat și permeabil, care nu reține apa în exces. Se recomandă {sub['name']} ({sub['brand']}) pentru îmbunătățirea calității solului la plantare și o înrădăcinare puternică."

            # Fertilizer text
            if fert is None:
                # Deciduous trees & shrubs rule: NO liquid fertilizer product recommendation
                cg['fertilizare'] = "Arborii și arbuștii ornamentali își asigură necesarul nutritiv dintr-un sol bine pregătit la plantare cu substrat de calitate și compost matur, fără a necesita fertilizanți lichizi."
            else:
                cg['fertilizare'] = f"Fertilizare regulată în perioada de creștere activă (primăvară–vară) cu {fert['name']} ({fert['brand']}) pentru susținerea vigorii și a decorului; toamna târziu și iarna fertilizarea se suspendă."

        # 6. Rebuild clean, rich botanical description without broken grammar
        cat = p.get('category', 'Plante de apartament')
        if is_conifer:
            cat_label = "un conifer decorativ veșnic verde"
        elif is_fern:
            cat_label = "o ferigă ornamentală apreciată pentru frunzișul său dantelat"
        elif is_succulent:
            cat_label = "o plantă suculentă decorativă și rezistentă"
        elif is_carnivorous:
            cat_label = "o plantă carnivoră exotică fascinantă"
        elif is_indoor:
            cat_label = "o plantă decorativă de interior și terasă"
        elif cat == 'Arbori':
            cat_label = "un arbore ornamental impunător"
        elif cat == 'Arbusti':
            cat_label = "un arbust ornamental deosebit"
        else:
            cat_label = "o plantă perenă decorativă de grădină"

        intro = f"{p['name']} ({clean_latin}) este {cat_label}, originară din {p['origin'].rstrip('.')}."
        morph_parts = []
        if p.get('shape'):
            morph_parts.append(p['shape'])
        if p.get('leaves'):
            l_txt = p['leaves']
            if not any(l_txt.lower().startswith(w) for w in ['frunz', 'acel', 'prezint', 'are ']):
                l_txt = f"Frunzișul se remarcă prin aspectul său: {l_txt[0].lower() + l_txt[1:]}"
            morph_parts.append(l_txt)
        if p.get('flowers'):
            f_txt = p['flowers']
            if not any(f_txt.lower().startswith(w) for w in ['flor', 'inflor', 'înflor', 'nu ', 'fiind', 'planta', 'speci', 'conur', 'spadice', 'cascad', 'sute']):
                f_txt = f"În perioada de decor, {f_txt[0].lower() + f_txt[1:]}"
            morph_parts.append(f_txt)

        if is_indoor:
            outro = "Se remarcă prin valoarea sa estetică ridicată în amenajarea locuințelor, birourilor luminoase sau a teraselor adăpostite pe timpul verii."
        elif is_conifer:
            outro = "Oferă structură arhitecturală și culoare persistentă în grădină pe tot parcursul anului, fiind ideal atât solitar, cât și în grupuri peisagistice."
        elif cat in ('Arbori', 'Arbusti'):
            outro = "Este o alegere excelentă pentru amenajări peisagistice, garduri vii libere sau plantări solitare de efect în grădini și parcuri."
        else:
            outro = "Constituie o alegere remarcabilă pentru borduri florale, ronduri perene, stâncării sau ca floare tăiată de lungă durată."

        p['description'] = " ".join([intro] + morph_parts + [outro])
        p['requirements'] = f"{cg.get('lumina', '')} {cg.get('udare', '')} {cg.get('sol', '')} {cg.get('temperatura', '')} {cg.get('fertilizare', '')}".strip()
        updated_count += 1

    with open('data/plants.json', 'w', encoding='utf-8') as f:
        json.dump(plants, f, ensure_ascii=False, indent=2)

    print(f"Successfully updated botanical data & dual Romanian-Latin names for {updated_count} plants!")

if __name__ == '__main__':
    main()
