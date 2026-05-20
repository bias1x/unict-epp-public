# 📢 Unict EPP Public Bot

Questo progetto nasce con l'obiettivo di supportare gli studenti del mio corso di laurea in **Economia e Politiche Pubbliche (LM-56)** dell'Università degli Studi di Catania, automatizzando la ricezione degli avvisi didattici.

## 🚀 Funzionamento
Il bot monitora costantemente diverse sezioni del portale **unict.it** e del dipartimento **DEI**. Grazie a un sistema di web scraping, identifica la pubblicazione di nuovi avvisi e invia istantaneamente una notifica su un canale Telegram dedicato, includendo:
- 🏷️ **Categoria** (EPP, DEI, UniCT, Docenti)
- 📌 **Titolo dell'avviso**
- 📝 **Anteprima del contenuto** (estratta automaticamente dal corpo della pagina)
- 🔗 **Link diretto** per la lettura completa

## 🛠️ Architettura Tecnica
Il sistema è progettato per essere leggero, efficiente e a costo zero (Serverless):
- **Linguaggio:** Python 3.9
- **Librerie principali:** `BeautifulSoup4` per il parsing HTML e `requests` per le chiamate HTTP.
- **Automazione:** GitHub Actions. Il bot viene eseguito ogni ora (o secondo schedulazione) su server GitHub, eliminando la necessità di mantenere un PC o un server sempre acceso.
- **Persistence:** Il bot utilizza file di stato (`.txt`) per memorizzare l'ultimo avviso inviato e prevenire notifiche duplicate.

## 📂 Struttura del Repository
- `bot.py`: Il cuore del sistema con la logica di scraping e invio notifiche.
- `.github/workflows/check_avvisi.yml`: Configurazione dell'automazione CI/CD.
- `pub_*.txt`: File di log per la sincronizzazione degli avvisi.
- `requirements.txt`: Elenco delle dipendenze necessarie.

## 🛡️ Sicurezza
Le credenziali sensibili (Telegram Token e Chat ID) non sono salvate nel codice, ma gestite tramite **GitHub Secrets**, garantendo l'integrità e la sicurezza del bot anche in un repository pubblico.
