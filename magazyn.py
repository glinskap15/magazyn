import streamlit as st
from supabase import create_client, Client

# --- Inicjalizacja połączenia ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji Secrets. Sprawdź ustawienia w Streamlit Cloud.")
        return None

supabase = init_connection()

# --- Funkcje bazy danych ---

def pobierz_kategorie():
    # Zmieniono na 'kategorie' (małe litery), aby uniknąć błędu PGRST205
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return res.data
    except Exception as e:
        # Jeśli nadal błąd, spróbuj 'Kategorie' (niektóre konfiguracje tak wymagają)
        try:
            res = supabase.table("Kategorie").select("id, nazwa").execute()
            return res.data
        except:
            st.error(f"Nie znaleziono tabeli kategorii: {e}")
            return []

def dodaj_kategorie(nazwa, opis):
    try:
        data = {"nazwa": nazwa, "opis": opis}
        supabase.table("kategorie").insert(data).execute()
        st.success(f"Dodano kategorię: {nazwa}")
    except Exception as e:
        st.error(f"Błąd dodawania kategorii: {e}")

def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
    try:
        data = {
            "nazwa": nazwa, 
            "liczba": int(liczba), 
            "cena": float(cena), 
            "kategoria_id": int(kategoria_id)
        }
        supabase.table("produkty").insert(data).execute()
        st.success(f"Dodano produkt: {nazwa}")
    except Exception as e:
        st.error(f"Błąd dodawania produktu: {e}")

# --- Interfejs użytkownika ---
st.title("📦 Zarządzanie Magazynem")

# 1. Zarządzanie Kategoriami
with st.expander("➕ Dodaj nową kategorię"):
    with st.form("form_kat", clear_on_submit=True):
        n_kat = st.text_input("Nazwa kategorii")
        o_kat = st.text_input("Opis")
        if st.form_submit_button("Zapisz kategorię"):
            if n_kat:
                dodaj_kategorie(n_kat, o_kat)
                st.rerun()

st.divider()

# 2. Zarządzanie Produktami
kategorie = pobierz_kategorie()

if kategorie:
    # Tworzymy słownik do łatwego wyboru
    lista_kat = {item['nazwa']: item['id'] for item in kategorie}
    
    with st.form("form_prod", clear_on_submit=True):
        st.subheader("Nowy produkt")
        c1, c2 = st.columns(2)
        with c1:
            prod_nazwa = st.text_input("Nazwa produktu")
            prod_liczba = st.number_input("Ilość", min_value=0, step=1)
        with c2:
            prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            prod_kat = st.selectbox("Wybierz kategorię", options=list(lista_kat.keys()))
        
        if st.form_submit_button("Dodaj produkt"):
            if prod_nazwa:
                dodaj_produkt(prod_nazwa, prod_liczba, prod_cena, lista_kat[prod_kat])
                st.rerun()
else:
    st.info("Baza kategorii jest pusta. Dodaj pierwszą kategorię powyżej.")

st.divider()

# 3. Podgląd tabeli
st.subheader("📋 Stan Magazynu")
try:
    # Pobieranie produktów wraz z nazwą kategorii (Relacja)
    # Używamy małych liter dla nazw tabel
    res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
    if res.data:
        st.dataframe(res.data, use_container_width=True)
    else:
        st.write("Brak produktów w bazie.")
except Exception as e:
    st.info("Dodaj produkty, aby zobaczyć zestawienie.")
