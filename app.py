import streamlit as st
import sqlite3
import os
import re
import csv
import io
import html
import base64
from datetime import datetime, timedelta

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

DB_PATH = os.path.join(DB_DIR, "tedx.db")

# EXACT LOGO NAME
LOGO_PATH = os.path.join(
    BASE_DIR,
    "tedx-bdarija-logo.png.jpg"
)

ADMIN_EMAIL = "outhmane@farah.love"
ADMIN_PASSWORD = "oufa@2026@!"

os.makedirs(DB_DIR, exist_ok=True)
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

    existing = conn.execute(
        "SELECT value FROM settings WHERE key = 'deadline'"
    ).fetchone()

    if not existing:

        default_deadline = (
            datetime.now() + timedelta(days=30)
        ).isoformat(timespec="minutes")

        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            """,
            ("deadline", default_deadline)
        )

    conn.commit()
    conn.close()


def get_deadline():

    conn = get_connection()

    row = conn.execute(
        """
        SELECT value
        FROM settings
        WHERE key = 'deadline'
        """
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

    conn.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (
            "deadline",
            value.isoformat(timespec="minutes")
        )
    )

    conn.commit()
    conn.close()


def add_registration(
    name,
    phone,
    major,
    year,
    photo_path
):

    conn = get_connection()

    conn.execute(
        """
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
        """,
        (
            name,
            phone,
            major,
            year,
            photo_path,
            datetime.now().isoformat(
                timespec="seconds"
            )
        )
    )

    conn.commit()
    conn.close()


def get_registrations():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM registrations
        ORDER BY datetime(created_at) DESC
        """
    ).fetchall()

    conn.close()

    return rows


def delete_registration(registration_id):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT photo_path
        FROM registrations
        WHERE id = ?
        """,
        (registration_id,)
    ).fetchone()

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

    conn.execute(
        """
        DELETE FROM registrations
        WHERE id = ?
        """,
        (registration_id,)
    )

    conn.commit()
    conn.close()


def delete_all_registrations():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT photo_path
        FROM registrations
        """
    ).fetchall()

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

    conn.execute(
        "DELETE FROM registrations"
    )

    conn.commit()
    conn.close()


# =========================================================
# HELPERS
# =========================================================

def normalize_moroccan_phone(value):

    raw = re.sub(
        r"[\s\-]",
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


def get_base64_image(path):

    try:

        with open(
            path,
            "rb"
        ) as f:

            return base64.b64encode(
                f.read()
            ).decode()

    except Exception:

        return None


def safe(value):

    return html.escape(
        str(value or "")
    )


# =========================================================
# AUTO REFRESH
# =========================================================

if st_autorefresh:

    st_autorefresh(
        interval=1000,
        limit=None,
        key="tedx_clock"
    )


# =========================================================
# PREMIUM CSS
# =========================================================

st.markdown(
"""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Cairo:wght@400;500;600;700;800;900&display=swap'
);

:root {

    --red: #e62b1e;
    --red2: #ff4a3d;

    --bg: #050505;
    --panel: rgba(17,17,18,.72);

    --white: #ffffff;
    --muted: #777;
    --line: rgba(255,255,255,.09);

    --shadow:
        0 30px 100px rgba(0,0,0,.65);

}

* {
    box-sizing: border-box;
}

html,
body,
.stApp {

    font-family:
        "Inter",
        sans-serif !important;

    background: #050505 !important;

    color: white !important;

}

.stApp {

    min-height: 100vh;

    background:

        radial-gradient(
            circle at 8% 10%,
            rgba(230,43,30,.18),
            transparent 25%
        ),

        radial-gradient(
            circle at 90% 20%,
            rgba(230,43,30,.10),
            transparent 25%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(230,43,30,.08),
            transparent 35%
        ),

        #050505 !important;

}


/* =====================================================
   ANIMATED GRID
===================================================== */

.stApp::before {

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    opacity: .22;

    background-image:

        linear-gradient(
            rgba(255,255,255,.025) 1px,
            transparent 1px
        ),

        linear-gradient(
            90deg,
            rgba(255,255,255,.025) 1px,
            transparent 1px
        );

    background-size:
        55px 55px;

    mask-image:
        radial-gradient(
            circle at center,
            black,
            transparent 78%
        );

    animation:
        gridMove 18s linear infinite;

    z-index: 0;

}

@keyframes gridMove {

    from {
        transform: translate3d(0,0,0);
    }

    to {
        transform: translate3d(55px,55px,0);
    }

}


/* =====================================================
   RED AMBIENT ORB
===================================================== */

.stApp::after {

    content: "";

    position: fixed;

    width: 420px;
    height: 420px;

    border-radius: 50%;

    left: -180px;
    top: 45%;

    background:
        radial-gradient(
            circle,
            rgba(230,43,30,.16),
            transparent 68%
        );

    filter: blur(10px);

    pointer-events: none;

    animation:
        orbFloat 9s ease-in-out infinite;

}

@keyframes orbFloat {

    0%,100% {
        transform:
            translate3d(0,0,0)
            scale(1);
    }

    50% {
        transform:
            translate3d(80px,-40px,0)
            scale(1.12);
    }

}


/* =====================================================
   STREAMLIT
===================================================== */

.block-container {

    position: relative;

    z-index: 2;

    max-width: 1380px !important;

    padding-top: 2rem !important;

    padding-bottom: 5rem !important;

}

header[data-testid="stHeader"] {

    background:
        rgba(0,0,0,.15) !important;

    backdrop-filter:
        blur(15px);

}

footer {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    display: none;
}


/* =====================================================
   MAIN 3D GLASS
===================================================== */

.premium-shell {

    position: relative;

    padding: 42px;

    border-radius: 36px;

    background:

        linear-gradient(
            145deg,
            rgba(30,30,31,.82),
            rgba(7,7,8,.74)
        );

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:

        0 40px 120px
        rgba(0,0,0,.68),

        inset 0 1px 0
        rgba(255,255,255,.07);

    backdrop-filter:
        blur(28px);

    overflow: hidden;

    transform:
        perspective(1500px)
        translateZ(0);

}

.premium-shell::before {

    content: "";

    position: absolute;

    inset: -2px;

    border-radius: inherit;

    background:

        linear-gradient(
            115deg,
            transparent 20%,
            rgba(230,43,30,.14),
            transparent 45%
        );

    pointer-events: none;

}

.premium-shell::after {

    content: "";

    position: absolute;

    width: 260px;
    height: 260px;

    right: -120px;
    top: -120px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(230,43,30,.22),
            transparent 70%
        );

    filter: blur(8px);

    pointer-events: none;

}


/* =====================================================
   HERO
===================================================== */

.hero-wrap {

    position: relative;

    text-align: center;

    padding:
        25px 10px
        35px;

}

.hero-logo {

    position: relative;

    width: 122px;
    height: 122px;

    object-fit: cover;

    border-radius: 50%;

    border:
        2px solid
        rgba(230,43,30,.75);

    box-shadow:

        0 0 0 8px
        rgba(230,43,30,.035),

        0 0 70px
        rgba(230,43,30,.28),

        0 25px 70px
        rgba(0,0,0,.65);

    animation:
        logoFloat 4s ease-in-out infinite;

}

@keyframes logoFloat {

    0%,100% {
        transform:
            translateY(0)
            rotateX(0deg);
    }

    50% {
        transform:
            translateY(-8px)
            rotateX(5deg);
    }

}

.hero-title {

    margin-top: 28px;

    font-size:
        clamp(
            2.5rem,
            6vw,
            5rem
        );

    line-height: .95;

    font-weight: 900;

    letter-spacing: -4px;

    text-shadow:
        0 15px 45px
        rgba(0,0,0,.6);

}

.hero-title span {

    color: var(--red);

    text-shadow:

        0 0 20px
        rgba(230,43,30,.45),

        0 0 60px
        rgba(230,43,30,.2);

}

.hero-ar {

    margin-top: 18px;

    font-family: "Cairo", sans-serif;

    color: #fff;

    font-size:
        clamp(
            1.25rem,
            3vw,
            2rem
        );

    font-weight: 800;

}

.hero-small {

    margin-top: 8px;

    color: #666;

    font-size: .68rem;

    letter-spacing: 5px;

    text-transform: uppercase;

}


/* =====================================================
   3D FLOATING CARDS
===================================================== */

.floating-stage {

    position: relative;

    height: 115px;

    margin:
        5px auto
        25px;

    max-width: 720px;

    perspective: 1000px;

}

.float-card {

    position: absolute;

    padding:
        13px 18px;

    border-radius: 15px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 25px 50px
        rgba(0,0,0,.4);

    backdrop-filter:
        blur(15px);

    color: #ddd;

    font-size: .75rem;

    font-weight: 700;

    letter-spacing: .5px;

}

.float-one {

    left: 7%;

    top: 25px;

    transform:
        rotateY(20deg)
        rotateZ(-5deg);

    animation:
        floatOne 5s ease-in-out infinite;

}

.float-two {

    right: 7%;

    top: 8px;

    transform:
        rotateY(-20deg)
        rotateZ(5deg);

    animation:
        floatTwo 6s ease-in-out infinite;

}

.float-three {

    left: 39%;

    top: 65px;

    color: var(--red);

    animation:
        floatThree 4s ease-in-out infinite;

}

@keyframes floatOne {

    0%,100% {
        transform:
            translateY(0)
            rotateY(20deg)
            rotateZ(-5deg);
    }

    50% {
        transform:
            translateY(-13px)
            rotateY(25deg)
            rotateZ(-3deg);
    }

}

@keyframes floatTwo {

    0%,100% {
        transform:
            translateY(0)
            rotateY(-20deg)
            rotateZ(5deg);
    }

    50% {
        transform:
            translateY(15px)
            rotateY(-25deg)
            rotateZ(3deg);
    }

}

@keyframes floatThree {

    0%,100% {
        transform:
            translateY(0)
            scale(1);
    }

    50% {
        transform:
            translateY(-8px)
            scale(1.04);
    }

}


/* =====================================================
   SECTION
===================================================== */

.section-heading {

    display: flex;

    align-items: center;

    gap: 12px;

    margin:
        15px 0
        20px;

    font-size: 1.4rem;

    font-weight: 900;

}

.section-heading::before {

    content: "";

    width: 4px;
    height: 27px;

    border-radius: 10px;

    background:
        linear-gradient(
            #ff4a3d,
            #b8170f
        );

    box-shadow:
        0 0 20px
        rgba(230,43,30,.35);

}


/* =====================================================
   COUNTDOWN
===================================================== */

.countdown-label {

    text-align: center;

    color: #666;

    font-size: .66rem;

    letter-spacing: 4px;

    text-transform: uppercase;

    margin-bottom: 10px;

}

.timer-grid {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 12px;

    margin:
        12px 0
        32px;

}

.timer-box {

    position: relative;

    overflow: hidden;

    padding:
        20px 10px;

    text-align: center;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(0,0,0,.35)
        );

    border:
        1px solid
        rgba(230,43,30,.22);

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,.04),

        0 20px 45px
        rgba(0,0,0,.3);

    transition:
        transform .25s ease,
        border .25s ease;

}

.timer-box:hover {

    transform:
        translateY(-5px)
        scale(1.015);

    border-color:
        rgba(230,43,30,.5);

}

.timer-number {

    font-size:
        clamp(
            1.5rem,
            4vw,
            2.7rem
        );

    font-weight: 900;

    letter-spacing: -1px;

}

.timer-label {

    margin-top: 3px;

    color: #666;

    font-size: .61rem;

    text-transform: uppercase;

    letter-spacing: 2px;

}


/* =====================================================
   INPUTS
===================================================== */

div[data-testid="stTextInput"],
div[data-testid="stSelectbox"],
div[data-testid="stFileUploader"] {

    margin-bottom: 8px;

}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {

    background:
        rgba(0,0,0,.45) !important;

    color: #fff !important;

    border:
        1px solid
        rgba(255,255,255,.10) !important;

    border-radius: 14px !important;

    min-height: 48px;

    transition:
        .2s ease;

}

div[data-testid="stTextInput"] input:focus {

    border-color:
        rgba(230,43,30,.7) !important;

    box-shadow:
        0 0 0 3px
        rgba(230,43,30,.08) !important;

}

label {

    color: #bbb !important;

    font-weight: 600 !important;

}


/* =====================================================
   BUTTON
===================================================== */

.stButton > button,
.stFormSubmitButton > button {

    width: 100%;

    min-height: 50px;

    border-radius: 14px;

    border:
        1px solid
        rgba(255,255,255,.10);

    background:

        linear-gradient(
            135deg,
            #ed3427,
            #a91912
        );

    color: white;

    font-weight: 800;

    box-shadow:
        0 15px 35px
        rgba(230,43,30,.18);

    transition:
        transform .2s ease,
        box-shadow .2s ease;

}

.stButton > button:hover,
.stFormSubmitButton > button:hover {

    transform:
        translateY(-3px);

    box-shadow:
        0 20px 45px
        rgba(230,43,30,.32);

}


/* =====================================================
   ADMIN STATS
===================================================== */

.stat-card {

    position: relative;

    overflow: hidden;

    min-height: 145px;

    padding: 24px;

    border-radius: 22px;

    background:

        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(255,255,255,.018)
        );

    border:
        1px solid
        rgba(255,255,255,.08);

    box-shadow:
        0 25px 60px
        rgba(0,0,0,.35);

    transition:
        transform .25s ease,
        border .25s ease;

}

.stat-card:hover {

    transform:
        translateY(-6px);

    border-color:
        rgba(230,43,30,.28);

}

.stat-card::after {

    content: "";

    position: absolute;

    width: 100px;
    height: 100px;

    right: -45px;
    bottom: -45px;

    border-radius: 50%;

    background:
        rgba(230,43,30,.12);

    filter: blur(8px);

}

.stat-label {

    color: #666;

    font-size: .64rem;

    text-transform: uppercase;

    letter-spacing: 2px;

}

.stat-number {

    margin-top: 10px;

    font-size: 2.5rem;

    font-weight: 900;

}

.stat-red {

    color: #ff4d40;

    text-shadow:
        0 0 30px
        rgba(230,43,30,.22);

}


/* =====================================================
   ADMIN HEADER
===================================================== */

.admin-title {

    font-size:
        clamp(
            1.7rem,
            4vw,
            2.5rem
        );

    font-weight: 900;

    letter-spacing: -1.5px;

}

.admin-online {

    display: inline-flex;

    align-items: center;

    gap: 7px;

    margin-top: 7px;

    color: #55e69e;

    font-size: .72rem;

}

.online-dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #55e69e;

    box-shadow:
        0 0 12px
        #55e69e;

    animation:
        onlinePulse 1.5s infinite;

}

@keyframes onlinePulse {

    0%,100% {
        opacity: 1;
        transform: scale(1);
    }

    50% {
        opacity: .45;
        transform: scale(.7);
    }

}


/* =====================================================
   PARTICIPANT
===================================================== */

.participant-card {

    padding: 17px;

    margin:
        8px 0;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.045),
            rgba(255,255,255,.018)
        );

    border:
        1px solid
        rgba(255,255,255,.065);

    transition:
        .25s ease;

}

.participant-card:hover {

    transform:
        translateX(4px);

    border-color:
        rgba(230,43,30,.24);

    box-shadow:
        0 20px 50px
        rgba(0,0,0,.3);

}

.name-text {

    font-size: 1rem;

    font-weight: 800;

}

.small-text {

    color: #777;

    font-size: .72rem;

    margin-top: 4px;

}

.wa-button {

    display: inline-flex;

    align-items: center;

    justify-content: center;

    gap: 7px;

    width: 100%;

    padding:
        10px 13px;

    border-radius: 11px;

    color: #52e89c;

    background:
        rgba(37,211,102,.08);

    border:
        1px solid
        rgba(37,211,102,.17);

    text-decoration: none;

    font-size: .73rem;

    font-weight: 800;

    transition:
        .2s ease;

}

.wa-button:hover {

    background:
        rgba(37,211,102,.16);

    transform:
        translateY(-2px);

}


/* =====================================================
   ADMIN BUTTON
===================================================== */

.admin-access button {

    background:
        rgba(255,255,255,.025) !important;

    border:
        1px solid
        rgba(255,255,255,.06) !important;

    color: #666 !important;

    box-shadow: none !important;

    min-height: 42px;

    font-size: .75rem;

}

.admin-access button:hover {

    color: #aaa !important;

    border-color:
        rgba(255,255,255,.12) !important;

}


/* =====================================================
   MOBILE
===================================================== */

@media(max-width: 700px) {

    .block-container {

        padding:
            .8rem !important;

    }

    .premium-shell {

        padding:
            22px 15px;

        border-radius: 25px;

    }

    .hero-title {

        font-size:
            2.55rem;

        letter-spacing:
            -2.5px;

    }

    .hero-logo {

        width: 95px;
        height: 95px;

    }

    .floating-stage {

        height: 85px;

    }

    .float-card {

        font-size: .58rem;

        padding:
            9px 11px;

    }

    .timer-grid {

        gap: 6px;

    }

    .timer-box {

        padding:
            13px 4px;

        border-radius: 15px;

    }

    .timer-number {

        font-size:
            1.3rem;

    }

    .stat-card {

        min-height: 110px;

        padding: 17px;

    }

    .stat-number {

        font-size: 2rem;

    }

}

</style>
""",
unsafe_allow_html=True
)


# =========================================================
# INIT
# =========================================================

init_database()


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
# LOGO
# =========================================================

def render_logo():

    if os.path.exists(LOGO_PATH):

        encoded = get_base64_image(
            LOGO_PATH
        )

        if encoded:

            return f"""
            <img
                src="data:image/jpeg;base64,{encoded}"
                class="hero-logo"
            >
            """

    return """
    <div
        class="hero-logo"
        style="
            display:flex;
            align-items:center;
            justify-content:center;
            background:#111;
            color:#e62b1e;
            font-size:22px;
            font-weight:900;
        "
    >
        TEDx
    </div>
    """


# =========================================================
# COUNTDOWN
# =========================================================

def render_countdown():

    deadline = get_deadline()

    now = datetime.now()

    seconds = max(
        0,
        int(
            (
                deadline - now
            ).total_seconds()
        )
    )

    days = seconds // 86400

    hours = (
        seconds % 86400
    ) // 3600

    minutes = (
        seconds % 3600
    ) // 60

    secs = seconds % 60

    st.markdown(
        """
        <div class="countdown-label">
            FIN DES INSCRIPTIONS DANS
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="timer-grid">

            <div class="timer-box">
                <div class="timer-number">
                    {days:02d}
                </div>
                <div class="timer-label">
                    Jours
                </div>
            </div>

            <div class="timer-box">
                <div class="timer-number">
                    {hours:02d}
                </div>
                <div class="timer-label">
                    Heures
                </div>
            </div>

            <div class="timer-box">
                <div class="timer-number">
                    {minutes:02d}
                </div>
                <div class="timer-label">
                    Minutes
                </div>
            </div>

            <div class="timer-box">
                <div class="timer-number">
                    {secs:02d}
                </div>
                <div class="timer-label">
                    Secondes
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# HERO
# =========================================================

def render_hero():

    logo = render_logo()

    st.markdown(
        f"""
        <div class="hero-wrap">

            {logo}

            <div class="hero-title">
                TED<span>x</span> B'DARIJA
            </div>

            <div class="hero-ar">
                انضموا إلينا هذا العام
            </div>

            <div class="hero-small">
                IDEAS WORTH SPREADING
            </div>

        </div>

        <div class="floating-stage">

            <div class="float-card float-one">
                ✦ IDEAS
            </div>

            <div class="float-card float-two">
                ⚡ PEOPLE
            </div>

            <div class="float-card float-three">
                TEDx
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# REGISTRATION
# =========================================================

def registration_page():

    st.markdown(
        '<div class="premium-shell">',
        unsafe_allow_html=True
    )

    render_hero()

    render_countdown()

    st.markdown(
        """
        <div class="section-heading">
            Inscription
        </div>
        """,
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

        col1, col2 = st.columns(2)

        with col1:

            major = st.text_input(
                "Filière",
                placeholder="Ex: SMI, Économie..."
            )

        with col2:

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
            "S'INSCRIRE  →"
        )

        if submitted:

            normalized = normalize_moroccan_phone(
                phone
            )

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

            elif datetime.now() >= get_deadline():

                st.error(
                    "Les inscriptions sont terminées."
                )

            else:

                try:

                    extension = (
                        os.path.splitext(
                            photo.name
                        )[1].lower()
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
                    ) as f:

                        f.write(
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
                        "✓ Votre inscription a été enregistrée avec succès."
                    )

                    st.balloons()

                except Exception as e:

                    st.error(
                        f"Erreur lors de l'inscription : {e}"
                    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="admin-access">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.button(
            "🔐  ACCÈS ADMINISTRATION",
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
        '<div class="premium-shell">',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hero-wrap">',
        unsafe_allow_html=True
    )

    st.markdown(
        render_logo(),
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="admin-title">
            Administration
        </div>

        <div style="
            color:#666;
            margin-top:8px;
            font-size:.75rem;
            letter-spacing:1px;
        ">
            ESPACE PRIVÉ • TEDx B'DARIJA
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '</div>',
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
            "SE CONNECTER  →"
        )

        if submitted:

            if (
                email.strip().lower()
                == ADMIN_EMAIL.lower()
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

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

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
# PARTICIPANT CARD
# =========================================================

def registration_card(row):

    photo_path = row["photo_path"]

    st.markdown(
        '<div class="participant-card">',
        unsafe_allow_html=True
    )

    left, middle, right = st.columns(
        [0.8, 3, 1.25]
    )

    with left:

        if (
            photo_path
            and os.path.exists(photo_path)
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
                    border-radius:50%;
                    background:
                        linear-gradient(
                            145deg,
                            #1b1b1b,
                            #090909
                        );
                    border:
                        2px solid
                        rgba(230,43,30,.55);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:22px;
                    font-weight:900;
                    color:#e62b1e;
                ">
                    {safe(initials.upper())}
                </div>
                """,
                unsafe_allow_html=True
            )

    with middle:

        st.markdown(
            f"""
            <div class="name-text">
                {safe(row["name"])}
            </div>

            <div class="small-text">
                {safe(row["major"])}
                •
                {safe(row["year"])}
            </div>

            <div class="small-text">
                📱 {safe(row["phone"])}
            </div>
            """,
            unsafe_allow_html=True
        )

        try:

            date = datetime.fromisoformat(
                row["created_at"]
            ).strftime(
                "%d/%m/%Y • %H:%M"
            )

        except Exception:

            date = "—"

        st.caption(
            f"Inscrit le {date}"
        )

    with right:

        phone = row["phone"]

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

        if st.button(
            "Supprimer",
            key=f"delete_{row['id']}"
        ):

            delete_registration(
                row["id"]
            )

            st.rerun()

    st.markdown(
        '</div>',
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

    # -----------------------------------------------------
    # TOP
    # -----------------------------------------------------

    st.markdown(
        '<div class="premium-shell">',
        unsafe_allow_html=True
    )

    top1, top2 = st.columns(
        [3, 1]
    )

    with top1:

        st.markdown(
            """
            <div class="admin-title">
                TEDx B'DARIJA
                <span style="color:#e62b1e">
                    /
                </span>
                Dashboard
            </div>

            <div class="admin-online">
                <span class="online-dot"></span>
                SYSTÈME ACTIF • BASE DE DONNÉES CONNECTÉE
            </div>
            """,
            unsafe_allow_html=True
        )

    with top2:

        if st.button(
            "🚪 Déconnexion",
            key="logout"
        ):

            st.session_state.admin_logged = False

            st.session_state.page = "registration"

            st.rerun()

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # STATS
    # -----------------------------------------------------

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

        if last_registration:

            try:

                dt = datetime.fromisoformat(
                    last_registration
                ).strftime(
                    "%d/%m/%Y %H:%M"
                )

            except Exception:

                dt = "—"

        else:

            dt = "—"

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="stat-label">
                    Dernière inscription
                </div>

                <div style="
                    font-size:.92rem;
                    font-weight:800;
                    margin-top:16px;
                ">
                    {dt}
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
                    color:#ff5146;
                    font-size:.9rem;
                    font-weight:800;
                    margin-top:16px;
                ">
                    {deadline.strftime("%d/%m/%Y %H:%M")}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # DEADLINE
    # -----------------------------------------------------

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    with st.expander(
        "⚙️  GESTION DE LA DEADLINE"
    ):

        d1, d2 = st.columns(2)

        with d1:

            new_date = st.date_input(
                "Date",
                value=deadline.date()
            )

        with d2:

            new_time = st.time_input(
                "Heure",
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

                save_deadline(
                    new_deadline
                )

                st.success(
                    "Deadline mise à jour."
                )

                st.rerun()

    # -----------------------------------------------------
    # ACTIONS
    # -----------------------------------------------------

    st.markdown(
        "<br>",
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

        csv_data = create_csv(
            registrations
        )

        st.download_button(
            "📥 Exporter CSV",
            data=csv_data,
            file_name=(
                "tedx-bdarija-"
                + datetime.now().strftime(
                    "%Y-%m-%d"
                )
                + ".csv"
            ),
            mime="text/csv"
        )

    with a3:

        if st.button(
            "🗑️ Vider les inscriptions",
            key="clear_all"
        ):

            st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:

        st.warning(
            "Cette action supprimera toutes les inscriptions."
        )

        x1, x2 = st.columns(2)

        with x1:

            if st.button(
                "Oui, supprimer tout",
                key="confirm_delete"
            ):

                delete_all_registrations()

                st.session_state.confirm_clear = False

                st.success(
                    "Toutes les inscriptions ont été supprimées."
                )

                st.rerun()

        with x2:

            if st.button(
                "Annuler",
                key="cancel_delete"
            ):

                st.session_state.confirm_clear = False

                st.rerun()

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    search = st.text_input(
        "🔎 Rechercher un participant",
        placeholder="Nom, WhatsApp, filière ou année..."
    )

    filtered = []

    query = search.strip().lower()

    for row in registrations:

        if not query:

            filtered.append(row)

            continue

        combined = " ".join([
            str(row["name"] or ""),
            str(row["phone"] or ""),
            str(row["major"] or ""),
            str(row["year"] or "")
        ]).lower()

        if query in combined:

            filtered.append(row)

    # -----------------------------------------------------
    # PARTICIPANTS
    # -----------------------------------------------------

    st.markdown(
        f"""
        <div class="section-heading">
            Participants
            <span style="
                color:#e62b1e;
                font-size:.8rem;
            ">
                {len(filtered)}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not filtered:

        st.info(
            "Aucune inscription trouvée."
        )

    for row in filtered:

        registration_card(row)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# ROUTER
# =========================================================

if st.session_state.page == "registration":

    registration_page()

elif st.session_state.page == "login":

    login_page()

elif st.session_state.page == "admin":

    admin_dashboard()
