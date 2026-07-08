from datetime import datetime


def enrich(record: dict, filename: str, protocol: str = "") -> dict:

    today = datetime.now().strftime("%Y-%m-%d")

    record["Fonte Contatto"] = "email"
    record["Tipo Contatto"] = "Customer"

    record["Pipeline"] = "LEAD GENERATI DA IN-SAFETY"
    record["Fase"] = "NUOVE OPPORTUNITÀ"
    record["Stato"] = "open"

    record["Valore Lead"] = "4000"

    record["Fonte Opportunità"] = "email"

    record["Privacy Contatto"] = "Accetto i termini del servizio e della privacy policy"
    record["Privacy Opportunity"] = "Accetto i termini del servizio e della privacy policy"

    record["Come ci hai conosciuto"] = "Motori di ricerca"

    record["Numero Protocollo"] = protocol

    record["Nome Opportunità"] = (
        f"{protocol} | {record.get('Azienda','')}"
        if protocol else ""
    )

    record["Data Creazione"] = today
    record["Data Ultima Interazione"] = today

    record["Allega File"] = filename

    return record