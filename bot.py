import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Configurazione bacheche (ora monitoriamo anche il Prof. Siviero singolarmente)
BACHECHE = [
    {"nome": "EPP", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi", "file": "pub_epp.txt", "emoji": "🔔"},
    {"nome": "EPP (Docenti)", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi-docente", "file": "pub_epp_docenti.txt", "emoji": "👨‍🏫"},
    {"nome": "Prof. Siviero", "url": "https://www.dei.unict.it/corsi/lm-56-epp/docenti/uid.dWtKQ08vZkRRVlJJaTNkUDdGY3U3WnJLam1SM2RrQS92R3NybUlHZUpUVT0=", "file": "pub_siviero.txt", "emoji": "📝"},
    {"nome": "DEI", "url": "https://www.dei.unict.it/Comunicazioni/elenco-news", "file": "pub_dei.txt", "emoji": "🏛️"},
    {"nome": "UNICT", "url": "https://www.unict.it/it/ateneo/news", "file": "pub_unict.txt", "emoji": "🌐"}
]

def get_anteprima(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return "Dettagli disponibili nel link."
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Selettori per trovare il testo vero dell'avviso
        corpo = (soup.find('div', class_='field-name-body') or 
                 soup.find('div', class_='field-item even') or
                 soup.find('div', id='parent-fieldname-text') or 
                 soup.find('article') or 
                 soup.find('div', class_='region-content'))
        
        if corpo:
            for s in corpo(['script', 'style']): s.decompose()
            testo = corpo.get_text(separator=' ', strip=True)
            if "non è stata trovata" in testo.lower(): return "Contenuto nel link."
            return testo[:350] + "..." if len(testo) > 350 else testo
        return "Contenuto disponibile nel link."
    except: return ""

def check():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for b in BACHECHE:
        try:
            print(f"Controllo: {b['nome']}")
            res = requests.get(b['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Cerchiamo nell'area centrale della pagina
            area = soup.find('section', id='main-content') or soup.find('div', class_='region-content') or soup
            links = area.find_all('a', href=True)
            
            avviso = None
            for l in links:
                href = l['href']
                testo = l.get_text(strip=True)
                
                # FILTRO AGGIORNATO (Riga 40): inclusi /content/ e /avviso/
                if any(x in href for x in ['/comunicazioni/', '/avvisi/', '/news/', '/avviso/', '/content/']):
                    if len(testo) > 15:
                        # Ignoriamo i link fissi dei menu
                        blacklist = ['avvisi del corso', 'avvisi docente', 'elenco-news', 'home', 'didattica']
                        if not any(word in testo.lower() for word in blacklist):
                            avviso = l
                            break
            
            if not avviso: continue

            titolo = avviso.get_text(strip=True)
            # Costruzione link pieno
            link_pieno = avviso['href'] if avviso['href'].startswith('http') else ("https://www.unict.it" if "unict.it" in b['url'] else "https://www.dei.unict.it") + avviso['href']
            
            ultimo = ""
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f: ultimo = f.read().strip()

            if titolo != ultimo:
                txt = get_anteprima(link_pieno, headers)
                if "non è stata trovata" in txt.lower(): continue
                
                msg = f"{b['emoji']} *{b['nome']}: {titolo}*\n\n{txt}\n\n🔗 [Leggi avviso completo]({link_pieno})"
                res_tg = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                
                # Salviamo il titolo solo se l'invio è riuscito
                if res_tg.status_code == 200:
                    with open(b['file'], "w", encoding="utf-8") as f: f.write(titolo)
        except Exception as e: 
            print(f"Errore {b['nome']}: {e}")

if __name__ == "__main__":
    check()
