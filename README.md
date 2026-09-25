# EML Parser API

Candidato v2.0: mantiene Dify → FastAPI → AI → CSV Delera e aggiunge risoluzione geografica offline e archiviazione pCloud opzionale.

Il piano file-per-file, le verifiche API e le condizioni per il rilascio sono in [PIANO_V2.md](PIANO_V2.md). Il link pCloud implementato è un **link di raccolta file**, distinto dal link condiviso con visualizzazione e upload. Il collaudo cloud autenticato e la validazione dei dati geografici restano da completare.

## Avvio

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Configurare le variabili d'ambiente indicate in `.env.example`. Il file non viene caricato automaticamente. pCloud è disabilitato per impostazione predefinita.

`POST /parse`: multipart `files` (.eml/.zip), `protocol_start` (es. `2026 4000`). Output: `contatti_delera.csv`, con le stesse colonne preesistenti.

## Test

```sh
pip install pytest
python -m pytest -q
```
