from datetime import datetime

from crm_schema import AI_MAPPING
from crm_schema import FIXED_VALUES


PROVINCE = {

    "AG": "Agrigento",
    "AL": "Alessandria",
    "AN": "Ancona",
    "AO": "Aosta",
    "AR": "Arezzo",
    "AP": "Ascoli Piceno",
    "AT": "Asti",
    "AV": "Avellino",
    "BA": "Bari",
    "BT": "Barletta-Andria-Trani",
    "BL": "Belluno",
    "BN": "Benevento",
    "BG": "Bergamo",
    "BI": "Biella",
    "BO": "Bologna",
    "BZ": "Bolzano",
    "BS": "Brescia",
    "BR": "Brindisi",
    "CA": "Cagliari",
    "CL": "Caltanissetta",
    "CB": "Campobasso",
    "CE": "Caserta",
    "CT": "Catania",
    "CZ": "Catanzaro",
    "CH": "Chieti",
    "CO": "Como",
    "CS": "Cosenza",
    "CR": "Cremona",
    "KR": "Crotone",
    "CN": "Cuneo",
    "EN": "Enna",
    "FM": "Fermo",
    "FE": "Ferrara",
    "FI": "Firenze",
    "FG": "Foggia",
    "FC": "Forlì-Cesena",
    "FR": "Frosinone",
    "GE": "Genova",
    "GO": "Gorizia",
    "GR": "Grosseto",
    "IM": "Imperia",
    "IS": "Isernia",
    "SP": "La Spezia",
    "AQ": "L'Aquila",
    "LT": "Latina",
    "LE": "Lecce",
    "LC": "Lecco",
    "LI": "Livorno",
    "LO": "Lodi",
    "LU": "Lucca",
    "MC": "Macerata",
    "MN": "Mantova",
    "MS": "Massa-Carrara",
    "MT": "Matera",
    "ME": "Messina",
    "MI": "Milano",
    "MO": "Modena",
    "MB": "Monza e Brianza",
    "NA": "Napoli",
    "NO": "Novara",
    "NU": "Nuoro",
    "OR": "Oristano",
    "PD": "Padova",
    "PA": "Palermo",
    "PR": "Parma",
    "PV": "Pavia",
    "PG": "Perugia",
    "PU": "Pesaro-Urbino",
    "PE": "Pescara",
    "PC": "Piacenza",
    "PI": "Pisa",
    "PT": "Pistoia",
    "PN": "Pordenone",
    "PZ": "Potenza",
    "PO": "Prato",
    "RG": "Ragusa",
    "RA": "Ravenna",
    "RC": "Reggio Calabria",
    "RE": "Reggio Emilia",
    "RI": "Rieti",
    "RN": "Rimini",
    "RM": "Roma",
    "RO": "Rovigo",
    "SA": "Salerno",
    "SS": "Sassari",
    "SV": "Savona",
    "SI": "Siena",
    "SR": "Siracusa",
    "SO": "Sondrio",
    "SU": "Sud Sardegna",
    "TA": "Taranto",
    "TE": "Teramo",
    "TR": "Terni",
    "TO": "Torino",
    "TP": "Trapani",
    "TN": "Trento",
    "TV": "Treviso",
    "TS": "Trieste",
    "UD": "Udine",
    "VA": "Varese",
    "VE": "Venezia",
    "VB": "Verbano-Cusio-Ossola",
    "VC": "Vercelli",
    "VR": "Verona",
    "VV": "Vibo Valentia",
    "VI": "Vicenza",
    "VT": "Viterbo"
}


def map_to_delera(
    ai: dict,
    filename: str,
    protocol: str = "",
    owner: str = "",
    interaction_date: str = ""
) -> dict:

    if not interaction_date:
        interaction_date = datetime.now().strftime("%Y-%m-%d")

    record = {}

    # -----------------------------
    # Mapping AI -> CRM
    # -----------------------------

    for ai_field, crm_field in AI_MAPPING.items():

        value = ai.get(ai_field, "")

        if crm_field == "Provincia":

            sigla = value.strip().upper()

            value = PROVINCE.get(sigla, value)

        record[crm_field] = value

    # -----------------------------
    # Valori fissi
    # -----------------------------

    record.update(FIXED_VALUES)

    # -----------------------------
    # Campi generati
    # -----------------------------

    record["Data di Ultima interazione del Contatto"] = interaction_date
    record["Date of birth"] = ""
    record["Data di Creazione"] = interaction_date
    record["Data di Chiusura Prevista"] = ""

    record["Lost Reason Name"] = ""
    record["Codice Promo Opportunità"] = ""
    record["Località di Intervento"] = ""

    record["Partner"] = ""
    record["Commenti Lost Reason"] = ""
    record["Coordinatore"] = ""

    record["Opportunity Owner"] = owner

    record["Numero di Protocollo"] = protocol

    record["Allega File"] = filename

    business = record.get("Business Name", "").strip()

    if protocol and business:
        record["Opportunity Name"] = f"{protocol} | {business}"
    elif protocol:
        record["Opportunity Name"] = protocol
    else:
        record["Opportunity Name"] = ""

    return record