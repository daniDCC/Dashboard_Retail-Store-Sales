# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CACHING DE DATOS PESADOS
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    return df.sort_values('Transaction Date')

df = load_data("retail_store_sales_clean.csv")

# 2. CONFIG PAGE & THEME
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide")
px.defaults.template = "plotly_white"

# 3. SIDEBAR DE FILTROS
st.sidebar.header("Filtros")
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

# Categorías
all_categories = df["Category"].unique().tolist()
sel_cat = st.sidebar.multiselect("Categorías", ["Todas"] + all_categories, ["Todas"])
categories_filter = all_categories if "Todas" in sel_cat else sel_cat

# Métodos de pago
all_payments = df["Payment Method"].unique().tolist()
sel_pay = st.sidebar.multiselect("Método de pago", ["Todos"] + all_payments, ["Todos"])
payments_filter = all_payments if "Todos" in sel_pay else sel_pay

# Ubicaciones
all_locations = df["Location"].unique().tolist()
sel_loc = st.sidebar.multiselect("Ubicación", ["Todas"] + all_locations, ["Todas"])
locations_filter = all_locations if "Todas" in sel_loc else sel_loc

# 4. FILTRADO y columnas auxiliares
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

# 5. KPIs
st.title("📊 Retail Store Sales Dashboard")
c1, c2, c3, c4 = st.columns(4)
total_sales = df_filt["Total Spent"].sum()
avg_ticket  = df_filt["Total Spent"].mean() if not df_filt.empty else 0
total_qty   = df_filt["Quantity"].sum()
pct_disc    = df_filt["HasDiscount"].mean() * 100 if not df_filt.empty else 0
c1.metric("🔖 Ventas Totales", f"${total_sales:,.0f}")
c2.metric("🎫 Ticket Promedio", f"${avg_ticket:,.2f}")
c3.metric("📦 Cantidad Vendida", f"{total_qty:,.0f}")
c4.metric("% Con Descuento", f"{pct_disc:.1f}%")

# --- TENDENCIAS TEMPORALES (gráfico con dropdown) ---
st.header("1. Tendencias Temporales")
freq_map = {"Diaria": "D", "Semanal": "W-MON", "Mensual": "M", "Anual": "A"}
agg_data = {}
for label, freq in freq_map.items():
    if label == "Anual":
        df_filt['Year'] = df_filt['Transaction Date'].dt.year
        tmp = (
            df_filt
            .groupby('Year')
            .agg({"Total Spent": "sum", "Quantity": "sum"})
            .reset_index()
        )
        tmp['Transaction Date'] = pd.to_datetime(tmp['Year'].astype(str) + "-01-01")
        agg_data[label] = tmp[['Transaction Date', 'Total Spent', 'Quantity']]
    else:
        tmp = df_filt.resample(freq, on="Transaction Date").agg({"Total Spent": "sum", "Quantity": "sum"}).reset_index()
        agg_data[label] = tmp

fig = go.Figure()
for idx, (label, df_agg) in enumerate(agg_data.items()):
    fig.add_trace(go.Scatter(
        x=df_agg["Transaction Date"],
        y=df_agg["Total Spent"],
        name=f"Ventas ({label})",
        visible=(label == agg_option)
    ))
buttons = []
for idx, label in enumerate(freq_map.keys()):
    vis = [i == idx for i in range(len(freq_map))]
    buttons.append(dict(
        label=label,
        method="update",
        args=[{"visible": vis},
              {"title": f"Ventas agregadas ({label.lower()})"}]
    ))
fig.update_layout(
    updatemenus=[dict(
        active=list(freq_map.keys()).index(agg_option),
        buttons=buttons,
        x=0, y=1.2, xanchor="left", yanchor="top"
    )],
    title=f"Ventas agregadas ({agg_option.lower()})",
    xaxis_title="Fecha", yaxis_title="Ventas ($)"
)
st.plotly_chart(fig, use_container_width=True)

# 7. EVOLUCIÓN DE VENTAS POR CANAL (dropdown igual)
st.header("1. Evolución de Ventas por Canal")
# Pre-agregaciones por canal y frecuencia
agg_chan = {}
channels = df_filt["Channel"].unique().tolist()
for label, freq in freq_map.items():
    df_tmp = (
        df_filt
        .groupby([pd.Grouper(key="Transaction Date", freq=freq), "Channel"])
        ["Total Spent"]
        .sum()
        .reset_index()
    )
    agg_chan[label] = df_tmp

# Construcción del figure
fig_ch = go.Figure()
for idx, (label, df_agg) in enumerate(agg_chan.items()):
    for canal in channels:
        df_sub = df_agg[df_agg["Channel"] == canal]
        fig_ch.add_trace(go.Scatter(
            x=df_sub["Transaction Date"],
            y=df_sub["Total Spent"],
            name=canal,
            visible=(label == agg_option)
        ))

# Botones dropdown
buttons = []
n_ch = len(channels)
for idx, label in enumerate(freq_map.keys()):
    visible = [(i // n_ch) == idx for i in range(len(freq_map) * n_ch)]
    buttons.append(dict(
        label=label,
        method="update",
        args=[{"visible": visible},
              {"title": f"Evolución {label.lower()} de Ventas por Canal"}]
    ))

fig_ch.update_layout(
    updatemenus=[dict(
        active=list(freq_map.keys()).index(agg_option),
        buttons=buttons,
        x=0, y=1.2, xanchor="left", yanchor="top"
    )],
    title=f"Evolución {agg_option.lower()} de Ventas por Canal",
    xaxis_title="Fecha",
    yaxis_title="Ventas ($)"
)
st.plotly_chart(fig_ch, use_container_width=True)

# 6. Ventas por Categoría
st.header("3. Ventas por Categoría")
df_cat = df_filt.groupby("Category")["Total Spent"].sum().sort_values().reset_index()
fig_cat = px.bar(df_cat, x="Total Spent", y="Category", orientation="h",
                 labels={"Total Spent": "Ventas ($)", "Category": "Categoría"})
st.plotly_chart(fig_cat, use_container_width=True)

# 8. Botón de descarga
csv = df_filt.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar datos filtrados", data=csv,
                   file_name="ventas_filtradas.csv", mime="text/csv")
