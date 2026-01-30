import streamlit as st

# Configuración de la página principal
st.set_page_config(
    page_title="Portafolio de Ingeniería",
    page_icon="👷‍♂️",
    layout="wide"
)

# --- TÍTULO Y PRESENTACIÓN ---
st.title("👷‍♂️ Portafolio de Herramientas de Ingeniería")
st.markdown("### Bienvenido a mi suite de cálculo estructural")

# --- COLUMNAS PARA PRESENTAR LOS MÓDULOS ---
col1, col2 = st.columns(2)

with col1:
    st.info("### 1. Esfuerzo Plano y Rosetas")
    st.markdown("""
    Esta herramienta permite realizar análisis de mecánica de materiales:
    * Cálculo de **Esfuerzos Principales** y Círculo de Mohr.
    * Procesamiento de datos experimentales de **Rosetas de Deformación**.
    * Criterios de falla (**Von Mises**) y reportes PDF.
    
    👈 **Ve a la barra lateral para abrir esta app.**
    """)

with col2:
    st.success("### 2. Otro Programa (Ejemplo)")
    st.markdown("""
    Aquí puedes describir tu segunda herramienta:
    * Análisis de vigas.
    * Dinámica de fluidos.
    * Ciencia de datos.
    
    👈 **Selecciona la segunda opción en el menú.**
    """)

st.markdown("---")
st.subheader("Acerca de este proyecto")
st.markdown("""
Desarrollado en Python utilizando **Streamlit**, **NumPy** y **Plotly**.
El código fuente está disponible en GitHub para uso educativo y profesional.
""")

# Puedes agregar una imagen si tienes una URL o archivo local
# st.image("https://ruta_a_tu_imagen.com/banner.png")