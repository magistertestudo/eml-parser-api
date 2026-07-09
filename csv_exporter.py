import csv
import io

from crm_schema import CSV_COLUMNS


def build_csv(records: list[dict]) -> str:

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        delimiter=",",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        extrasaction="ignore",
        lineterminator="\n"
    )

    writer.writeheader()

    for record in records:

        row = {}

        for column in CSV_COLUMNS:
            row[column] = record.get(column, "")

        writer.writerow(row)

    return output.getvalue()