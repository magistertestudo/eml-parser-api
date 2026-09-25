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
