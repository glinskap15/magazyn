import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- Konfiguracja Wyglądu ---
st.set_page_config(page_title="Magazyn Pro Pink & Blue", layout="wide")

# Niestandardowy CSS dla kolorystyki Pink & Blue
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #fce4ec 0%, #e3f2fd 100%);
    }
    h1, h2, h3 {
        color: #1565C0 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #f06292;
        color: white;
        border-radius: 20px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #0d47a1;
        color: white;
        transform: scale(1.05);
    }
    .stDataFrame {
        border: 2px solid #f06292;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Inicjalizacja Połączenia ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return None

supabase = init_connection()

# --- Funkcje Logiki Magazynowej ---

def pobierz_dane(tabela):
    res = supabase.table(tabela).select("*").execute()
    return res.data

def aktualizuj_ilosc(produkt_id, nowa_ilosc):
    if nowa_ilosc <= 0:
        supabase.table("produkty").delete().eq("id", produkt_id).execute()
    else:
        supabase.table("produkty").update({"liczba": nowa_ilosc}).eq("id", produkt_id).execute()

# --- INTERFEJS UŻYTKOWNIKA ---

st.title("💖 Magazyn Pro: Pink & Blue Edition 💙")

if supabase:
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Wykresy", "📦 Produkty", "📂 Kategorie"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        st.header("Statystyki Magazynu")
        produkty_raw = pobierz_dane("produkty")
        if produkty_raw:
            df = pd.DataFrame(produkty_raw)
            df['wartosc_calkowita'] = df['liczba'] * df['cena']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Suma Produktów", len(df))
            c2.metric("Łączna ilość sztuk", int(df['liczba'].sum()))
            c3.metric("Wartość Magazynu", f"{df['wartosc_calkowita'].sum():,.2f} PLN")
            
            st.subheader("Wizualizacja Stanu")
            st.bar_chart(df.set_index('nazwa')['liczba'])
        else:
            st.info("Brak danych do wyświetlenia wykresów.")

    # --- TAB 2: PRODUKTY (DODAWANIE / USUWANIE ILOŚCI) ---
    with tab2:
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("➕ Nowy Produkt")
            kat_data = pobierz_dane("kategorie")
            opcje_kat = {k['nazwa']: k['id'] for k in kat_data} if kat_data else {}
            
            with st.form("dodaj_prod_form"):
                p_nazwa = st.text_input("Nazwa")
                p_ilosc = st.number_input("Ilość początkowa", min_value=1)
                p_cena = st.number_input("Cena za szt.", min_value=0.0)
                p_kat = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
                if st.form_submit_button("Dodaj do bazy"):
                    supabase.table("produkty").insert({
                        "nazwa": p_nazwa, "liczba": p_ilosc, 
                        "cena": p_cena, "kategoria_id": opcje_kat[p_kat]
                    }).execute()
                    st.rerun()

        with col_right:
            st.subheader("🔄 Zarządzaj Ilością")
            if produkty_raw:
                prod_do_zmiany = st.selectbox("Wybierz produkt", options=[p['nazwa'] for p in produkty_raw])
                wybrany_p = next(p for p in produkty_raw if p['nazwa'] == prod_do_zmiany)
                
                st.write(f"Aktualny stan: **{wybrany_p['liczba']}** szt.")
                ile_zmienic = st.number_input("Ile sztuk dodać/odjąć? (użyj minusa aby odjąć)", value=0)
                
                if st.button("Zastosuj zmianę"):
                    nowa_ilosc = wybrany_p['liczba'] + ile_zmienic
                    aktualizuj_ilosc(wybrany_p['id'], nowa_ilosc)
                    st.success("Zaktualizowano stan magazynowy!")
                    st.rerun()
            
            st.divider()
            st.dataframe(pd.DataFrame(produkty_raw)[['nazwa', 'liczba', 'cena']] if produkty_raw else [])

    # --- TAB 3: KATEGORIE ---
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📂 Dodaj Kategorię")
            with st.form("kat_form"):
                n_kat = st.text_input("Nazwa kategorii")
                o_kat = st.text_input("Opis")
                if st.form_submit_button("Zapisz"):
                    supabase.table("kategorie").insert({"nazwa": n_kat, "opis": o_kat}).execute()
                    st.rerun()
        
        with c2:
            st.subheader("🗑️ Usuń Kategorię")
            if kat_data:
                kat_del = st.selectbox("Kategoria do usunięcia", options=[k['nazwa'] for k in kat_data])
                if st.button("Usuń bezpowrotnie"):
                    try:
                        id_del = next(k['id'] for k in kat_data if k['nazwa'] == kat_del)
                        supabase.table("kategorie").delete().eq("id", id_del).execute()
                        st.rerun()
                    except:
                        st.error("Nie można usunąć kategorii, która ma przypisane produkty!")
