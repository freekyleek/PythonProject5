from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_mail import Mail, Message
import os, json, re, datetime, unicodedata
from docx import Document

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Gmail konfiguracija po zahtjevu korisnika ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'webtest806@gmail.com'
app.config['MAIL_PASSWORD'] = 'rchf ggwe esyl kejy'  # Gmail App Password (na zahtjev korisnika)
app.config['MAIL_DEFAULT_SENDER'] = 'webtest806@gmail.com'

db = SQLAlchemy(app)
CORS(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# -------------------- MODELI --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="user")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_superadmin(self):
        return self.role == "superadmin"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- JSON pomoćne funkcije --------------------
STATIC_DIR = os.path.join(app.root_path, 'static')
OPERATERI_JSON_PATH = os.path.join(STATIC_DIR, 'operateri.json')
KLJENTI_JSON_PATH = os.path.join(STATIC_DIR, 'klijenti.json')
NALOZI_JSON_PATH = os.path.join(STATIC_DIR, 'nalozi.json')

def _read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_operateri(): return _read_json(OPERATERI_JSON_PATH)
def write_operateri(data): _write_json(OPERATERI_JSON_PATH, data)
def read_klijenti(): return _read_json(KLJENTI_JSON_PATH)
def write_klijenti(data): _write_json(KLJENTI_JSON_PATH, data)
def read_nalozi(): return _read_json(NALOZI_JSON_PATH)
def write_nalozi(data): _write_json(NALOZI_JSON_PATH, data)
# -------------------- TEHNIČARI / ZADUŽENI UREĐAJI JSON --------------------
TEHNICARI_JSON_PATH = os.path.join(STATIC_DIR, 'tehnicari.json')
ZADUZENI_UREDJAJI_JSON_PATH = os.path.join(STATIC_DIR, 'zaduzeni.uredjaji.json')
# -------------------- ZADUŽENI SIM JSON --------------------
ZADUZENI_SIM_JSON_PATH = os.path.join(STATIC_DIR, 'zaduzeni.sim.json')

def read_zaduzene_sim(): return _read_json(ZADUZENI_SIM_JSON_PATH)
def write_zaduzene_sim(data): _write_json(ZADUZENI_SIM_JSON_PATH, data)


def read_tehnicari(): return _read_json(TEHNICARI_JSON_PATH)
def write_tehnicari(data): _write_json(TEHNICARI_JSON_PATH, data)
# -------------------- KLIJENTI JSON --------------------
KLIJENTI_JSON_PATH = os.path.join(STATIC_DIR, 'klijenti.json')
def read_klijenti(): return _read_json(KLIJENTI_JSON_PATH)
def write_klijenti(data): _write_json(KLIJENTI_JSON_PATH, data)


# -------------------- ZADUŽENI NALOZI JSON --------------------
ZADUZENI_NALOZI_JSON_PATH = os.path.join(STATIC_DIR, 'zaduzeni.nalozi.json')
def read_zaduzene_nalozi(): return _read_json(ZADUZENI_NALOZI_JSON_PATH)
def write_zaduzene_nalozi(data): _write_json(ZADUZENI_NALOZI_JSON_PATH, data)

def read_zaduzene_uredjaje(): return _read_json(ZADUZENI_UREDJAJI_JSON_PATH)
def write_zaduzene_uredjaje(data): _write_json(ZADUZENI_UREDJAJI_JSON_PATH, data)

def refresh_tehnicari():
    ops = read_operateri()
    tehn = [o for o in ops if str(o.get('role','')).strip().lower() in ('tehničar','tehnicar','tehnicar/serviser','tehničar/serviser')]
    write_tehnicari(tehn)
    return tehn


# -------------------- UREĐAJI JSON --------------------
NAZIVI_UREDJaja_JSON_PATH = os.path.join(STATIC_DIR, 'naziv_uredjaja.json')
UREDJAJI_JSON_PATH = os.path.join(STATIC_DIR, 'uredjaji.json')

def read_nazivi_uredjaja(): return _read_json(NAZIVI_UREDJaja_JSON_PATH)
def write_nazivi_uredjaja(data): _write_json(NAZIVI_UREDJaja_JSON_PATH, data)
def read_uredjaji(): return _read_json(UREDJAJI_JSON_PATH)
def write_uredjaji(data): _write_json(UREDJAJI_JSON_PATH, data)

# -------------------- SIM JSON --------------------
PROVIDER_JSON_PATH = os.path.join(STATIC_DIR, 'provider.json')
SIM_JSON_PATH = os.path.join(STATIC_DIR, 'sim.json')

def read_provider(): return _read_json(PROVIDER_JSON_PATH)
def write_provider(data): _write_json(PROVIDER_JSON_PATH, data)
def read_sim(): return _read_json(SIM_JSON_PATH)
def write_sim(data): _write_json(SIM_JSON_PATH, data)

# -------------------- SIM RUTE --------------------
@app.route('/sim')
@login_required
def sim():
    items = read_sim()
    items.sort(key=lambda x: (x.get('provider',''), x.get('serijski','')))
    return render_template('sim.html', title="SIM", username=current_user.username, sims=items)

@app.route('/dodaj-sim', methods=['GET','POST'])
@login_required
def dodaj_sim():
    providers = read_provider()
    if request.method == 'POST':
        provider = request.form.get('provider','').strip()
        serijski = request.form.get('serijski','').strip()
        if not provider:
            flash("Provider je obavezan.", "danger")
            return render_template('dodaj_sim.html', title="Dodaj SIM", username=current_user.username, providers=providers)
        if not re.fullmatch(r'[A-Za-z0-9\-_/\.]+', serijski or ''):
            flash("Serijski broj smije sadržavati samo slova i brojeve.", "danger")
            return render_template('dodaj_sim.html', title="Dodaj SIM", username=current_user.username, providers=providers, provider_sel=provider, serijski=serijski)
        lst = read_sim()
        if any(u.get('serijski','').lower() == serijski.lower() for u in lst):
            flash("SIM s istim serijskim brojem već postoji.", "warning")
            return render_template('dodaj_sim.html', title="Dodaj SIM", username=current_user.username, providers=providers, provider_sel=provider, serijski=serijski)
        lst.append({'provider': provider, 'serijski': serijski, 'created_at': datetime.datetime.now().isoformat()})
        write_sim(lst)
        flash("SIM je spremljen.", "success")
        return redirect(url_for('sim'))
    return render_template('dodaj_sim.html', title="Dodaj SIM", username=current_user.username, providers=providers)

@app.route('/api/sim/<serijski>/delete', methods=['POST'])
@login_required
def api_delete_sim(serijski):
    if not current_user.is_superadmin:
        return jsonify({'ok': False, 'error': 'Brisanje dozvoljeno samo superadminu.'}), 403
    lst = read_sim()
    new_lst = [u for u in lst if u.get('serijski') != serijski]
    if len(new_lst) == len(lst):
        return jsonify({'ok': False, 'error': 'SIM nije pronađen.'}), 404
    write_sim(new_lst)
    return jsonify({'ok': True})


# -------------------- UREĐAJI RUTE --------------------
@app.route('/uredjaji')
@login_required
def uredjaji():
    items = read_uredjaji()
    items.sort(key=lambda x: (x.get('model',''), x.get('serijski','')))
    return render_template('uredjaji.html', title="Uređaji", username=current_user.username, uredjaji=items)

@app.route('/dodaj-uredjaj', methods=['GET','POST'])
@login_required
def dodaj_uredjaj():
    models = read_nazivi_uredjaja()
    if request.method == 'POST':
        model = request.form.get('model','').strip()
        serijski = request.form.get('serijski','').strip()
        if not model:
            flash("Model uređaja je obavezan.", "danger")
            return render_template('dodaj_uredjaj.html', title="Dodaj uređaj", username=current_user.username, models=models)
        if not re.fullmatch(r'[A-Za-z0-9\-_/\.]+', serijski or ''):
            flash("Serijski broj smije sadržavati samo slova i brojeve (dozvoljeni su - _ / .).", "danger")
            return render_template('dodaj_uredjaj.html', title="Dodaj uređaj", username=current_user.username, models=models, model_sel=model, serijski=serijski)
        lst = read_uredjaji()
        if any(u.get('serijski','').lower() == serijski.lower() for u in lst):
            flash("Uređaj s istim serijskim brojem već postoji.", "warning")
            return render_template('dodaj_uredjaj.html', title="Dodaj uređaj", username=current_user.username, models=models, model_sel=model, serijski=serijski)
        lst.append({'model': model, 'serijski': serijski, 'created_at': datetime.datetime.now().isoformat()})
        write_uredjaji(lst)
        flash("Uređaj je spremljen.", "success")
        return redirect(url_for('uredjaji'))
    return render_template('dodaj_uredjaj.html', title="Dodaj uređaj", username=current_user.username, models=models)

@app.route('/api/uredjaj/<serijski>/delete', methods=['POST'])
@login_required
def api_delete_uredjaj(serijski):
    if not current_user.is_superadmin:
        return jsonify({'ok': False, 'error': 'Brisanje dozvoljeno samo superadminu.'}), 403
    lst = read_uredjaji()
    new_lst = [u for u in lst if u.get('serijski') != serijski]
    if len(new_lst) == len(lst):
        return jsonify({'ok': False, 'error': 'Uređaj nije pronađen.'}), 404
    write_uredjaji(new_lst)
    return jsonify({'ok': True})

# -------------------- NALOZI – brisanje (samo superadmin) --------------------
@app.route('/api/nalog/<path:rn>/delete', methods=['POST'])
@login_required
def api_delete_nalog(rn):
    if not current_user.is_superadmin:
        return jsonify({'ok': False, 'error': 'Brisanje dozvoljeno samo superadminu.'}), 403
    lst = read_nalozi()
    new_lst = [n for n in lst if n.get('rn') != rn]
    if len(new_lst) == len(lst):
        return jsonify({'ok': False, 'error': 'Nalog nije pronađen.'}), 404
    write_nalozi(new_lst)
    return jsonify({'ok': True})


# -------------------- SEED SUPERADMIN --------------------
def ensure_superadmin():
    db.create_all()
    sa = User.query.filter_by(username="hlisac").first()
    if not sa:
        sa = User(username="hlisac", role="superadmin")
        sa.set_password("123")
        db.session.add(sa)
        db.session.commit()
        print("[seed] Superadmin kreiran: hlisac/123")
    else:
        changed = False
        if sa.role != "superadmin":
            sa.role = "superadmin"; changed = True
        if not sa.check_password("123"):
            sa.set_password("123"); changed = True
        if changed:
            db.session.commit()
            print("[seed] Superadmin ažuriran: hlisac/123")

# -------------------- UTIL --------------------
def slugify(value: str) -> str:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-zA-Z0-9_-]+', '-', value).strip('-').lower()
    return value or 'klijent'

def find_table_with_header(doc: Document, header_cells):
    for tbl in doc.tables:
        if len(tbl.rows) > 0:
            headers = [c.text.strip() for c in tbl.rows[0].cells]
            if all(any(h.lower() in cell.lower() for cell in headers) for h in header_cells):
                return tbl
    return None

def replace_text_in_doc(doc: Document, mapping: dict):
    for p in doc.paragraphs:
        for k, v in mapping.items():
            if k in p.text:
                for run in p.runs:
                    run.text = run.text.replace(k, v)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for k, v in mapping.items():
                    if k in cell.text:
                        cell.text = cell.text.replace(k, v)

def next_rn_for_year(nalozi, year):
    # Broji samo instalacije u tekućoj godini i vrati sljedeći redni broj
    nums = []
    for n in nalozi:
        if n.get('type') == 'instalacija':
            try:
                dt = datetime.datetime.fromisoformat(n.get('created_at','')[:19])
            except Exception:
                continue
            if dt.year == year and 'rn' in n:
                # rn format 0001/2025
                m = re.match(r'(\d{4})/(\d{4})', n['rn'])
                if m and int(m.group(2)) == year:
                    nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


# -------------------- ZADUŽI / RAZDUŽI UREĐAJ --------------------
@app.route('/zaduzi-uredjaj', methods=['GET','POST'])
@login_required
def zaduzi_uredjaj():
    tehnicari = refresh_tehnicari()
    uredjaji = read_uredjaji()
    if request.method == 'POST':
        tech_username = request.form.get('tehnicar','').strip()
        serijski = request.form.get('uredjaj','').strip()
        if not tech_username or not serijski:
            flash("Odaberi tehničara i uređaj.", "danger")
            return render_template('zaduzi.uredjaj.html', title="Zaduži uređaj", username=current_user.username, tehnicari=tehnicari, uredjaji=uredjaji)
        # find device in available list
        lst = read_uredjaji()
        dev = next((d for d in lst if d.get('serijski') == serijski), None)
        if not dev:
            flash("Uređaj nije pronađen ili je već zadužen.", "warning")
            return render_template('zaduzi.uredjaj.html', title="Zaduži uređaj", username=current_user.username, tehnicari=tehnicari, uredjaji=uredjaji)
        # move to zaduzeni
        zlist = read_zaduzene_uredjaje()
        if any(z.get('serijski','').lower()==serijski.lower() for z in zlist):
            flash("Uređaj je već zadužen.", "warning")
            return redirect(url_for('zaduzi_uredjaj'))
        # remove from available
        lst = [d for d in lst if d.get('serijski') != serijski]
        write_uredjaji(lst)
        zitem = {
            'model': dev.get('model',''),
            'serijski': dev.get('serijski',''),
            'assigned_to': tech_username,
            'assigned_at': datetime.datetime.now().isoformat()
        }
        zlist.append(zitem)
        write_zaduzene_uredjaje(zlist)
        flash(f"Uređaj {serijski} zadužen za {tech_username}.", "success")
        return redirect(url_for('uredjaji'))
    return render_template('zaduzi.uredjaj.html', title="Zaduži uređaj", username=current_user.username, tehnicari=tehnicari, uredjaji=uredjaji)

@app.route('/api/razduzi/<serijski>', methods=['POST'])
@login_required
def api_razduzi(serijski):
    zlist = read_zaduzene_uredjaje()
    item = next((z for z in zlist if z.get('serijski') == serijski), None)
    if not item:
        return jsonify({'ok': False, 'error': 'Uređaj nije pronađen u zaduženima.'}), 404
    # Dozvoli razduživanje superadminu ili samom tehničaru
    if not (current_user.is_superadmin or current_user.username == item.get('assigned_to')):
        return jsonify({'ok': False, 'error': 'Nedovoljna prava za razduživanje.'}), 403
    # remove from zaduzeni and return to available
    zlist = [z for z in zlist if z.get('serijski') != serijski]
    write_zaduzene_uredjaje(zlist)
    # add back to available devices
    lst = read_uredjaji()
    lst.append({'model': item.get('model',''), 'serijski': item.get('serijski',''), 'created_at': datetime.datetime.now().isoformat()})
    write_uredjaji(lst)
    return jsonify({'ok': True})



# -------------------- ZADUŽI / RAZDUŽI SIM --------------------
@app.route('/zaduzi-sim', methods=['GET','POST'])
@login_required
def zaduzi_sim():
    tehnicari = refresh_tehnicari() if 'refresh_tehnicari' in globals() else read_tehnicari()
    sims = read_sim()
    if request.method == 'POST':
        tech_username = request.form.get('tehnicar','').strip()
        serijski = request.form.get('sim','').strip()
        if not tech_username or not serijski:
            flash("Odaberi tehničara i SIM.", "danger")
            return render_template('zaduzi.sim.html', title="Zaduži SIM", username=current_user.username, tehnicari=tehnicari, sims=sims)
        # find SIM in available list
        lst = read_sim()
        sim_item = next((s for s in lst if s.get('serijski') == serijski), None)
        if not sim_item:
            flash("SIM nije pronađen ili je već zadužen.", "warning")
            return render_template('zaduzi.sim.html', title="Zaduži SIM", username=current_user.username, tehnicari=tehnicari, sims=sims)
        # move to zaduzeni.sim.json
        zlist = read_zaduzene_sim()
        if any(z.get('serijski','').lower()==serijski.lower() for z in zlist):
            flash("SIM je već zadužen.", "warning")
            return redirect(url_for('zaduzi_sim'))
        # remove from available
        lst = [s for s in lst if s.get('serijski') != serijski]
        write_sim(lst)
        zitem = {
            'provider': sim_item.get('provider',''),
            'serijski': sim_item.get('serijski',''),
            'assigned_to': tech_username,
            'assigned_at': datetime.datetime.now().isoformat()
        }
        zlist.append(zitem)
        write_zaduzene_sim(zlist)
        flash(f"SIM {serijski} zadužen za {tech_username}.", "success")
        return redirect(url_for('sim'))
    return render_template('zaduzi.sim.html', title="Zaduži SIM", username=current_user.username, tehnicari=tehnicari, sims=sims)

@app.route('/api/razduzi-sim/<serijski>', methods=['POST'])
@login_required
def api_razduzi_sim(serijski):
    zlist = read_zaduzene_sim()
    item = next((z for z in zlist if z.get('serijski') == serijski), None)
    if not item:
        return jsonify({'ok': False, 'error': 'SIM nije pronađen u zaduženima.'}), 404
    if not (current_user.is_superadmin or current_user.username == item.get('assigned_to')):
        return jsonify({'ok': False, 'error': 'Nedovoljna prava za razduživanje.'}), 403
    # remove from zaduzeni and return to available sim.json
    zlist = [z for z in zlist if z.get('serijski') != serijski]
    write_zaduzene_sim(zlist)
    lst = read_sim()
    lst.append({'provider': item.get('provider',''), 'serijski': item.get('serijski',''), 'created_at': datetime.datetime.now().isoformat()})
    write_sim(lst)
    return jsonify({'ok': True})



# -------------------- ZADUŽI / RAZDUŽI NALOG --------------------
@app.route('/zaduzi-nalog', methods=['GET','POST'])
@app.route('/zaduzi_nalog', methods=['GET','POST'])
@login_required
def zaduzi_nalog():
    tehnicari = refresh_tehnicari() if 'refresh_tehnicari' in globals() else read_tehnicari()
    _all = read_nalozi()
    nalozi = [n for n in _all if (n.get('status') or '').lower() != 'zaključen' and (n.get('type') or '').lower() in ('instalacija','deinstalacija','servis')]
    nalozi.sort(key=lambda x: x.get('created_at',''), reverse=True)
    if request.method == 'POST':
        tech_username = request.form.get('tehnicar','').strip()
        rn = request.form.get('nalog','').strip()
        if not tech_username or not rn:
            flash("Odaberi tehničara i nalog.", "danger")
            return render_template('zaduzi.nalog.html', title="Zaduži nalog", username=current_user.username, tehnicari=tehnicari, nalozi=nalozi)
        lst = read_nalozi()
        nalog = next((n for n in lst if str(n.get('rn')) == rn), None)
        if not nalog:
            flash("Nalog nije pronađen ili je već zadužen.", "warning")
            return render_template('zaduzi.nalog.html', title="Zaduži nalog", username=current_user.username, tehnicari=tehnicari, nalozi=nalozi)
        zlist = read_zaduzene_nalozi()
        if any(str(z.get('rn')) == rn for z in zlist):
            flash("Nalog je već zadužen.", "warning")
            return redirect(url_for('zaduzi_nalog'))
    # zapiši samo u zaduzeni.nalozi.json (nalog ostaje i u nalozi.json)
        zitem = dict(nalog)
        if not zitem.get('rn'):
            zitem['rn'] = str(nalog.get('rn') or nalog.get('RN') or nalog.get('broj') or nalog.get('id') or nalog.get('number'))
        zitem['assigned_to'] = tech_username
        zitem['assigned_at'] = datetime.datetime.now().isoformat()
        zlist.append(zitem)
        write_zaduzene_nalozi(zlist)
        flash(f"Nalog RN {rn} zadužen za {tech_username}.", "success")
        return redirect(url_for('zaduzeni_nalozi'))
    return render_template('zaduzi.nalog.html', title="Zaduži nalog", username=current_user.username, tehnicari=tehnicari, nalozi=nalozi)

@app.route('/api/razduzi-nalog/<path:rn>', methods=['POST'])
@login_required
def api_razduzi_nalog(rn):
    zlist = read_zaduzene_nalozi()
    item = next((z for z in zlist if str(z.get('rn')) == rn), None)
    if not item:
        return jsonify({'ok': False, 'error': 'Nalog nije pronađen u zaduženima.'}), 404
    if not (current_user.is_superadmin or current_user.username == item.get('assigned_to')):
        return jsonify({'ok': False, 'error': 'Nedovoljna prava za razduživanje.'}), 403
    # remove from zaduzeni; nalog i dalje postoji u nalozi.json pa ga nije potrebno vraćati
    zlist = [z for z in zlist if str(z.get('rn')) != rn]
    write_zaduzene_nalozi(zlist)
    return jsonify({'ok': True})



# -------------------- ZAKLJUČI NALOG --------------------
@app.route('/zakljuci-nalog/<path:rn>', methods=['GET','POST'])
@app.route('/zaduzeni.nalog/<path:rn>', methods=['GET','POST'])
@login_required
def zakljuci_nalog(rn):
    # pronađi nalog među zaduženima
    z_nalozi = read_zaduzene_nalozi()
    nalog = next((n for n in z_nalozi if str(n.get('rn')) == str(rn)), None)
    if not nalog:
        abort(404)
    
    # tehničar i klijent
    tech = (nalog.get('assigned_to') or nalog.get('tehnicar') or '').strip()
    klijenti = read_klijenti()
    cli = None
    cid = nalog.get('client_id') or nalog.get('oib')
    cname = nalog.get('client') or nalog.get('klijent')
    if cid:
        cli = next((k for k in klijenti if str(k.get('id') or k.get('oib')) == str(cid)), None)
    if not cli and cname:
        cli = next((k for k in klijenti if (k.get('name') or k.get('naziv')) == cname), None)
    
    # zaduženi uređaji/SIM-ovi; filtriraj na konkretnog tehničara
    try:
        zdev = read_zaduzene_uredjaje()
    except Exception:
        zdev = []
    try:
        zsim = read_zaduzene_sim()
    except Exception:
        zsim = []
    
    dev_for_tech = [d for d in zdev if not tech or (d.get('assigned_to') or '').strip() == tech]
    sim_for_tech = [s for s in zsim if not tech or (s.get('assigned_to') or '').strip() == tech]
    
    # grupiranje po tipu (ako nema type, koristi model za uređaje; provider za SIM)
    def group_devices(items):
        groups = {}
        for it in items:
            key = (it.get('type') or it.get('model') or 'Ostalo')
            groups.setdefault(key, []).append(it)
        return groups
    
    def group_sims(items):
        groups = {}
        for it in items:
            key = (it.get('type') or it.get('provider') or 'Ostalo')
            groups.setdefault(key, []).append(it)
        return groups
    
    dev_groups = group_devices(dev_for_tech)
    sim_groups = group_sims(sim_for_tech)
    
    if request.method == 'POST':
        # odabrano iz formi (moguće višestruki odabir)
        uredjaji_sel = request.form.getlist('uredjaji') or request.form.getlist('uredjaj') or []
        sim_sel = request.form.getlist('sim') or request.form.getlist('sims') or []
    
        # zapisnik: upload slike (ne diraj drugo)
        f = request.files.get('zapisnik') or request.files.get('zapisnik_img')
        zapisnik_rel = None
        if f and f.filename:
            updir = os.path.join(STATIC_DIR, 'uploads', 'nalozi')
            os.makedirs(updir, exist_ok=True)
            # jednostavna normalizacija naziva
            safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', f.filename)
            fname = f"{rn}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            fpath = os.path.join(updir, fname)
            f.save(fpath)
            zapisnik_rel = os.path.join('uploads', 'nalozi', fname)  # relativno na /static
    
        # makni nalog iz zaduženih
        z_nalozi = [z for z in z_nalozi if str(z.get('rn')) != str(rn)]
        write_zaduzene_nalozi(z_nalozi)
    
        # dodaj zaključen nalog u nalozi.json
        base = read_nalozi()
        closed = dict(nalog)
        closed['status'] = 'zaključen'
        closed['closed_at'] = datetime.datetime.now().isoformat()
        closed['closed_by'] = tech
        closed['devices_used'] = uredjaji_sel
        closed['sims_used'] = sim_sel
        if zapisnik_rel:
            closed['zapisnik_image'] = os.path.join('static', zapisnik_rel)
        base.append(closed)
        write_nalozi(base)
    
        # premjesti uređaje u aktivne (kod klijenta) i izbaci iz zaduženih
        try:
            zlist_dev = read_zaduzene_uredjaje()
        except Exception:
            zlist_dev = []
        akt_dev = read_aktivni_uredjaji()
        for s in uredjaji_sel:
            it = next((d for d in zlist_dev if d.get('serijski') == s), None)
            if it:
                zlist_dev = [d for d in zlist_dev if d.get('serijski') != s]
                akt_dev.append({
                    'model': it.get('model',''),
                    'serijski': it.get('serijski',''),
                    'client': (cli.get('name') if isinstance(cli, dict) and cli else (cname or '')),
                    'assigned_at': datetime.datetime.now().isoformat()
                })
        write_zaduzene_uredjaje(zlist_dev)
        write_aktivni_uredjaji(akt_dev)
    
        # premjesti SIM u aktivne (kod klijenta) i izbaci iz zaduženih
        zlist_sim = read_zaduzene_sim()
        akt_sim = read_aktivni_sim()
        for s in sim_sel:
            it = next((d for d in zlist_sim if d.get('serijski') == s), None)
            if it:
                zlist_sim = [d for d in zlist_sim if d.get('serijski') != s]
                akt_sim.append({
                    'provider': it.get('provider',''),
                    'serijski': it.get('serijski',''),
                    'client': (cli.get('name') if isinstance(cli, dict) and cli else (cname or '')),
                    'assigned_at': datetime.datetime.now().isoformat()
                })
        write_zaduzene_sim(zlist_sim)
        write_aktivni_sim(akt_sim)
    
        flash(f'Nalog RN {rn} zaključen.', 'success')
        if tech:
            return redirect(url_for('operater_profil', username=tech))
        return redirect(url_for('zaduzeni_nalozi'))
    
    # GET – prikaži formu za zaključivanje
    return render_template('zakljuci.nalog.html',
                           title='Zaključi nalog',
                           username=current_user.username,
                           nalog=nalog,
                           klijent=cli,
                           dev_groups=dev_groups,
                           sim_groups=sim_groups)

@app.route('/')
@login_required
def home():
    return redirect(url_for('nalozi'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash("Neispravno korisničko ime ili lozinka.", "danger")
    return render_template('login.html', username=None, title="Prijava")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/nalozi')
@login_required
def nalozi():

    all_orders = read_nalozi()
    # Otvorene instalacije
    instalacije = [n for n in all_orders if (n.get('type') or '').lower() == 'instalacija' and (n.get('status') or '').lower() != 'zaključen']
    instalacije.sort(key=lambda x: x.get('created_at',''), reverse=True)
    # Otvorene deinstalacije
    deinstalacije = [n for n in all_orders if (n.get('type') or '').lower() == 'deinstalacija' and (n.get('status') or '').lower() != 'zaključen']
    deinstalacije.sort(key=lambda x: x.get('created_at',''), reverse=True)
    # Otvoreni servisi
    servisi = [n for n in all_orders if (n.get('type') or '').lower() == 'servis' and (n.get('status') or '').lower() != 'zaključen']
    servisi.sort(key=lambda x: x.get('created_at',''), reverse=True)
    # Zaključeni nalozi
    zakljuceni = [n for n in all_orders if (n.get('status') or '').lower() == 'zaključen']
    def _ctime(n):
        return (n.get('closed_at') or n.get('created_at') or '')
    zakljuceni.sort(key=_ctime, reverse=True)
    assigned_map = { str(z.get('rn') or z.get('RN') or z.get('broj') or z.get('id') or z.get('number')): (z.get('assigned_to') or '') for z in read_zaduzene_nalozi() }
    return render_template('nalozi.html', title="Nalozi", username=current_user.username, instalacije=instalacije, deinstalacije=deinstalacije, servisi=servisi, zakljuceni=zakljuceni, assigned_map=assigned_map)

@app.route('/zaduzeni-nalozi')
@login_required
def zaduzeni_nalozi():
    items = read_zaduzene_nalozi()
    try:
        items = sorted(items, key=lambda x: (x.get('assigned_at',''), str(x.get('rn',''))), reverse=True)
    except Exception:
        pass
    return render_template('zaduzeni.nalozi.html', title="Zaduženi nalozi", username=current_user.username, nalozi=items)


@app.route('/aktivni-uredjaji')
@login_required
def aktivni_uredjaji():
    return render_template('aktivni.uredjaji.html', title="Aktivni uređaji", username=current_user.username)

@app.route('/datoteke')
@login_required
def datoteke():
    return render_template('datoteke.html', title="Datoteke", username=current_user.username)

@app.route('/info')
@login_required
def info():
    return render_template('info.html', title="Info", username=current_user.username)

# -------------------- OPERATERI --------------------
@app.route('/operateri')
@login_required
def operateri():
    ops = read_operateri()
    ops.sort(key=lambda x: x.get('role',''))
    return render_template('operateri.html', title="Operateri", username=current_user.username, operators=ops)

@app.route('/kreiraj-profil', methods=['GET','POST'])
@login_required
def kreiraj_profil():
    if not current_user.is_superadmin:
        flash("Samo superadmin može kreirati profile.", "warning")
        return redirect(url_for('operateri'))
    if request.method == 'POST':
        first_name = request.form.get('first_name','').strip()
        last_name = request.form.get('last_name','').strip()
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        role = request.form.get('role','').strip()
        if not all([first_name,last_name,username,password,email,phone,role]):
            flash("Sva polja su obavezna.", "danger")
            return render_template('kreiraj_profil.html', title="Kreiraj profil", username=current_user.username)
        ops = read_operateri()
        if any(o['username']==username or o['email']==email for o in ops):
            flash("Korisničko ime ili Email već postoji.", "danger")
            return render_template('kreiraj_profil.html', title="Kreiraj profil", username=current_user.username)
        new_op = dict(first_name=first_name,last_name=last_name,
                      username=username,email=email,phone=phone,role=role)
        ops.append(new_op)
        write_operateri(ops)
        flash("Uspješno kreiran", "success")
        return redirect(url_for('operateri'))
    return render_template('kreiraj_profil.html', title="Kreiraj profil", username=current_user.username)

@app.route('/operater/<username>')
@login_required
def operater_profil(username):
    ops = read_operateri()
    op = next((o for o in ops if o['username']==username), None)
    if not op: abort(404)
    zlist = read_zaduzene_uredjaje()
    my_devices = [z for z in zlist if z.get('assigned_to') == username]
    my_devices.sort(key=lambda x: (x.get('model',''), x.get('serijski','')))
    # --- SIM ---
    zsim = read_zaduzene_sim()
    my_sims = [z for z in zsim if z.get('assigned_to') == username]
    my_sims.sort(key=lambda x: (x.get('provider',''), x.get('serijski','')))
    # --- NALOZI ---
    zn = read_zaduzene_nalozi()
    my_nalozi = [z for z in zn if (str(z.get('assigned_to') or z.get('assignedTo') or z.get('tehnicar') or '')).lower() == username.lower()]
    my_nalozi.sort(key=lambda x: (str(x.get('rn','')), x.get('client','')))
    return render_template(
        'operater_profil.html',
        title="Profil operatera",
        username=current_user.username,
        operater=op,
        zaduzeni_uredjaji=my_devices,
        zaduzeni_sim=my_sims,
        zaduzeni_nalozi=my_nalozi,
    )

@app.route('/profile/<username>')
@login_required
def profile(username):
    return operater_profil(username)

# -------------------- KLIJENTI --------------------
@app.route('/klijenti')
@login_required
def klijenti():
    kl = read_klijenti()
    kl.sort(key=lambda x: x.get('name',''))
    return render_template('klijenti.html', title="Klijenti", username=current_user.username, klijenti=kl)

@app.route('/klijent/<name>')
@login_required
def klijent_profil(name):
    klijenti = read_klijenti()
    k = next((c for c in klijenti if c['name'] == name), None)
    if not k: abort(404)
    orders = [n for n in read_nalozi() if n.get('client') == k['name']]
    orders.sort(key=lambda x: x.get('created_at',''), reverse=True)
    return render_template('klijent_profil.html',
                           title=f"Profil klijenta - {k['name']}",
                           username=current_user.username,
                           klijent=k, nalozi=orders)

@app.route('/api/klijent', methods=['POST'])
@login_required
def api_klijent_save():
    data = request.get_json(silent=True) or {}
    required = ['name','oib','headquarters','email','phone']
    if not all(data.get(k) for k in required):
        return jsonify({'ok': False, 'error': 'Sva polja osim adrese isporuke su obavezna.'}), 400
    if not re.fullmatch(r'\d{11}', data.get('oib','')):
        return jsonify({'ok': False, 'error': 'OIB mora imati točno 11 znamenki.'}), 400
    kl = read_klijenti()
    if any(c.get('name') == data['name'] for c in kl):
        return jsonify({'ok': False, 'error': 'Klijent s tim nazivom već postoji.'}), 409
    data['created_at'] = datetime.datetime.now().isoformat()
    kl.append({
        'name': data['name'],
        'oib': data['oib'],
        'headquarters': data['headquarters'],
        'shipping': data.get('shipping',''),
        'email': data['email'],
        'phone': data['phone'],
        'created_at': data['created_at']
    })
    write_klijenti(kl)
    return jsonify({'ok': True}), 200

# -------------------- NALOZI + dodatne stranice --------------------
@app.route('/kreiraj-nalog/<name>')
@login_required
def kreiraj_nalog(name):
    klijenti = read_klijenti()
    k = next((c for c in klijenti if c['name'] == name), None)
    if not k: abort(404)
    return render_template('kreiraj_nalog.html',
                           title=f'Kreiraj nalog — {k["name"]}',
                           username=current_user.username,
                           klijent=k)

@app.route('/instalacija/<name>', methods=['GET','POST'])
@login_required
def instalacija(name):
    klijenti = read_klijenti()
    k = next((c for c in klijenti if c['name'] == name), None)
    if not k: abort(404)

    # dozvoljeno više instalacija za istog klijenta
    if request.method == 'POST':
        return generate_nalog_docx(k, request.form)

    return render_template('instalacija.html',
                           title=f'Instalacija — {k["name"]}',
                           username=current_user.username,
                           klijent=k)

@app.route('/deinstalacija/<name>')
@login_required
def deinstalacija(name):
    klijenti = read_klijenti()
    k = next((c for c in klijenti if c['name'] == name), None)
    if not k: abort(404)
    return render_template('deinstalacija.html',
                           title=f'Deinstalacija — {k["name"]}',
                           username=current_user.username,
                           klijent=k)

@app.route('/servis/<name>')
@login_required
def servis(name):
    klijenti = read_klijenti()
    k = next((c for c in klijenti if c['name'] == name), None)
    if not k: abort(404)
    return render_template('servis.html',
                           title=f'Servis — {k["name"]}',
                           username=current_user.username,
                           klijent=k)

# -------------------- GENERIRANJE NALOGA --------------------
def generate_nalog_docx(klijent, formdata):
    template_path = os.path.join(STATIC_DIR, 'datoteke', 'rn_template.docx')
    if not os.path.exists(template_path):
        abort(500, description="Nedostaje rn_template.docx u static/datoteke")

    doc = Document(template_path)

    # selections
    usluge = formdata.getlist('usluge')
    uredjaji_qty = {k:int(v) for k,v in formdata.items() if k not in ['usluge','nacin','podopcija'] and v.isdigit() and int(v)>=0}
    dodatne_qty = {}
    ADD_KEYS = ["SIM kartica","Termo traka (58mm)","Termo traka (80mm)","Ladica za novac","Kasa","Bar kod skener","SumUp čitač","Stylus olovka"]
    for k,v in formdata.items():
        if k in ADD_KEYS and v.isdigit():
            dodatne_qty[k] = int(v)

    nacin = formdata.get('nacin','')
    podopc = formdata.getlist('podopcija')

    korisnik = klijent['name']
    adresa = klijent.get('shipping') or klijent.get('headquarters') or ''
    year = datetime.datetime.now().year

    # RN broj: 0001/YYYY (samo za instalacije; reset 1.1. nove godine)
    nalozi = read_nalozi()
    rn_num = next_rn_for_year(nalozi, year)
    rn_str = f"{rn_num:04d}/{year}"

    mapping = {
        '{{KORISNIK}}': korisnik,
        '{{ADRESA_ISPORUKE}}': adresa,
        '{{OIB}}': klijent.get('oib',''),
        '{{KONTAKT}}': klijent.get('phone',''),
        '{{RN}}': rn_str
    }

    has_sim = (dodatne_qty.get('SIM kartica',0) > 0) or ('SIM kartica' in usluge)
    has_additional = any(q>0 for k,q in dodatne_qty.items() if k!='SIM kartica')
    mapping['{{SIM}}'] = 'X' if has_sim else ''
    mapping['{{DODATNA_OPREMA}}'] = 'X' if has_additional else ''

    has_device_one = any(q==1 for q in uredjaji_qty.values())
    mapping['{{Uređaj}}'] = 'X' if has_device_one else ''

    replace_text_in_doc(doc, mapping)

    table = find_table_with_header(doc, ['Naziv Opreme','TID','Serijski broj','OTP'])
    rows_to_add = []
    for dev_name, qty in uredjaji_qty.items():
        if qty and qty>0:
            for i in range(qty):
                rows_to_add.append({'Naziv Opreme': dev_name, 'TID': '', 'Serijski broj': '', 'OTP': ''})
    sim_qty = dodatne_qty.get('SIM kartica', 0)
    for i in range(sim_qty):
        rows_to_add.append({'Naziv Opreme': 'SIM', 'TID': '', 'Serijski broj': '', 'OTP': ''})

    if table and rows_to_add:
        for item in rows_to_add:
            row = table.add_row().cells
            cols = [c.text.strip().lower() for c in table.rows[0].cells]
            def setcol(colname, value):
                try:
                    idx = next(i for i,c in enumerate(cols) if colname.lower() in c)
                    row[idx].text = value
                except StopIteration:
                    pass
            setcol('Naziv', item['Naziv Opreme'])
            setcol('TID', item['TID'])
            setcol('Serijski', item['Serijski broj'])
            setcol('OTP', item['OTP'])

    # Save to static/nalozi/<client-slug>/INSTALL RN 0001-YYYY Klijent,Adresa.docx
    client_slug = slugify(korisnik)
    out_dir = os.path.join(STATIC_DIR, 'nalozi', client_slug)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"INSTALL RN {rn_str.replace('/', '-') } {korisnik},{adresa}.docx"
    out_path = os.path.join(out_dir, filename)
    doc.save(out_path)

    # Save record (status: nezadužen | zadužen | zaključen)
    order = {
        'type': 'instalacija',
        'client': korisnik,
        'file': f"nalozi/{client_slug}/{filename}",
        'created_at': datetime.datetime.now().isoformat(),
        'nacin': nacin,
        'podopc': podopc,
        'rn': rn_str,
        'status': 'nezadužen',
        'assigned_to': '-'  # korisničko ime operatera
    }
    nalozi.append(order)
    write_nalozi(nalozi)

    try:
        if app.config.get('MAIL_SERVER') and app.config.get('MAIL_USERNAME'):
            with app.open_resource(out_path) as fp:
                msg = Message(subject=f"RN {rn_str} za {korisnik}", recipients=['webtest806@gmail.com'])
                msg.body = f"U prilogu je RN {rn_str} za klijenta {korisnik}."
                msg.attach(filename, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', fp.read())
                mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Slanje e-pošte nije uspjelo: {e}")

    # Nakon kreiranja — redirect na profil klijenta
    flash(f"Nalog {rn_str} uspješno kreiran.", "success")
    return redirect(url_for('klijent_profil', name=korisnik))

# -------------------- STATIC BANNERS --------------------
@app.route('/static/banners/<path:filename>')
def banners(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'banners'), filename)

if __name__ == '__main__':
    with app.app_context():
        ensure_superadmin()
    for p, init in [(OPERATERI_JSON_PATH, []),(KLJENTI_JSON_PATH, []),(NALOZI_JSON_PATH, [])]:
        if not os.path.exists(p):
            _write_json(p, init)
    app.run(debug=True)
