# EML Parser API — candidato v2.0

## Configurazione corrente: link pubblico di lettura

L'ultima scelta dell'utente sostituisce tutte le opzioni intermedie sotto:
`PCLOUD_LINK_MODE=public_read`. L'app archivia EML e allegati e inserisce nel CSV
il link normale pCloud per consultare/scaricare. Nessuna richiesta file e nessun
upload dal link per i destinatari. Rimosso il ramo sperimentale shared_upload.
Conservati architettura FastAPI/Dify e token OAuth originale già inserito su Railway.

Collaudo reale riuscito: `getfolderpublink` con token OAuth originale sulla cartella
TEST ID 33367484071; `showpublink` senza autenticazione restituisce la stessa cartella
con i due file sintetici. Prima verificati creazione cartella, upload EML/allegato e
checksum dell'allegato. Test locali: 69 superati. `git diff --check` superato.
Variabili necessarie: PCLOUD_AUTH_TYPE=oauth, PCLOUD_LINK_MODE=public_read,
PCLOUD_API_HOST=api.pcloud.com, PCLOUD_PARENT_FOLDER_ID=29662386698,
PCLOUD_ACCESS_TOKEN riservato, PCLOUD_ENABLED=true solo all'attivazione del codice v2.
Il collaudo completo Dify/AI/CSV in produzione resta da eseguire dopo la distribuzione.

## Stato aggiornato al 29 settembre 2026

### Collaudo reale dopo autorizzazione a procedere

Verifica successiva con nuovo token ottenuto dopo autorizzazione con
`permissions=manageshares`: `listfolder` risponde HTTP 200/result 0 e conferma
la destinazione; `listuploadlinks` risponde HTTP 200/result 1000. Il permesso
aggiuntivo non risolve il blocco osservato. Il nuovo token è conservato in
`.env.pcloud.oauth.manageshares.secret`, escluso da Git, senza sostituire quello
precedente. Non sostituire il token Railway come presunta soluzione. Serve
conferma pCloud sul supporto OAuth delle richieste file; nessun deploy eseguito.

Creata nella destinazione la cartella `TEST TECNICO EML v2 - 2026-09-29` con
email sintetica e allegato di prova (2 file). `listfolder`, creazione cartella,
upload e `listpublinks` funzionano con il token OAuth. **Sia `listuploadlinks`
sia `createuploadlink` restituiscono codice 1000 con il medesimo token**.
Di conseguenza il collaudo si interrompe prima della generazione del link;
nessun caricamento anonimo è stato provato con successo. Il token non è
globalmente invalido: altre operazioni autenticate hanno avuto successo.
La causa specifica (supporto OAuth dell'endpoint o permessi aggiuntivi) non è
ancora confermata. Non distribuire/attivare pCloud finché non risolto.
I file di test sono lasciati nella cartella per controllo, nessun dato cliente
è stato caricato. I 67 test locali restano simulazioni e non provano questo
permesso reale. Il tentativo di aprire Railway è terminato per timeout;
nessuna variabile né distribuzione è stata modificata da questo collaudo.

**Scelta finale successiva dell'utente:** link diretto pCloud per caricare senza
account, rinunciando alla consultazione dal medesimo link. Usare
`PCLOUD_LINK_MODE=upload_request` e `PCLOUD_AUTH_TYPE=oauth`. Questa scelta sostituisce
il requisito intermedio di link unico lettura+upload descritto sotto. Non serve
aggiungere un portale su Railway. L'EML e gli allegati restano nella cartella offerta.

Questa sezione sostituisce le indicazioni storiche sotto relative a token mancanti.
App OAuth attiva; scambio del codice eseguito localmente con `pcloud_oauth.py`.
Token salvato in `.env.pcloud.oauth.secret`, escluso da Git e con permessi 0600.
Verifica reale `listfolder`: ID 29662386698, cartella e proprietà confermati.
L'utente ha dichiarato di aver inserito PCLOUD_ACCESS_TOKEN e PCLOUD_AUTH_TYPE=oauth
su Railway; non ancora verificati nella UI né distribuiti. Nessun deploy eseguito.
Il login diretto precedente è fallito con codice 1022, senza token; non usarlo per questa installazione.

L'utente ha confermato che Cartella Allegati deve contenere **un unico link per
vedere/scaricare e caricare**. La modalità upload_request esistente non soddisfa
questo requisito e non va attivata come sostituto. Le API pubblicate getfolderpublink
e changepublink non documentano il parametro per abilitare l'upload sul link condiviso.
La guida ufficiale https://help.pcloud.com/article/file-requests chiarisce inoltre
che il caricamento su un link condiviso richiede un account pCloud; l'upload senza
account è proprio delle File Requests. Occorre verificare l'opzione richiesta e il
suo contratto API prima di completare la release. Test OAuth aggiunti senza segreti.

Analisi e implementazione del 25 settembre 2026. Base verificata: `0c0ca9cdb1017a25e2c92bec6e00fa7d600c436e` (`update crm`), uguale alla HEAD GitHub alla verifica. Repository originale: `/Users/emanuelemazzieri/Documents/GitHub/eml-parser-api`. Copia isolata: `eml-parser-api-v2`, branch `release/v2.0`. Nessun deploy eseguito.

## Architettura conservata

Dify invia `files` (EML o ZIP) e `protocol_start` a `POST /parse`. La stessa API estrae i contenuti, chiama l'AI, costruisce i record Delera e restituisce `contatti_delera.csv`. pCloud è un adattatore HTTP nella stessa applicazione, senza nuovi servizi, database, code o nodi Dify. I file binari non vengono inclusi nel prompt: all'AI continuano ad arrivare solo i nomi degli allegati. L'originale è caricato senza riserializzarlo.

Il codice preesistente dichiara già la versione 2.0: questo branch identifica il nuovo candidato funzionale, senza sovrascrivere tag o release precedenti.

## Piano e modifiche file per file

| File | Intervento | Stato |
|---|---|---|
| `parser.py` | Conservare byte e metadati degli allegati; includere inline, allegati senza nome, email annidate; testo da HTML quando manca plain text; evitare che le firme delle email allegate contaminino l'estrazione. | Implementato |
| `province_resolver.py` | Ricerca offline per sigla/nome, comune, CAP esatto e località postale nell'indirizzo; normalizzazione accenti/punteggiatura; controllo conflitti e Paesi esteri. | Implementato |
| `province_legacy.py` | Spostare la tabella esistente delle sigle, mantenendo le denominazioni CRM già utilizzate, ad esempio Firenze, Bolzano, Aosta. | Implementato |
| `data/comuni.json` | Anagrafica ufficiale ISTAT, 7.894 comuni, alternative linguistiche; CAP integrati separatamente. | Aggiornato; limiti postali sotto |
| `scripts/update_istat.py` | Import offline ripetibile dello XLSX ISTAT, controllo schema e codici, nessuna invenzione di CAP. | Implementato |
| `data/README.md`, `data/LICENSE-DATA` | Provenienza, revisione esatta, attribuzione, trasformazioni e limiti del dataset. | Inclusi |
| `crm_mapper.py` | Sostituire la conversione della sola sigla con il resolver. Opportunity Name e altri campi rimangono come prima. | Implementato |
| `pcloud_client.py` | Configurazione, verifica cartella proprietaria, creazione/riuso per Opportunity Name, caricamenti, verifica dimensioni, creazione/riuso link raccolta, gestione errori. | Implementato e simulato; manca prova autenticata |
| `main.py` | Collegare archiviazione e campo Cartella Allegati dopo il mapping; errore 502 su fallimento cloud; controllare input e ZIP; eseguire il lavoro bloccante fuori dall'event loop. | Implementato |
| `prompt_v1.md` | Richiedere i campi geografici già previsti, tutti riferiti alla stessa sede del mittente; evitare confusione con luogo di intervento e email precedenti. | Implementato |
| `requirements.txt` | Dichiarare `httpx==0.28.1`, già famiglia di dipendenze usata dal client AI. | Implementato |
| `.env.example`, `.gitignore` | Configurazione senza segreti e esclusione ambiente locale. | Inclusi |
| `tests/test_v2.py` | Test geografici, MIME, upload simulati, errori, retry, ZIP e contratto CSV. | 56 test superati |
| `crm_schema.py`, `csv_exporter.py`, `openai_client.py`, `models.py` | Nessuna modifica necessaria. Cartella Allegati è già nello schema; i modelli Pydantic non sono usati nel flusso corrente. | Invariati |

## Provincia: comportamento e limiti

Esempi: `fi` → Firenze; `Sesto Fiorentino` → Firenze; CAP `00118` → Roma; `Via Roma 20, 50019 Sesto Fiorentino (FI)` → Firenze. `Via Roma 20` da sola non dimostra la provincia di Roma. I CAP restano stringhe di cinque cifre. Sigle, comune e CAP riconosciuti devono convergere: Milano con FI produce campo vuoto e avviso nei log con il protocollo, senza riportare il testo dell'email.

Le denominazioni estese italiane seguono la tabella CRM preesistente; vengono riconosciute anche alcune varianti ufficiali/bilingui. Le località estere, i dati assenti, i CAP sconosciuti e i conflitti non vengono indovinati. Non si scandisce tutto il corpo cercando sigle isolate: parole comuni o sedi di destinatari creerebbero falsi positivi.

L'anagrafica è ora importata direttamente dall'[elenco ufficiale ISTAT al 21 febbraio 2026](https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/): 7.894 comuni, inclusa la riforma della Sardegna. Sigle CI, OG, OT e VS sono associate alle denominazioni correnti; SU da sola non genera più Sud Sardegna. Comune e CAP possono risolvere il caso anche se la firma riporta SU. Una sigla storica ancora valida altrove ma in conflitto con il comune produce un avviso, non una correzione arbitraria.

I CAP restano quelli best-effort del [dataset RP92/comuni-italiani](https://github.com/RP92/comuni-italiani), trasferiti solo a denominazioni identiche. Quattro comuni nuovi/ridenominati sono senza CAP nella tabella: Murisengo Monferrato, Castegnero Nanto, Tripi - Abakainon e Jonadi; la ricerca per nome funziona. Non si dichiara una garanzia del 100% sui CAP o sull'estrazione AI. Fonte, hash del file ufficiale e licenze sono in data/README.md; scripts/update_istat.py consente di ripetere l'importazione.

## Verifica pCloud: API, SDK e requisito del link

Documentazione ufficiale consultata il 25 settembre 2026:

| Funzione | API documentata | Dipendenze |
|---|---|---|
| Creare/riusare cartella | [createfolderifnotexists](https://docs.pcloud.com/methods/folder/createfolderifnotexists.html) | Autenticazione, `folderid` padre, nome |
| Caricare EML/allegati | [uploadfile](https://docs.pcloud.com/methods/file/uploadfile.html) | Autenticazione, destinazione, multipart; verifica `result` e metadati |
| Generare link per ricevere file | [createuploadlink](https://docs.pcloud.com/methods/upload_links/createuploadlink.html) | Autenticazione, cartella di proprietà, commento; restituisce URL |
| Riusare link raccolta | [listuploadlinks](https://docs.pcloud.com/methods/upload_links/listuploadlinks.html) | Autenticazione; il codice seleziona un link senza scadenza/limiti |
| Link pubblico di cartella | [getfolderpublink](https://docs.pcloud.com/methods/public_links/getfolderpublink.html) | Autenticazione; non documenta il permesso anonimo di upload |
| Modificare link pubblico | [changepublink](https://docs.pcloud.com/methods/public_links/changepublink.html) | I parametri pubblicati non includono un interruttore «chiunque può caricare» |

**Distinzione essenziale:** un link di raccolta permette di inviare documenti senza account, come descritto nelle [File Requests pCloud](https://help.pcloud.com/article/file-requests). Non equivale al link di cartella con visualizzazione/scaricamento più upload richiesto nella conversazione. Il candidato implementa soltanto il link di raccolta documentato e lo inserisce in Cartella Allegati quando si configura esplicitamente `PCLOUD_LINK_MODE=upload_request`. Non presenta questo come implementazione verificata dell'opzione della UI.

Il [blog ufficiale pCloud](https://blog.pcloud.com/improved-sharing-options-in-pcloud-to-help-you-do-more/) conferma la disponibilità di lettura e upload sullo stesso link nell’interfaccia. Per ottenere precisamente il link condiviso con upload via API serve verificare sull'account il comportamento della UI e ottenere da pCloud il contratto/supporto dell'endpoint o dei parametri specifici. Non sono stati inventati parametri `enableupload` o simili, né usati endpoint privati. Questo punto rimane aperto per la release definitiva.

Il portale [pCloud Developers](https://docs.pcloud.com/) elenca SDK per C, Java, JavaScript, PHP e Swift. Non vi è un SDK Python ufficiale elencato: per evitare un wrapper comunitario ulteriore, il progetto usa le API HTTP JSON direttamente.

## Credenziali e cartella di destinazione

L'[OAuth code flow](https://docs.pcloud.com/methods/oauth_2.0/authorize.html) richiede un'app registrata (`client_id`), autorizzazione del proprietario e scambio del codice con `client_secret` tramite [oauth2_token](https://docs.pcloud.com/methods/oauth_2.0/oauth2_token.html). Il token viene poi configurato sul server. Il candidato consuma un token già ottenuto; non aggiunge pagine/callback OAuth all'API esistente.

Usare l'hostname restituito dall'autorizzazione: `api.pcloud.com` oppure `eapi.pcloud.com`. Il client accetta solo questi host HTTPS. Il parametro [access_token](https://docs.pcloud.com/methods/intro/global_parameters.html) viene inviato nel corpo POST, mai nel link CSV o nell'URL di richiesta. Un link pubblico non sostituisce il token, la proprietà della cartella o l'accesso dell'app a quella cartella. L'account deve poter creare link; gestire anche gli errori di verifica email e permessi.

Verifica reale di sola lettura del link ricevuto:

- Server US: `result=0`, nome **IN-SAFETY-2026**, `folderid=29662386698`.
- Server EU: `result=7001` (codice non valido).
- L’utente ha confermato che questa è la destinazione effettiva: creare le cartelle offerta direttamente al suo interno, senza una cartella intermedia OFFERTE 2026.

Destinazione predefinita e riportata in `.env.example`: `PCLOUD_API_HOST=api.pcloud.com`, `PCLOUD_PARENT_FOLDER_ID=29662386698`. Il codice verifica ID, tipo cartella e proprietà tramite `listfolder`, senza imporre un nome. Una rinomina della cartella non cambia la destinazione. Serve ancora il token del proprietario per eseguire le scritture.

## Attivazione e collaudo reale da completare

1. Configurare `OPENAI_API_KEY`, `PCLOUD_ACCESS_TOKEN`, `PCLOUD_API_HOST`, `PCLOUD_PARENT_FOLDER_ID` nelle variabili del servizio; non in Git o in chat. `.env.example` è solo un esempio: non viene caricato automaticamente dall'app.
2. Scegliere consapevolmente `PCLOUD_LINK_MODE=upload_request` se il link di sola raccolta soddisfa il flusso operativo; altrimenti completare il punto sul link condiviso prima di attivare.
3. Impostare `PCLOUD_ENABLED=true` in ambiente di prova. Con `false`, il CSV funziona senza pCloud e Cartella Allegati resta vuoto.
4. Inviare un'email di prova con allegati, verificare cartella e file, confrontare hash dell'originale e contenuti degli allegati, aprire il link in una finestra anonima e provare l'upload. Provare anche token errato e cartella errata.
5. Validare l'anagrafica geografica e casi reali anonimizzati. Solo dopo questi controlli promuovere il candidato e collegare la release al deploy Railway.

Non sono stati eseguiti upload, generati link sull'account, chiamati modelli a pagamento, pubblicati commit o distribuita una release. La destinazione è confermata; manca il token per il collaudo reale.

## Retry, nomi e limiti operativi

La cartella coincide con Opportunity Name; caratteri non validi e nomi troppo lunghi sono normalizzati con suffisso hash per evitare collisioni. I file sono prefissati con hash SHA-256 dell'EML; gli allegati hanno anche indice MIME e nome originale normalizzato. Allegati omonimi e messaggi diversi non si sovrascrivono. Stessa email e stesso Opportunity Name producono gli stessi nomi al retry; pCloud aggiorna la medesima risorsa. EML annidati sono estratti dal MIME e possono essere riserializzati: l'EML originale principale resta byte per byte intatto.

Non esiste transazione tra tutti gli upload: un errore può lasciare file/cartelle parziali, ma impedisce il CSV di successo. Riprovare gli stessi input e protocollo. Se l'AI cambia Azienda al retry, cambia anche Opportunity Name: per idempotenza forte servirebbe persistere il risultato AI/ID operazione, escluso da questa modifica minima. Richieste concorrenti possono creare più link raccolta per la stessa cartella; i file hanno nomi stabili. Nessuna cancellazione automatica viene eseguita.

Il servizio conserva l'impostazione sincrona per batch e legge i file in memoria. Batch grandi possono superare memoria o timeout Dify/Railway: il collaudo deve stabilire i limiti operativi. L'endpoint preesistente non ha autenticazione applicativa; controllarne l'accessibilità prima di attivare una credenziale che consente scritture sul cloud.

## Verifica locale

Eseguiti `python -m pytest -q`: **56 passed**, Python 3.9 locale con dipendenze del progetto. Verificati contratto CSV e progressivi, HTML, byte binari, EML annidati, omonimi, nomi sicuri, errori pCloud a ogni fase, timeout, controllo destinazione, dimensione upload, riuso link e configurazione esplicita. Le chiamate AI e le scritture pCloud nei test sono simulate. `git diff --check` superato.

## Ripresa del lavoro

Aggiornata l’anagrafica ufficiale; aggiunti 16 controlli, compreso il conflitto tra provincia esplicita e località senza CAP nell’indirizzo. Totale 56 test superati. Nessuna modifica ai permessi pCloud e nessun deploy: la destinazione è stata confermata nel link originale; restano necessarie credenziali server e verifica del contratto API per il link condiviso con upload.

## Destinazione confermata dall’utente

Le cartelle Opportunity Name vengono create direttamente dentro IN-SAFETY-2026 (ID 29662386698), sul server api.pcloud.com. Rimosso il controllo sul nome OFFERTE 2026; verificati ID, tipo e proprietà. Due test aggiuntivi controllano configurazione e creazione diretta, senza cartelle intermedie. Totale: 56 test.

## Alternativa 1 — autenticazione diretta (27 settembre 2026)

Implementata la selezione `PCLOUD_AUTH_TYPE=direct` con `PCLOUD_AUTH_TOKEN`, inviato nel parametro POST `auth`. La modalità OAuth resta disponibile con `PCLOUD_AUTH_TYPE=oauth` e `PCLOUD_ACCESS_TOKEN`. I token non compaiono nella rappresentazione della configurazione.

`pcloud_login.py` esegue su terminale locale un login HTTPS documentato `userinfo/getauth`, leggendo la password senza eco. Richiede durata massima e inattività di 30 giorni. Non conserva la password e non legge credenziali del browser. Salva il token in `.env.pcloud.secret` (permessi 0600, escluso da Git), poi verifica proprietà e ID della cartella senza scritture remote. Se il servizio richiede 2FA o rifiuta la procedura, interrompe senza indebolire le protezioni. La password si inserisce solo nel terminale, mai in chat.

La durata richiesta va verificata con pCloud e il token rinnovato alla scadenza; il file locale non è caricato automaticamente dall’app. Trasferire il token nelle variabili riservate Railway solo dopo il successo del test. L’attivazione resta separata: il codice v2 è ancora nel branch locale e il link condiviso con upload non è ancora verificato.

Test: 64 superati; autenticazione reale in attesa dell’inserimento locale delle credenziali da parte dell’utente.
