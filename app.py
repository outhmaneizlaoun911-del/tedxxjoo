import streamlit as st
import sqlite3
import os
import re
import csv
import io
from datetime import datetime, timedelta

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="TEDx B'DARIJA",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_DIR = "data"
UPLOAD_DIR = "uploads"
DB_PATH = os.path.join(DB_DIR, "tedx.db")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ADMIN_EMAIL = "outhmane@farah.love"
ADMIN_PASSWORD = "oufa@2026@!"

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            major TEXT NOT NULL,
            year TEXT NOT NULL,
            photo_path TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute(
        "SELECT value FROM settings WHERE key = ?",
        ("deadline",)
    )

    row = cur.fetchone()

    if not row:
        deadline = (
            datetime.now() + timedelta(days=30)
        ).isoformat()

        cur.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            """,
            ("deadline", deadline)
        )

    conn.commit()
    conn.close()


init_db()


# =========================================================
# HELPERS
# =========================================================

def normalize_phone(phone):
    p = re.sub(r"[\s\-().]", "", phone.strip())

    if re.fullmatch(r"0[67]\d{8}", p):
        return "+212" + p[1:]

    if re.fullmatch(r"\+212[67]\d{8}", p):
        return p

    if re.fullmatch(r"00212[67]\d{8}", p):
        return "+" + p[2:]

    return None


def get_deadline():
    conn = get_db()

    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?",
        ("deadline",)
    ).fetchone()

    conn.close()

    if not row:
        return datetime.now() + timedelta(days=30)

    try:
        return datetime.fromisoformat(row["value"])
    except Exception:
        return datetime.now() + timedelta(days=30)


def set_deadline(value):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO settings(key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        ("deadline", value.isoformat())
    )

    conn.commit()
    conn.close()


def get_registrations():
    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM registrations
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return rows


def delete_registration(registration_id):
    conn = get_db()

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
            if os.path.exists(row["photo_path"]):
                os.remove(row["photo_path"])
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


def clear_all():
    conn = get_db()

    rows = conn.execute(
        "SELECT photo_path FROM registrations"
    ).fetchall()

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


def save_registration(
    name,
    phone,
    major,
    year,
    photo_file
):

    conn = get_db()

    existing = conn.execute(
        """
        SELECT id
        FROM registrations
        WHERE phone = ?
        """,
        (phone,)
    ).fetchone()

    if existing:
        conn.close()
        return False, "Ce numéro WhatsApp est déjà enregistré."

    created_at = datetime.now().isoformat()

    cur = conn.cursor()

    cur.execute(
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
            None,
            created_at,
        )
    )

    registration_id = cur.lastrowid

    photo_path = None

    if photo_file:

        extension = (
            photo_file.name
            .split(".")[-1]
            .lower()
        )

        filename = (
            f"{registration_id}_"
            f"{int(datetime.now().timestamp())}."
            f"{extension}"
        )

        photo_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        with open(photo_path, "wb") as f:
            f.write(photo_file.getbuffer())

        conn.execute(
            """
            UPDATE registrations
            SET photo_path = ?
            WHERE id = ?
            """,
            (
                photo_path,
                registration_id
            )
        )

    conn.commit()
    conn.close()

    return True, "Votre candidature a été enregistrée avec succès."


def admin_logged():
    return st.session_state.get(
        "admin_logged",
        False
    )


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap'
);

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(227,27,35,.20),
            transparent 35%
        ),
        #070707;
    color: white;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero {
    text-align: center;
    padding: 35px 10px;
}

.badge {
    display: inline-block;
    padding: 8px 15px;
    border-radius: 999px;
    border: 1px solid rgba(227,27,35,.4);
    background: rgba(227,27,35,.08);
    color: #ff6b70;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

.hero h1 {
    font-size: clamp(42px, 8vw, 80px);
    line-height: .95;
    font-weight: 900;
    letter-spacing: -4px;
    margin: 20px 0 0;
}

.hero h1 span {
    color: #e31b23;
}

.hero p {
    max-width: 680px;
    margin: 22px auto;
    color: #999;
    line-height: 1.7;
}

.glass {
    background: rgba(18,18,18,.72);
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 25px 70px rgba(0,0,0,.35);
}

.countdown {
    text-align: center;
    padding: 18px;
    border-radius: 18px;
    background: rgba(227,27,35,.07);
    border: 1px solid rgba(227,27,35,.20);
    margin-bottom: 30px;
}

.countdown-label {
    color: #888;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.countdown-value {
    color: #ff4d54;
    font-size: 25px;
    font-weight: 900;
    margin-top: 5px;
}

.admin-card {
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 12px;
}

.admin-card h4 {
    margin: 0 0 8px;
}

.meta {
    color: #999;
    font-size: 13px;
    line-height: 1.8;
}

footer {
    visibility: hidden;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# LOGO
# =========================================================

if os.path.exists("tedx-bdarija-logo.png"):

    st.markdown(
        """
        <div style="text-align:center;margin-top:10px;">
        """,
        unsafe_allow_html=True
    )

    st.image(
        "tedx-bdarija-logo.png",
        width=180
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# SESSION
# =========================================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">

    <div class="badge">
        TEDx B'DARIJA
    </div>

    <h1>
        YOUR IDEA.<br>
        <span>YOUR STAGE.</span>
    </h1>

    <p>
        Une idée peut changer une personne.
        Une idée peut changer une génération.
        Partagez votre histoire et faites partie
        de TEDx B'DARIJA.
    </p>

</div>
""",
    unsafe_allow_html=True
)


# =========================================================
# DEADLINE
# =========================================================

deadline = get_deadline()
now = datetime.now()

if now < deadline:

    remaining = deadline - now

    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (
        remaining.seconds % 3600
    ) // 60
    seconds = remaining.seconds % 60

    st.markdown(
        f"""
        <div class="countdown">

            <div class="countdown-label">
                INSCRIPTIONS OUVERTES
            </div>

            <div class="countdown-value">
                {days}J
                &nbsp;
                {hours:02d}H
                &nbsp;
                {minutes:02d}M
                &nbsp;
                {seconds:02d}S
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# FORM
# =========================================================

if now < deadline:

    st.markdown(
        '<div class="glass">',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h2>Candidate Registration</h2>

        <div style="
            color:#888;
            margin-bottom:20px;
        ">
            Remplissez vos informations avec attention.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form(
        "registration_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Nom complet *",
                placeholder="Votre nom complet"
            )

        with c2:

            phone = st.text_input(
                "WhatsApp *",
                placeholder="06XXXXXXXX"
            )

        c3, c4 = st.columns(2)

        with c3:

            major = st.text_input(
                "Filière / Spécialité *",
                placeholder="Ex: Informatique"
            )

        with c4:

            year = st.selectbox(
                "Année d'étude *",
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
            "Photo *",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ]
        )

        consent = st.checkbox(
            "J'accepte que les informations fournies soient utilisées dans le cadre de l'organisation de TEDx B'DARIJA."
        )

        submit = st.form_submit_button(
            "ENVOYER MA CANDIDATURE",
            use_container_width=True
        )

        if submit:

            errors = []

            if not name.strip():
                errors.append(
                    "Veuillez entrer votre nom."
                )

            normalized = normalize_phone(phone)

            if not normalized:
                errors.append(
                    "Numéro WhatsApp invalide."
                )

            if not major.strip():
                errors.append(
                    "Veuillez entrer votre filière."
                )

            if year == "Choisir...":
                errors.append(
                    "Veuillez choisir votre année."
                )

            if not photo:
                errors.append(
                    "Veuillez ajouter votre photo."
                )

            if photo and photo.size > 3 * 1024 * 1024:
                errors.append(
                    "La photo ne doit pas dépasser 3 MB."
                )

            if not consent:
                errors.append(
                    "Vous devez accepter les conditions."
                )

            if errors:

                for error in errors:
                    st.error(error)

            else:

                success, message = save_registration(
                    name.strip(),
                    normalized,
                    major.strip(),
                    year,
                    photo
                )

                if success:

                    st.success(message)

                    st.balloons()

                else:

                    st.error(message)

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =========================================================
# ADMIN
# =========================================================

st.markdown("---")

with st.expander("🔐 Administration"):

    if not admin_logged():

        st.markdown("### Admin Login")

        email = st.text_input(
            "Email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Se connecter",
            use_container_width=True
        ):

            if (
                email.strip().lower()
                == ADMIN_EMAIL.lower()
                and
                password
                == ADMIN_PASSWORD
            ):

                st.session_state.admin_logged = True
                st.rerun()

            else:

                st.error(
                    "Email ou mot de passe incorrect."
                )

    else:

        c1, c2 = st.columns([4, 1])

        with c1:

            st.markdown(
                """
                <h2>Admin Dashboard</h2>

                <div style="color:#888;">
                    Gestion des candidatures
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            if st.button(
                "Logout",
                use_container_width=True
            ):

                st.session_state.admin_logged = False
                st.rerun()


        # =================================================
        # DATA
        # =================================================

        registrations = get_registrations()

        st.metric(
            "Total participants",
            len(registrations)
        )


        # =================================================
        # SEARCH
        # =================================================

        search = st.text_input(
            "🔎 Rechercher un participant"
        )

        filtered = registrations

        if search.strip():

            q = search.lower().strip()

            filtered = [
                row
                for row in registrations
                if q in row["name"].lower()
                or q in row["phone"].lower()
                or q in row["major"].lower()
                or q in row["year"].lower()
            ]


        # =================================================
        # EXPORT CSV
        # =================================================

        if registrations:

            buffer = io.StringIO()

            writer = csv.writer(buffer)

            writer.writerow([
                "ID",
                "Nom",
                "WhatsApp",
                "Filière",
                "Année",
                "Date"
            ])

            for row in registrations:

                writer.writerow([
                    row["id"],
                    row["name"],
                    row["phone"],
                    row["major"],
                    row["year"],
                    row["created_at"]
                ])

            st.download_button(
                "⬇️ Télécharger CSV",
                buffer.getvalue(),
                "tedx_bdarija.csv",
                "text/csv",
                use_container_width=True
            )


        # =================================================
        # DEADLINE ADMIN
        # =================================================

        st.markdown("### ⏳ Deadline")

        selected_date = st.date_input(
            "Date",
            deadline.date()
        )

        selected_time = st.time_input(
            "Heure",
            deadline.time()
        )

        if st.button(
            "💾 Sauvegarder deadline"
        ):

            new_deadline = datetime.combine(
                selected_date,
                selected_time
            )

            set_deadline(new_deadline)

            st.success(
                "Deadline mise à jour."
            )

            st.rerun()


        # =================================================
        # DELETE ALL
        # =================================================

        if registrations:

            if st.button(
                "⚠️ Supprimer toutes les candidatures"
            ):

                st.session_state.confirm_delete = True

            if st.session_state.get(
                "confirm_delete",
                False
            ):

                st.warning(
                    "Cette action est irréversible."
                )

                a, b = st.columns(2)

                with a:

                    if st.button(
                        "Oui, supprimer tout",
                        use_container_width=True
                    ):

                        clear_all()

                        st.session_state.confirm_delete = False

                        st.success(
                            "Toutes les candidatures ont été supprimées."
                        )

                        st.rerun()

                with b:

                    if st.button(
                        "Annuler",
                        use_container_width=True
                    ):

                        st.session_state.confirm_delete = False
                        st.rerun()


        # =================================================
        # PARTICIPANTS
        # =================================================

        st.markdown("### 👥 Participants")

        if not filtered:

            st.info(
                "Aucun participant."
            )

        for row in filtered:

            st.markdown(
                '<div class="admin-card">',
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(
                [1, 4, 1]
            )

            with c1:

                if (
                    row["photo_path"]
                    and
                    os.path.exists(
                        row["photo_path"]
                    )
                ):

                    st.image(
                        row["photo_path"],
                        width=100
                    )

                else:

                    st.write("📷")


            with c2:

                st.markdown(
                    f"""
                    <h4>{row["name"]}</h4>

                    <div class="meta">

                    🎓 {row["major"]}<br>
                    📚 {row["year"]}<br>
                    📱 {row["phone"]}<br>
                    🕒 {row["created_at"]}

                    </div>
                    """,
                    unsafe_allow_html=True
                )


            with c3:

                whatsapp = (
                    "https://wa.me/"
                    +
                    row["phone"].replace(
                        "+",
                        ""
                    )
                )

                st.link_button(
                    "WhatsApp",
                    whatsapp,
                    use_container_width=True
                )

                if st.button(
                    "🗑️ Supprimer",
                    key=f"delete_{row['id']}",
                    use_container_width=True
                ):

                    delete_registration(
                        row["id"]
                    )

                    st.rerun()


            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
<div style="
    text-align:center;
    color:#555;
    margin-top:50px;
    font-size:11px;
">
    TEDx B'DARIJA
</div>
""",
    unsafe_allow_html=True
)
