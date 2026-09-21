import streamlit as st
import sqlite3
import os
import re
import csv
import io
import html
from datetime import datetime, timedelta

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="TEDx B'DARIJA",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "TEDx B'DARIJA"
DB_DIR = "data"
UPLOAD_DIR = "uploads"
DB_PATH = os.path.join(DB_DIR, "tedx.db")
LOGO_PATH = "tedx-bdarija-logo.png"

ADMIN_EMAIL = "outhmane@farah.love"
ADMIN_PASSWORD = "oufa@2026@!"

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            major TEXT NOT NULL,
            year TEXT NOT NULL,
            photo_path TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    existing = conn.execute(
        "SELECT value FROM settings WHERE key = 'deadline'"
    ).fetchone()

    if not existing:
        default_deadline = (
            datetime.now() + timedelta(days=30)
        ).isoformat(timespec="minutes")

        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            ("deadline", default_deadline)
        )

    conn.commit()
    conn.close()


def get_deadline():
    conn = get_connection()

    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'deadline'"
    ).fetchone()

    conn.close()

    if not row:
        return datetime.now() + timedelta(days=30)

    try:
        return datetime.fromisoformat(row["value"])
    except Exception:
        return datetime.now() + timedelta(days=30)


def save_deadline(value):
    conn = get_connection()

    conn.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, ("deadline", value.isoformat(timespec="minutes")))

    conn.commit()
    conn.close()


def add_registration(name, phone, major, year, photo_path):
    conn = get_connection()

    conn.execute("""
        INSERT INTO registrations
        (name, phone, major, year, photo_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        major,
        year,
        photo_path,
        datetime.now().isoformat(timespec="seconds")
    ))

    conn.commit()
    conn.close()


def get_registrations():
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM registrations
        ORDER BY datetime(created_at) DESC
    """).fetchall()

    conn.close()

    return rows


def delete_registration(registration_id):
    conn = get_connection()

    row = conn.execute(
        "SELECT photo_path FROM registrations WHERE id = ?",
        (registration_id,)
    ).fetchone()

    if row and row["photo_path"]:
        try:
            if os.path.exists(row["photo_path"]):
                os.remove(row["photo_path"])
        except Exception:
            pass

    conn.execute(
        "DELETE FROM registrations WHERE id = ?",
        (registration_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# PHONE
# =========================================================

def normalize_moroccan_phone(value):
    raw = re.sub(r"[\s\-]", "", str(value or ""))

    if re.fullmatch(r"0[67]\d{8}", raw):
        return "+212" + raw[1:]

    if re.fullmatch(r"\+212[67]\d{8}", raw):
        return raw

    if re.fullmatch(r"00212[67]\d{8}", raw):
        return "+" + raw[2:]

    return None


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Cairo:wght@500;600;700;800&display=swap');

:root {
    --red: #e62b1e;
    --red-dark: #9e1710;
    --black: #080808;
    --panel: rgba(18,18,18,.78);
    --border: rgba(255,255,255,.09);
}

html, body, [class*="css"] {
    font-family: "Inter", sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(230,43,30,.14),
            transparent 32%
        ),
        radial-gradient(
            circle at 85% 90%,
            rgba(230,43,30,.10),
            transparent 32%
        ),
        #080808;
    color: white;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(
            120deg,
            transparent 0%,
            rgba(255,255,255,.015) 50%,
            transparent 100%
        );
    z-index: 0;
}

.block-container {
    max-width: 1250px !important;
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

footer {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    background: #090909;
}

.glass {
    background: linear-gradient(
        145deg,
        rgba(28,28,28,.82),
        rgba(8,8,8,.72)
    );
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 28px;
    padding: 30px;
    box-shadow:
        0 30px 80px rgba(0,0,0,.55),
        inset 0 1px 0 rgba(255,255,255,.04);
    backdrop-filter: blur(20px);
}

.logo {
    width: 105px;
    height: 105px;
    object-fit: cover;
    border-radius: 50%;
    border: 2px solid rgba(230,43,30,.6);
    box-shadow:
        0 0 35px rgba(230,43,30,.28);
}

.hero-title {
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1;
    margin-top: 15px;
}

.hero-red {
    color: #e62b1e;
}

.arabic {
    font-family: "Cairo", sans-serif;
}

.hero-sub {
    color: #e62b1e;
    font-family: "Cairo", sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 12px;
}

.muted {
    color: #888;
    font-size: .78rem;
    letter-spacing: 3px;
    text-transform: uppercase;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 18px;
}

.timer-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 22px 0 28px;
}

.timer-box {
    background: rgba(0,0,0,.52);
    border: 1px solid rgba(230,43,30,.28);
    border-radius: 15px;
    padding: 15px 8px;
    text-align: center;
}

.timer-number {
    color: #fff;
    font-size: 1.55rem;
    font-weight: 800;
}

.timer-label {
    color: #777;
    font-size: .65rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {
    background: rgba(0,0,0,.48) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 13px !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: rgba(0,0,0,.65) !important;
    color: white !important;
    border-radius: 13px !important;
    border: 1px solid rgba(255,255,255,.14) !important;
}

label {
    color: #ccc !important;
}

.stButton > button {
    width: 100%;
    min-height: 48px;
    border-radius: 13px;
    border: 1px solid rgba(255,255,255,.10);
    background: linear-gradient(
        135deg,
        #e62b1e,
        #b51e15
    );
    color: white;
    font-weight: 800;
    transition: .2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        0 12px 30px rgba(230,43,30,.25);
    border-color: rgba(255,255,255,.18);
}

.admin-btn > button {
    background: rgba(255,255,255,.05) !important;
    color: #777 !important;
    border: none !important;
    font-size: .8rem;
}

.stat-card {
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 20px;
    padding: 20px;
    min-height: 125px;
}

.stat-label {
    color: #777;
    font-size: .7rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    margin-top: 7px;
}

.stat-red {
    color: #e62b1e;
}

.admin-header {
    display: flex;
    align-items: center;
    gap: 15px;
}

.admin-status {
    color: #48d597;
    font-size: .8rem;
}

.wa-button {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 12px;
    border-radius: 9px;
    color: #49df93;
    background: rgba(37,211,102,.09);
    border: 1px solid rgba(37,211,102,.18);
    text-decoration: none;
    font-size: .75rem;
    font-weight: 800;
}

.wa-button:hover {
    background: rgba(37,211,102,.16);
}

.small-text {
    color: #777;
    font-size: .72rem;
}

.name-text {
    font-size: 1rem;
    font-weight: 800;
}

@media (max-width: 700px) {
    .block-container {
        padding: 1rem !important;
    }
    .glass {
        padding: 20px 16px;
        border-radius: 22px;
    }
    .timer-grid {
        gap: 6px;
    }
    .timer-box {
        padding: 11px 4px;
    }
    .timer-number {
        font-size: 1.15rem;
    }
    .hero-title {
        font-size: 2.1rem;
    }
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATABASE INIT
# =========================================================

init_database()


# =========================================================
# SESSION
# =========================================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

if "page" not in st.session_state:
    st.session_state.page = "registration"

if "success" not in st.session_state:
    st.session_state.success = False

if "login_error" not in st.session_state:
    st.session_state.login_error = False


# =========================================================
# COUNTDOWN
# =========================================================

def render_countdown():
    deadline = get_deadline()
    now = datetime.now()

    seconds = max(
        0,
        int((deadline - now).total_seconds())
    )

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    st.markdown(f"""
    <div class="timer-grid">
        <div class="timer-box">
            <div class="timer-number">{days:02d}</div>
            <div class="timer-label">Jours</div>
        </div>
        <div class="timer-box">
            <div class="timer-number">{hours:02d}</div>
            <div class="timer-label">Heures</div>
        </div>
        <div class="timer-box">
            <div class="timer-number">{minutes:02d}</div>
            <div class="timer-label">Min</div>
        </div>
        <div class="timer-box">
            <div class="timer-number">{secs:02d}</div>
            <div class="timer-label">Sec</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# REGISTRATION PAGE
# =========================================================

def registration_page():
    st.markdown('<div class="glass">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=105)

        st.markdown("""
        <div style="text-align:center">
            <div class="hero-title">
                TED<span class="hero-red">x</span> B'DARIJA
            </div>
            <div class="hero-sub">
                انضموا إلينا هذا العام!
            </div>
            <div class="muted">
                Ideas Worth Spreading
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    st.markdown(
        '<div style="text-align:center;color:#777;font-size:.72rem;'
        'text-transform:uppercase;letter-spacing:2px;">'
        'Fin des inscriptions dans'
        '</div>',
        unsafe_allow_html=True
    )

    render_countdown()

    st.markdown("""
    <div class="section-title">
        Inscription
    </div>
    """, unsafe_allow_html=True)

    with st.form("registration_form", clear_on_submit=False):
        name = st.text_input(
            "Nom et Prénom",
            placeholder="Votre nom complet"
        )

        phone = st.text_input(
            "Numéro WhatsApp",
            placeholder="Ex: 0612345678"
        )

        st.caption(
            "06 / 07 ou +212 — le numéro sera vérifié automatiquement."
        )

        col_a, col_b = st.columns(2)

        with col_a:
            major = st.text_input(
                "Filière",
                placeholder="Ex: SMI, Économie..."
            )

        with col_b:
            year = st.selectbox(
                "Année",
                [
                    "Choisir...",
                    "1ère Année",
                    "2ème Année",
                    "3ème Année",
                    "4ème Année",
                    "5ème Année",
                ]
            )

        photo = st.file_uploader(
            "Photo — Visage clair",
            type=["jpg", "jpeg", "png", "webp"],
            help="Photo claire du visage. Maximum 3 MB."
        )

        submitted = st.form_submit_button(
            "S'inscrire  →"
        )

        if submitted:
            normalized = normalize_moroccan_phone(phone)

            if not name.strip():
                st.error("Veuillez entrer votre nom.")
            elif not normalized:
                st.error("Veuillez entrer un numéro marocain valide.")
            elif not major.strip():
                st.error("Veuillez entrer votre filière.")
            elif year == "Choisir...":
                st.error("Veuillez choisir votre année.")
            elif photo is None:
                st.error("Veuillez ajouter votre photo.")
            elif photo.size > 3 * 1024 * 1024:
                st.error("La photo est trop volumineuse. Maximum 3 MB.")
            elif datetime.now() >= get_deadline():
                st.error("Les inscriptions sont terminées.")
            else:
                try:
                    extension = os.path.splitext(photo.name)[1].lower()
                    filename = (
                        datetime.now().strftime("%Y%m%d_%H%M%S_%f") + extension
                    )
                    photo_path = os.path.join(UPLOAD_DIR, filename)

                    with open(photo_path, "wb") as f:
                        f.write(photo.getbuffer())

                    add_registration(
                        name.strip(),
                        normalized,
                        major.strip(),
                        year,
                        photo_path
                    )

                    st.success("Votre inscription a été enregistrée avec succès !")
                    st.balloons()
                    st.session_state.success = True

                except Exception as e:
                    st.error(f"Erreur lors de l'inscription : {e}")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown(
        '<div style="text-align:center;color:#333;">TEDx B\'DARIJA</div>',
        unsafe_allow_html=True
    )

    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="admin-btn">', unsafe_allow_html=True)
        if st.button("🔒 Accès Administration", key="open_admin"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================

def login_page():
    st.markdown('<div class="glass">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=90)

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:1.7rem;
                font-weight:800;
                margin-bottom:20px;
            ">
                Accès Sécurisé
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="Email administrateur"
            )
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Mot de passe"
            )
            submitted = st.form_submit_button("Connexion")

            if submitted:
                if (
                    email.strip().lower() == ADMIN_EMAIL.lower()
                    and password == ADMIN_PASSWORD
                ):
                    st.session_state.admin_logged = True
                    st.session_state.page = "admin"
                    st.session_state.login_error = False
                    st.rerun()
                else:
                    st.session_state.login_error = True

        if st.session_state.login_error:
            st.error("Identifiants incorrects.")

        st.markdown("")

        if st.button("← Retour à l'inscription"):
            st.session_state.page = "registration"
            st.session_state.login_error = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():
    if not st.session_state.admin_logged:
        st.session_state.page = "login"
        st.rerun()

    registrations = get_registrations()
    total = len(registrations)
    majors = set(
        r["major"].strip().lower()
        for r in registrations
        if r["major"]
    )
    last_registration = (
        registrations[0]["created_at"]
        if registrations
        else None
    )
    deadline = get_deadline()

    st.markdown('<div class="glass">', unsafe_allow_html=True)

    header1, header2 = st.columns([2, 1])

    with header1:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=62)

        st.markdown("""
        <div class="admin-header">
            <div>
                <div style="font-size:1.6rem; font-weight:800;">
                    Dashboard Admin
                </div>
                <div class="admin-status">
                    ● Base de données locale active
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with header2:
        if st.button("🚪 Quitter", key="logout"):
            st.session_state.admin_logged = False
            st.session_state.page = "registration"
            st.rerun()

    st.markdown("")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Inscriptions</div>
            <div class="stat-number">{total}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Filières</div>
            <div class="stat-number stat-red">{len(majors)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        if last_registration:
            try:
                dt = datetime.fromisoformat(last_registration).strftime("%d/%m/%Y %H:%M")
            except Exception:
                dt = "—"
        else:
            dt = "—"

        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Dernière inscription</div>
            <div style="font-size:.9rem; font-weight:700; margin-top:13px;">
                {dt}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Deadline</div>
            <div style="color:#ff6258; font-size:.9rem; font-weight:700; margin-top:13px;">
                {deadline.strftime("%d/%m/%Y %H:%M")}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    with st.expander("⚙️ Modifier la deadline", expanded=False):
        new_date = st.date_input("Date", value=deadline.date(), key="deadline_date")
        new_time = st.time_input("Heure", value=deadline.time().replace(second=0, microsecond=0), key="deadline_time")

        if st.button("Enregistrer la deadline", key="save_deadline"):
            new_deadline = datetime.combine(new_date, new_time)
            if new_deadline <= datetime.now():
                st.error("La deadline doit être dans le futur.")
            else:
                save_deadline(new_deadline)
                st.success("Deadline mise à jour avec succès.")
                st.rerun()

    st.markdown("")

    action1, action2, action3 = st.columns(3)

    with action1:
        if st.button("🔄 Actualiser", key="refresh_admin"):
            st.rerun()

    with action2:
        csv_data = create_csv(registrations)
        st.download_button(
            "📥 Exporter CSV",
            data=csv_data,
            file_name="tedx-bdarija-inscriptions-" + datetime.now().strftime("%Y-%m-%d") + ".csv",
            mime="text/csv",
            key="export_csv"
        )

    with action3:
        if st.button("🗑️ Vider toutes les inscriptions", key="clear_all"):
            st.session_state.confirm_clear = True

    if st.session_state.get("confirm_clear", False):
        st.warning("Cette action supprimera toutes les inscriptions.")
        confirm1, confirm2 = st.columns(2)

        with confirm1:
            if st.button("Oui, supprimer tout", key="confirm_delete"):
                conn = get_connection()
                rows = conn.execute("SELECT photo_path FROM registrations").fetchall()
                for row in rows:
                    if row["photo_path"]:
                        try:
                            if os.path.exists(row["photo_path"]):
                                os.remove(row["photo_path"])
                        except Exception:
                            pass
                conn.execute("DELETE FROM registrations")
                conn.commit()
                conn.close()
                st.session_state.confirm_clear = False
                st.success("Toutes les inscriptions ont été supprimées.")
                st.rerun()

        with confirm2:
            if st.button("Annuler", key="cancel_delete"):
                st.session_state.confirm_clear = False
                st.rerun()

    st.markdown("")

    search = st.text_input("🔎 Rechercher", placeholder="Nom, WhatsApp, filière...")
    filtered = []

    for row in registrations:
        if not search.strip():
            filtered.append(row)
            continue
        q = search.lower()
        combined = " ".join([
            str(row["name"] or ""),
            str(row["phone"] or ""),
            str(row["major"] or ""),
            str(row["year"] or "")
        ]).lower()
        if q in combined:
            filtered.append(row)

    st.markdown(
        f"""
        <div style="margin-top:20px; margin-bottom:15px; font-size:1.25rem; font-weight:800;">
            Participants
            <span style="color:#e62b1e; font-size:.9rem;">
                {len(filtered)}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered:
        st.info("Aucune inscription pour le moment.")

    for row in filtered:
        registration_card(row)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# REGISTRATION CARD
# =========================================================

def registration_card(row):
    photo_path = row["photo_path"]
    left, middle, right = st.columns([0.8, 3, 1.2])

    with left:
        if photo_path and os.path.exists(photo_path):
            st.image(photo_path, width=65)
        else:
            initials = row["name"][:1] if row["name"] else "?"
            st.markdown(
                f"""
                <div style="
                    width:65px;
                    height:65px;
                    border-radius:50%;
                    background:#171717;
                    border:2px solid #e62b1e;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:22px;
                    font-weight:800;
                    color:#e62b1e;
                ">
                    {html.escape(initials.upper())}
                </div>
                """,
                unsafe_allow_html=True
            )

    with middle:
        st.markdown(
            f"""
            <div class="name-text">
                {html.escape(row["name"])}
            </div>
            <div class="small-text">
                {html.escape(row["major"])}
                •
                {html.escape(row["year"])}
            </div>
            <div class="small-text" style="margin-top:5px;">
                📱 {html.escape(row["phone"])}
            </div>
            """,
            unsafe_allow_html=True
        )

        try:
            date = datetime.fromisoformat(row["created_at"]).strftime("%d/%m/%Y à %H:%M")
        except Exception:
            date = "—"

        st.caption(f"Inscrit le {date}")

    with right:
        phone = row["phone"]
        wa_number = phone.replace("+", "")
        wa_url = f"https://wa.me/{wa_number}"

        st.markdown(
            f"""
            <a href="{wa_url}" target="_blank" class="wa-button">
                🟢 WhatsApp
            </a>
            """,
            unsafe_allow_html=True
        )

        st.markdown("")

        if st.button("Supprimer", key=f"delete_{row['id']}"):
            delete_registration(row["id"])
            st.success("Inscription supprimée.")
            st.rerun()

    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,.05);margin:12px 0;"></div>',
        unsafe_allow_html=True
    )


# =========================================================
# CSV
# =========================================================

def create_csv(rows):
    output = io.StringIO()
    writer = csv.writer(
        output,
        delimiter=";",
        quoting=csv.QUOTE_ALL
    )

    writer.writerow([
        "Nom et prénom",
        "WhatsApp",
        "Filière",
        "Année",
        "Date"
    ])

    for row in rows:
        writer.writerow([
            row["name"],
            row["phone"],
            row["major"],
            row["year"],
            row["created_at"]
        ])

    return "\ufeff" + output.getvalue()


# =========================================================
# ROUTING
# =========================================================

if st.session_state.page == "registration":
    registration_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "admin":
    admin_dashboard()
