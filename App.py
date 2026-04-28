import sys
import os

# Garante que o diretório raiz está no path para imports funcionarem no Streamlit Cloud
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="AgroGestão - Gestão de Fazenda",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Source+Sans+3:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Merriweather', serif;
    }

    .main { background-color: #f5f0e8; }
    
    [data-testid="stSidebar"] {
        background-color: #2d4a22;
        color: white;
    }

    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #e8dcc8 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #f0e6cc !important;
    }

    .metric-card {
        background: white;
        border: 1px solid #d4c5a9;
        border-left: 4px solid #5a8a3c;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .stButton > button {
        background-color: #5a8a3c;
        color: white;
        border: none;
        border-radius: 4px;
        font-family: 'Source Sans 3', sans-serif;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #2d4a22;
    }

    .alert-card {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-left: 4px solid #dc3545;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #d4c5a9;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("# 🐄 AgroGestão")
    st.markdown("---")
    st.markdown("### Navegação")

    page = st.radio(
        "",
        [
            "🏠 Dashboard",
            "📦 Lotes",
            "⚖️ Pesagens",
            "🏥 Ocorrências",
            "📊 Análises & GMD",
            "🔍 Comparativos",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**Fazenda:** Rancho Belo")
    st.markdown("**Responsável:** Admin")

# Route to pages
if page == "🏠 Dashboard":
    from modulos import dashboard
    dashboard.show()
elif page == "📦 Lotes":
    from modulos import lotes
    lotes.show()
elif page == "⚖️ Pesagens":
    from modulos import pesagens
    pesagens.show()
elif page == "🏥 Ocorrências":
    from modulos import ocorrencias
    ocorrencias.show()
elif page == "📊 Análises & GMD":
    from modulos import analises
    analises.show()
elif page == "🔍 Comparativos":
    from modulos import comparativos
    comparativos.show()
