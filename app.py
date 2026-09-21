import streamlit as st
import re
import csv
import io
import html
import base64
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client


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
LOGO_PATH = "tedx-bdarija-logo.png"
STORAGE_BUCKET = "participant-photos"


# =========================================================
# SECRETS
# =========================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

except Exception:
    st.error(
        "Configuration manquante. "
        "Ajoutez SUPABASE_URL, SUPABASE_KEY, ADMIN_EMAIL "
        "et ADMIN_PASSWORD dans Streamlit Secrets."
    )
    st.stop()


# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


supabase = get_supabase()


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Cairo:wght@500;600;700;800&display=swap'
);

:root {
    --red: #e62b1e;
    --red-dark: #9e1710;
    --black: #080808;
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

.glass {
    background: linear-gradient(
        145deg,
        rgba(28,28,28,.84),
        rgba(8,8,8,.74)
    );
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 28px;
    padding: 30px;
    box-shadow:
        0 30px 80px rgba(0,0,0,.55),
        inset 0 1px 0 rgba(255,255,255,.04);
    backdrop-filter: blur(20px);
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

.hero-sub {
    color: #e62b1e;
    font-family: "Cairo", sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 12px;
}

.muted {
    color: #777;
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
div[data-testid="stTextArea"] textarea {
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

div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {
    background: rgba(0,0,0,.48) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 13px !important;
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
}

.admin-btn > button {
    background: rgba(255,255,255,.05) !important;
    color: #777 !important;
    border: none !important;
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

.registration-card {
    background: rgba(255,255,255,.025);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 18px;
    padding: 14px;
    margin-bottom: 10px;
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
""",
    unsafe_allow_html=True
)


# =========================================================
# SESSION
# =========================================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

if "page" not in st.session_state:
    st.session_state.page = "registration"

if "login_error" not in st.session_state:
    st.session_state.login_error = False

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc)


def get_logo_base64():
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def normalize_moroccan_phone(value):
    raw = re.sub(r"[\s\-]", "", str(value or ""))

    if re.fullmatch(r"0[67]\d{8}", raw):
        return "+212" + raw[1:]

    if re.fullmatch(r"\+212[67]\d{8}", raw):
        return raw

    if re.fullmatch(r"00212[67]\d{8}", raw):
        return "+" + raw[2:]

    return None


def parse_datetime(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt

    except Exception:
        return None


# =========================================================
# SETTINGS / DEADLINE
# =========================================================

def get_deadline():

    try:
        response = (
            supabase
            .table("settings")
            .select("value")
            .eq("key", "deadline")
            .limit(1)
            .execute()
        )

        if response.data:
            deadline = parse_datetime(
                response.data[0]["value"]
            )

            if deadline:
                return deadline

    except Exception:
        pass

    return utc_now() + timedelta(days=30)


def save_deadline(value):

    value_utc = value.astimezone(
        timezone.utc
    )

    supabase.table("settings").upsert({
        "key": "deadline",
        "value": value_utc.isoformat()
    }).execute()


# =========================================================
# REGISTRATIONS
# =========================================================

def get_registrations():

    response = (
        supabase
        .table("registrations")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def add_registration(
    name,
    phone,
    major,
    year,
    photo_path
):

    response = (
        supabase
        .table("registrations")
        .insert({
            "name": name,
            "phone": phone,
            "major": major,
            "year": year,
            "photo_path": photo_path
        })
        .execute()
    )

    return response.data


def delete_registration(
    registration_id,
    photo_path=None
):

    if photo_path:

        try:
            supabase.storage.from_(
                STORAGE_BUCKET
            ).remove([photo_path])

        except Exception:
            pass

    (
        supabase
        .table("registrations")
        .delete()
        .eq("id", registration_id)
        .execute()
    )


def clear_all_registrations():

    rows = get_registrations()

    paths = [
        r["photo_path"]
        for r in rows
        if r.get("photo_path")
    ]

    if paths:

        try:
            supabase.storage.from_(
                STORAGE_BUCKET
            ).remove(paths)

        except Exception:
            pass

    (
        supabase
        .table("registrations")
        .delete()
        .neq("id", 0)
        .execute()
    )


# =========================================================
# PHOTO STORAGE
# =========================================================

def upload_photo(uploaded_file):

    extension = uploaded_file.name.split(".")[-1].lower()

    filename = (
        datetime.now(timezone.utc)
        .strftime("%Y%m%d_%H%M%S_%f")
        + "."
        + extension
    )

    file_bytes = uploaded_file.getvalue()

    (
        supabase
        .storage
        .from_(STORAGE_BUCKET)
        .upload(
            filename,
            file_bytes,
            {
                "content-type": uploaded_file.type,
                "upsert": "false"
            }
        )
    )

    return filename


def get_photo_url(path):

    if not path:
        return None

    try:

        result = (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .create_signed_url(
                path,
                3600
            )
        )

        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl")

    except Exception:
        return None

    return None


# =========================================================
# COUNTDOWN
# =========================================================

def render_countdown():

    deadline = get_deadline()
    now = utc_now()

    seconds = max(
        0,
        int((deadline - now).total_seconds())
    )

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True
    )


# =========================================================
# REGISTRATION PAGE
# =========================================================

def registration_page():

    st.markdown(
        '<div class="glass">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if get_logo_base64():

            st.image(
                LOGO_PATH,
                width=105
            )

        st.markdown(
            """
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
            """,
            unsafe_allow_html=True
        )

    st.markdown("")

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#777;
            font-size:.72rem;
            text-transform:uppercase;
            letter-spacing:2px;
        ">
            Fin des inscriptions dans
        </div>
        """,
        unsafe_allow_html=True
    )

    render_countdown()

    st.markdown(
        '<div class="section-title">Inscription</div>',
        unsafe_allow_html=True
    )

    with st.form(
        "registration_form",
        clear_on_submit=False
    ):

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
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            help="Photo claire du visage. Maximum 3 MB."
        )

        submitted = st.form_submit_button(
            "S'inscrire  →"
        )

        if submitted:

            normalized = normalize_moroccan_phone(phone)

            deadline = get_deadline()

            if not name.strip():

                st.error(
                    "Veuillez entrer votre nom."
                )

            elif not normalized:

                st.error(
                    "Veuillez entrer un numéro marocain valide."
                )

            elif not major.strip():

                st.error(
                    "Veuillez entrer votre filière."
                )

            elif year == "Choisir...":

                st.error(
                    "Veuillez choisir votre année."
                )

            elif photo is None:

                st.error(
                    "Veuillez ajouter votre photo."
                )

            elif photo.size > 3 * 1024 * 1024:

                st.error(
                    "La photo est trop volumineuse. Maximum 3 MB."
                )

            elif utc_now() >= deadline:

                st.error(
                    "Les inscriptions sont terminées."
                )

            else:

                try:

                    photo_path = upload_photo(
                        photo
                    )

                    add_registration(
                        name.strip(),
                        normalized,
                        major.strip(),
                        year,
                        photo_path
                    )

                    st.success(
                        "Votre inscription a été enregistrée avec succès !"
                    )

                    st.balloons()

                except Exception as e:

                    st.error(
                        "Une erreur est survenue lors de "
                        f"l'inscription : {e}"
                    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("")

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#333;
        ">
            TEDx B'DARIJA
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.markdown(
            '<div class="admin-btn">',
            unsafe_allow_html=True
        )

        if st.button(
            "🔒 Accès Administration",
            key="open_admin"
        ):

            st.session_state.page = "login"
            st.rerun()

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


# =========================================================
# LOGIN
# =========================================================

def login_page():

    st.markdown(
        '<div class="glass">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if get_logo_base64():

            st.image(
                LOGO_PATH,
                width=90
            )

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

            submitted = st.form_submit_button(
                "Connexion"
            )

            if submitted:

                if (
                    email.strip().lower()
                    == ADMIN_EMAIL.strip().lower()
                    and password
                    == ADMIN_PASSWORD
                ):

                    st.session_state.admin_logged = True
                    st.session_state.page = "admin"
                    st.session_state.login_error = False

                    st.rerun()

                else:

                    st.session_state.login_error = True

        if st.session_state.login_error:

            st.error(
                "Identifiants incorrects."
            )

        st.markdown("")

        if st.button(
            "← Retour à l'inscription"
        ):

            st.session_state.page = "registration"
            st.session_state.login_error = False

            st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# REGISTRATION CARD
# =========================================================

def registration_card(row):

    photo_path = row.get("photo_path")

    left, middle, right = st.columns(
        [0.8, 3, 1.2]
    )

    with left:

        photo_url = get_photo_url(
            photo_path
        )

        if photo_url:

            st.image(
                photo_url,
                width=65
            )

        else:

            initials = (
                row.get("name", "?")[:1]
                if row.get("name")
                else "?"
            )

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
                {html.escape(str(row.get("name", "")))}
            </div>

            <div class="small-text">
                {html.escape(str(row.get("major", "")))}
                •
                {html.escape(str(row.get("year", "")))}
            </div>

            <div class="small-text" style="margin-top:5px;">
                📱 {html.escape(str(row.get("phone", "")))}
            </div>
            """,
            unsafe_allow_html=True
        )

        dt = parse_datetime(
            row.get("created_at")
        )

        if dt:

            date_text = dt.astimezone().strftime(
                "%d/%m/%Y à %H:%M"
            )

        else:

            date_text = "—"

        st.caption(
            f"Inscrit le {date_text}"
        )

    with right:

        phone = str(
            row.get("phone", "")
        )

        wa_number = phone.replace(
            "+",
            ""
        )

        wa_url = (
            f"https://wa.me/{wa_number}"
        )

        st.markdown(
            f"""
            <a
                href="{wa_url}"
                target="_blank"
                class="wa-button"
            >
                🟢 WhatsApp
            </a>
            """,
            unsafe_allow_html=True
        )

        st.markdown("")

        if st.button(
            "Supprimer",
            key=f"delete_{row['id']}"
        ):

            delete_registration(
                row["id"],
                row.get("photo_path")
            )

            st.success(
                "Inscription supprimée."
            )

            st.rerun()

    st.markdown(
        """
        <div style="
            height:1px;
            background:rgba(255,255,255,.05);
            margin:12px 0;
        "></div>
        """,
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
            row.get("name", ""),
            row.get("phone", ""),
            row.get("major", ""),
            row.get("year", ""),
            row.get("created_at", "")
        ])

    return (
        "\ufeff"
        + output.getvalue()
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    if not st.session_state.admin_logged:

        st.session_state.page = "login"
        st.rerun()

    try:

        registrations = get_registrations()

    except Exception as e:

        st.error(
            f"Impossible de charger les inscriptions : {e}"
        )

        return

    total = len(registrations)

    majors = set(
        str(r.get("major", "")).strip().lower()
        for r in registrations
        if r.get("major")
    )

    last_registration = (
        registrations[0].get("created_at")
        if registrations
        else None
    )

    deadline = get_deadline()

    # HEADER

    st.markdown(
        '<div class="glass">',
        unsafe_allow_html=True
    )

    header1, header2 = st.columns([2, 1])

    with header1:

        if get_logo_base64():

            st.image(
                LOGO_PATH,
                width=62
            )

        st.markdown(
            """
            <div style="
                font-size:1.6rem;
                font-weight:800;
            ">
                Dashboard Admin
            </div>

            <div class="admin-status">
                ● Online database active
            </div>
            """,
            unsafe_allow_html=True
        )

    with header2:

        if st.button(
            "🚪 Quitter",
            key="logout"
        ):

            st.session_state.admin_logged = False
            st.session_state.page = "registration"

            st.rerun()

    st.markdown("")

    # STATS

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">
                    Inscriptions
                </div>

                <div class="stat-number">
                    {total}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">
                    Filières
                </div>

                <div class="stat-number stat-red">
                    {len(majors)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        last_dt = parse_datetime(
            last_registration
        )

        last_text = (
            last_dt.astimezone().strftime(
                "%d/%m/%Y %H:%M"
            )
            if last_dt
            else "—"
        )

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">
                    Dernière inscription
                </div>

                <div style="
                    font-size:.9rem;
                    font-weight:700;
                    margin-top:13px;
                ">
                    {last_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">
                    Deadline
                </div>

                <div style="
                    color:#ff6258;
                    font-size:.9rem;
                    font-weight:700;
                    margin-top:13px;
                ">
                    {deadline.astimezone().strftime(
                        "%d/%m/%Y %H:%M"
                    )}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # DEADLINE

    st.markdown("")

    with st.expander(
        "⚙️ Modifier la deadline"
    ):

        local_deadline = deadline.astimezone()

        new_date = st.date_input(
            "Date",
            value=local_deadline.date(),
            key="deadline_date"
        )

        new_time = st.time_input(
            "Heure",
            value=local_deadline.time().replace(
                second=0,
                microsecond=0
            ),
            key="deadline_time"
        )

        if st.button(
            "Enregistrer la deadline",
            key="save_deadline"
        ):

            new_deadline = datetime.combine(
                new_date,
                new_time
            ).astimezone()

            if new_deadline <= datetime.now().astimezone():

                st.error(
                    "La deadline doit être dans le futur."
                )

            else:

                save_deadline(
                    new_deadline
                )

                st.success(
                    "Deadline mise à jour avec succès."
                )

                st.rerun()

    # ACTIONS

    st.markdown("")

    action1, action2, action3 = st.columns(3)

    with action1:

        if st.button(
            "🔄 Actualiser",
            key="refresh_admin"
        ):

            st.rerun()

    with action2:

        csv_data = create_csv(
            registrations
        )

        st.download_button(
            "📥 Exporter CSV",
            data=csv_data,
            file_name=(
                "tedx-bdarija-inscriptions-"
                + datetime.now().strftime("%Y-%m-%d")
                + ".csv"
            ),
            mime="text/csv",
            key="export_csv"
        )

    with action3:

        if st.button(
            "🗑️ Vider toutes les inscriptions",
            key="clear_all"
        ):

            st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:

        st.warning(
            "Cette action supprimera toutes les inscriptions et photos."
        )

        confirm1, confirm2 = st.columns(2)

        with confirm1:

            if st.button(
                "Oui, supprimer tout",
                key="confirm_delete"
            ):

                try:

                    clear_all_registrations()

                    st.session_state.confirm_clear = False

                    st.success(
                        "Toutes les inscriptions ont été supprimées."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Erreur : {e}"
                    )

        with confirm2:

            if st.button(
                "Annuler",
                key="cancel_delete"
            ):

                st.session_state.confirm_clear = False
                st.rerun()

    # SEARCH

    st.markdown("")

    search = st.text_input(
        "🔎 Rechercher",
        placeholder="Nom, WhatsApp, filière..."
    )

    filtered = []

    for row in registrations:

        if not search.strip():

            filtered.append(row)
            continue

        q = search.lower().strip()

        combined = " ".join([
            str(row.get("name", "")),
            str(row.get("phone", "")),
            str(row.get("major", "")),
            str(row.get("year", ""))
        ]).lower()

        if q in combined:

            filtered.append(row)

    st.markdown(
        f"""
        <div style="
            margin-top:20px;
            margin-bottom:15px;
            font-size:1.25rem;
            font-weight:800;
        ">
            Participants
            <span style="
                color:#e62b1e;
                font-size:.9rem;
            ">
                {len(filtered)}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered:

        st.info(
            "Aucune inscription pour le moment."
        )

    for row in filtered:

        registration_card(row)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# ROUTING
# =========================================================

if st.session_state.page == "registration":

    registration_page()

elif st.session_state.page == "login":

    login_page()

elif st.session_state.page == "admin":

    admin_dashboard()
