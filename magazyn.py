import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- 1. Konfiguracja Stylu BabyBlue Warehouse ---
st.set_page_config(page_title="BabyBlue Warehouse", layout="wide", page_icon="💙")

# Definicja kolorystyki Baby Blue & Pink
BABY_BLUE = "#A2D2FF"
SOFT_PINK = "#FFC8DD"
PASTEL_WHITE = "#F0F8FF" # Bardzo jasny błękitny
TEXT_BLUE = "#0077B6"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {PASTEL_WHITE}; }}
    h1, h2, h3 {{ color: {TEXT_BLUE} !important; font-family: 'Segoe UI', sans-serif; }}
    
    /* Przyciski BabyBlue */
    .stButton>button {{
        background-color: {BABY_BLUE};
        color: white;
        border-radius: 20px;
        border: 2px solid #BDE0FE;
        padding: 0.6rem 2.5rem;
        font-weight: bold;
        transition: 0.3s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: {SOFT_PINK};
        color: #444;
        border-color: #FFAFCC;
    }}
    
    /* Karty i Formularze */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #E1EEFF;
        border-radius: 10px 10px 0 0;
        padding: 10px 25px;
        color: {TEXT_BLUE};
    }}
    .stTabs [aria-selected="true"] {{ 
        background-color: {BABY_BLUE} !important; 
        color: white !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Połączenie z Supabase ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("❌ Błąd konfiguracji! Dodaj klucze do Secrets w Streamlit Cloud.")
        return None

supabase = init_connection()

# --- 3. Funkcje Logiki (odporne na nazwy tabel) ---
def get_table_name(target):
    options = [target.lower(), target.capitalize()]
    for opt in options:
        try:
            supabase.table(opt).select("id").limit(1).execute()
            return opt
        except: continue
    return options[0]

def pobierz_dane(tabela):
    try:
        name = get_table_name(tabela)
        res = supabase.table(name).select("*").execute()
        return res.data
    except: return []

# --- 4. Interfejs Użytkownika ---
st.title("💙 BabyBlue Warehouse")
st.caption("Nowoczesny Niebieski Magazyn z systemem zarządzania kategoriami")

if supabase:
    tab_dash, tab_inv, tab_cat = st.tabs(["📊 Panel Statystyk", "📦 Zarządzanie Zapasami", "📂 Kategorie"])

    # --- TAB: DASHBOARD ---
    with tab_dash:
        produkty_raw = pobierz_dane("produkty")
        if produkty_raw:
            df = pd.DataFrame(produkty_raw)
            df['Wartość (PLN)'] = df['liczba'] * df['cena']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Unikalne Produkty", len(df))
            c2.metric("Suma Wszystkich Sztuk", int(df['liczba'].sum()))
            c3.metric("Wartość Całego Magazynu", f"{df['Wartość (PLN)'].sum():,.2f}")

            st.subheader("Aktualne stany w BabyBlue Warehouse")
            fig = px.bar(df, x='nazwa', y='liczba',
                         color_discrete_sequence=[BABY_BLUE],
                         labels={'nazwa': 'Nazwa Produktu', 'liczba': 'Dostępna Ilość'})
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font_color=TEXT_BLUE
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Magazyn jest pusty. Zacznij od dodania kategorii i produktów.")

    # --- TAB: ZARZĄDZANIE ZAPASAMI ---
    with tab_inv:
        col_ctrl, col_table = st.columns([1, 1.5])
        
        with col_ctrl:
            st.subheader("🛠️ Operacje na stanie")
            if produkty_raw:
                p_lista = {p['nazwa']: p for p in produkty_raw}
                wybor = st.selectbox("Wybierz produkt", options=list(p_lista.keys()))
                item = p_lista[wybor]
                
                st.write(f"Stan obecny: **{item['liczba']}**")
                akcja = st.radio("Rodzaj zmiany:", ["Dostawa (+)", "Wydanie (-)"])
                ilosc_zmiana = st.number_input("O ile sztuk?", min_value=1, step=1)
                
                if st.button("Zapisz zmianę"):
                    nowa_suma = item['liczba'] + (ilosc_zmiana if akcja == "Dostawa (+)" else -ilosc_zmiana)
                    if nowa_suma < 0:
                        st.error("Błąd: Brak wystarczającej ilości towaru!")
                    else:
                        supabase.table(get_table_name("produkty")).update({"liczba": nowa_suma}).eq("id", item['id']).execute()
                        st.success("Zaktualizowano stan w BabyBlue Warehouse!")
                        st.rerun()

                if st.button("🗑️ Usuń produkt z systemu"):
                    supabase.table(get_table_name("produkty")).delete().eq("id", item['id']).execute()
                    st.rerun()

            st.divider()
            st.subheader("🆕 Dodaj nowy towar")
            kat_raw = pobierz_dane("kategorie")
            if kat_raw:
                kat_map = {k['nazwa']: k['id'] for k in kat_raw}
                with st.form("new_item_form"):
                    n_p = st.text_input("Nazwa przedmiotu")
                    l_p = st.number_input("Ilość na start", min_value=1)
                    c_p = st.number_input("Cena jednostkowa", min_value=0.0)
                    k_p = st.selectbox("Przypisz kategorię", options=list(kat_map.keys()))
                    if st.form_submit_button("Dodaj do magazynu"):
                        supabase.table(get_table_name("produkty")).insert({
                            "nazwa": n_p, "liczba": l_p, "cena": c_p, "kategoria_id": kat_map[k_p]
                        }).execute()
                        st.rerun()

        with col_table:
            st.subheader("📋 Inwentaryzacja")
            if produkty_raw:
                st.dataframe(df[['nazwa', 'liczba', 'cena', 'Wartość (PLN)']], use_container_width=True)

    # --- TAB: KATEGORIE ---
    with tab_cat:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("📂 Nowa Grupa Towarowa")
            with st.form("kat_add"):
                n_k = st.text_input("Nazwa kategorii")
                o_k = st.text_input("Opis (opcjonalnie)")
                if st.form_submit_button("Dodaj kategorię"):
                    supabase.table(get_table_name("kategorie")).insert({"nazwa": n_k, "opis": o_k}).execute()
                    st.rerun()
        
        with cl2:
            st.subheader("🗑️ Zarządzaj listą kategorii")
            if kat_raw:
                k_del = st.selectbox("Wybierz kategorię do usunięcia", options=[k['nazwa'] for k in kat_raw])
                if st.button("Usuń bezpowrotnie"):
                    id_k = next(k['id'] for k in kat_raw if k['nazwa'] == k_del)
                    try:
                        supabase.table(get_table_name("kategorie")).delete().eq("id", id_k).execute()
                        st.rerun()
                    except:
                        st.error("Nie można usunąć! Kategoria zawiera produkty.")
