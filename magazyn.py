import streamlit as st
from supabase import create_client, Client

# --- Połączenie ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- Funkcje Kategorii ---
def pobierz_kategorie():
    # Próba pobrania tabeli 'Kategorie'
    try:
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return res.data
    except Exception as e:
        st.error(f"Błąd pobierania kategorii: {e}")
        return []

def dodaj_kategorie(nazwa, opis):
    data = {"nazwa": nazwa, "opis": opis}
    supabase.table("Kategorie").insert(data).execute()

# --- Funkcje Produktów ---
def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
    data = {
        "nazwa": nazwa,
        "liczba": int(liczba),
        "cena": float(cena),
        "kategoria_id": int(kategoria_id)
    }
    supabase.table("produkty").insert(data).execute()

# --- Interfejs Użytkownika ---
st.title("📦 Zarządzanie Magazynem")

# --- SEKCJA 1: DODAWANIE KATEGORII ---
with st.expander("➕ Dodaj nową kategorię"):
    with st.form("form_kategoria", clear_on_submit=True):
        nowa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis kategorii")
        if st.form_submit_button("Zapisz kategorię"):
            if nowa_kat:
                dodaj_kategorie(nowa_kat, opis_kat)
                st.success("Dodano kategorię!")
                st.rerun()

st.divider()

# --- SEKCJA 2: DODAWANIE PRODUKTU ---
kategorie_data = pobierz_kategorie()
if kategorie_data:
    opcje_kat = {item['nazwa']: item['id'] for item in kategorie_data}
    
    with st.form("form_produkt", clear_on_submit=True):
        st.subheader("Nowy produkt")
        col1, col2 = st.columns(2)
        with col1:
            n_produkt = st.text_input("Nazwa produktu")
            l_produkt = st.number_input("Ilość", min_value=0)
        with col2:
            c_produkt = st.number_input("Cena", min_value=0.0)
            k_produkt = st.selectbox("Kategoria", options=list(opcje_kat.keys()))
        
        if st.form_submit_button("Dodaj produkt"):
            dodaj_produkt(n_produkt, l_produkt, c_produkt, opcje_kat[k_produkt])
            st.success("Dodano produkt!")
            st.rerun()
else:
    st.warning("Najpierw dodaj kategorię, aby móc przypisać do niej produkty.")

# --- SEKCJA 3: PODGLĄD ---
st.subheader("📋 Stan Magazynu")
try:
    # Zgodnie ze schematem pobieramy produkty i nazwę kategorii przez klucz obcy
    produkty = supabase.table("produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()
    if produkty.data:
        st.dataframe(produkty.data, use_container_width=True)
except:
    st.info("Baza produktów jest pusta.")
