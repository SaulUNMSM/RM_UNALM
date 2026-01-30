import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

# Configuración de la página
st.set_page_config(page_title="Suite de Ingeniería: Esfuerzos y Rosetas", layout="wide")

# --- CLASE PARA EL PDF ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte de Ingenieria Mecanica', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 10, body)
        self.ln()

def main():
    st.title("🧪 Suite de Ingeniería: Esfuerzos y Rosetas")
    st.markdown("Herramienta dual: Análisis teórico de esfuerzos y procesamiento experimental de rosetas de deformación.")

    # --- BARRA LATERAL: SELECCIÓN DE MODO ---
    st.sidebar.header("⚙️ Configuración")
    modo = st.sidebar.selectbox("Modo de Análisis", ["Teórico (Ingresar Esfuerzos)", "Experimental (Roseta de Deformación)"])
    
    st.sidebar.markdown("---")
    st.sidebar.header("🧱 Material")
    E_GPa = st.sidebar.number_input("Módulo de Young (E) [GPa]", value=200.0)
    nu = st.sidebar.number_input("Coeficiente de Poisson (ν)", value=0.3)
    sigma_yield = st.sidebar.number_input("Límite de Fluencia (σy) [MPa]", value=250.0)

    # Variables de estado que calcularemos (inicialización)
    sigma_x, sigma_y, tau_xy = 0.0, 0.0, 0.0
    epsilon_x, epsilon_y, gamma_xy = 0.0, 0.0, 0.0
    
    # Constantes calculadas
    E_MPa = E_GPa * 1000
    G_MPa = E_MPa / (2 * (1 + nu))

    # --- LÓGICA SEGÚN MODO ---
    if modo == "Teórico (Ingresar Esfuerzos)":
        st.sidebar.markdown("---")
        st.sidebar.header("1. Estado de Esfuerzos")
        sigma_x = st.sidebar.number_input("Esfuerzo Normal X (σx) [MPa]", value=50.0)
        sigma_y = st.sidebar.number_input("Esfuerzo Normal Y (σy) [MPa]", value=-10.0)
        tau_xy = st.sidebar.number_input("Esfuerzo Cortante (τxy) [MPa]", value=40.0)
        
        # Calcular deformaciones asociadas (Ley de Hooke directa)
        epsilon_x = (1/E_MPa) * (sigma_x - nu * sigma_y)
        epsilon_y = (1/E_MPa) * (sigma_y - nu * sigma_x)
        gamma_xy = tau_xy / G_MPa

    else: # MODO EXPERIMENTAL (ROSETA)
        st.sidebar.markdown("---")
        st.sidebar.header("1. Lecturas de Roseta (µε)")
        tipo_roseta = st.sidebar.radio("Tipo de Roseta", ["Rectangular (0°, 45°, 90°)", "Delta (0°, 60°, 120°)"])
        
        st.sidebar.info("Ingrese valores en Microstrain (µε)")
        ea_u = st.sidebar.number_input("Galga A (0°) [µε]", value=200.0)
        eb_u = st.sidebar.number_input(f"Galga B ({'45' if 'Rect' in tipo_roseta else '60'}°) [µε]", value=150.0)
        ec_u = st.sidebar.number_input(f"Galga C ({'90' if 'Rect' in tipo_roseta else '120'}°) [µε]", value=-100.0)
        
        # Convertir microstrain a strain unitario
        ea, eb, ec = ea_u * 1e-6, eb_u * 1e-6, ec_u * 1e-6
        
        # Cálculo de deformaciones cartesianas según el tipo
        if "Rectangular" in tipo_roseta:
            epsilon_x = ea
            epsilon_y = ec
            gamma_xy = 2 * eb - (ea + ec)
        else: # Delta
            epsilon_x = ea
            epsilon_y = (1/3) * (2*eb + 2*ec - ea)
            gamma_xy = (2 / np.sqrt(3)) * (eb - ec)
            
        # Calcular Esfuerzos a partir de Deformaciones (Ley de Hooke Generalizada para Esfuerzo Plano)
        # σx = E/(1-v^2) * (εx + v*εy)
        factor = E_MPa / (1 - nu**2)
        sigma_x = factor * (epsilon_x + nu * epsilon_y)
        sigma_y = factor * (epsilon_y + nu * epsilon_x)
        tau_xy = G_MPa * gamma_xy

        # Mostrar qué se calculó
        st.success(f"✅ Conversión Experimental completada: σx = {sigma_x:.1f} MPa, σy = {sigma_y:.1f} MPa")

    # --- BARRA LATERAL: ROTACIÓN ---
    st.sidebar.markdown("---")
    st.sidebar.header("2. Rotación de Análisis")
    theta_deg = st.sidebar.slider("Ángulo θ (grados)", -90.0, 90.0, 0.0)
    theta_rad = np.radians(theta_deg)

    # --- CÁLCULOS COMUNES (MOHR Y FALLA) ---
    # Esfuerzos Principales
    sigma_avg = (sigma_x + sigma_y) / 2
    R = np.sqrt(((sigma_x - sigma_y) / 2)**2 + tau_xy**2)
    sigma_1 = sigma_avg + R
    sigma_2 = sigma_avg - R
    tau_max = R

    # Esfuerzos Rotados
    sigma_x_p = (sigma_x + sigma_y)/2 + (sigma_x - sigma_y)/2 * np.cos(2*theta_rad) + tau_xy * np.sin(2*theta_rad)
    tau_xy_p = -(sigma_x - sigma_y)/2 * np.sin(2*theta_rad) + tau_xy * np.cos(2*theta_rad)

    # Criterio Von Mises y FOS
    sigma_vm = np.sqrt(sigma_1**2 - sigma_1*sigma_2 + sigma_2**2)
    fos = sigma_yield / sigma_vm if sigma_vm != 0 else float('inf')

    # --- EXPORTAR ---
    with st.expander("📂 Exportar Resultados"):
        if st.button("📄 Generar PDF del Análisis"):
            pdf_bytes = create_pdf(modo, sigma_x, sigma_y, tau_xy, sigma_1, sigma_2, tau_max, sigma_vm, fos, E_GPa, nu)
            st.download_button("⬇️ Descargar PDF", pdf_bytes, "analisis_ingenieria.pdf", "application/pdf")

    # --- VISUALIZACIÓN ---
    tab1, tab2, tab3 = st.tabs(["🔴 Esfuerzos (Mohr)", "🔵 Deformaciones (Calculadas)", "🟢 Criterio de Falla"])

    # TAB 1: MOHR
    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("σ1 (Principal Mayor)", f"{sigma_1:.2f} MPa")
            st.metric("σ2 (Principal Menor)", f"{sigma_2:.2f} MPa")
            st.metric("τ_max (Cortante Max)", f"{tau_max:.2f} MPa")
            st.markdown(f"**Ángulo Principal:** {np.degrees(0.5*np.arctan2(2*tau_xy, sigma_x-sigma_y)):.1f}°")
        with c2:
            fig = dibujar_mohr(sigma_avg, R, sigma_x, sigma_y, tau_xy, sigma_x_p, tau_xy_p)
            st.plotly_chart(fig, use_container_width=True)

    # TAB 2: DEFORMACIONES
    with tab2:
        st.markdown(f"**Origen de datos:** {modo}")
        c1, c2, c3 = st.columns(3)
        c1.metric("εx", f"{epsilon_x*1e6:.1f} µε")
        c2.metric("εy", f"{epsilon_y*1e6:.1f} µε")
        c3.metric("γxy", f"{gamma_xy*1e6:.1f} µrad")
        
        # Deformaciones Principales
        ep_avg = (epsilon_x + epsilon_y) / 2
        ep_R = np.sqrt(((epsilon_x - epsilon_y)/2)**2 + (gamma_xy/2)**2)
        ep_1 = ep_avg + ep_R
        ep_2 = ep_avg - ep_R
        
        st.markdown("#### Deformaciones Principales")
        st.latex(r"\epsilon_1 = " + f"{ep_1*1e6:.1f} " + r"\mu\epsilon \quad \epsilon_2 = " + f"{ep_2*1e6:.1f} " + r"\mu\epsilon")

    # TAB 3: FALLA
    with tab3:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Esfuerzo Von Mises", f"{sigma_vm:.2f} MPa")
            delta_val = fos - 1
            color = "normal" if fos > 1.5 else "off" if fos > 1 else "inverse"
            st.metric("Factor de Seguridad (FoS)", f"{fos:.2f}", delta=f"{delta_val:.2f}", delta_color=color)
            
            if fos < 1: st.error("❌ FALLA ESTRUCTURAL")
            elif fos < 1.2: st.warning("⚠️ CRÍTICO")
            else: st.success("✅ DISEÑO SEGURO")
        with col_f2:
            fig_vm = dibujar_von_mises(sigma_yield, sigma_1, sigma_2)
            st.plotly_chart(fig_vm, use_container_width=True)

# --- FUNCIONES GRÁFICAS Y REPORTE ---
def dibujar_mohr(center, radius, sx, sy, txy, sx_p, txy_p):
    theta = np.linspace(0, 2*np.pi, 360)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=center + radius * np.cos(theta), y=radius * np.sin(theta), mode='lines', name='Círculo Mohr'))
    fig.add_trace(go.Scatter(x=[sx, sy], y=[txy, -txy], mode='lines+markers', name='Estado Actual', marker=dict(size=10, color='red')))
    sy_p = 2*center - sx_p
    fig.add_trace(go.Scatter(x=[sx_p, sy_p], y=[txy_p, -txy_p], mode='lines+markers', name='Rotado', line=dict(dash='dot', color='green')))
    fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1), height=400, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="σ (MPa)", yaxis_title="τ (MPa)")
    return fig

def dibujar_von_mises(syield, s1, s2):
    # Elipse simple rotada 45 grados para representacion visual
    fig = go.Figure()
    theta_ell = np.linspace(0, 2*np.pi, 100)
    major = np.sqrt(2) * syield
    minor = np.sqrt(2/3) * syield
    x_ell = (major * np.cos(theta_ell) * np.cos(np.pi/4) - minor * np.sin(theta_ell) * np.sin(np.pi/4))
    y_ell = (major * np.cos(theta_ell) * np.sin(np.pi/4) + minor * np.sin(theta_ell) * np.cos(np.pi/4))
    
    fig.add_trace(go.Scatter(x=x_ell, y=y_ell, fill='toself', fillcolor='rgba(255,0,0,0.1)', line=dict(color='red'), name='Fluencia'))
    fig.add_trace(go.Scatter(x=[s1], y=[s2], mode='markers', marker=dict(size=12, color='black'), name='Estado'))
    fig.update_layout(title="Von Mises", xaxis_title="σ1", yaxis_title="σ2", yaxis=dict(scaleanchor="x", scaleratio=1))
    return fig

def create_pdf(mode, sx, sy, txy, s1, s2, tmax, svm, fos, E, nu):
    pdf = PDFReport()
    pdf.add_page()
    pdf.chapter_title(f"1. Resumen de Analisis ({mode})")
    pdf.chapter_body(f"Modulo Young: {E} GPa | Poisson: {nu}")
    pdf.chapter_title("2. Estado de Esfuerzos Calculado")
    pdf.chapter_body(f"Sigma X: {sx:.2f} MPa\nSigma Y: {sy:.2f} MPa\nTau XY: {txy:.2f} MPa")
    pdf.chapter_title("3. Esfuerzos Principales")
    pdf.chapter_body(f"Sigma 1: {s1:.2f} MPa\nSigma 2: {s2:.2f} MPa\nTau Max: {tmax:.2f} MPa")
    pdf.chapter_title("4. Seguridad")
    pdf.chapter_body(f"Von Mises: {svm:.2f} MPa\nFoS: {fos:.2f}\n{'SEGURO' if fos > 1 else 'FALLA'}")
    return pdf.output(dest='S').encode('latin-1')

if __name__ == '__main__':
    main()

# streamlit run Esfuerzo_plano.py