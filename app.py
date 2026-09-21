import streamlit as st
import re
import csv
import io
import html
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="TEDx B'DARIJA — Registration",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BUCKET_NAME = "participant-photos"


# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = get_supabase()


# =========================================================
# ADMIN
# =========================================================

ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --red: #e31b23;
    --red2: #ff3038;
    --bg: #070707;
    --card: rgba(20,20,20,.72);
    --border: rgba(255,255,255,.10);
    --muted: #9b9b9b;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 50% -10%, rgba(227,27,35,.20), transparent 35%),
        radial-gradient(circle at 0% 40%, rgba(227,27,35,.07), transparent 30%),
        #070707;
    color: white;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero {
    text-align: center;
    padding: 35px 15px 25px;
}

.hero-badge {
    display: inline-block;
    padding: 7px 13px;
    border: 1px solid rgba(227,27,35,.45);
    border-radius: 999px;
    color: #ff6b70;
    background: rgba(227,27,35,.08);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-bottom: 18px;
}

.hero h1 {
    font-size: clamp(38px, 7vw, 78px);
    line-height: .95;
    margin: 0;
    font-weight: 900;
    letter-spacing: -4px;
}

.hero h1 span {
    color: var(--red);
}

.hero p {
    max-width: 650px;
    margin: 20px auto 0;
    color: #a8a8a8;
    font-size: 16px;
    line-height: 1.7;
}

.glass {
    background: rgba(18,18,18,.70);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 28px;
    box-shadow:
        0 20px 70px rgba(0,0,0,.35),
        inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(18px);
}

.section-title {
    font-size: 23px;
    font-weight: 800;
    margin-bottom: 5px;
}

.section-subtitle {
    color: #858585;
    font-size: 13px;
    margin-bottom: 24px;
}

.countdown {
    text-align: center;
    margin: 10px auto 30px;
    padding: 16px;
    border-radius: 18px;
    background: rgba(227,27,35,.07);
    border: 1px solid rgba(227,27,35,.18);
}

.countdown-label {
    color: #999;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.countdown-value {
    margin-top: 6px;
    font-size: 25px;
    font-weight: 900;
    color: #ff4a51;
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
    font-size: 17px;
}

.admin-meta {
    color: #999;
    font-size: 13px;
    line-height: 1.7;
}

.stButton > button {
    border-radius: 12px;
    min-height: 45px;
    font-weight: 700;
}

div[data-testid="stFormSubmitButton"] > button {
    background: var(--red);
    color: white;
    border: none;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--red2);
}

footer {
    visibility: hidden;
}

@media (max-width: 700px) {
    .block-container {
        padding: 1rem .8rem 3rem;
    }

    .glass {
        padding: 20px 16px;
        border-radius: 20px;
    }

    .hero {
        padding-top: 20px;
    }

    .hero h1 {
        letter-spacing: -2px;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def normalize_phone(phone: str):
    p = re.sub(r"[\s\-().]", "", phone.strip())

    if re.fullmatch(r"0[67]\d{8}", p):
        return "+212" + p[1:]

    if re.fullmatch(r"\+212[67]\d{8}", p):
        return p

    if re.fullmatch(r"00212[67]\d{8}", p):
        return "+" + p[2:]

    return None


def get_setting(key: str, default=None):
    try:
        result = (
            supabase
            .table("settings")
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]["value"]

    except Exception:
        pass

    return default


def save_setting(key: str, value: str):
    supabase.table("settings").upsert(
        {
            "key": key,
            "value": value
        }
    ).execute()


def get_deadline():
    value = get_setting("deadline")

    if not value:
        deadline = datetime.now(timezone.utc) + timedelta(days=30)
        save_setting("deadline", deadline.isoformat())
        return deadline

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt

    except Exception:
        deadline = datetime.now(timezone.utc) + timedelta(days=30)
        save_setting("deadline", deadline.isoformat())
        return deadline


def is_admin():
    return st.session_state.get("admin_logged", False)


def logout():
    st.session_state.admin_logged = False
    st.rerun()


def get_registrations():
    result = (
        supabase
        .table("registrations")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []


def delete_registration(reg_id, photo_path=None):
    supabase.table("registrations").delete().eq("id", reg_id).execute()

    if photo_path:
        try:
            supabase.storage.from_(BUCKET_NAME).remove([photo_path])
        except Exception:
            pass


def clear_registrations():
    rows = get_registrations()

    paths = [
        row["photo_path"]
        for row in rows
        if row.get("photo_path")
    ]

    supabase.table("registrations").delete().neq("id", 0).execute()

    if paths:
        try:
            supabase.storage.from_(BUCKET_NAME).remove(paths)
        except Exception:
            pass


def upload_photo(uploaded_file, registration_id):
    if uploaded_file is None:
        return None

    ext = uploaded_file.name.split(".")[-1].lower()

    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise ValueError("Format photo non supporté.")

    file_path = f"{registration_id}_{datetime.now().timestamp()}.{ext}"

    file_bytes = uploaded_file.getvalue()

    supabase.storage.from_(BUCKET_NAME).upload(
        file_path,
        file_bytes,
        {
            "content-type": uploaded_file.type,
            "upsert": "false",
        }
    )

    return file_path


def get_signed_url(path):
    if not path:
        return None

    try:
        result = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path,
            3600
        )

        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl")

    except Exception:
        return None

    return None


# =========================================================
# HEADER
# =========================================================

logo_path = "tedx-bdarija-logo.png"

try:
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()

    import base64

    logo_b64 = base64.b64encode(logo_bytes).decode()

    st.markdown(
        f"""
        <div style="text-align:center;margin-top:5px;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="max-width:180px;max-height:100px;object-fit:contain;">
        </div>
        """,
        unsafe_allow_html=True
    )

except Exception:
    pass


# =========================================================
# ADMIN LOGIN
# =========================================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False


# =========================================================
# MAIN REGISTRATION PAGE
# =========================================================

deadline = get_deadline()
now = datetime.now(timezone.utc)

st.markdown(
    """
<div class="hero">
    <div class="hero-badge">TEDx B'DARIJA</div>

    <h1>
        Your idea.<br>
        <span>Your stage.</span>
    </h1>

    <p>
        Une idée peut changer une personne.
        Une idée peut changer une génération.
        Partagez votre histoire et faites partie de TEDx B'DARIJA.
    </p>
</div>
""",
    unsafe_allow_html=True
)


# =========================================================
# COUNTDOWN
# =========================================================

if now < deadline:

    remaining = deadline - now

    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    seconds = remaining.seconds % 60

    st.markdown(
        f"""
        <div class="countdown">
            <div class="countdown-label">
                Inscriptions ouvertes
            </div>

            <div class="countdown-value">
                {days}j&nbsp;&nbsp;
                {hours:02d}h&nbsp;&nbsp;
                {minutes:02d}m&nbsp;&nbsp;
                {seconds:02d}s
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.warning(
        "Les inscriptions sont actuellement fermées."
    )


# =========================================================
# REGISTRATION
# =========================================================

if now < deadline:

    st.markdown(
        """
        <div class="glass">
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-title">
            Candidate Registration
        </div>

        <div class="section-subtitle">
            Remplissez vos informations avec attention.
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("registration_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Nom complet *",
                placeholder="Votre nom complet"
            )

        with col2:
            phone = st.text_input(
                "WhatsApp *",
                placeholder="06XXXXXXXX",
                help="06 / 07 ou +212 — le numéro sera vérifié automatiquement."
            )

        col3, col4 = st.columns(2)

        with col3:
            major = st.text_input(
                "Filière / Spécialité *",
                placeholder="Ex: Informatique"
            )

        with col4:
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
            type=["jpg", "jpeg", "png", "webp"],
            help="Maximum 3 MB."
        )

        consent = st.checkbox(
            "J'accepte que les informations fournies soient utilisées dans le cadre de l'organisation de TEDx B'DARIJA."
        )

        submitted = st.form_submit_button(
            "ENVOYER MA CANDIDATURE",
            use_container_width=True
        )

        if submitted:

            errors = []

            if not name.strip():
                errors.append("Veuillez entrer votre nom.")

            normalized_phone = normalize_phone(phone)

            if not normalized_phone:
                errors.append(
                    "Numéro WhatsApp invalide. Exemple : 0612345678"
                )

            if not major.strip():
                errors.append("Veuillez entrer votre filière.")

            if year == "Choisir...":
                errors.append("Veuillez choisir votre année.")

            if photo is None:
                errors.append("Veuillez ajouter votre photo.")

            if photo is not None and photo.size > 3 * 1024 * 1024:
                errors.append("La photo ne doit pas dépasser 3 MB.")

            if not consent:
                errors.append("Vous devez accepter les conditions.")

            if errors:

                for error in errors:
                    st.error(error)

            else:

                try:

                    duplicate = (
                        supabase
                        .table("registrations")
                        .select("id")
                        .eq("phone", normalized_phone)
                        .limit(1)
                        .execute()
                    )

                    if duplicate.data:
                        st.error(
                            "Ce numéro WhatsApp est déjà enregistré."
                        )

                    else:

                        result = (
                            supabase
                            .table("registrations")
                            .insert(
                                {
                                    "name": name.strip(),
                                    "phone": normalized_phone,
                                    "major": major.strip(),
                                    "year": year,
                                    "photo_path": None,
                                }
                            )
                            .execute()
                        )

                        if not result.data:
                            raise Exception(
                                "Impossible de créer l'inscription."
                            )

                        registration_id = result.data[0]["id"]

                        photo_path = upload_photo(
                            photo,
                            registration_id
                        )

                        if photo_path:

                            supabase.table("registrations").update(
                                {
                                    "photo_path": photo_path
                                }
                            ).eq(
                                "id",
                                registration_id
                            ).execute()

                        st.success(
                            "✓ Votre candidature a été enregistrée avec succès."
                        )

                        st.balloons()

                except Exception as e:

                    st.error(
                        "Une erreur est survenue pendant l'inscription."
                    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# ADMIN SECTION
# =========================================================

st.markdown("---")

with st.expander("🔐 Administration"):

    if not is_admin():

        st.markdown(
            "### Admin Login"
        )

        admin_email = st.text_input(
            "Email",
            key="admin_email_input"
        )

        admin_password = st.text_input(
            "Password",
            type="password",
            key="admin_password_input"
        )

        if st.button(
            "Se connecter",
            use_container_width=True
        ):

            if (
                admin_email.strip().lower() == ADMIN_EMAIL.lower()
                and admin_password == ADMIN_PASSWORD
            ):

                st.session_state.admin_logged = True
                st.rerun()

            else:

                st.error(
                    "Email ou mot de passe incorrect."
                )

    else:

        # =================================================
        # ADMIN HEADER
        # =================================================

        top1, top2 = st.columns([4, 1])

        with top1:

            st.markdown(
                """
                <div class="section-title">
                    Admin Dashboard
                </div>

                <div class="section-subtitle">
                    Gestion des candidatures TEDx B'DARIJA
                </div>
                """,
                unsafe_allow_html=True
            )

        with top2:

            if st.button(
                "Logout",
                use_container_width=True
            ):
                logout()


        # =================================================
        # DATA
        # =================================================

        registrations = get_registrations()

        total = len(registrations)

        st.markdown(
            f"""
            <div class="glass">
                <div style="
                    font-size:12px;
                    color:#888;
                    text-transform:uppercase;
                    letter-spacing:1px;
                ">
                    Total participants
                </div>

                <div style="
                    font-size:46px;
                    font-weight:900;
                    margin-top:4px;
                ">
                    {total}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")


        # =================================================
        # DEADLINE
        # =================================================

        st.markdown(
            "### ⏳ Deadline"
        )

        current_deadline = get_deadline()

        new_date = st.date_input(
            "Date de fermeture",
            value=current_deadline.date()
        )

        new_time = st.time_input(
            "Heure de fermeture",
            value=current_deadline.time().replace(microsecond=0)
        )

        if st.button(
            "💾 Modifier la deadline"
        ):

            new_deadline = datetime.combine(
                new_date,
                new_time,
                tzinfo=timezone.utc
            )

            save_setting(
                "deadline",
                new_deadline.isoformat()
            )

            st.success(
                "Deadline mise à jour."
            )

            st.rerun()


        # =================================================
        # SEARCH
        # =================================================

        st.markdown(
            "### 🔎 Rechercher"
        )

        search = st.text_input(
            "Nom, WhatsApp, filière...",
            placeholder="Rechercher..."
        )

        filtered = registrations

        if search.strip():

            q = search.strip().lower()

            filtered = [
                row
                for row in registrations
                if q in str(row.get("name", "")).lower()
                or q in str(row.get("phone", "")).lower()
                or q in str(row.get("major", "")).lower()
                or q in str(row.get("year", "")).lower()
            ]


        # =================================================
        # EXPORT
        # =================================================

        if registrations:

            csv_buffer = io.StringIO()

            writer = csv.writer(csv_buffer)

            writer.writerow(
                [
                    "ID",
                    "Nom",
                    "WhatsApp",
                    "Filière",
                    "Année",
                    "Date"
                ]
            )

            for row in registrations:

                writer.writerow(
                    [
                        row.get("id"),
                        row.get("name"),
                        row.get("phone"),
                        row.get("major"),
                        row.get("year"),
                        row.get("created_at"),
                    ]
                )

            st.download_button(
                "⬇️ Exporter CSV",
                data=csv_buffer.getvalue(),
                file_name="tedx_bdarija_registrations.csv",
                mime="text/csv",
                use_container_width=True
            )


        # =================================================
        # DELETE ALL
        # =================================================

        if registrations:

            if st.button(
                "⚠️ Supprimer toutes les candidatures",
                type="secondary"
            ):

                st.session_state.confirm_delete_all = True


            if st.session_state.get(
                "confirm_delete_all",
                False
            ):

                st.warning(
                    "Cette action supprimera toutes les candidatures."
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "Oui, supprimer tout",
                        type="primary",
                        use_container_width=True
                    ):

                        clear_registrations()

                        st.session_state.confirm_delete_all = False

                        st.success(
                            "Toutes les candidatures ont été supprimées."
                        )

                        st.rerun()

                with c2:

                    if st.button(
                        "Annuler",
                        use_container_width=True
                    ):

                        st.session_state.confirm_delete_all = False

                        st.rerun()


        # =================================================
        # PARTICIPANTS
        # =================================================

        st.markdown(
            "### 👥 Participants"
        )

        if not filtered:

            st.info(
                "Aucun participant trouvé."
            )

        else:

            for row in filtered:

                photo_url = get_signed_url(
                    row.get("photo_path")
                )

                created_at = row.get(
                    "created_at",
                    ""
                )

                if created_at:

                    try:

                        dt = datetime.fromisoformat(
                            created_at.replace(
                                "Z",
                                "+00:00"
                            )
                        )

                        created_display = dt.strftime(
                            "%d/%m/%Y %H:%M"
                        )

                    except Exception:

                        created_display = created_at

                else:

                    created_display = "—"


                with st.container():

                    st.markdown(
                        '<div class="admin-card">',
                        unsafe_allow_html=True
                    )

                    c1, c2, c3 = st.columns(
                        [1, 3, 1]
                    )

                    with c1:

                        if photo_url:

                            st.image(
                                photo_url,
                                width=100
                            )

                        else:

                            st.write("📷")


                    with c2:

                        safe_name = html.escape(
                            str(row.get("name", ""))
                        )

                        safe_major = html.escape(
                            str(row.get("major", ""))
                        )

                        safe_year = html.escape(
                            str(row.get("year", ""))
                        )

                        safe_phone = html.escape(
                            str(row.get("phone", ""))
                        )

                        st.markdown(
                            f"""
                            <h4>{safe_name}</h4>

                            <div class="admin-meta">
                                🎓 {safe_major}<br>
                                📚 {safe_year}<br>
                                📱 {safe_phone}<br>
                                🕒 {created_display}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


                    with c3:

                        whatsapp_number = str(
                            row.get("phone", "")
                        ).replace(
                            "+",
                            ""
                        )

                        whatsapp_url = (
                            "https://wa.me/"
                            + whatsapp_number
                        )

                        st.link_button(
                            "WhatsApp",
                            whatsapp_url,
                            use_container_width=True
                        )

                        if st.button(
                            "🗑️ Supprimer",
                            key=f"delete_{row['id']}",
                            use_container_width=True
                        ):

                            delete_registration(
                                row["id"],
                                row.get("photo_path")
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
    font-size:11px;
    margin-top:50px;
">
    TEDx B'DARIJA • Registration Platform
</div>
""",
    unsafe_allow_html=True
)
