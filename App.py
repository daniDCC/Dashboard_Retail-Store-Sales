# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Carga de datos
df = pd.read_csv("retail_store_sales_clean.csv")
df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')

# CONFIG PAGE & THEME
st.set_page_config(page_title="Dashboard de Tienda Minorista", layout="wide")
px.defaults.template = "plotly_white"

# SIDEBAR DE FILTROS
st.sidebar.header("Filtros")
min_date = df["Transaction Date"].dt.date.min()
max_date = df["Transaction Date"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

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

# FILTRADO y columnas auxiliares
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

# KPIs
st.title("Dashboard de Tienda Minorista")
c1, c2, c3, c4, c5 = st.columns(5)

total_sales = df_filt["Total Spent"].sum()
total_sales_online = df_filt[df_filt["Location"] == "Online"]["Total Spent"].sum()
total_sales_instore = df_filt[df_filt["Location "] == "In-Store"]["Total Spent"].sum()
avg_ticket  = df_filt["Total Spent"].mean() if not df_filt.empty else 0
total_qty   = df_filt["Quantity"].sum()

c1.metric("Ventas Totales",    f"${total_sales:,.0f}")
c2.metric("Ventas Online",     f"${total_sales_online:,.0f}")
c3.metric("Ventas In-Store",   f"${total_sales_instore:,.0f}")
c4.metric("Ticket Promedio",   f"${avg_ticket:,.2f}")
c5.metric("Cantidad Vendida",  f"{total_qty:,.0f}")

# PREPARAR DATOS DE TENDENCIAS Y CANAL
freq = "D"

# Tendencias
records_time = []
for period, grp in df_filt.groupby(pd.Grouper(key="Transaction Date", freq=freq)):
    if grp.empty: continue
    records_time.append({
        "Transaction Date": grp["Transaction Date"].max(),
        "Total Spent": grp["Total Spent"].sum()
    })
df_time = pd.DataFrame(records_time).sort_values("Transaction Date")

# online o in-store
records_chan = []
for (period, canal), grp in df_filt.groupby([pd.Grouper(key="Transaction Date", freq=freq), "Channel"]):
    if grp.empty: continue
    records_chan.append({
        "Transaction Date": grp["Transaction Date"].max(),
        "Channel": canal,
        "Total Spent": grp["Total Spent"].sum()
    })
df_ch_t = pd.DataFrame(records_chan).sort_values(["Channel","Transaction Date"])

# GRAFICOS LADO A LADO
col1, col2 = st.columns(2)

with col1:
    st.subheader("Ventas")
    fig_sales = px.line(
        df_time,
        x="Transaction Date",
        y="Total Spent",
        labels={"Transaction Date":"Fecha","Total Spent":"Ventas ($)"},
        title=f"Evolución de las Ventas",
        hover_data={"Total Spent":":.2f"}
    )
    st.plotly_chart(fig_sales, use_container_width=True)

with col2:
    st.subheader("")
    fig_ch_t = px.line(
        df_ch_t,
        x="Transaction Date",
        y="Total Spent",
        color="Channel",
        labels={"Transaction Date":"Fecha","Total Spent":"Ventas ($)"},
        title=f"Evolución de las Ventas por Ubicación"
    )
    st.plotly_chart(fig_ch_t, use_container_width=True)

# Ventas por Categoría
st.header("Ventas por Categoría")
df_cat = df_filt.groupby("Category")["Total Spent"].sum().sort_values().reset_index()
fig_cat = px.bar(
    df_cat,
    x="Total Spent",
    y="Category",
    orientation="h",
    labels={"Total Spent":"Ventas ($)","Category":"Categoría"}
)
st.plotly_chart(fig_cat, use_container_width=True)

# Botón de descarga
csv = df_filt.to_csv(index=False).encode('utf-8')
st.download_button(
    "Descargar datos filtrados",
    data=csv,
    file_name="ventas_filtradas.csv",
    mime="text/csv"
)
