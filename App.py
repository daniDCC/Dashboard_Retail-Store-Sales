# **Vizualizaciones**

# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Retail Sales Dashboard",layout="wide")

# 2. Carga de datos
df = pd.read_csv("retail_store_sales_clean.csv")
# Conversión de “Transaction Date” a datetime
df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')

# 3. Sidebar de filtros
st.sidebar.header("Filtros")

# 3.1 Rango de fechas
min_date = df["Transaction Date"].min().date()
max_date = df["Transaction Date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 3.2 Categorías
all_categories = df["Category"].unique().tolist()
selected_categories = st.sidebar.multiselect(
    "Categorías",
    options=all_categories,
    default=all_categories
)

# 3.3 Método de pago
all_payments = df["Payment Method"].unique().tolist()
selected_payments = st.sidebar.multiselect(
    "Método de pago",
    options=all_payments,
    default=all_payments
)

# 3.4 Ubicaciones
all_locations = df["Location"].unique().tolist()
selected_locations = st.sidebar.multiselect(
    "Ubicación",
    options=all_locations,
    default=all_locations
)

# 3.5 Nivel de agregación temporal
agg_option = st.sidebar.radio(
    "Agregación temporal",
    ("Diaria", "Semanal", "Mensual")
)

# 4. Filtrado del DataFrame
mask = (
    (df["Transaction Date"].dt.date >= start_date) &
    (df["Transaction Date"].dt.date <= end_date) &
    (df["Category"].isin(selected_categories)) &
    (df["Payment Method"].isin(selected_payments)) &
    (df["Location"].isin(selected_locations))
)
df_filt = df.loc[mask].copy()

# 5. Agregación temporal
if agg_option == "Diaria":
    df_time = df_filt.resample("D", on="Transaction Date")["Total Spent"].sum().reset_index()
elif agg_option == "Semanal":
    df_time = df_filt.resample("W-MON", on="Transaction Date")["Total Spent"].sum().reset_index()
else:  # Mensual
    df_time = df_filt.resample("M", on="Transaction Date")["Total Spent"].sum().reset_index()

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

# 6.4 Top 10 Ubicaciones por Ventas
st.subheader("Top 10 Ubicaciones por Ventas")
df_loc = df_filt.groupby("Location")["Total Spent"].sum().sort_values(ascending=False).head(10).reset_index()
fig_loc = px.bar(
    df_loc,
    x="Total Spent",
    y="Location",
    orientation="h",
    labels={"Total Spent": "Ventas ($)", "Location": "Ubicación"},
    title="Top 10 Ubicaciones"
)
fig_loc.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_loc, use_container_width=True)

# 7. Tabla de datos filtrados (opcional)
with st.expander("Ver datos filtrados"):
    st.dataframe(df_filt.reset_index(drop=True))
