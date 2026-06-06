import streamlit as st
import folium
from streamlit_folium import st_folium
from tta_engine import (
    load_and_process, 
    get_essentials, 
    get_academic, 
    format_for_map, 
    get_navigation_index
)

# Configuración de página
st.set_page_config(page_title="The Traveling Architect", layout="centered")

# Lógica de estado
if 'started' not in st.session_state: st.session_state.started = False
if 'tour_data' not in st.session_state: st.session_state.tour_data = None
if 'mode' not in st.session_state: st.session_state.mode = "Essentials"

# Colores para los días
COLORS = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue']

# --- PANTALLA DE BIENVENIDA ---
if not st.session_state.started:
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image("tta_logo.jpg", width=500)
        if st.button("ENTER", use_container_width=True):
            st.session_state.started = True
            st.rerun()

# --- APLICACIÓN PRINCIPAL ---
else:
    st.title("The Traveling Architect")
    try:
        data_index = get_navigation_index('tta_destinations.json')
        continent = st.selectbox("Continent", list(data_index.keys()))
        country = st.selectbox("Country", list(data_index[continent].keys()))
        city = st.selectbox("City", data_index[continent][country])
        mode = st.radio("Routing Mode", ["Essentials", "Academics"], horizontal=True)

        if st.button("Load Architectural Tour"):
            landmarks = load_and_process('tta_destinations.json', continent, country, city)
            st.session_state.mode = mode
            st.session_state.tour_full = get_academic(landmarks) if mode == "Academics" else get_essentials(landmarks)
            st.session_state.tour_data = st.session_state.tour_full["urban_days"] if mode == "Academics" else st.session_state.tour_full
            st.rerun()

        # --- MOSTRAR RESULTADOS ---
        if st.session_state.tour_data:
            st.write("---")
            st.subheader(f"Itinerary for {city}")
            
            for i, (day_name, day_landmarks) in enumerate(st.session_state.tour_data.items()):
                st.write("---")
                st.subheader(f"{day_name}")
                col_text, col_map = st.columns([1, 2])
                day_points = format_for_map(day_landmarks)
                
                with col_text:
                    st.write("**Route:**")
                    for idx, p in enumerate(day_points, 1):
                        st.write(f"{idx}. {p['name']}")
                
                with col_map:
                    color = COLORS[i % len(COLORS)]
                    m = folium.Map(tiles="cartodbpositron")
                    coords = [[p['lat'], p['lon']] for p in day_points]
                    
                    for p in day_points:
                        # Enlace estilizado y limpio
                        wiki_url = f"https://es.wikipedia.org/wiki/{p['name'].replace(' ', '_')}"
                        popup_html = f"<b>{p['name']}</b><br>Arquitecto: {p['architect']}<br><a href='{wiki_url}' target='_blank' style='color: blue; text-decoration: underline;'>Wikipedia</a>"
                        
                        folium.Marker(
                            [p['lat'], p['lon']], 
                            popup=folium.Popup(popup_html, max_width=200),
                            icon=folium.Icon(color=color, icon='info-sign')
                        ).add_to(m)
                        
                    if coords: m.fit_bounds(coords)
                    st_folium(m, width=400, height=300, key=f"map_{i}", returned_objects=[])

            if st.session_state.mode == "Academics":
                excursions = st.session_state.tour_full.get("excursions", [])
                if excursions:
                    st.write("---")
                    st.subheader("Excursions (Out-of-town)")
                    for ex in excursions:
                        st.write(f"📍 **{ex.get('landmark', 'Unknown')}** - Architect: {ex.get('architect', 'Unknown')}")
            
            if st.button("Reset Search"):
                st.session_state.tour_data = None
                st.rerun()
                
    except Exception as e:
        st.error(f"Error: {e}")