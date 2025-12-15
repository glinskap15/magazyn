import streamlit as st

# --- Konfiguracja Stanu Sesji ---
# Inicjalizacja listy towarów w st.session_state, jeśli jeszcze nie istnieje.
# To zapewni, że lista jest utrzymywana podczas sesji użytkownika.
if 'inventory' not in st.session_state:
    st.session_state.inventory = []

# --- Funkcje Logiki Magazynu ---

def add_item(item_name):
    """Dodaje towar do magazynu, jeśli pole nie jest puste."""
    if item_name.strip():
        # Używamy metody append() do dodania elementu do listy
        st.session_state.inventory.append(item_name.strip())
        st.success(f"Dodano: **{item_name.strip()}** do magazynu.")
    else:
        st.warning("Nazwa towaru nie może być pusta.")

def delete_item(item_name):
    """Usuwa towar z magazynu, jeśli istnieje."""
    try:
        # Używamy metody remove() do usunięcia pierwszego wystąpienia elementu
        st.session_state.inventory.remove(item_name)
        st.success(f"Usunięto: **{item_name}** z magazynu.")
    except ValueError:
        st.error(f"Błąd: Towar **{item_name}** nie został znaleziony w magazynie.")

# --- Interfejs Użytkownika Streamlit ---

st.title("🗃️ Prosty Magazyn (Streamlit + Listy)")
st.caption("Dane są przechowywane tylko na czas bieżącej sesji w pamięci.")

# --- 1. Dodawanie Towaru ---
st.header("➕ Dodaj Towar")
# Pole tekstowe dla nowego towaru
new_item = st.text_input("Wprowadź nazwę nowego towaru:", key="new_item_input")

# Przycisk do dodawania towaru. Używamy lambdy, aby przekazać argument do funkcji.
if st.button("Dodaj do Magazynu"):
    add_item(new_item)
    # Opcjonalnie: wyczyść pole wprowadzania po dodaniu
    # st.session_state.new_item_input = "" 


# --- 2. Aktualny Stan Magazynu ---
st.header("📋 Stan Magazynu")

if not st.session_state.inventory:
    st.info("Magazyn jest pusty.")
else:
    # Wyświetlanie listy towarów
    # Możemy użyć st.dataframe lub st.write
    st.markdown("##### Towary w Magazynie:")
    st.dataframe(
        {"Nazwa Towaru": st.session_state.inventory},
        hide_index=True,
        use_container_width=True
    )

# --- 3. Usuwanie Towaru ---
st.header("🗑️ Usuń Towar")

# Używamy st.selectbox, aby wybrać towar do usunięcia z listy dostępnych
if st.session_state.inventory:
    item_to_delete = st.selectbox(
        "Wybierz towar do usunięcia:",
        options=st.session_state.inventory,
        key="delete_item_select"
    )
    
    # Przycisk do usuwania. 
    # Używamy lambdy, aby przekazać argument do funkcji.
    if st.button("Usuń Wybrany Towar"):
        delete_item(item_to_delete)
        # Rerun aplikacji, aby odświeżyć stan SelectBoxa i listy
        st.rerun() 
else:
    st.info("Brak towarów do usunięcia.")
