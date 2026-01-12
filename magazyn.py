import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. Konfiguracja Stylu Baby Blue & Pink ---
st.set_page_config(page_title="Magazyn Pastel Pro", layout="wide", page_icon="☁️")

# Kolory przewodnie
BABY_BLUE = "#A2D2FF"
SOFT_PINK = "#FFC8DD"
PASTEL_WHITE = "#FBFAFF"
TEXT_BLUE = "#5E60CE"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {PASTEL_WHITE}; }}
    h1, h2, h3 {{ color: {TEXT_BLUE} !important; font-family: 'Quicksand', sans-serif; }}
    .stButton>button {{
        background-color: {BABY_BLUE};
        color: white;
        border-radius: 15px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: 0.3s;
    }}
    .stButton>button:hover {{
        background-color: {SOFT_PINK};
        color: #555;
        transform: translateY(-2px);
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #f0f2f6;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }}
    .stTabs [aria-selected="true"] {{ background-color: {BABY_BLUE} !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Połączenie z Supabase ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("❌ Błąd konfiguracji! Sprawdź Secrets w Streamlit Cloud.")
        return None

supabase = init_connection()

# --- 3. Funkcje Pomocnicze (Obsługa błędów nazw tabel) ---
def get_table_name(target):
    """Sprawdza czy tabela istnieje jako 'produkty' czy 'Produkty'."""
    options = [target.lower(), target.capitalize()]
    for opt in options:
        try:
            supabase.table(opt).select("id").limit(1).execute()
            return opt
        except: continue
    return options[0]

def pobierz_dane(tabela):
    real_name = get_table_name(tabela)
    res = supabase.table(real_name).select("*").execute()
    return res.data

# --- 4. Interfejs Główny ---
st.title("☁️ Pastelowy Magazyn: Baby Blue Edition")

if supabase:
    tab_dash, tab_prod, tab_kat = st.tabs(["📊 Statystyki", "📦 Zarządzanie Towarem", "📂 Kategorie"])

    # --- TAB: DASHBOARD ---
    with tab_dash:
        data_p = pobierz_dane("produkty")
        if data_p:
            df = pd.DataFrame(data_p)
            df['Wartość'] = df['liczba'] * df['cena']
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Liczba Produktów", len(df))
            m2.metric("Suma Sztuk", int(df['liczba'].sum()))
            m3.metric("Wartość Magazynu", f"{df['Wartość'].sum():,.2f} PLN")

            st.subheader("Wizualizacja Stanów")
            fig = px.bar(df, x='nazwa', y='liczba', 
                         color_discrete_sequence=[BABY_BLUE],
                         labels={'nazwa': 'Produkt', 'liczba': 'Ilość'})
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Baza jest pusta. Dodaj produkty w kolejnej zakładce!")

    # --- TAB: ZARZĄDZANIE TOWAREM ---
    with tab_prod:
        col_inc, col_list = st.columns([1, 1.5])
        
        with col_inc:
            st.subheader("🔄 Zmień Ilość / Dodaj")
            if data_p:
                wybor = st.selectbox("Wybierz produkt do edycji", options=[p['nazwa'] for p in data_p])
                p_obj = next(item for item in data_p if item["nazwa"] == wybor)
                
                st.write(f"Aktualnie w bazie: **{p_obj['liczba']}** szt.")
                delta = st.number_input("O ile zmienić? (użyj minusa aby odjąć)", value=0)
                
                if st.button("Zaktualizuj Ilość"):
                    nowa_ilosc = p_obj['liczba'] + delta
                    if nowa_ilosc < 0: st.error("Nie można zejść poniżej zera!")
                    else:
                        supabase.table(get_table_name("produkty")).update({"liczba": nowa_ilosc}).eq("id", p_obj['id']).execute()
                        st.success("Zmieniono ilość!")
                        st.rerun()
                
                if st.button("🗑️ Usuń całkowicie produkt", type="secondary"):
                    supabase.table(get_table_name("produkty")).delete().eq("id", p_obj['id']).execute()
                    st.rerun()

            st.divider()
            st.subheader("✨ Nowy Produkt")
            kat_list = pobierz_dane("kategorie")
            if kat_list:
                kat_map = {k['nazwa']: k['id'] for k in kat_list}
                with st.form("new_product"):
                    n = st.text_input("Nazwa")
                    l = st.number_input("Ilość", min_value=1)
                    c = st.number_input("Cena", min_value=0.0)
                    k = st.selectbox("Kategoria", options=list(kat_map.keys()))
                    if st.form_submit_button("Dodaj produkt"):
                        supabase.table(get_table_name("produkty")).insert({
                            "nazwa": n, "liczba": l, "cena": c, "kategoria_id": kat_map[k]
                        }).execute()
                        st.rerun()

        with col_list:
            st.subheader("📋 Aktualna Lista")
            if data_p:
                st.dataframe(df[['nazwa', 'liczba', 'cena', 'Wartość']], use_container_width=True)

    # --- TAB: KATEGORIE ---
    with tab_kat:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📂 Nowa Kategoria")
            with st.form("new_kat"):
                nk = st.text_input("Nazwa")
                ok = st.text_area("Opis")
                if st.form_submit_button("Dodaj"):
                    supabase.table(get_table_name("kategorie")).insert({"nazwa": nk, "opis": ok}).execute()
                    st.rerun()
        with c2:
            st.subheader("🗑️ Usuń Kategorię")
            if kat_list:
                to_del = st.selectbox("Wybierz do usunięcia", options=[k['nazwa'] for k in kat_list])
                if st.button("Usuń bezpowrotnie"):
                    id_del = next(k['id'] for k in kat_list if k['nazwa'] == to_del)
                    try:
                        supabase.table(get_table_name("kategorie")).delete().eq("id", id_del).execute()
                        st.rerun()
                    except:
                        st.error("Nie można usunąć kategorii, która ma przypisane produkty!")
