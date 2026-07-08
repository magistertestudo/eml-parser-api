from datetime import datetime


DEFAULTS = {

    "Fonte Contatto": "email",

    "Tipo Contatto": "Customer",

    "Pipeline": "LEAD GENERATI DA IN-SAFETY",

    "Fase": "NUOVE OPPORTUNITÀ",

    "Stato": "open",

    "Valore Lead": "4000",

    "Fonte Opportunità": "email",

    "Privacy Contatto": "Accetto i termini del servizio e della privacy policy",

    "Privacy Opportunity": "Accetto i termini del servizio e della privacy policy",

    "Come ci hai conosciuto": "Motori di ricerca"

}


def enrich(
    record: dict,
    filename: str,
    protocol: str = ""
):

    today = datetime.now().strftime("%Y-%m-%d")

    enriched = DEFAULTS.copy()

    enriched.update(record)

    enriched["Data Creazione"] = today

    enriched["Data Ultima Interazione"] = today

    enriched["Numero Protocollo"] = protocol

    enriched["Nome Opportunità"] = (
        f"{protocol} | {enriched.get('Azienda','')}"
        if protocol else ""
    )

    enriched["Allega File"] = filename

    return enriched