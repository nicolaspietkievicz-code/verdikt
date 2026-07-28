"""Como se DICEN las cosas que estan escritas en ingles.

El sintetizador solo habla español: lee "finance" como fi-nan-se y "Nike" como
ni-ke. La solucion no es cambiar de motor sino escribirle las palabras como
suenan, que es lo que hace este archivo.

DOS REGLAS AL EDITAR:

1. Se puede usar tilde, y conviene: en español la tilde es lo unico que fija
   donde cae el acento. "Amazon" sin tilde se lee ama-ZON; con tilde, A-mazon.
   (Ojo: las tildes solo funcionan porque el texto va al sintetizador POR
   ARCHIVO. Por la entrada estandar llegan rotas y las lee en voz alta; ver
   narrar.py::_decir_piper.)

2. El diccionario es CERRADO: los 135 nombres del catalogo tienen que estar,
   aunque sea apuntando a None ("se lee igual"). Asi un nombre nuevo no pasa
   desapercibido — `faltantes()` lo caza.

Si algo suena mal, se corrige aca y listo: es el unico lugar donde vive esto.
"""
import re

# Terminos tecnicos que aparecen en las razones del motor.
TECNICOS = {
    "MACD": "macdi",
    "RSI": "erre ese i",
    "ADX": "a de equis",
}

# La marca.
MARCA = {
    "finance": "fáinans",
    "Verdikt": "vérdict",
}

# Los 135 del catalogo. None = se lee igual en español, no hay que tocarlo.
ACTIVOS = {
    # --- Cripto ---
    "0x": "cero equis", "Aave": "áave", "Algorand": None, "Avalanche": "ávalanch",
    "BNB": "be ene be", "Basic Attention": "béisic aténshon", "Bitcoin": None,
    "Bitcoin Cash": "bitcoin cash", "Cardano": None, "Chainlink": "chéinlink",
    "Chiliz": "chíliz", "Compound": "cómpaund", "Cosmos": None, "Curve": "kerv",
    "Dash": "dash", "Decentraland": None, "Dogecoin": "dóuchcoin",
    "EOS": "e o ese", "Enjin": "énllin", "Ethereum": "etéreum",
    "Ethereum Classic": "etéreum clásic", "Filecoin": "fáilcoin",
    "ICON": "áicon", "Kusama": None, "Litecoin": "láitcoin", "Maker": "méiker",
    "Monero": None, "Neo": None, "OMG Network": "o eme ge nétwork",
    "Polkadot": "pólkadot", "Polygon": "póligon", "Qtum": "cutum",
    "Solana": None, "Stellar": "stélar", "SushiSwap": "súshiswap",
    "Synthetix": "sinthétix", "TRON": "tron", "Tezos": "tésos",
    "The Graph": "de graf", "The Sandbox": "de sándbox", "Uniswap": "iúniswap",
    "XRP": "equis erre pe", "Zcash": "zi cash", "yearn.finance": "yern fáinans",

    # --- Acciones y CEDEARs ---
    "AMD": "a eme de", "ASML": "a ese eme ele", "AT&T": "éi ti ti",
    "AbbVie": "ábvi", "Adobe": "adóbi", "Airbnb": "érbienbí",
    "Alibaba": None, "Alphabet (Google)": "álfabet, gúgel", "Amazon": "ámazon",
    "Anheuser-Busch InBev": "ánhauser bush ínbev", "Apple": "ápel",
    "AstraZeneca": None, "Baidu": "báidu", "Banco Macro": None,
    "Bank of America": "bánk of américa", "Boeing": "bóing",
    "British American Tobacco": "brítish américan tobáco", "Broadcom": "bródcom",
    "Caterpillar": "cáterpilar", "Central Puerto": None, "Chevron": "chévron",
    "Cisco": "sísco", "Citigroup": "sítigrup", "Coca-Cola": None,
    "Coinbase": "cóinbeis", "Costco": "cóstco", "Cresud": None,
    "Diageo": "diáyeo", "Disney": "dísney", "Eli Lilly": "élai líli",
    "ExxonMobil": "éxon móbil", "Ford": "ford", "General Motors": "yéneral mótors",
    "Globant": None, "Goldman Sachs": "góldman saks", "Grupo Galicia": None,
    "HDFC Bank": "áche de efe ce bank", "HSBC": "áche ese be ce",
    "Home Depot": "jom dípot", "IBM": "i be éme", "Infosys": "ínfosis",
    "Intel": "íntel", "JD.com": "yei di punto com", "JPMorgan": "yeipí mórgan",
    "Johnson & Johnson": "yónson y yónson", "Li Auto": "li áuto",
    "McDonald's": "macdónals", "MercadoLibre": None, "Merck": "merk",
    "Meta": None, "Micron": "máicron", "Microsoft": "máicrosoft",
    "Morgan Stanley": "mórgan stánli", "NIO": "nío", "NVIDIA": "envídia",
    "Netflix": "nétflix", "Nike": "náik", "Novartis": None,
    "Novo Nordisk": "nóvo nórdisk", "Oracle": "óracol",
    "PDD (Pinduoduo)": "pe de de", "Palantir": "palantír", "Pampa Energía": None,
    "PayPal": "péipal", "PepsiCo": "pépsico", "Pfizer": "fáiser",
    "Procter & Gamble": "prócter y gámbol", "Qualcomm": "cuálcom",
    "SAP": "sap", "Salesforce": "séilsfors", "Sanofi": None,
    "Sea Limited": "si límited", "Shell": "shel", "Shopify": "shópifai",
    "Sony": "sóni", "Starbucks": "stárbaks", "TSMC": "te ese eme ce",
    "Telecom Argentina": None, "Tesla": None,
    "Texas Instruments": "téxas ínstruments", "TotalEnergies": "tótal enerlles",
    "Toyota": None, "Uber": "úber", "Unilever": "unilíver",
    "UnitedHealth": "iunáited jelz", "Verizon": "verízon", "Visa": None,
    "Vista Energy": "vista énerlli", "Walmart": "wólmart",
    "Wells Fargo": "wéls fárgo", "YPF": "i pe éfe",
}

# Todo junto. Se reemplaza de la clave mas larga a la mas corta para que
# "Bitcoin Cash" gane sobre "Bitcoin" y "Ethereum Classic" sobre "Ethereum".
TABLA = {**TECNICOS, **MARCA, **{k: v for k, v in ACTIVOS.items() if v}}
_CLAVES = sorted(TABLA, key=len, reverse=True)


def hablado(texto: str) -> str:
    """Devuelve el texto listo para el sintetizador.

    Solo cambia lo que se MANDA A LA VOZ: lo que se ve en pantalla y el caption
    siguen escritos como corresponde."""
    for clave in _CLAVES:
        if clave in texto:
            texto = texto.replace(clave, TABLA[clave])
        # Los acronimos tambien aparecen en mayuscula dentro de otras frases;
        # el resto se compara tal cual porque los nombres propios vienen del
        # catalogo con su capitalizacion exacta.
        elif clave.isupper() and clave.lower() in texto:
            texto = texto.replace(clave.lower(), TABLA[clave])
    return texto


def faltantes(nombres) -> list:
    """Nombres del catalogo que nadie decidio como se dicen.

    No alcanza con que 'no este en el diccionario': un nombre puede leerse
    igual en español y estar bien. Por eso el diccionario guarda None explicito
    y esto solo devuelve los que NUNCA se miraron."""
    return sorted(n for n in nombres if n not in ACTIVOS)


def sospechosas(texto: str) -> list:
    """Palabras que parecen inglesas y no estan en la tabla. Es una red de
    seguridad para las razones del motor, que pueden sumar terminos nuevos sin
    que nadie avise: cazamos las que tienen combinaciones que el español no
    usa (sh, ck, w, doble consonante final, -ing)."""
    pistas = re.compile(r"(sh|ck|ph|w|th|ing\b|ee|oo)", re.IGNORECASE)
    fuera = []
    for palabra in re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ][\w.&'-]{2,}", texto):
        if palabra in TABLA or palabra.lower() in (k.lower() for k in TABLA):
            continue
        if pistas.search(palabra):
            fuera.append(palabra)
    return fuera
