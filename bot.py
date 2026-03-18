import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
# Qui metteremo il nome del canale (es: @MioCanale)
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BACHECHE = [
    {"nome": "EPP", "url": "https://www.dei.unict.it/corsi/lm-56-epp/avvisi", "file": "pub_epp.txt", "emoji": "🔔"},
    {"nome": "DEI", "url": "https://www.dei.unict.it/Comunicazioni/elenco-news", "file": "pub_dei.txt", "emoji": "🏛️"},
    {"nome": "UNICT", "url": "https://www.unict.it/it/ateneo/news", "file": "pub_unict.txt", "emoji": "🌐"},
    {"nome": "Barone", "url": "https://www.dei.unict.it/corsi/lm-56-epp/docenti/uid.amxrSnRCMUs2TmhXandDMGM4VllTNXJLam1SM2RrQS92R3NybUlHZUpUVT0=?archivio-avvisi", "file": "pub_barone.txt", "emoji": "🏃🏻"},
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
            
            # Carichiamo la cronologia completa per confrontare più avvisi
            cronologia = []
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f:
                    cronologia = [line.strip() for line in f.readlines()]

            inviati_ora = 0 # Contatore per non superare i 3 invii
            
            for l in links:
                if inviati_ora >= 3: break # Limite di sicurezza: max 3 nuovi per volta
                
                href = l['href']
                titolo = l.get_text(strip=True)
                parole_chiave = ['/comunicazioni/', '/avvisi/', '/content/', '/lezioni/', '/esami/', '/news/']
                
                # Controllo validità link
                if any(x in href for x in parole_chiave) and len(titolo) > 10:
                    if not any(href.lower().endswith(x) for x in ['/home', '/elenco-news', '/news', '/avvisi-docente']):
                        
                        # Se il titolo non è tra quelli già inviati in passato
                        if titolo not in cronologia:
                            link = href if href.startswith('http') else ("https://www.unict.it" if "unict.it/it" in b['url'] else "https://www.dei.unict.it") + href
                            
                            txt = get_anteprima(link, headers)
                            msg = f"{b['emoji']} *{b['nome']}: {titolo}*\n\n{txt}\n\n🔗 [Leggi avviso completo]({link})"
                            
                            # Invio a Telegram
                            r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            
                            if r.status_code == 200:
                                # Salviamo il titolo nel file (in modalità "append" per non cancellare i vecchi)
                                with open(b['file'], "a", encoding="utf-8") as f:
                                    f.write(titolo + "\n")
                                cronologia.append(titolo)
                                inviati_ora += 1
                                
        except Exception as e: print(f"Errore {b['nome']}: {e}")

if __name__ == "__main__":
    check()
