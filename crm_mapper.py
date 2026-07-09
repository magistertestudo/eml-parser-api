from datetime import datetime


def map_to_delera(
    ai: dict,
    filename: str,
    protocol: str = "",
    owner: str = "",
    interaction_date: str = ""
) -> dict:

    if not interaction_date:
        interaction_date = datetime.now().strftime("%Y-%m-%d")

    province = ai.get("Provincia", "").upper()

    opportunity_name = ""

    if protocol:
        opportunity_name = f"{protocol} | {ai.get('Azienda','')}"

    return {

        "First Name": ai.get("Nome", ""),
        "Last Name": ai.get("Cognome", ""),
        "Email": ai.get("Email", ""),
        "Phone": ai.get("Telefono", ""),
        "Additional Phones": ai.get("Telefono Secondario", ""),
        "Titolo": ai.get("Titolo", ""),
        "Provincia": province,

        "Contact Source": "email",
        "Contact Type": "Customer",

        "Privacy Policy Contatto":
        "Accetto i termini del servizio e della privacy policy",

        "Data di Ultima interazione del Contatto":
        interaction_date,

        "Date of birth": "",

        "Opportunity Name":
        opportunity_name,

        "Pipeline":
        "LEAD GENERATI DA IN-SAFETY",

        "Stage":
        "NUOVE OPPORTUNITÀ",

        "Status":
        "open",

        "Opportunity Value":
        "4000",

        "Opportunity Owner":
        owner,

        "Opportunity Source":
        "email",

        "Lost Reason Name": "",

        "Codice Promo Opportunità": "",

        "Località di Intervento": "",

        "Business Name":
        ai.get("Azienda", ""),

        "Data di Chiusura Prevista": "",

        "Data di Creazione":
        interaction_date,

        "Privacy Policy":
        "Accetto i termini del servizio e della privacy policy",

        "Cartella Allegati": "",

        "Partner": "",

        "Commenti Lost Reason": "",

        "Coordinatore": "",

        "Numero di Protocollo":
        protocol,

        "Allega File":
        filename,

        "Descrizione della Richiesta":
        ai.get("Descrizione Richiesta", ""),

        "Soluzione Richiesta":
        ai.get("Soluzione Richiesta", ""),

        "Come ci hai conosciuto":
        "Motori di ricerca"

    }