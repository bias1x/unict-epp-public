import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Configurazione bacheche (4 fonti)
BACHECHE = [
    {"nome": "EPP", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi", "file": "pub_epp.txt", "emoji": "🔔"},
    {"nome": "EPP (Docenti)", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi-docente", "file": "pub_epp_docenti.txt", "emoji": "👨‍🏫"},
    {"nome": "DEI", "url": "https://www.dei.unict.it/Comunicazioni/elenco-news", "file": "pub_dei.txt", "emoji": "🏛️"},
    {"nome": "UNICT", "url": "https://www.unict.it/it/ateneo/news", "file": "pub_unict.txt", "emoji": "🌐"}
]

def get_anteprima(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Selettori originali che funzionano bene su UNICT e DEI
        corpo = soup.find('div', class_='field-name-body') or soup.find('div', id='parent-fieldname-text') or soup.find('article')
        if not corpo: corpo = soup.find('div', class_='region-content')
        if corpo:
            for s in corpo(['script', 'style']): s.decompose()
            testo = corpo.get_text(separator=' ', strip=True)
            # Evita di inviare il testo dell'errore 404 come anteprima
            if "non è stata trovata" in testo: return "Dettagli nel link."
            return testo[:350] + "..." if len(testo) > 350 else testo
        return "Dettagli disponibili nel link."
    except: return ""

def check():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for b in BACHECHE:
        try:
            print(f"Controllo: {b['nome']}")
            res = requests.get(b['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            area = soup.find('section', id='main-content') or soup.find('div', class_='region-content') or soup
            links = area.find_all('a', href=True)
            
            avviso = None
            for l in links:
                href = l['href']
                testo = l.get_text(strip=True)
                
                # FILTRO POTENZIATO:
                # 1. Deve contenere i percorsi tipici degli avvisi (incluso /avviso/ al singolare)
                # 2. Il testo deve essere un titolo vero (lungo più di 18 caratteri)
                # 3. NON deve essere un link di navigazione o il titolo della pagina stessa
                if any(x in href for x in ['/comunicazioni/', '/avvisi/', '/news/', '/avviso/']):
                    if len(testo) > 18:
                        blacklist = ['/home', '/elenco-news', '/news', '/avvisi-docente', 'avvisi docente', 'avvisi didattica']
                        if not any(word in href.lower() or word in testo.lower() for word in blacklist):
                            avviso = l
                            break
            
            if not avviso: 
                print(f"Nessun nuovo avviso valido trovato per {b['nome']}")
                continue

            titolo = avviso.get_text(strip=True)
            # Costruzione link
            link = avviso['href'] if avviso['href'].startswith('http') else ("https://www.unict.it" if "unict.it" in b['url'] else "https://www.dei.unict.it") + avviso['href']
            
            ultimo = ""
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f: ultimo = f.read().strip()

            if titolo != ultimo:
                print(f"INVIO NOTIFICA: {titolo}")
                txt = get_anteprima(link, headers)
                # Se l'anteprima indica un errore, saltiamo l'invio
                if "non è stata trovata" in txt: continue
                
                msg = f"{b['emoji']} *{b['nome']}: {titolo}*\n\n{txt}\n\n🔗 [Leggi avviso completo]({link})"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                
                with open(b['file'], "w", encoding="utf-8") as f: f.write(titolo)
        except Exception as e: 
            print(f"Errore su {b['nome']}: {e}")

if __name__ == "__main__":
    check()
