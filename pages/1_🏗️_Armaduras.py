import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# --- Configuración de la página ---
st.set_page_config(page_title="Análisis de Armaduras 2D", layout="wide")

st.title("🔧 Calculadora de Armaduras 2D")
st.write("Esta aplicación utiliza el método matricial de la rigidez para analizar armaduras 2D.")
st.success("✅ OJO: los nodos empiezan en fila cero.")

# --- Columnas para la entrada de datos ---
col1, col2 = st.columns(2)

with col1:
    st.header("1. Definir Nodos")
    # Usamos el editor de datos de Streamlit para una entrada de tabla interactiva
    nodos_df = st.data_editor(
        pd.DataFrame(
            [
                {"x": 0.0, "y": 0.0, "apoyo_x": True, "apoyo_y": True},
                {"x": 4.0, "y": 3.0, "apoyo_x": False, "apoyo_y": False},
                {"x": 8.0, "y": 0.0, "apoyo_x": False, "apoyo_y": True},
            ],
            columns=["x", "y", "apoyo_x", "apoyo_y"]
        ),
        num_rows="dynamic",
        key="nodos"
    )

    st.header("2. Definir Miembros")
    miembros_df = st.data_editor(
        pd.DataFrame(
            [
                {"nodo_inicio": 0, "nodo_fin": 1, "Area (A)": 0.01, "Modulo (E)": 2.1e11},
                {"nodo_inicio": 1, "nodo_fin": 2, "Area (A)": 0.01, "Modulo (E)": 2.1e11},
            ],
            columns=["nodo_inicio", "nodo_fin", "Area (A)", "Modulo (E)"]
        ),
        num_rows="dynamic",
        key="miembros"
    )

with col2:
    st.header("3. Definir Cargas")
    cargas_df = st.data_editor(
        pd.DataFrame(
            [
                {"nodo": 1, "fuerza_x": 10000.0, "fuerza_y": -20000.0},
            ],
            columns=["nodo", "fuerza_x", "fuerza_y"]
        ),
        num_rows="dynamic",
        key="cargas"
    )

# --- Botón para iniciar el cálculo ---
if st.button("📊 Calcular Armadura"):

    try:
        # --- Preparación de Datos ---
        coords = nodos_df[['x', 'y']].values
        members = miembros_df[['nodo_inicio', 'nodo_fin']].values
        n_nodos = len(coords)
        n_miembros = len(members)
        gdl = 2 * n_nodos  # Grados de libertad

        # --- Vector de Cargas ---
        F = np.zeros(gdl)
        for index, row in cargas_df.iterrows():
            nodo = int(row['nodo'])
            F[2 * nodo] = row['fuerza_x']
            F[2 * nodo + 1] = row['fuerza_y']

        # --- Matriz de Rigidez Global (K) ---
        K = np.zeros((gdl, gdl))
        fuerzas_internas = np.zeros(n_miembros)

        for i, member in enumerate(members):
            n1_idx, n2_idx = int(member[0]), int(member[1])
            n1, n2 = coords[n1_idx], coords[n2_idx]
            
            E = miembros_df.loc[i, "Modulo (E)"]
            A = miembros_df.loc[i, "Area (A)"]

            dx, dy = n2[0] - n1[0], n2[1] - n1[1]
            L = np.sqrt(dx**2 + dy**2)
            
            c = dx / L  # Coseno director
            s = dy / L  # Seno director

            # Matriz de rigidez local en coordenadas globales
            k_local = (A * E / L) * np.array([
                [ c*c,  c*s, -c*c, -c*s],
                [ c*s,  s*s, -c*s, -s*s],
                [-c*c, -c*s,  c*c,  c*s],
                [-c*s, -s*s,  c*s,  s*s]
            ])
            
            # Ensamblaje en la matriz global
            idx = np.array([2*n1_idx, 2*n1_idx+1, 2*n2_idx, 2*n2_idx+1])
            K[np.ix_(idx, idx)] += k_local

        # --- Aplicar Condiciones de Borde (Apoyos) ---
        restringidos = []
        for index, row in nodos_df.iterrows():
            if row['apoyo_x']: restringidos.append(2 * index)
            if row['apoyo_y']: restringidos.append(2 * index + 1)
        
        libres = np.setdiff1d(range(gdl), restringidos)
        
        K_reducida = K[np.ix_(libres, libres)]
        F_reducido = F[libres]

        # --- Resolver para desplazamientos ---
        U_reducido = np.linalg.solve(K_reducida, F_reducido)
        U = np.zeros(gdl)
        U[libres] = U_reducido

        # --- Calcular Fuerzas y Reacciones ---
        F_global = K @ U
        Reacciones = F_global[restringidos] - F[restringidos]

        for i, member in enumerate(members):
            n1_idx, n2_idx = int(member[0]), int(member[1])
            n1, n2 = coords[n1_idx], coords[n2_idx]
            E = miembros_df.loc[i, "Modulo (E)"]
            A = miembros_df.loc[i, "Area (A)"]
            dx, dy = n2[0] - n1[0], n2[1] - n1[1]
            L = np.sqrt(dx**2 + dy**2)
            c, s = dx / L, dy / L
            
            u_local = np.array([U[2*n1_idx], U[2*n1_idx+1], U[2*n2_idx], U[2*n2_idx+1]])
            
            # Deformación axial
            deformacion = (A * E / L) * (np.array([-c, -s, c, s]) @ u_local)
            fuerzas_internas[i] = deformacion

        # --- Visualización de Resultados ---
        st.header("Resultados del Análisis")
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            # --- Tabla de Fuerzas Internas ---
            st.subheader("Fuerzas en Miembros (N)")
            fuerzas_df = pd.DataFrame({
                "Miembro": [f"{int(m[0])}-{int(m[1])}" for m in members],
                "Fuerza (N)": fuerzas_internas,
                "Estado": ["Tensión" if f > 0 else "Compresión" for f in fuerzas_internas]
            })
            st.dataframe(fuerzas_df)

            # --- Tabla de Reacciones ---
            st.subheader("Reacciones en Apoyos (N)")
            reacciones_dict = {"Nodo": [], "Dirección": [], "Reacción (N)": []}
            for i, idx in enumerate(restringidos):
                reacciones_dict["Nodo"].append(idx // 2)
                reacciones_dict["Dirección"].append("Rx" if idx % 2 == 0 else "Ry")
                reacciones_dict["Reacción (N)"].append(Reacciones[i])
            st.dataframe(pd.DataFrame(reacciones_dict))

        with res_col2:
            # --- Gráfico de la Armadura ---
            st.subheader("Diagrama de la Armadura")
            fig = go.Figure()
            
            # Dibujar miembros coloreados por estado
            for i, member in enumerate(members):
                fuerza = fuerzas_internas[i]
                color = "blue" if fuerza < 0 else "red" # Azul para compresión, Rojo para tensión
                width = 2 + 5 * abs(fuerza) / max(abs(fuerzas_internas)) if max(abs(fuerzas_internas)) > 0 else 2

                n1, n2 = coords[int(member[0])], coords[int(member[1])]
                fig.add_trace(go.Scatter(x=[n1[0], n2[0]], y=[n1[1], n2[1]],
                                         mode='lines', line=dict(color=color, width=width),
                                         hoverinfo='text', hovertext=f"Miembro {i}: {fuerza:.2f} N"))

            # Dibujar nodos
            fig.add_trace(go.Scatter(x=coords[:, 0], y=coords[:, 1], mode='markers+text',
                                     marker=dict(size=15, color='black'),
                                     text=[str(i) for i in range(n_nodos)], textposition="top center"))
            
            fig.update_layout(title_text="Fuerzas: Rojo (Tensión), Azul (Compresión)", showlegend=False)
            st.plotly_chart(fig)
            
    except Exception as e:
        st.error(f"Ocurrió un error en el cálculo: {e}")
        st.warning("Verifica que la armadura sea estable y los datos sean correctos.")
    
# streamlit run Armaduras.py