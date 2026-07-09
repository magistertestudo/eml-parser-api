import csv
import io


CSV_COLUMNS = [
    "Nome",
    "Cognome",
    "Email",
    "Telefono",
    "Telefono Secondario",
    "Titolo",
    "Provincia",
    "Fonte Contatto",
    "Tipo Contatto",
    "Privacy Contatto",
    "Data Ultima Interazione",
    "Data Nascita",
    "Nome Opportunità",
    "Pipeline",
    "Fase",
    "Stato",
    "Valore Lead",
    "Titolare",
    "Fonte Opportunità",
    "Motivo Perdita",
    "Codice Promo",
    "Località Intervento",
    "Azienda",
    "Data Chiusura Prevista",
    "Data Creazione",
    "Privacy Opportunity",
    "Cartella Allegati",
    "Partner",
    "Commenti Lost Reason",
    "Coordinatore",
    "Numero Protocollo",
    "Allega File",
    "Descrizione Richiesta",
    "Soluzione Richiesta",
    "Come ci hai conosciuto",
]


def build_csv(records: list[dict]) -> str:
    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",
        delimiter=",",
        quoting=csv.QUOTE_MINIMAL,
    )

    writer.writeheader()

    for record in records:
        row = {col: record.get(col, "") for col in CSV_COLUMNS}
        writer.writerow(row)

    return output.getvalue()