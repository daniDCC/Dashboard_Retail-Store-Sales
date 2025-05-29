# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# 1. CACHING DE DATOS PESADOS
# -------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    return df.sort_values('Transaction Date')

df = load_data("retail_store_sales_clean.csv")

# -------------------------
# 2. CONFIG PAGE & THEME
# -------------------------
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide")
px.defaults.template = "plotly_white"

# -------------------------
# 3. SIDEBAR DE FILTROS
# -------------------------
st.sidebar.header("Filtros")

# 3.1 Rango de fechas
min_date = df["Transaction Date"].dt.date.min()
max_date = df["Transaction Date"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if start_date > end_date:
    st.sidebar.error("⚠️ El rango inicial no puede ser mayor que el final.")

# 3.2 Categorías
all_categories = df["Category"].unique().tolist()
cat_options = ["Todas"] + all_categories
selected_categories = st.sidebar.multiselect("Categorías", options=cat_options, default=["Todas"])
categories_filter = all_categories if "Todas" in selected_categories else selected_categories

# 3.3 Métodos de pago
all_payments = df["Payment Method"].unique().tolist()
pay_options = ["Todos"] + all_payments
selected_payments = st.sidebar.multiselect("Método de pago", options=pay_options, default=["Todos"])
payments_filter = all_payments if "Todos" in selected_payments else selected_payments

# 3.4 Ubicaciones
all_locations = df["Location"].unique().tolist()
loc_options = ["Todas"] + all_locations
selected_locations = st.sidebar.multiselect("Ubicación", options=loc_options, default=["Todas"])
locations_filter = all_locations if "Todas" in selected_locations else selected_locations

# 3.5 (Opcional) seguimos manteniendo agg_option para título inicial
agg_option = st.sidebar.radio("Agregación temporal", ("Diaria", "Semanal", "Mensual", "Anual"))

# -------------------------
# 4. FILTRADO Y COLUMNAS AUX
# -------------------------
mask = (
    (df["Transaction Date"].dt.date >= start_date) &
    (df["Transaction Date"].dt.date <= end_date) &
    (df["Category"].isin(categories_filter)) &
    (df["Payment Method"].isin(payments_filter)) &
    (df["Location"].isin(locations_filter))
)
df_filt = df[mask].copy().sort_values("Transaction Date")
df_filt['DayOfWeek']   = df_filt['Transaction Date'].dt.day_name()
df_filt['Month']       = df_filt['Transaction Date'].dt.month_name()
df_filt['Channel']     = df_filt['Location'].apply(lambda x: 'Online' if x.lower()=='online' else 'In-Store')
df_filt['HasDiscount'] = df_filt['Discount Applied'] > 0

# -------------------------
# 5. KPIs EN LA PARTE SUPERIOR
# -------------------------
st.title("📊 Retail Store Sales Dashboard")
col1, col2, col3, col4 = st.columns(4)
total_sales = df_filt["Total Spent"].sum()
avg_ticket  = df_filt["Total Spent"].mean() if not df_filt.empty else 0
total_qty    = df_filt["Quantity"].sum()
pct_disc     = df_filt["HasDiscount"].mean() * 100 if not df_filt.empty else 0
col1.metric("🔖 Ventas Totales", f"${total_sales:,.0f}")
col2.metric("🎫 Ticket Promedio", f"${avg_ticket:,.2f}")
col3.metric("📦 Cantidad Vendida", f"{total_qty:,.0f}")
col4.metric("% Con Descuento", f"{pct_disc:.1f}%")

# -------------------------
# TENDENCIAS TEMPORALES (UN SOLO GRÁFICO CON DROPDOWN)
# -------------------------
st.header("1. Tendencias Temporales")

# 6.1 Definimos frecuencias
freq_map = {"Diaria": "D", "Semanal": "W-MON", "Mensual": "M", "Anual": "A"}

# 6.2 Pre‐agregamos datos para cada frecuencia
agg_data = {}
for label, freq in freq_map.items():
    tmp = (
        df_filt
        .resample(freq, on="Transaction Date")
        .agg({"Total Spent": "sum", "Quantity": "sum"})
        .reset_index()
    )
    agg_data[label] = tmp

# 6.3 Construimos la figura con un trace por frecuencia (solo uno visible al inicio)
fig = go.Figure()
for idx, (label, df_agg) in enumerate(agg_data.items()):
    fig.add_trace(go.Scatter(
        x=df_agg["Transaction Date"],
        y=df_agg["Total Spent"],
        name=f"Ventas ({label})",
        visible=(label == agg_option)
    ))

# 6.4 Dropdown para cambiar frecuencia
buttons = []
for idx, label in enumerate(freq_map.keys()):
    visible = [i == idx for i in range(len(freq_map))]
    buttons.append(dict(
        label=label,
        method="update",
        args=[{"visible": visible},
              {"title": f"Ventas agregadas ({label.lower()})"}]
    ))

fig.update_layout(
    updatemenus=[dict(active=list(freq_map.keys()).index(agg_option),
                      buttons=buttons,
                      x=0.0, y=1.15,
                      xanchor="left",
                      yanchor="top")],
    title=f"Ventas agregadas ({agg_option.lower()})",
    xaxis_title="Fecha",
    yaxis_title="Ventas ($)"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 8. BOTÓN DE DESCARGA
# -------------------------
csv = df_filt.to_csv(index=False).encode('utf-8')
st.download_button(
    "📥 Descargar datos filtrados",
    data=csv,
    file_name="ventas_filtradas.csv",
    mime="text/csv"
)