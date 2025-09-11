# Flask Login Site

Ovaj projekt implementira traženu Python (Flask) web stranicu sa:
- prijavom (korisničko ime/lozinka),
- `base.html` predloškom,
- `style.css` stilovima,
- `slide.js` za rotirajući banner (svakih 5 sekundi),
- lijevim sideboxom s linkovima na stranice u točnom poretku,
- početnom stranicom `index.html`.

## Pokretanje (lokalno)

1) **Kreirajte virtualno okruženje i instalirajte zahtjeve**
```bash
python -m venv .venv
. .venv/bin/activate   # na Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> Napomena: neke ovisnosti su specifične za pojedine OS-ove (npr. `pywin32`) – ako dobijete greške pri instalaciji, uklonite/prekomentirajte ih iz `requirements.txt` za svoj OS.

2) **Inicijalizirajte bazu i demo korisnika**
```bash
flask --app app.py init-db
```

3) **Pokrenite server**
```bash
flask --app app.py run --debug
```
Otvorite http://127.0.0.1:5000/ i prijavite se s **admin / admin**.

## Struktura
```
flask_login_site/
  app.py
  requirements.txt
  templates/
    base.html
    login.html
    index.html
    klijenti.html
    nalozi.html
    zaduzeni.nalozi.html
    uredjaji.html
    aktivni.uredjaji.html
    operateri.html
    datoteke.html
    info.html
  static/
    style.css
    slide.js
    banners/
      banner1.jpg
      banner2.jpg
      banner3.jpg
```

## Dalje što napraviti
- Zamijenite *placeholder* bannere u `static/banners/` stvarnim JPG/PNG slikama.
- Po potrebi prilagodite `style.css` i `base.html`. Trenutni izgled je rađen prema vašim datotekama *base.txt* i *css.txt*.
- Dodajte prave modele/podatke u stranice (Klijenti, Nalozi, ...). Trenutno su to **placeholder** predlošci.
- Ako vam ne treba `pyodbc`/`sqlalchemy-access`, slobodno ih uklonite iz zahtjeva.
