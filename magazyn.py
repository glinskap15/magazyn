import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA ---
# Upewnij się, że te dane są poprawne w Twoim panelu Supabase Settings -> API
SUPABASE_URL = "TWOJ_URL" 
SUPABASE_KEY = "TWOJ_ANON_KEY"

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Nie udało się połączyć z Supabase: {e}")
        return None

supabase = init_connection()

# --- FUNKCJE LOGIKI ---

def fetch_categories():
    """Pobiera kategorie z bazy."""
    try:
        # Uwaga: Supabase domyślnie używa nazw tabel wrażliwych na wielkość liter
        res = supabase.table("Kategorie").select("id, nazwa").execute()
        return res.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania kategorii: {e}")
        return []

def add_product_to_db(nazwa, liczba, cena, kategoria_id):
    """Wysyła nowy produkt do bazy."""
    payload = {
        "nazwa": nazwa,
        "liczba": int(liczba),
        "cena": float(cena),
        "kategoria_id": int(kategoria_id)
    }
    try:
        supabase.table("Produkty").insert(payload).execute()
        st.success(f"Pomyślnie dodano: {nazwa}")
    except Exception as e:
        st.error(f"Błąd zapisu: {e}")

# --- INTERFEJS ---

st.title("📦 System Zarządzania Produktami")

if supabase:
    # 1. Pobieranie danych
    categories_data = fetch_categories()
    
    if not categories_data:
        st.warning("Baza kategorii jest pusta. Dodaj najpierw kategorie w panelu Supabase.")
    else:
        # Mapowanie nazwy na ID dla Selectboxa
        cat_options = {item['nazwa']: item['id'] for item in categories_data}

        # 2. Formularz
        with st.form("product_form"):
            st.subheader("Dodaj nowy produkt")
            name = st.text_input("Nazwa produktu")
            quantity = st.number_input("Ilość", min_value=1, step=1)
            price = st.number_input("Cena (PLN)", min_value=0.0, format="%.2f")
            category_name = st.selectbox("Wybierz kategorię", options=list(cat_options.keys()))
            
            submitted = st.form_submit_button("Wyślij do bazy")
            
            if submitted:
                if name:
                    add_product_to_db(name, quantity, price, cat_options[category_name])
                else:
                    st.error("Nazwa produktu jest wymagana!")

    st.divider()

    # 3. Podgląd tabeli (JOIN)
    st.subheader("Aktualna lista produktów")
    try:
        # Pobieramy produkty i nazwę kategorii przez relację FK
        query = supabase.table("Produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()
        if query.data:
            st.write(query.data) # Surowy podgląd dla testu, czy dane płyną
        else:
            st.info("Brak produktów w tabeli.")
    except Exception as e:
        st.error(f"Błąd wyświetlania tabeli: {e}")
