# EML Parser API

Candidato v2.0: mantiene Dify → FastAPI → AI → CSV Delera e aggiunge risoluzione geografica offline e archiviazione pCloud opzionale.

Il piano file-per-file, le verifiche API e le condizioni per il rilascio sono in [PIANO_V2.md](PIANO_V2.md). Il link pCloud implementato è un **link di raccolta file**, distinto dal link condiviso con visualizzazione e upload. Il collaudo cloud autenticato e la validazione dei CAP restano da completare.

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

### Provincia dal sito del contatto (2.0.1)

Quando la provincia non è ricavabile dai campi estratti dall'email, il server
visita il sito HTTPS del dominio dell'email del contatto (oppure del mittente,
solo se l'email del contatto è assente). Consulta home e collegamenti interni
Contatti/Sedi/Chi siamo, fino a quattro richieste di pagina. Cerca coppie
CAP-comune italiane e usa il medesimo archivio di normalizzazione provinciale.
Non invia il testo dell'email né l'indirizzo email al sito.

I principali provider pubblici internazionali, italiani, PEC e temporanei sono
esclusi tramite elenco locale aggiornabile in `website_province.py`; non è una
classificazione universale di tutti i provider esistenti. Domini aggiuntivi si
possono escludere con `PROVINCE_EXCLUDED_DOMAINS`, separati da virgole.
I domini aziendali che usano Google Workspace/Microsoft 365 restano ammessi.

Province già risolte, dati geografici contraddittori e contatti dichiarati esteri
non vengono sovrascritti. Siti irraggiungibili e indirizzi
non riconoscibili o pagine disponibili solo tramite JavaScript lasciano il campo
vuoto. La lettura usa timeout, limiti di dimensione e un budget di 12 secondi
(controllato tra le operazioni; la risoluzione DNS dipende dal sistema operativo).
Sono vietati IP privati e redirect verso altri domini. TLS resta verificato.
Per disattivare il ripiego: `PROVINCE_WEBSITE_ENABLED=false` (default `true`).

File modificati: `main.py` integra il ripiego dopo l'estrazione e prima del CSV;
`website_province.py` gestisce esclusioni, lettura pubblica e indirizzi;
`tests/test_website_province.py` verifica risoluzione, esclusioni, conflitti,
errori e destinazioni private. Schema CSV, flusso Dify e archivio pCloud invariati.

### Priorità sede legale (2.0.2)

Fra più sedi sul sito, prevale la provincia dell'indirizzo esplicitamente indicato
come **sede legale** (anche sede legale e operativa, registered/legal office).
La scelta considera tutte le pagine consultate. Dalla versione 2.0.3, se la sede
legale non è identificabile con certezza, viene scelta fra le province effettivamente
ricavate dagli indirizzi quella con più abitanti, secondo la regola richiesta
dall'utente. Il confronto riguarda l'intera provincia, non il capoluogo.
Si usa lo snapshot ISTAT provvisorio al 31 dicembre 2025, aggregato sui confini
provinciali attuali. Nessuna provincia viene aggiunta se non trovata sul sito.
Se non ci sono candidate, mancano valori demografici o c'è parità, il campo
resta vuoto. La priorità ai dati risolti dall'email resta invariata.
