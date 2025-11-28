import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# --- Configuración de la página ---
st.set_page_config(page_title="Dashboard de Procesos", layout="wide")

# --- Cargar datos desde Exc#el ---
#@st.cache_data#
#def cargar_datos():
 #   df = pd.read#_csv("comparativo1.2.csv", encoding="utf-8-sig")
  #  df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"])
   # df["Año"] = df["Fecha inicio"].dt.year
  #  #df["Mes"] = df["Fecha inicio"].dt.month_name(locale="es_ES")
   # df["Día"] = df["Fecha inicio"].dt.day
   # return df

#df = cargar_datos()

archivo=st.file_uploader("sube tu archivo CSV",type=["csv","xlsx"])

def procesar_datos(df):
    df["Fecha inicio"] = pd.to_datetime(df["Fecha inicio"])
    df["Año"] = df["Fecha inicio"].dt.year
    df["Mes"] = df["Fecha inicio"].dt.month_name(locale="es_ES")
    df["Día"] = df["Fecha inicio"].dt.day
    return df

    if archivo is not None:
        if archivo.name.endswith(".csv"):
            df=pd.read_csv(archivo,encoding="utf-8-sig")
        else:
            df=pd.read_excel(archivo)

        df=procesar_datos(df)
        
        st.success("Archivo cargado correctamente")
        st.dataframe(df.head())
    else:
        st.warning("Por favor sube un archivo para continuar")
    
        
st.markdown(
    """
    <h1 style='text-align: center;'>📊 Dashboard de Mesas Operativas</h1>
    """,
    unsafe_allow_html=True
)

# --- Filtros ---
st.markdown("### 🔍 Filtros")
col1, col2, col3, col4 = st.columns(4)

with col1:
    anio_sel = st.multiselect("Selecciona año(s):", sorted(df["Año"].unique()), default=sorted(df["Año"].unique()))
with col2:
    mes_sel = st.multiselect("Selecciona mes(es):", list(df["Mes"].unique()), default=list(df["Mes"].unique()))
with col3:
    dia_sel = st.multiselect("Selecciona día(s):", sorted(df["Día"].unique()), default=sorted(df["Día"].unique()))
with col4:
    mesa_sel = st.selectbox("Selecciona una mesa:", df["Mesa original"].unique())

# --- Aplicar filtros ---
df_filtrado = df[
    (df["Mesa original"] == mesa_sel)
    & (df["Año"].isin(anio_sel))
    & (df["Mes"].isin(mes_sel))
    & (df["Día"].isin(dia_sel))
]

# --- Gráfico 1: Total de folios por día ---
df_diario = (
    df_filtrado.groupby(df_filtrado["Fecha inicio"].dt.date)
    .size()
    .reset_index(name="Total Folios")
)

if df_diario.empty:
    st.warning("⚠️ No hay datos disponibles con los filtros seleccionados.")
else:

    promedio=df_diario["Total Folios"].mean()
    st.metric(label="Promedio diario de folios", value=f"{promedio:.1f}")

    fig1 = px.bar(
        df_diario,
        x="Fecha inicio",
        y="Total Folios",
        text="Total Folios",
        labels={"Fecha inicio": "Fecha", "Total Folios": "Cantidad de folios"},
        template="plotly_white",
    )
    fig1.update_xaxes(
	dtick="Fecha inicio",
	tickformat="%b %d",
	tickangle=45
	)


    fig1.update_layout(title={
        'text': f"{mesa_sel} - Total de folios por día",
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    			     },
    title_font=dict(size=22, color='black', family='Arial')
)

    st.plotly_chart(fig1, use_container_width=True)

#-------------------------------------------------------------------------------------------
# --- Convertir columnas de tiempo a timedelta ---
for col in ["tiempo_espera", "tiempo_ejecucion", "tiempo_total"]:
    if col in df_filtrado.columns:
        df_filtrado[col] = pd.to_timedelta(df_filtrado[col], errors="coerce")

# --- Agrupar por día y calcular promedios ---
df_tiempo = (
    df_filtrado.groupby(df_filtrado["Fecha inicio"].dt.date)[["tiempo_espera", "tiempo_ejecucion", "tiempo_total"]]
    .mean()
    .reset_index()
)

# --- Convertir promedios a minutos (para graficar fácilmente) ---
df_tiempo["tiempo_espera"] = df_tiempo["tiempo_espera"].dt.total_seconds() / 60
df_tiempo["tiempo_ejecucion"] = df_tiempo["tiempo_ejecucion"].dt.total_seconds() / 60
df_tiempo["tiempo_total"] = df_tiempo["tiempo_total"].dt.total_seconds() / 60

# --- Gráfico 2: Línea + área de objetivo ---
if not df_tiempo.empty:
    # Definir objetivo según la mesa
    objetivos = {
        "VALIDACIÓN COMPLETEZ": 50,   # minutos
        "VALIDACIÓN DOCUMENTAL": 40,
        "VALIDACIÓN DOCUMENTAL FACTURA": 15,
        "GENERACIÓN KIT DE FIRMAS": 40,
        "VALIDACIÓN DE CONTRATOS FIRMADOS": 35,
        "CON OBSERVACIÓN": 25,
        "OBSERVACIÓN ACOC": 25,
    }
    objetivo = objetivos.get(mesa_sel.upper(), 50)  # valor por defecto: 50 min



    fig2 = go.Figure()

    # --- Área de objetivo (eje secundario) ---
    fig2.add_trace(
        go.Scatter(
            x=df_tiempo["Fecha inicio"],
            y=[objetivo] * len(df_tiempo),
            fill="tozeroy",
            mode="none",
            name=f"Objetivo ({objetivo} min)",
            fillcolor="rgba(0,150,255,0.15)",
            yaxis="y2"
        )
    )

    # --- Líneas principales ---
    fig2.add_trace(go.Scatter(
        x=df_tiempo["Fecha inicio"], y=df_tiempo["tiempo_espera"],
        mode="lines+markers", name="Tiempo de espera", line=dict(color="#FF5733", width=2)
    ))
    fig2.add_trace(go.Scatter(
        x=df_tiempo["Fecha inicio"], y=df_tiempo["tiempo_ejecucion"],
        mode="lines+markers", name="Tiempo de ejecución", line=dict(color="#33C3FF", width=2)
    ))
    fig2.add_trace(go.Scatter(
        x=df_tiempo["Fecha inicio"], y=df_tiempo["tiempo_total"],
        mode="lines+markers", name="Tiempo total", line=dict(color="#2ECC71", width=3)
    ))

    # --- Configuración de ejes ---

    fig2.update_xaxes(
	dtick="Fecha inicio",
	tickformat="%b %d",
	tickangle=45
	)

    fig2.update_layout(
        title=f"{mesa_sel} - Promedio de tiempos diarios",
        title_x=0.5,
        template="plotly_white",
        xaxis=dict(title="Fecha"),
        yaxis=dict(title="Tiempos (minutos)", side="left"),
        yaxis2=dict(
            overlaying="y",
            side="right",
            range=[0, objetivo * 1.2],  # un poco más arriba del objetivo
            showgrid=False,
            visible=False  # ocultamos el eje secundario
        ),
        legend=dict(orientation="h", y=-0.2, x=0.3)
    )

    st.plotly_chart(fig2, use_container_width=True)

else:
    st.warning("⚠️ No hay datos disponibles para los tiempos promedio.")


# --- Gráfico 3: Distribución de Cumplimiento (Gráfico de Dona) ---

if not df_filtrado.empty:
    # Agrupamos por categoría de cumplimiento
    df_cumplimiento = df_filtrado["Cumplimiento"].value_counts().reset_index()
    df_cumplimiento.columns = ["Cumplimiento", "Cantidad"]

    # Definimos colores según la categoría
    colores_cumplimiento = {
        "VF": "#006400",  # verde fuerte
        "VN": "#00B050",  # verde normal
        "VL": "#99FF99",  # verde limón
        "A": "#FFFF00",   # amarillo
        "N": "#FFA500",   # naranja
        "R": "#FF0000"    # rojo
    }

    # Gráfico de dona
    fig3 = px.pie(
        df_cumplimiento,
        values="Cantidad",
        names="Cumplimiento",
        color="Cumplimiento",
        color_discrete_map=colores_cumplimiento,
        hole=0.5,  # esto convierte el pastel en una dona
        title=f"Distribución de cumplimiento - {mesa_sel}"
    )

    fig3.update_traces(
        textinfo="percent+label",
        textfont_size=14
    )

    fig3.update_layout(
        title_x=0.5,
        showlegend=True,
        legend_title_text="Categoría",
        legend=dict(orientation="h", y=-0.1, x=0.25)
    )

    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("⚠️ No hay datos disponibles para graficar el cumplimiento.")

