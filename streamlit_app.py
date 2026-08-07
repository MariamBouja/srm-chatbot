import html
import re
from datetime import datetime

import markdown as md
import streamlit as st

from chatbot.agencies import list_regions
from chatbot.conversation import handle_message, new_state
from chatbot.rag import get_source_metadata

WELCOME_MESSAGE = (
    "Bonjour 👋 Je suis l'assistant virtuel officiel de la **SRM-SM** "
    "(Société Régionale Multiservices Souss-Massa).\n\n"
    "Je peux répondre à vos questions sur nos missions, nos procédures de "
    "branchement et d'abonnement, nos agences d'accueil, et nos coordonnées.\n\n"
    "Posez-moi votre question ci-dessous 👇"
)

_SCRIPT_TAG_RE = re.compile(r"<\s*script", re.IGNORECASE)

st.set_page_config(
    page_title="Assistant SRM-SM",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --primary: #0B5FA5;
        --primary-dark: #084a84;
        --primary-light: #E8F1FA;
        --bg: #F5F8FC;
        --text: #1A2332;
        --muted: #6B7787;
        --border: #E0E6ED;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
    }

    #MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden;}

    .stApp { background: var(--bg); }

    .block-container {
        max-width: 880px;
        margin: 0 auto;
        padding-top: 1.5rem;
        padding-bottom: 6rem;
    }

    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--border);
    }

    .sidebar-logo {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--primary);
        letter-spacing: -0.02em;
        margin-bottom: 0.1rem;
    }
    .sidebar-logo span { color: var(--text); font-weight: 600; }
    .sidebar-subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }

    .app-header {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 1.1rem 1.4rem;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        border-radius: 16px;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 14px rgba(11, 95, 165, 0.18);
    }
    .app-header .icon { font-size: 2rem; }
    .app-header .title { color: #FFFFFF; font-size: 1.25rem; font-weight: 700; margin: 0; }
    .app-header .subtitle { color: #DCEBF9; font-size: 0.85rem; margin: 0; }

    .chat-row {
        display: flex;
        align-items: flex-end;
        gap: 0.6rem;
        margin-bottom: 1.1rem;
        animation: fadeIn 0.25s ease-in;
    }
    .user-row { flex-direction: row-reverse; }
    .assistant-row { flex-direction: row; }

    .avatar {
        flex-shrink: 0;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    .user-avatar { background: var(--primary-light); }
    .assistant-avatar { background: var(--primary); }

    .bubble {
        max-width: 74%;
        padding: 0.7rem 1rem;
        line-height: 1.55;
        font-size: 0.95rem;
    }
    .user-bubble {
        background: var(--primary);
        color: #FFFFFF;
        border-radius: 16px 16px 4px 16px;
    }
    .assistant-bubble {
        background: #FFFFFF;
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 16px 16px 16px 4px;
        box-shadow: 0 1px 3px rgba(20, 30, 50, 0.05);
    }
    .bubble-content p { margin: 0 0 0.5rem 0; }
    .bubble-content p:last-child { margin-bottom: 0; }
    .bubble-content ul, .bubble-content ol { margin: 0.3rem 0 0.5rem 1.1rem; padding: 0; }
    .bubble-time {
        font-size: 0.7rem;
        opacity: 0.65;
        text-align: right;
        margin-top: 0.35rem;
    }

    .source-links {
        max-width: 74%;
        margin: 0.35rem 0 1.1rem 46px;
        font-size: 0.8rem;
        color: var(--muted);
    }
    .source-links a {
        color: var(--primary);
        text-decoration: none;
    }
    .source-links a:hover { text-decoration: underline; }

    .welcome-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(20, 30, 50, 0.05);
        animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = new_state()


def render_markdown_safe(text):
    """Render LLM/user text as HTML, defensively stripping literal script tags."""
    text = _SCRIPT_TAG_RE.sub("&lt;script", text)
    return md.markdown(text, extensions=["nl2br", "sane_lists", "fenced_code"])


def render_message(msg):
    timestamp = msg.get("timestamp", "")

    if msg["role"] == "user":
        content_html = html.escape(msg["content"]).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="chat-row user-row">
                <div class="avatar user-avatar">🧑</div>
                <div class="bubble user-bubble">
                    <div class="bubble-content">{content_html}</div>
                    <div class="bubble-time">{timestamp}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    content_html = render_markdown_safe(msg["content"])
    st.markdown(
        f"""
        <div class="chat-row assistant-row">
            <div class="avatar assistant-avatar">💧</div>
            <div class="bubble assistant-bubble">
                <div class="bubble-content">{content_html}</div>
                <div class="bubble-time">{timestamp}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sources = msg.get("sources") or []
    if sources:
        links = []
        for source in sources:
            meta = get_source_metadata(source)
            label = html.escape(meta["title"])
            if meta["url"]:
                url = html.escape(meta["url"], quote=True)
                links.append(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>')
            else:
                links.append(label)

        st.markdown(
            '<div class="source-links">📄 Sources : ' + " &nbsp;·&nbsp; ".join(links) + "</div>",
            unsafe_allow_html=True,
        )


with st.sidebar:
    st.markdown('<div class="sidebar-logo">SRM<span>-SM</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Assistant virtuel officiel</div>', unsafe_allow_html=True)

    if st.button("🆕 Nouvelle conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.conversation_state = new_state()
        st.rerun()

    if st.button("🗑️ Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_state = new_state()
        st.rerun()

    st.divider()
    st.caption(
        "Cet assistant répond exclusivement à partir du contenu officiel du "
        "site srm-sm.ma. Il ne peut pas répondre aux questions hors sujet."
    )
    st.divider()
    st.caption("Société Régionale Multiservices Souss-Massa")
    st.caption("Distribution d'eau · Électricité · Assainissement liquide")

st.markdown(
    """
    <div class="app-header">
        <div class="icon">💧</div>
        <div>
            <p class="title">Assistant SRM-SM</p>
            <p class="subtitle">Société Régionale Multiservices Souss-Massa — Assistant virtuel</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        f'<div class="welcome-card">{render_markdown_safe(WELCOME_MESSAGE)}</div>',
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    render_message(message)

prompt = st.chat_input("Posez votre question sur la SRM-SM...")

awaiting_region = st.session_state.conversation_state.get("pending") == "agency_region"
region_choice = None
if awaiting_region:
    st.markdown("**Choisissez une région :**")
    region_cols = st.columns(2)
    for i, region in enumerate(list_regions()):
        if region_cols[i % 2].button(region, key=f"region_btn_{region}", use_container_width=True):
            region_choice = region

user_text = prompt or region_choice

if user_text:
    user_message = {
        "role": "user",
        "content": user_text,
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    st.session_state.messages.append(user_message)
    render_message(user_message)

    try:
        with st.spinner("💭 L'assistant rédige une réponse..."):
            result = handle_message(user_text, st.session_state.conversation_state)

        assistant_message = {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    except Exception as exc:
        print(f"[streamlit_app] answer_question failed: {exc!r}")
        assistant_message = {
            "role": "assistant",
            "content": (
                "Une erreur inattendue s'est produite pendant la génération de la "
                "réponse. Veuillez réessayer dans quelques instants ou contacter "
                "le support technique de la SRM-SM si le problème persiste."
            ),
            "sources": [],
            "timestamp": datetime.now().strftime("%H:%M"),
        }

    st.session_state.messages.append(assistant_message)

    if st.session_state.conversation_state.get("pending") == "agency_region":
        # A fresh rerun is needed so the region-button block (evaluated
        # earlier in this same script pass, before handle_message ran) sees
        # the updated pending state and actually renders the buttons.
        st.rerun()

    render_message(assistant_message)

    st.markdown(
        """
        <script>
        window.parent.document.querySelectorAll('section.main')
            .forEach(el => el.scrollTo({top: el.scrollHeight, behavior: 'smooth'}));
        </script>
        """,
        unsafe_allow_html=True,
    )
