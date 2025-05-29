# **Visualizaciones**

# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Retail Sales Dashboard", layout="wide")

# 2. Carga de datos
df = pd.read_csv("retail_store_sales_clean.csv")
# Conversión de “Transaction Date” a datetime
df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')

# Ordenar todo el DataFrame por fecha
df = df.sort_values('Transaction Date')

# 3. Sidebar de filtros
st.sidebar.header("Filtros")

# 3.1 Rango de fechas (desde la primera hasta la última transacción)
min_date = df["Transaction Date"].dt.date.min()
max_date = df["Transaction Date"].dt.date.max()
start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 3.2 Categorías (con opción "Todas")
all_categories = df["Category"].unique().tolist()
cat_options = ["Todas"] + all_categories
selected_categories = st.sidebar.multiselect(
    "Categorías",
    options=cat_options,
    default=["Todas"]
)
if "Todas" not in selected_categories:
    categories_filter = selected_categories
else:
    categories_filter = all_categories

# 3.3 Método de pago (con opción "Todos")
all_payments = df["Payment Method"].unique().tolist()
pay_options = ["Todos"] + all_payments
selected_payments = st.sidebar.multiselect(
    "Método de pago",
    options=pay_options,
    default=["Todos"]
)
if "Todos" not in selected_payments:
    payments_filter = selected_payments
else:
    payments_filter = all_payments

# 3.4 Ubicaciones (con opción "Todas")
all_locations = df["Location"].unique().tolist()
loc_options = ["Todas"] + all_locations
selected_locations = st.sidebar.multiselect(
    "Ubicación",
    options=loc_options,
    default=["Todas"]
)
if "Todas" not in selected_locations:
    locations_filter = selected_locations
else:
    locations_filter = all_locations

# 3.5 Nivel de agregación temporal (incluye Annual)
agg_option = st.sidebar.radio(
    "Agregación temporal",
    ("Diaria", "Semanal", "Mensual", "Anual")
)

# 4. Filtrado del DataFrame
mask = (
    (df["Transaction Date"].dt.date >= start_date) &
    (df["Transaction Date"].dt.date <= end_date) &
    (df["Category"].isin(categories_filter)) &
    (df["Payment Method"].isin(payments_filter)) &
    (df["Location"].isin(locations_filter))
)
df_filt = df.loc[mask].copy()

# Asegurarnos de que permanece ordenado
df_filt = df_filt.sort_values("Transaction Date")

# 5. Agregación temporal
if agg_option == "Diaria":
    df_time = df_filt.resample("D", on="Transaction Date")["Total Spent"].sum().reset_index()
elif agg_option == "Semanal":
    df_time = df_filt.resample("W-MON", on="Transaction Date")["Total Spent"].sum().reset_index()
elif agg_option == "Mensual":
    df_time = df_filt.resample("M", on="Transaction Date")["Total Spent"].sum().reset_index()
else:  # Anual
    df_time = df_filt.resample("A", on="Transaction Date")["Total Spent"].sum().reset_index()

# 6. Visualizaciones
st.title("📊 Retail Store Sales Dashboard")

# 6.1 Serie temporal de ventas
st.subheader("Ventas Totales a lo largo del tiempo")
fig_time = px.line(
    df_time,
    x="Transaction Date",
    y="Total Spent",
    labels={"Transaction Date": "Fecha", "Total Spent": "Ventas ($)"},
    title=f"Ventas {agg_option.lower()} agregadas"
)
st.plotly_chart(fig_time, use_container_width=True)

# 6.2 Ventas por categoría
st.subheader("Ventas por Categoría")
df_cat = df_filt.groupby("Category")["Total Spent"].sum().sort_values(ascending=False).reset_index()
fig_cat = px.bar(
    df_cat,
    x="Category",
    y="Total Spent",
    labels={"Total Spent": "Ventas ($)", "Category": "Categoría"},
    title="Total Vendido por Categoría"
)
st.plotly_chart(fig_cat, use_container_width=True)

# 6.3 Distribución de Métodos de Pago
st.subheader("Métodos de Pago")
df_pay = df_filt["Payment Method"].value_counts().reset_index()
df_pay.columns = ["Payment Method", "Count"]
fig_pay = px.pie(
    df_pay,
    names="Payment Method",
    values="Count",
    title="Participación de Métodos de Pago"
)
st.plotly_chart(fig_pay, use_container_width=True)

# 6.4 Comparación In-Store vs Online
st.subheader("Comparación: In-Store vs Online")
# Crear etiqueta
df_filt['Channel'] = df_filt['Location'].apply(lambda x: 'Online' if x.lower() == 'online' else 'In-Store')
df_chan = df_filt.groupby("Channel")["Total Spent"].sum().reset_index()
fig_chan = px.bar(
    df_chan,
    x="Channel",
    y="Total Spent",
    labels={"Total Spent": "Ventas ($)", "Channel": "Canal"},
    title="Ventas por Canal"
)
st.plotly_chart(fig_chan, use_container_width=True)

# 7. Tabla de datos filtrados (opcional)
with st.expander("Ver datos filtrados"):
    st.dataframe(df_filt.reset_index(drop=True))