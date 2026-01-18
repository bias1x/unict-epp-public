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
        
        # Selettori per trovare il testo vero ed evitare i menu
        corpo = (soup.find('div', class_='field-name-body') or 
                 soup.find('div', id='parent-fieldname-text') or 
                 soup.find('article') or 
                 soup.find('div', class_='region-content'))
        
        if corpo:
            for s in corpo(['script', 'style']): s.decompose()
            # separator=' ' evita che le parole si attacchino
            testo = corpo.get_text(separator=' ', strip=True)
            
            # Se il testo trovato è troppo corto, prova a scavare di più
            if len(testo) < 40:
                testo = soup.get_text(separator=' ', strip=True)
                testo = testo[400:] # Salta l'intestazione della pagina
                
            return testo[:350] + "..." if len(testo) > 350 else testo
        
        return "Dettagli disponibili nel link."
    except:
        return ""

def check():
    # User-agent completo per essere più "invisibili" ai blocchi
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for b in BACHECHE:
        try:
            print(f"Controllo: {b['nome']}")
            res = requests.get(b['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Isola l'area dei contenuti
            area = soup.find('section', id='main-content') or soup.find('div', class_='region-content') or soup
            links = area.find_all('a', href=True)
            
            avviso = None
            for l in links:
                href = l['href']
                testo_link = l.get_text(strip=True)
                
                # Filtra solo i link che portano ad avvisi reali
                if any(x in href for x in ['/comunicazioni/', '/avvisi/', '/news/']) and len(testo_link) > 15:
                    if not any(href.lower().endswith(x) for x in ['/home', '/elenco-news', '/news']):
                        avviso = l
                        break

            if not avviso:
                continue

            titolo = avviso.get_text(strip=True)
            
            # Costruzione link robusta
            if avviso['href'].startswith('http'):
                link_pieno = avviso['href']
            else:
                # Se l'URL della bacheca contiene unict.it, usa il base di UNICT, altrimenti DEI
                base = "https://www.unict.it" if "unict.it" in b['url'] else "https://www.dei.unict.it"
                link_pieno = base + avviso['href']
            
            ultimo = ""
            if os.path.exists(b['file']):
                with open(b['file'], "r", encoding="utf-8") as f:
                    ultimo = f.read().strip()

            # Invia il messaggio solo se il titolo è diverso dall'ultimo salvato
            if titolo != ultimo:
                txt = get_anteprima(link_pieno, headers)
                msg = f"{b['emoji']} *{b['nome']}: {titolo}*\n\n{txt}\n\n🔗 [Leggi avviso completo]({link_pieno})"
                
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                
                # Aggiorna il file di memoria
                with open(b['file'], "w", encoding="utf-8") as f:
                    f.write(titolo)
                    
        except Exception as e:
            print(f"Errore {b['nome']}: {e}")

if __name__ == "__main__":
    check()
