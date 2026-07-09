from datetime import datetime

from crm_schema import AI_MAPPING
from crm_schema import FIXED_VALUES


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

    # ===========================
    # MAPPING AI -> CRM
    # ===========================

    for ai_field, crm_field in AI_MAPPING.items():

        value = ai.get(ai_field, "")

        if crm_field == "Provincia":
            value = value.upper()

        record[crm_field] = value

    # ===========================
    # VALORI FISSI
    # ===========================

    record.update(FIXED_VALUES)

    # ===========================
    # CAMPI GENERATI
    # ===========================

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

    if protocol:
        record["Opportunity Name"] = (
            f"{protocol} | {record.get('Business Name', '')}"
        )
    else:
        record["Opportunity Name"] = ""

    return record