import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- Konfiguracja Wyglądu ---
st.set_page_config(page_title="Magazyn Pastel Pro", layout="wide")

# Definicja kolorów Baby Blue i Pink
BABY_BLUE = "#A2D2FF"
SOFT_PINK = "#FFC8DD"
DEEP_BLUE = "#5E60CE"

# Niestandardowy CSS
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #F8FBFF;
    }}
    h1, h2, h3 {{
        color: {DEEP_BLUE} !important;
    }}
    /* Przyciski w kolorze Baby Blue */
    .stButton>button {{
        background-color: {BABY_BLUE};
        color: white;
        border-radius: 12px;
        border: none;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {SOFT_PINK};
        color: #444;
    }}
    /* Stylizacja metryk */
    [data-testid="stMetricValue"] {{
        color: {DEEP_BLUE};
    }}
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

# --- Funkcje Logiki ---
def pobierz_dane(tabela):
    res = supabase.table(tabela).select("*").execute()
    return res.data

# --- INTERFEJS ---
st.title("☁️ Pastelowy Magazyn: Baby Blue Edition")

if supabase:
    tab1, tab2, tab3 = st.tabs(["📊 Statystyki", "📦 Towary", "📂 Kategorie"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        produkty_raw = pobierz_dane("produkty")
        if produkty_raw:
            df = pd.DataFrame(produkty_raw)
            df['wartosc'] = df['liczba'] * df['cena']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Wszystkie Produkty", len(df))
            c2.metric("Suma sztuk", int(df['liczba'].sum()))
            c3.metric("Wartość (PLN)", f"{df['wartosc'].sum():,.2f}")

            st.subheader("Ilość towarów na stanie")
            
            # Wykres Plotly w kolorze Baby Blue
            fig = px.bar(
                df, 
                x='nazwa', 
                y='liczba',
                color_discrete_sequence=[BABY_BLUE],
                labels={'nazwa': 'Produkt', 'liczba': 'Ilość sztuk'}
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color=DEEP_BLUE,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dodaj produkty, aby zobaczyć wykresy.")

    # --- TAB 2: TOWARY (DODAWANIE I USUWANIE SZTUK) ---
    with tab2:
        col_form, col_view = st.columns([1, 2])
        
        with col_form:
            st.subheader("Dodaj / Zdejmij sztuki")
            if produkty_raw:
                prod_opcje = {p['nazwa']: p for p in produkty_raw}
                wybrany_n = st.selectbox("Wybierz produkt z listy", options=list(prod_opcje.keys()))
                wybrany_p = prod_opcje[wybrany_n]
                
                st.write(f"Obecnie masz: **{wybrany_p['liczba']}** szt.")
                operacja = st.radio("Akcja:", ["Dodaj sztuki", "Odejmij sztuki"])
                ile = st.number_input("Ilość", min_value=1, step=1)
                
                if st.button("Zatwierdź zmianę"):
                    nowa_ilosc = wybrany_p['liczba'] + (ile if operacja == "Dodaj sztuki" else -ile)
                    
                    if nowa_ilosc < 0:
                        st.error("Nie możesz odjąć więcej niż masz!")
                    else:
                        supabase.table("produkty").update({"liczba": nowa_ilosc}).eq("id", wybrany_p['id']).execute()
                        st.success("Zaktualizowano stan!")
                        st.rerun()
            
            st.divider()
            st.subheader("✨ Całkowicie nowy produkt")
            kat_data = pobierz_dane("kategorie")
            if kat_data:
                kat_map = {k['nazwa']: k['id'] for k in kat_data}
                with st.form("new_p"):
                    n = st.text_input("Nazwa produktu")
                    l = st.number_input("Ilość", min_value=0)
                    c = st.number_input("Cena", min_value=0.0)
                    k = st.selectbox("Kategoria", options=list(kat_map.keys()))
                    if st.form_submit_button("Dodaj produkt"):
                        supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria_id": kat_map[k]}).execute()
                        st.rerun()

        with col_view:
            st.subheader("Lista towarów")
            if produkty_raw:
                st.dataframe(df[['nazwa', 'liczba', 'cena', 'wartosc']], use_container_width=True)
            
            # Przycisk usuwania całego produktu
            st.subheader("🗑️ Usuń produkt z bazy")
            if produkty_raw:
                p_usun = st.selectbox("Produkt do całkowitego usunięcia", options=list(prod_opcje.keys()), key="del_prod")
                if st.button("Usuń trwale"):
                    supabase.table("produkty").delete().eq("id", prod_opcje[p_usun]['id']).execute()
                    st.rerun()

    # --- TAB 3: KATEGORIE ---
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Nowa kategoria")
            with st.form("kat_f"):
                nk = st.text_input("Nazwa")
                if st.form_submit_button("Dodaj"):
                    supabase.table("kategorie").insert({"nazwa": nk}).execute()
                    st.rerun()
        with c2:
            st.subheader("Usuń kategorię")
            if kat_data:
                kd = st.selectbox("Wybierz do usunięcia", options=[k['nazwa'] for k in kat_data])
                if st.button("Usuń kategorię"):
                    id_k = next(k['id'] for k in kat_data if k['nazwa'] == kd)
                    supabase.table("kategorie").delete().eq("id", id_k).execute()
                    st.rerun()
