"""
CRM SCHEMA
Versione 2.0

Questo file contiene tutta la configurazione del CRM.

NON inserire logica.

Contiene solamente:

- intestazioni CSV
- mapping AI → CRM
- valori fissi
"""

# ==========================================================
# INTESTAZIONI CSV DELERA
# ==========================================================

CSV_COLUMNS = [

    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "Additional Phones",
    "Titolo",
    "Provincia",

    "Contact Source",
    "Contact Type",
    "Privacy Policy Contatto",

    "Data di Ultima interazione del Contatto",
    "Date of birth",

    "Opportunity Name",
    "Pipeline",
    "Stage",
    "Status",
    "Opportunity Value",
    "Opportunity Owner",
    "Opportunity Source",

    "Lost Reason Name",

    "Codice Promo Opportunità",

    "Località di Intervento",

    "Business Name",

    "Data di Chiusura Prevista",

    "Data di Creazione",

    "Privacy Policy",

    "Cartella Allegati",

    "Partner",

    "Commenti Lost Reason",

    "Coordinatore",

    "Numero di Protocollo",

    "Allega File",

    "Descrizione della Richiesta",

    "Soluzione Richiesta",

    "Come ci hai conosciuto"

]

# ==========================================================
# MAPPING AI → CRM
# ==========================================================

AI_MAPPING = {

    "Nome": "First Name",

    "Cognome": "Last Name",

    "Email": "Email",

    "Telefono": "Phone",

    "Telefono Secondario": "Additional Phones",

    "Titolo": "Titolo",

    "Provincia": "Provincia",

    "Azienda": "Business Name",

    "Descrizione Richiesta":
    "Descrizione della Richiesta",

    "Soluzione Richiesta":
    "Soluzione Richiesta"

}

# ==========================================================
# VALORI FISSI CRM
# ==========================================================

FIXED_VALUES = {

    "Contact Source":
    "email",

    "Contact Type":
    "Customer",

    "Privacy Policy Contatto":
    "Accetto i termini del servizio e della privacy policy",

    "Pipeline":
    "LEAD GENERATI DA IN-SAFETY",

    "Stage":
    "NUOVE OPPORTUNITÀ",

    "Status":
    "open",

    "Opportunity Value":
    "4000",

    "Opportunity Source":
    "email",

    "Privacy Policy":
    "Accetto i termini del servizio e della privacy policy",

    "Come ci hai conosciuto":
    "Motori di ricerca"

}