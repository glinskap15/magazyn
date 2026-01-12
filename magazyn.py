import streamlit as st
from supabase import create_client, Client

# --- Łączenie z bazą przy użyciu Secrets ---
# Adresy URL i klucze pobierane są z ustawień Streamlit Cloud
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Problem z konfiguracją kluczy: {e}")
    st.stop()

# --- Funkcje bazy danych ---

def pobierz_kategorie():
    # Zgodnie ze schematem: tabela 'Kategorie' (duża litera K)
    res = supabase.table("Kategorie").select("id, nazwa").execute()
    return res.data

def dodaj_produkt(nazwa, liczba, cena, kategoria_id):
    # Zgodnie ze schematem: tabela 'produkty' (mała litera p)
    data = {
        "nazwa": nazwa,
        "liczba": int(liczba),
        "cena": float(cena),
        "kategoria_id": int(kategoria_id)
    }
    supabase.table("produkty").insert(data).execute()

# --- Interfejs Streamlit ---

st.title("📦 Zarządzanie Kategoriami i Produktami")

# Pobieranie kategorii do listy wyboru
kategorie = pobierz_kategorie()
opcje_kategorii = {cat['nazwa']: cat['id'] for cat in kategorie}

with st.form("form_produkt", clear_on_submit=True):
    st.subheader("Dodaj nowy produkt")
    
    col1, col2 = st.columns(2)
    with col1:
        nazwa_p = st.text_input("Nazwa produktu")
        liczba_p = st.number_input("Ilość (int8)", min_value=0, step=1)
    
    with col2:
        cena_p = st.number_input("Cena (numeric)", min_value=0.0, format="%.2f")
        # Tu realizujemy relację ze schematu (FK kategoria_id)
        kat_p = st.selectbox("Kategoria", options=list(opcje_kategorii.keys()))

    if st.form_submit_button("Zapisz produkt"):
        if nazwa_p:
            try:
                dodaj_produkt(nazwa_p, liczba_p, cena_p, opcje_kategorii[kat_p])
                st.success(f"Dodano produkt {nazwa_p} do kategorii {kat_p}!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd bazy: {e}")
        else:
            st.warning("Podaj nazwę produktu.")

st.divider()

# --- Wyświetlanie tabeli ---
st.subheader("📋 Lista Produktów")
try:
    # Pobieranie produktów z nazwą kategorii (Join)
    query = supabase.table("produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()
    if query.data:
        st.dataframe(query.data, use_container_width=True)
except Exception as e:
    st.info("Dodaj pierwszy produkt, aby zobaczyć tabelę.")
