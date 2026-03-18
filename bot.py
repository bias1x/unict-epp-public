import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BACHECHE = [
    {"nome": "EPP", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi", "file": "pub_epp.txt", "emoji": "🔔"},
    {"nome": "DEI", "url": "https://www.dei.unict.it/Comunicazioni/elenco-news", "file": "pub_dei.txt", "emoji": "🏛️"},
    {"nome": "UNICT", "url": "https://www.unict.it/it/ateneo/news", "file": "pub_unict.txt", "emoji": "🌐"},
    {"nome": "Docenti", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi-docente", "file": "pub_docenti.txt", "emoji": "👩🏻‍🏫"}
]

def get_anteprima(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        corpo = soup.find('div', class_='field-name-body') or soup.find('div', id='parent-fieldname-text') or soup.find('article')
        if not corpo: corpo = soup.find('div', class_='region-content')
        if corpo:
            for s in corpo(['script', 'style']): s.decompose()
            testo = corpo.get_text(separator=' ', strip=True)
            return testo[:350] + "..." if len(testo) > 350 else testo
        return "Dettagli disponibili nel link."
    except: return ""

def check():
    headers = {'User-Agent': 'Mozilla/5.0'}
    for b in BACHECHE:
        try:
            res = requests.get(b['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            area = soup.find('section', id='main-content') or soup.find('div', class_='region-content') or soup
            links = area.find_all('a', href=True)
            
            # --- MODIFICA 1: Legge tutta la cronologia nel file ---
            cronologia = []
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f:
                    cronologia = [line.strip() for line in f.readlines()]

            avviso = None
            for l in links:
                href = l['href']
                if any(x in href for x in ['/comunicazioni/', '/avvisi/', '/lezioni/', '/esami/', '/content/', '/news/']) and len(l.text) > 15:
                    if not any(href.lower().endswith(x) for x in ['/home', '/elenco-news', '/news', '/avvisi-docente']):
                        
                        titolo_attuale = l.get_text(strip=True)
                        # --- MODIFICA 2: Controllo se è già stato inviato in passato ---
                        if titolo_attuale not in cronologia:
                            avviso = l
                            break # MANTENIAMO IL BREAK A 1 (guarda solo il primo nuovo)
            
            if not avviso: continue

            titolo = avviso.get_text(strip=True)
            link = avviso['href'] if avviso['href'].startswith('http') else ("https://www.unict.it" if "unict.it/it" in b['url'] else "https://www.dei.unict.it") + avviso['href']
            
            txt = get_anteprima(link, headers)
            msg = f"{b['emoji']} *{b['nome']}: {titolo}*\n\n{txt}\n\n🔗 [Leggi avviso completo]({link})"
            
            r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            
            # Se l'invio è riuscito, aggiunge il titolo al file (append "a")
            if r.status_code == 200:
                with open(b['file'], "a", encoding="utf-8") as f:
                    f.write(titolo + "\n")
                    
        except Exception as e: print(f"Errore {b['nome']}: {e}")

if __name__ == "__main__":
    check()
