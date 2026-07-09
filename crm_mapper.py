from datetime import datetime


def map_to_delera(
    ai: dict,
    filename: str,
    protocol: str = "",
    owner: str = ""
) -> dict:

    today = datetime.now().strftime("%Y-%m-%d")

    return {

        # =========================
        # CONTATTO
        # =========================

        "First Name": ai.get("Nome", ""),
        "Last Name": ai.get("Cognome", ""),
        "Email": ai.get("Email", ""),
        "Phone": ai.get("Telefono", ""),
        "Additional Phones": ai.get("Telefono Secondario", ""),
        "Titolo": ai.get("Titolo", ""),
        "Provincia": ai.get("Provincia", ""),

        "Contact Source": "email",

        "Contact Type": "Customer",

        "Privacy Policy Contatto":
        "Accetto i termini del servizio e della privacy policy",

        "Data di Ultima interazione del Contatto":
        today,

        "Date of birth": "",

        # =========================
        # OPPORTUNITY
        # =========================

        "Opportunity Name":
        f"{protocol} | {ai.get('Azienda','')}" if protocol else "",

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

        "Lost Reason Name":
        "",

        "Codice Promo Opportunità":
        "",

        "Località di Intervento":
        "",

        "Business Name":
        ai.get("Azienda", ""),

        "Data di Chiusura Prevista":
        "",

        "Data di Creazione":
        today,

        "Privacy Policy":
        "Accetto i termini del servizio e della privacy policy",

        "Cartella Allegati":
        "",

        "Partner":
        "",

        "Commenti Lost Reason":
        "",

        "Coordinatore":
        "",

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