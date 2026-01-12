import streamlit as st
from supabase import create_client, Client

# --- Konfiguracja Połączenia Supabase ---
# W wersji produkcyjnej użyj st.secrets (https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
URL = "TWOJ_SUPABASE_URL"
KEY = "TWOJ_SUPABASE_ANON_KEY"

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

# --- Funkcje Obsługi Bazy Danych ---

def get_categories():
    """Pobiera listę wszystkich kategorii."""
    response = supabase.table("Kategorie").select("*").execute()
    return response.data

def add_product(nazwa, liczba, cena, kategoria_id):
    """Dodaje nowy produkt powiązany z kategorią."""
    data = {
        "nazwa": nazwa,
        "liczba": liczba,
        "cena": cena,
        "kategoria_id": kategoria_id
    }
    supabase.table("Produkty").insert(data).execute()
    st.success(f"Dodano produkt: {nazwa}")

# --- Interfejs Użytkownika ---

st.title("📦 Zarządzanie Magazynem (Supabase)")

# Pobieramy kategorie do selectboxa
kategorie = get_categories()
kategorie_dict = {cat['nazwa']: cat['id'] for cat in kategorie}

# --- Formularz Dodawania Produktu ---
st.header("➕ Dodaj Nowy Produkt")

with st.form("add_product_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nazwa = st.text_input("Nazwa produktu")
        liczba = st.number_input("Liczba (szt.)", min_value=0, step=1)
    
    with col2:
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        # Tutaj wybieramy kategorię na podstawie relacji ze schematu
        wybrana_kat_nazwa = st.selectbox("Kategoria", options=list(kategorie_dict.keys()))
    
    submit = st.form_submit_button("Zapisz w bazie")

    if submit:
        if nazwa and wybrana_kat_nazwa:
            kat_id = kategorie_dict[wybrana_kat_nazwa]
            add_product(nazwa, liczba, cena, kat_id)
        else:
            st.error("Wypełnij wszystkie pola!")

st.divider()

# --- Widok Tabeli ---
st.header("📋 Stan Magazynu")
# Pobieramy produkty wraz z danymi o kategoriach (Join)
response = supabase.table("Produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()

if response.data:
    # Formatowanie danych do ładnej tabeli
    formatted_data = [
        {
            "Produkt": p['nazwa'],
            "Ilość": p['liczba'],
            "Cena": f"{p['cena']} zł",
            "Kategoria": p['Kategorie']['nazwa'] if p['Kategorie'] else "Brak"
        } for p in response.data
    ]
    st.dataframe(formatted_data, use_container_width=True)
else:
    st.info("Brak produktów w bazie danych.")
