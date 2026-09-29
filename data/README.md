# Dati geografici

Anagrafica: ISTAT, Elenco dei comuni italiani, foglio CODICI al 21_02_2026, acquisito il 25 settembre 2026.
Fonte: https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx
Pagina: https://www.istat.it/classificazione/codici-dei-comuni-delle-province-e-delle-regioni/
SHA-256 XLSX: 83842076860450f7e482daecea6b7a769f5f93d0bf5b0d48802b44896d7a26d5
7.894 comuni e relativi codici ISTAT; include il nuovo assetto della Sardegna.
Trasformazione: selezione denominazione italiana, altra lingua, provincia, sigla e codice ISTAT.
Import ripetibile offline con scripts/update_istat.py; richiede lo XLSX ufficiale e il precedente JSON per conservare i CAP.

CAP: conservati solo per comuni con identica denominazione nello snapshot RP92/comuni-italiani,
commit e0df3f548dc8ef94e0d30fba69bb5344858ab26f, https://github.com/RP92/comuni-italiani.
Derivazione originaria ISTAT/Garda Informatica, best-effort, non fonte ufficiale di Poste.
Per Murisengo Monferrato, Castegnero Nanto, Tripi - Abakainon e Jonadi non sono stati trasferiti
CAP da denominazioni precedenti senza una verifica postale. Questi comuni si risolvono comunque per nome.

Attribuzione e licenze: dati amministrativi ISTAT CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/it/);
componente CAP RP92/ISTAT/Garda Informatica CC BY 4.0, con avviso originario in LICENSE-DATA.
Questo file e l'importer documentano le modifiche. Non attribuire a ISTAT i CAP integrati da terzi.
Nessuna interrogazione esterna con indirizzi/email durante la normalizzazione.

## Popolazione provinciale per ripiego (2.0.3)

Fonte: ISTAT Demo, bilancio demografico e popolazione residente al 31 dicembre
2025 (dato provvisorio), https://demo.istat.it/app/?i=P02.
Download: https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip
Acquisizione: 29 settembre 2026.
SHA-256 ZIP: 614fef7e3e5fe559aafac4ecf82cf6ac8a968d4d4f03103ee90d9aaa692de5f2.

`province_population.json` aggrega i 7.896 comuni del bilancio 2025 nelle 110
province dell'anagrafica attuale: 58.942.828 residenti complessivi. Campo usato:
“Popolazione al 31 dicembre - Totale”, entrambi i sessi. Non sono popolazioni
dei capoluoghi, né previsioni demografiche. I dati non si aggiornano da soli:
il file riporta data, fonte, stato e hash; rigenerazione con
`scripts/update_population.py /percorso/P2_2025_it_Comuni.zip`.

Le ricodifiche della Sardegna sono abbinate per nome univoco entro la regione;
Lirio è aggregato a Montalto Pavese e Castegnero/Nanto a Castegnero Nanto.
Fonte delle fusioni: https://www.istat.it/wp-content/uploads/2026/02/Novita-2026-2017-26febbraio2026.pdf.
Import interrotto se risultano duplicati, abbinamenti ambigui o comuni mancanti.
Dati ISTAT CC BY 3.0 IT, aggregazione effettuata da questo progetto.
