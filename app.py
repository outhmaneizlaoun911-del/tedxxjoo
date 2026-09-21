import streamlit as st
import sqlite3
import os
import re
import csv
import io
import html
import base64
import time
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

DB_PATH = "tedx_bdarija.db"
UPLOAD_DIR = "uploads"
LOGO_PATH = "tedx-bdarija-logo.png.jpg"

ADMIN_EMAIL = "outhmane@farah.love"
ADMIN_PASSWORD = "oufa@2026@!"

MAX_PHOTO_SIZE = 3 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
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

    row = conn.execute("""
        SELECT value
        FROM settings
        WHERE key = 'deadline'
    """).fetchone()

    if not row:

        deadline = (
            datetime.now() +
            timedelta(days=30)
        )

        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
        """, (
            "deadline",
            deadline.isoformat(
                timespec="minutes"
            )
        ))

    conn.commit()
    conn.close()


def get_setting(key, default=None):

    conn = get_connection()

    row = conn.execute("""
        SELECT value
        FROM settings
        WHERE key = ?
    """, (key,)).fetchone()

    conn.close()

    if row:
        return row["value"]

    return default


def save_setting(key, value):

    conn = get_connection()

    conn.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, value))

    conn.commit()
    conn.close()


def get_deadline():

    value = get_setting("deadline")

    if not value:
        return datetime.now() + timedelta(days=30)

    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now() + timedelta(days=30)


def add_registration(
    name,
    phone,
    major,
    year,
    photo_path
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO registrations
        (
            name,
            phone,
            major,
            year,
            photo_path,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        major,
        year,
        photo_path,
        datetime.now().isoformat(
            timespec="seconds"
        )
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

    row = conn.execute("""
        SELECT photo_path
        FROM registrations
        WHERE id = ?
    """, (registration_id,)).fetchone()

    if row and row["photo_path"]:

        try:
            if os.path.exists(
                row["photo_path"]
            ):
                os.remove(
                    row["photo_path"]
                )
        except Exception:
            pass

    conn.execute("""
        DELETE FROM registrations
        WHERE id = ?
    """, (registration_id,))

    conn.commit()
    conn.close()


def clear_registrations():

    conn = get_connection()

    rows = conn.execute("""
        SELECT photo_path
        FROM registrations
    """).fetchall()

    for row in rows:

        if row["photo_path"]:

            try:
                if os.path.exists(
                    row["photo_path"]
                ):
                    os.remove(
                        row["photo_path"]
                    )
            except Exception:
                pass

    conn.execute("""
        DELETE FROM registrations
    """)

    conn.commit()
    conn.close()


# =========================================================
# HELPERS
# =========================================================

def get_logo_base64():

    if not os.path.exists(LOGO_PATH):
        return None

    try:

        with open(
            LOGO_PATH,
            "rb"
        ) as file:

            return base64.b64encode(
                file.read()
            ).decode()

    except Exception:
        return None


def normalize_phone(value):

    raw = re.sub(
        r"[\s\-().]",
        "",
        str(value or "")
    )

    if re.fullmatch(
        r"0[67]\d{8}",
        raw
    ):
        return "+212" + raw[1:]

    if re.fullmatch(
        r"\+212[67]\d{8}",
        raw
    ):
        return raw

    if re.fullmatch(
        r"00212[67]\d{8}",
        raw
    ):
        return "+" + raw[2:]

    return None


def safe_filename(name):

    extension = os.path.splitext(
        name
    )[1].lower()

    allowed = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]

    if extension not in allowed:
        return ".jpg"

    return extension


def format_date(value):

    try:

        return datetime.fromisoformat(
            value
        ).strftime(
            "%d/%m/%Y • %H:%M"
        )

    except Exception:
        return "—"


def create_csv(rows):

    output = io.StringIO()

    writer = csv.writer(
        output,
        delimiter=";",
        quoting=csv.QUOTE_ALL
    )

    writer.writerow([
        "ID",
        "Nom et prénom",
        "WhatsApp",
        "Filière",
        "Année",
        "Date"
    ])

    for row in rows:

        writer.writerow([
            row["id"],
            row["name"],
            row["phone"],
            row["major"],
            row["year"],
            row["created_at"]
        ])

    return "\ufeff" + output.getvalue()


# =========================================================
# DATABASE INIT
# =========================================================

init_database()


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

if "login_error" not in st.session_state:
    st.session_state.login_error = False

if "success" not in st.session_state:
    st.session_state.success = False

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Cairo:wght@400;500;600;700;800;900&display=swap'
);

:root {
    --red: #e62b1e;
    --red2: #ff4438;
    --black: #050505;
    --white: #ffffff;
    --muted: #8b8b8b;
    --glass: rgba(255,255,255,.055);
    --border: rgba(255,255,255,.10);
}

* {
    box-sizing: border-box;
}

html,
body,
[data-testid="stAppViewContainer"],
.stApp {

    margin: 0 !important;
    padding: 0 !important;

    font-family:
        "Inter",
        sans-serif !important;

    background:
        radial-gradient(
            circle at 12% 5%,
            rgba(230,43,30,.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 80%,
            rgba(230,43,30,.12),
            transparent 30%
        ),
        #050505 !important;

    color: white !important;
}

body {
    overflow-x: hidden;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {

    max-width: 1400px !important;

    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
}

/* ===================================================== */
/* BACKGROUND */
/* ===================================================== */

.stApp::before {

    content: "";

    position: fixed;

    width: 700px;
    height: 700px;

    top: -350px;
    left: -250px;

    background:
        radial-gradient(
            circle,
            rgba(230,43,30,.15),
            transparent 68%
        );

    pointer-events: none;

    z-index: 0;

    animation:
        floatingGlow 10s ease-in-out infinite;
}

.stApp::after {

    content: "";

    position: fixed;

    width: 500px;
    height: 500px;

    bottom: -250px;
    right: -180px;

    background:
        radial-gradient(
            circle,
            rgba(230,43,30,.12),
            transparent 70%
        );

    pointer-events: none;

    z-index: 0;

    animation:
        floatingGlow2 12s ease-in-out infinite;
}

@keyframes floatingGlow {

    0%,100% {
        transform: translate3d(0,0,0);
    }

    50% {
        transform: translate3d(80px,60px,0);
    }
}

@keyframes floatingGlow2 {

    0%,100% {
        transform: translate3d(0,0,0);
    }

    50% {
        transform: translate3d(-70px,-40px,0);
    }
}

/* ===================================================== */
/* HERO */
/* ===================================================== */

.hero-shell {

    position: relative;

    min-height: 680px;

    display: flex;

    align-items: center;

    justify-content: center;

    overflow: hidden;

    border-radius: 42px;

    border:
        1px solid rgba(255,255,255,.10);

    background:

        linear-gradient(
            135deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.015)
        );

    box-shadow:

        0 50px 120px rgba(0,0,0,.65),

        inset 0 1px 0
        rgba(255,255,255,.08);

    backdrop-filter: blur(25px);

    transform-style: preserve-3d;
}

.hero-shell::before {

    content: "";

    position: absolute;

    inset: 0;

    background:

        linear-gradient(
            120deg,
            transparent 25%,
            rgba(255,255,255,.035) 45%,
            transparent 65%
        );

    animation:
        shine 7s linear infinite;

    pointer-events: none;
}

@keyframes shine {

    0% {
        transform: translateX(-100%);
    }

    100% {
        transform: translateX(100%);
    }
}

/* ===================================================== */
/* 3D ORBIT */
/* ===================================================== */

.orbit-scene {

    position: absolute;

    width: 620px;
    height: 620px;

    right: -80px;
    top: 30px;

    perspective: 1000px;

    pointer-events: none;

    opacity: .95;
}

.orbit {

    position: absolute;

    inset: 70px;

    border:
        1px solid rgba(230,43,30,.35);

    border-radius: 50%;

    transform:
        rotateX(70deg)
        rotateZ(15deg);

    box-shadow:
        0 0 60px
        rgba(230,43,30,.12);

    animation:
        orbitRotate 16s linear infinite;
}

.orbit.two {

    inset: 120px;

    transform:
        rotateX(70deg)
        rotateZ(-25deg);

    animation-duration: 12s;

    border-color:
        rgba(255,255,255,.12);
}

.orbit.three {

    inset: 165px;

    transform:
        rotateX(70deg)
        rotateZ(45deg);

    animation-duration: 20s;

    border-color:
        rgba(230,43,30,.22);
}

@keyframes orbitRotate {

    from {
        transform:
            rotateX(70deg)
            rotateZ(0deg);
    }

    to {
        transform:
            rotateX(70deg)
            rotateZ(360deg);
    }
}

.core {

    position: absolute;

    width: 220px;
    height: 220px;

    left: 200px;
    top: 200px;

    border-radius: 45px;

    display: flex;

    align-items: center;

    justify-content: center;

    background:

        linear-gradient(
            145deg,
            rgba(230,43,30,.20),
            rgba(0,0,0,.75)
        );

    border:
        1px solid
        rgba(230,43,30,.45);

    box-shadow:

        0 0 100px
        rgba(230,43,30,.22),

        inset 0 1px 0
        rgba(255,255,255,.12);

    transform:
        rotateX(8deg)
        rotateY(-12deg);

    animation:
        coreFloat 5s ease-in-out infinite;
}

@keyframes coreFloat {

    0%,100% {
        transform:
            translateY(0)
            rotateX(8deg)
            rotateY(-12deg);
    }

    50% {
        transform:
            translateY(-18px)
            rotateX(12deg)
            rotateY(-18deg);
    }
}

.core span {

    font-size: 3.5rem;

    font-weight: 900;

    letter-spacing: -4px;

    color: white;

    text-shadow:
        0 0 30px
        rgba(230,43,30,.45);
}

.core span b {
    color: var(--red);
}

/* ===================================================== */
/* HERO CONTENT */
/* ===================================================== */

.hero-content {

    position: relative;

    z-index: 5;

    width: 58%;

    margin-right: auto;

    padding: 70px;

}

.logo-main {

    width: 86px;
    height: 86px;

    object-fit: cover;

    border-radius: 24px;

    border:
        1px solid
        rgba(255,255,255,.16);

    box-shadow:

        0 25px 50px
        rgba(0,0,0,.5),

        0 0 45px
        rgba(230,43,30,.25);

    animation:
        logoFloat 5s ease-in-out infinite;
}

@keyframes logoFloat {

    0%,100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-8px);
    }
}

.eyebrow {

    margin-top: 28px;

    color: #999;

    font-size: .75rem;

    font-weight: 700;

    letter-spacing: 4px;

    text-transform: uppercase;
}

.hero-title {

    margin-top: 12px;

    font-size:
        clamp(3.2rem, 7vw, 6.8rem);

    line-height: .9;

    letter-spacing: -6px;

    font-weight: 900;

    color: white;

    text-shadow:
        0 20px 60px
        rgba(0,0,0,.55);
}

.hero-title .red {
    color: var(--red);
}

.hero-ar {

    margin-top: 22px;

    font-family:
        "Cairo",
        sans-serif;

    font-size:
        clamp(1.2rem, 2.2vw, 1.7rem);

    color: #f1f1f1;

    font-weight: 700;
}

.hero-description {

    max-width: 570px;

    margin-top: 15px;

    color: #999;

    line-height: 1.8;

    font-size: .95rem;
}

/* ===================================================== */
/* BADGE */
/* ===================================================== */

.live-badge {

    display: inline-flex;

    align-items: center;

    gap: 9px;

    padding: 9px 13px;

    border-radius: 999px;

    background:
        rgba(230,43,30,.09);

    border:
        1px solid
        rgba(230,43,30,.22);

    color: #ff776e;

    font-size: .72rem;

    font-weight: 800;

    letter-spacing: 1px;

    text-transform: uppercase;
}

.live-dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--red);

    box-shadow:
        0 0 15px
        rgba(230,43,30,.9);

    animation:
        pulseDot 1.5s infinite;
}

@keyframes pulseDot {

    0%,100% {
        opacity: 1;
        transform: scale(1);
    }

    50% {
        opacity: .4;
        transform: scale(.7);
    }
}

/* ===================================================== */
/* BUTTON */
/* ===================================================== */

.stButton > button {

    min-height: 52px;

    border-radius: 15px !important;

    border:
        1px solid
        rgba(255,255,255,.10) !important;

    background:
        linear-gradient(
            135deg,
            #f13a2d,
            #9e1710
        ) !important;

    color: white !important;

    font-weight: 800 !important;

    transition:
        transform .25s ease,
        box-shadow .25s ease,
        border .25s ease !important;

    box-shadow:
        0 12px 30px
        rgba(230,43,30,.15);
}

.stButton > button:hover {

    transform:
        translateY(-3px)
        scale(1.01);

    box-shadow:
        0 20px 45px
        rgba(230,43,30,.28) !important;

    border-color:
        rgba(255,255,255,.22) !important;
}

/* ===================================================== */
/* FORM */
/* ===================================================== */

.form-card {

    margin-top: 35px;

    padding: 38px;

    border-radius: 32px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.025)
        );

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 35px 90px
        rgba(0,0,0,.45),

        inset 0 1px 0
        rgba(255,255,255,.05);

    backdrop-filter:
        blur(24px);
}

.section-kicker {

    color: var(--red);

    font-size: .7rem;

    font-weight: 900;

    letter-spacing: 3px;

    text-transform: uppercase;
}

.section-title {

    font-size:
        clamp(1.8rem, 4vw, 2.8rem);

    font-weight: 900;

    letter-spacing: -2px;

    margin-top: 7px;
}

/* ===================================================== */
/* INPUTS */
/* ===================================================== */

div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {

    background:
        rgba(0,0,0,.55) !important;

    color: white !important;

    border:
        1px solid
        rgba(255,255,255,.12) !important;

    border-radius: 14px !important;

    min-height: 48px !important;
}

label {

    color: #d0d0d0 !important;

    font-weight: 600 !important;
}

/* ===================================================== */
/* COUNTDOWN */
/* ===================================================== */

.countdown {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 12px;

    margin-top: 30px;
}

.time-box {

    position: relative;

    overflow: hidden;

    padding: 20px 10px;

    text-align: center;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.018)
        );

    border:
        1px solid
        rgba(255,255,255,.08);

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,.05);
}

.time-box::after {

    content: "";

    position: absolute;

    width: 80px;
    height: 80px;

    right: -45px;
    top: -45px;

    border-radius: 50%;

    background:
        rgba(230,43,30,.12);

    filter: blur(20px);
}

.time-number {

    font-size:
        clamp(1.5rem, 4vw, 2.5rem);

    font-weight: 900;

    letter-spacing: -2px;
}

.time-label {

    color: #777;

    margin-top: 4px;

    font-size: .65rem;

    text-transform: uppercase;

    letter-spacing: 2px;
}

/* ===================================================== */
/* ADMIN */
/* ===================================================== */

.admin-shell {

    padding: 30px;

    border-radius: 32px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.02)
        );

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 40px 100px
        rgba(0,0,0,.55);

    backdrop-filter:
        blur(25px);
}

.stat-card {

    min-height: 145px;

    padding: 25px;

    border-radius: 22px;

    background:
        rgba(255,255,255,.035);

    border:
        1px solid
        rgba(255,255,255,.08);

    transition:
        transform .25s ease,
        border .25s ease;
}

.stat-card:hover {

    transform:
        translateY(-5px);

    border-color:
        rgba(230,43,30,.3);
}

.stat-label {

    color: #777;

    font-size: .68rem;

    text-transform: uppercase;

    letter-spacing: 2px;
}

.stat-number {

    margin-top: 8px;

    font-size: 2.4rem;

    font-weight: 900;
}

.stat-red {
    color: var(--red);
}

/* ===================================================== */
/* PARTICIPANT CARD */
/* ===================================================== */

.participant {

    padding: 18px;

    margin-bottom: 12px;

    border-radius: 22px;

    background:
        rgba(255,255,255,.035);

    border:
        1px solid
        rgba(255,255,255,.075);

    transition:
        transform .25s ease,
        border .25s ease,
        background .25s ease;
}

.participant:hover {

    transform:
        translateX(5px);

    border-color:
        rgba(230,43,30,.3);

    background:
        rgba(255,255,255,.05);
}

.participant-name {

    font-size: 1rem;

    font-weight: 850;
}

.participant-meta {

    color: #888;

    font-size: .75rem;

    margin-top: 5px;
}

.wa {

    display: inline-flex;

    padding: 9px 13px;

    border-radius: 11px;

    color: #4de49a !important;

    text-decoration: none !important;

    background:
        rgba(37,211,102,.08);

    border:
        1px solid
        rgba(37,211,102,.15);

    font-size: .72rem;

    font-weight: 800;
}

/* ===================================================== */
/* ADMIN LOGIN */
/* ===================================================== */

.login-card {

    max-width: 560px;

    margin:
        70px auto;

    padding: 45px;

    border-radius: 32px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.02)
        );

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 50px 120px
        rgba(0,0,0,.65);
}

/* ===================================================== */
/* MOBILE */
/* ===================================================== */

@media (max-width: 900px) {

    .block-container {

        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero-shell {

        min-height: 650px;

        border-radius: 30px;
    }

    .hero-content {

        width: 100%;

        padding: 35px 25px;

        text-align: center;
    }

    .hero-description {

        margin-left: auto;
        margin-right: auto;
    }

    .orbit-scene {

        width: 420px;
        height: 420px;

        right: 50%;

        top: 310px;

        transform:
            translateX(50%)
            scale(.75);

        opacity: .42;
    }

    .core {

        left: 100px;
        top: 100px;
    }

    .form-card {

        padding: 22px 16px;

        border-radius: 24px;
    }

}

@media (max-width: 600px) {

    .hero-title {

        font-size: 3.3rem;

        letter-spacing: -4px;
    }

    .countdown {

        gap: 6px;
    }

    .time-box {

        padding: 15px 5px;

        border-radius: 14px;
    }

    .time-number {

        font-size: 1.3rem;
    }

    .time-label {

        font-size: .55rem;

        letter-spacing: 1px;
    }

    .login-card {

        margin: 25px auto;

        padding: 25px 18px;
    }

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOGO
# =========================================================

logo_b64 = get_logo_base64()


# =========================================================
# COUNTDOWN
# =========================================================

def render_countdown():

    deadline = get_deadline()

    remaining = max(
        0,
        int(
            (
                deadline -
                datetime.now()
            ).total_seconds()
        )
    )

    days = remaining // 86400

    hours = (
        remaining % 86400
    ) // 3600

    minutes = (
        remaining % 3600
    ) // 60

    seconds = remaining % 60

    st.markdown(f"""
    <div class="countdown">

        <div class="time-box">
            <div class="time-number">
                {days:02d}
            </div>
            <div class="time-label">
                Jours
            </div>
        </div>

        <div class="time-box">
            <div class="time-number">
                {hours:02d}
            </div>
            <div class="time-label">
                Heures
            </div>
        </div>

        <div class="time-box">
            <div class="time-number">
                {minutes:02d}
            </div>
            <div class="time-label">
                Minutes
            </div>
        </div>

        <div class="time-box">
            <div class="time-number">
                {seconds:02d}
            </div>
            <div class="time-label">
                Secondes
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)


# =========================================================
# HOME / REGISTRATION
# =========================================================

def home_page():

    logo_html = ""

    if logo_b64:

        logo_html = f"""
        <img
            src="data:image/jpeg;base64,{logo_b64}"
            class="logo-main"
        >
        """

    st.markdown(f"""
    <section class="hero-shell">

        <div class="orbit-scene">

            <div class="orbit"></div>
            <div class="orbit two"></div>
            <div class="orbit three"></div>

            <div class="core">
                <span>
                    TED<b>x</b>
                </span>
            </div>

        </div>

        <div class="hero-content">

            {logo_html}

            <div class="eyebrow">
                Ideas Worth Spreading
            </div>

            <div class="hero-title">
                TED<span class="red">x</span><br>
                B'DARIJA
            </div>

            <div class="hero-ar">
                أكبر الأفكار كتبدأ من فكرة صغيرة.
            </div>

            <div class="hero-description">
                Une scène pour les idées, les histoires
                et les personnes qui veulent créer un impact.
                Rejoignez TEDx B'DARIJA et faites partie
                de cette expérience.
            </div>

            <div style="margin-top:25px;">
                <span class="live-badge">
                    <span class="live-dot"></span>
                    Inscriptions ouvertes
                </span>
            </div>

        </div>

    </section>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="height:35px;"></div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # FORM
    # =====================================================

    st.markdown("""
    <div class="form-card">

        <div class="section-kicker">
            Registration
        </div>

        <div class="section-title">
            Faites partie de l'expérience.
        </div>

        <div style="
            color:#888;
            margin-top:8px;
            line-height:1.7;
        ">
            Complétez vos informations pour participer
            à TEDx B'DARIJA.
        </div>

    </div>
    """, unsafe_allow_html=True)

    render_countdown()

    with st.form(
        "registration_form",
        clear_on_submit=False
    ):

        st.markdown(
            '<div style="height:10px;"></div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Nom et Prénom",
                placeholder="Votre nom complet"
            )

        with col2:

            phone = st.text_input(
                "Numéro WhatsApp",
                placeholder="06 XX XX XX XX"
            )

        col3, col4 = st.columns(2)

        with col3:

            major = st.text_input(
                "Filière",
                placeholder="Ex: Informatique"
            )

        with col4:

            year = st.selectbox(
                "Année",
                [
                    "Choisir...",
                    "1ère Année",
                    "2ème Année",
                    "3ème Année",
                    "4ème Année",
                    "5ème Année"
                ]
            )

        photo = st.file_uploader(
            "Photo — visage clair",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]
        )

        st.caption(
            "Formats acceptés : JPG, JPEG, PNG, WEBP • "
            "Maximum 3 MB"
        )

        submitted = st.form_submit_button(
            "S'INSCRIRE  →"
        )

        if submitted:

            normalized = normalize_phone(
                phone
            )

            if not name.strip():

                st.error(
                    "Veuillez entrer votre nom."
                )

            elif not normalized:

                st.error(
                    "Veuillez entrer un numéro "
                    "WhatsApp marocain valide."
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

            elif photo.size > MAX_PHOTO_SIZE:

                st.error(
                    "La photo dépasse 3 MB."
                )

            elif datetime.now() >= get_deadline():

                st.error(
                    "Les inscriptions sont terminées."
                )

            else:

                try:

                    extension = safe_filename(
                        photo.name
                    )

                    filename = (
                        datetime.now().strftime(
                            "%Y%m%d_%H%M%S_%f"
                        )
                        + extension
                    )

                    photo_path = os.path.join(
                        UPLOAD_DIR,
                        filename
                    )

                    with open(
                        photo_path,
                        "wb"
                    ) as file:

                        file.write(
                            photo.getbuffer()
                        )

                    add_registration(
                        name.strip(),
                        normalized,
                        major.strip(),
                        year,
                        photo_path
                    )

                    st.success(
                        "✓ Votre inscription a été "
                        "enregistrée avec succès."
                    )

                    st.session_state.success = True

                    time.sleep(.5)

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Une erreur est survenue : {error}"
                    )

    if st.session_state.success:

        st.markdown("""
        <div style="
            margin-top:25px;
            padding:22px;
            border-radius:20px;
            background:rgba(40,220,140,.06);
            border:1px solid rgba(40,220,140,.18);
            text-align:center;
        ">

            <div style="
                font-size:1.3rem;
                font-weight:900;
                color:#55e6a0;
            ">
                Inscription confirmée ✓
            </div>

            <div style="
                color:#888;
                margin-top:7px;
            ">
                Merci d'avoir rejoint TEDx B'DARIJA.
            </div>

        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div style="height:35px;"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="text-align:center;">',
        unsafe_allow_html=True
    )

    if st.button(
        "🔒 Accès Administration",
        key="admin_access"
    ):

        st.session_state.page = "login"
        st.rerun()

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="
        text-align:center;
        margin-top:35px;
        color:#444;
        font-size:.7rem;
        letter-spacing:2px;
    ">
        TEDx B'DARIJA • IDEAS WORTH SPREADING
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# LOGIN
# =========================================================

def login_page():

    logo_html = ""

    if logo_b64:

        logo_html = f"""
        <img
            src="data:image/jpeg;base64,{logo_b64}"
            style="
                width:80px;
                height:80px;
                object-fit:cover;
                border-radius:22px;
                margin-bottom:20px;
            "
        >
        """

    st.markdown(
        f"""
        <div class="login-card">

            <div style="text-align:center;">

                {logo_html}

                <div style="
                    color:#e62b1e;
                    font-size:.7rem;
                    font-weight:900;
                    letter-spacing:3px;
                    text-transform:uppercase;
                ">
                    Restricted Area
                </div>

                <div style="
                    font-size:2rem;
                    font-weight:900;
                    margin-top:8px;
                ">
                    Admin Access
                </div>

                <div style="
                    color:#777;
                    margin-top:8px;
                    font-size:.85rem;
                ">
                    TEDx B'DARIJA
                </div>

            </div>

        """,
        unsafe_allow_html=True
    )

    with st.form(
        "admin_login"
    ):

        email = st.text_input(
            "Email"
        )

        password = st.text_input(
            "Mot de passe",
            type="password"
        )

        submitted = st.form_submit_button(
            "SE CONNECTER  →"
        )

        if submitted:

            if (
                email.strip().lower()
                == ADMIN_EMAIL.lower()
                and
                password
                == ADMIN_PASSWORD
            ):

                st.session_state.admin_logged = True
                st.session_state.login_error = False
                st.session_state.page = "admin"

                st.rerun()

            else:

                st.session_state.login_error = True

    if st.session_state.login_error:

        st.error(
            "Email ou mot de passe incorrect."
        )

    if st.button(
        "← Retour"
    ):

        st.session_state.login_error = False
        st.session_state.page = "home"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# ADMIN CARD
# =========================================================

def render_participant(row):

    photo_path = row["photo_path"]

    left, center, right = st.columns(
        [0.75, 3.1, 1.25]
    )

    with left:

        if (
            photo_path
            and
            os.path.exists(photo_path)
        ):

            st.image(
                photo_path,
                width=65
            )

        else:

            initials = (
                row["name"][:1]
                if row["name"]
                else "?"
            )

            st.markdown(
                f"""
                <div style="
                    width:65px;
                    height:65px;
                    border-radius:20px;
                    background:
                        linear-gradient(
                            145deg,
                            #181818,
                            #080808
                        );
                    border:
                        1px solid
                        rgba(230,43,30,.4);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:#e62b1e;
                    font-size:1.5rem;
                    font-weight:900;
                ">
                    {html.escape(initials.upper())}
                </div>
                """,
                unsafe_allow_html=True
            )

    with center:

        st.markdown(
            f"""
            <div class="participant-name">
                {html.escape(row["name"])}
            </div>

            <div class="participant-meta">
                {html.escape(row["major"])}
                &nbsp; • &nbsp;
                {html.escape(row["year"])}
            </div>

            <div class="participant-meta">
                📱 {html.escape(row["phone"])}
            </div>

            <div style="
                color:#555;
                font-size:.65rem;
                margin-top:8px;
            ">
                Inscrit le
                {format_date(row["created_at"])}
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:

        number = row["phone"].replace(
            "+",
            ""
        )

        whatsapp_url = (
            f"https://wa.me/{number}"
        )

        st.markdown(
            f"""
            <a
                href="{whatsapp_url}"
                target="_blank"
                class="wa"
            >
                🟢 WhatsApp
            </a>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="height:8px;"></div>',
            unsafe_allow_html=True
        )

        if st.button(
            "Supprimer",
            key=f"delete_{row['id']}"
        ):

            delete_registration(
                row["id"]
            )

            st.rerun()


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard():

    if not st.session_state.admin_logged:

        st.session_state.page = "login"

        st.rerun()

        return

    rows = get_registrations()

    total = len(rows)

    majors = set(
        row["major"].strip().lower()
        for row in rows
        if row["major"]
    )

    deadline = get_deadline()

    st.markdown(
        '<div class="admin-shell">',
        unsafe_allow_html=True
    )

    # =====================================================
    # TOP BAR
    # =====================================================

    top1, top2 = st.columns(
        [4, 1]
    )

    with top1:

        st.markdown("""
        <div>

            <div style="
                color:#e62b1e;
                font-size:.7rem;
                font-weight:900;
                letter-spacing:3px;
                text-transform:uppercase;
            ">
                TEDx B'DARIJA
            </div>

            <div style="
                font-size:2.3rem;
                font-weight:900;
                letter-spacing:-2px;
                margin-top:5px;
            ">
                Command Center
            </div>

            <div style="
                color:#777;
                margin-top:5px;
                font-size:.8rem;
            ">
                Gestion des participants et inscriptions
            </div>

        </div>
        """, unsafe_allow_html=True)

    with top2:

        if st.button(
            "🚪 Déconnexion",
            key="logout"
        ):

            st.session_state.admin_logged = False
            st.session_state.page = "home"

            st.rerun()

    st.markdown(
        '<div style="height:25px;"></div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # STATS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Participants
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

        latest = (
            format_date(
                rows[0]["created_at"]
            )
            if rows
            else "—"
        )

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Dernière inscription
                </div>

                <div style="
                    margin-top:14px;
                    font-size:.9rem;
                    font-weight:800;
                ">
                    {latest}
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
                    margin-top:14px;
                    color:#ff655d;
                    font-size:.9rem;
                    font-weight:800;
                ">
                    {deadline.strftime("%d/%m/%Y")}
                </div>

                <div style="
                    color:#666;
                    font-size:.7rem;
                    margin-top:3px;
                ">
                    {deadline.strftime("%H:%M")}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # SETTINGS
    # =====================================================

    st.markdown(
        '<div style="height:25px;"></div>',
        unsafe_allow_html=True
    )

    with st.expander(
        "⚙️ Paramètres des inscriptions"
    ):

        d1, d2 = st.columns(2)

        with d1:

            new_date = st.date_input(
                "Date limite",
                value=deadline.date()
            )

        with d2:

            new_time = st.time_input(
                "Heure limite",
                value=deadline.time().replace(
                    second=0,
                    microsecond=0
                )
            )

        if st.button(
            "Enregistrer la deadline",
            key="save_deadline"
        ):

            new_deadline = datetime.combine(
                new_date,
                new_time
            )

            if new_deadline <= datetime.now():

                st.error(
                    "La deadline doit être dans le futur."
                )

            else:

                save_setting(
                    "deadline",
                    new_deadline.isoformat(
                        timespec="minutes"
                    )
                )

                st.success(
                    "Deadline mise à jour."
                )

                st.rerun()

    # =====================================================
    # ACTIONS
    # =====================================================

    st.markdown(
        '<div style="height:15px;"></div>',
        unsafe_allow_html=True
    )

    a1, a2, a3 = st.columns(3)

    with a1:

        if st.button(
            "🔄 Actualiser",
            key="refresh"
        ):

            st.rerun()

    with a2:

        st.download_button(
            "📥 Exporter CSV",
            data=create_csv(rows),
            file_name=(
                "TEDx_BDARija_"
                + datetime.now().strftime(
                    "%Y-%m-%d"
                )
                + ".csv"
            ),
            mime="text/csv",
            key="csv"
        )

    with a3:

        if st.button(
            "🗑️ Vider la base",
            key="clear"
        ):

            st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:

        st.warning(
            "Toutes les inscriptions seront supprimées."
        )

        y, n = st.columns(2)

        with y:

            if st.button(
                "Oui, supprimer tout",
                key="confirm"
            ):

                clear_registrations()

                st.session_state.confirm_clear = False

                st.success(
                    "Base nettoyée."
                )

                st.rerun()

        with n:

            if st.button(
                "Annuler",
                key="cancel"
            ):

                st.session_state.confirm_clear = False

                st.rerun()

    # =====================================================
    # SEARCH
    # =====================================================

    st.markdown(
        '<div style="height:20px;"></div>',
        unsafe_allow_html=True
    )

    search = st.text_input(
        "🔎 Recherche participant",
        placeholder="Nom • WhatsApp • filière • année..."
    )

    filtered = []

    query = search.strip().lower()

    for row in rows:

        if not query:

            filtered.append(row)

            continue

        searchable = " ".join([
            str(row["name"] or ""),
            str(row["phone"] or ""),
            str(row["major"] or ""),
            str(row["year"] or "")
        ]).lower()

        if query in searchable:

            filtered.append(row)

    # =====================================================
    # PARTICIPANTS
    # =====================================================

    st.markdown(
        f"""
        <div style="
            margin-top:25px;
            margin-bottom:15px;
            display:flex;
            align-items:center;
            justify-content:space-between;
        ">

            <div style="
                font-size:1.4rem;
                font-weight:900;
            ">
                Participants
            </div>

            <div style="
                color:#e62b1e;
                font-weight:900;
                font-size:.9rem;
            ">
                {len(filtered)} résultat(s)
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered:

        st.info(
            "Aucun participant trouvé."
        )

    for row in filtered:

        st.markdown(
            '<div class="participant">',
            unsafe_allow_html=True
        )

        render_participant(row)

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# ROUTER
# =========================================================

if st.session_state.page == "home":

    home_page()

elif st.session_state.page == "login":

    login_page()

elif st.session_state.page == "admin":

    admin_dashboard()

else:

    st.session_state.page = "home"

    st.rerun()
