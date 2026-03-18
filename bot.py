import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BACHECHE = [
    {"nome": "EPP", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi", "file": "pub_epp.txt", "emoji": "🔔"},
    {"nome": "DEI [Notizie]", "url": "https://www.dei.unict.it/Comunicazioni/elenco-news", "file": "pub_dei.txt", "emoji": "🏛️"},
    {"nome": "DEI [Eventi]", "url": "https://www.dei.unict.it/Comunicazioni/elenco-eventi_dei", "file": "pub_dei_eventi.txt", "emoji": "🏛️"},
    {"nome": "UNICT", "url": "https://www.unict.it/it/ateneo/news", "file": "pub_unict.txt", "emoji": "🌐"},
    {"nome": "Prof. Barone", "url": "https://www.dei.unict.it/corsi/lm-56-epp/docenti/uid.amxrSnRCMUs2TmhXandDMGM4VllTNXJLam1SM2RrQS92R3NybUlHZUpUVT0=?archivio-avvisi", "file": "pub_barone.txt", "emoji": "🏃🏻‍♂️"},
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for b in BACHECHE:
        try:
            res = requests.get(b['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            area = soup.find('section', id='main-content') or soup.find('div', class_='region-content') or soup
            links = area.find_all('a', href=True)
            
            # Carichiamo la cronologia degli avvisi già inviati
            history = []
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f:
                    history = f.read().splitlines()

            # Troviamo tutti i link validi (non solo il primo!)
            nuovi_avvisi = []
            for l in links:
                href = l['href']
                titolo = l.get_text(strip=True)
                
                # Filtri di validità
                if any(x in href for x in ['/comunicazioni/', '/avvisi/', '/content/', '/news/']) and len(titolo) > 15:
                    if not any(href.lower().endswith(x) for x in ['/home', '/elenco-news', '/news', '/avvisi-docente', '/elenco-eventi_dei']):
                        link_completo = urljoin(b['url'], href)
                        
                        # Se il titolo non è nella cronologia, è nuovo
                        if titolo not in history:
                            nuovi_avvisi.append({"titolo": titolo, "link": link_completo})

            # Inviamo i nuovi avvisi (dal più vecchio al più recente)
            for item in reversed(nuovi_avvisi):
                txt = get_anteprima(item['link'], headers)
                # Usiamo HTML invece di Markdown per evitare errori con caratteri speciali
                msg = f"{b['emoji']} <b>{b['nome']}: {item['titolo']}</b>\n\n{txt}\n\n<a href='{item['link']}'>🔗 Leggi avviso completo</a>"
                
                r = requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                    json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
                )
                
                if r.status_code == 200:
                    with open(b['file'], "a", encoding="utf-8") as f:
                        f.write(item['titolo'] + "\n")
                
        except Exception as e:
            print(f"Errore {b['nome']}: {e}")

if __name__ == "__main__":
    check()
