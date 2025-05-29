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
sel_cat = st.sidebar.multiselect("Categorías", ["Todas"]+all_categories, ["Todas"])
categories_filter = all_categories if "Todas" in sel_cat else sel_cat

# Métodos de pago
all_payments = df["Payment Method"].unique().tolist()
sel_pay = st.sidebar.multiselect("Método de pago", ["Todos"]+all_payments, ["Todos"])
payments_filter = all_payments if "Todos" in sel_pay else sel_pay

# Ubicaciones
all_locations = df["Location"].unique().tolist()
sel_loc = st.sidebar.multiselect("Ubicación", ["Todas"]+all_locations, ["Todas"])
locations_filter = all_locations if "Todas" in sel_loc else sel_loc

# Nivel de agregación inicial (sólo para título)
agg_option = st.sidebar.radio("Agregación temporal", ("Diaria","Semanal","Mensual","Anual"))

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
c1,c2,c3,c4 = st.columns(4)
total_sales = df_filt["Total Spent"].sum()
avg_ticket  = df_filt["Total Spent"].mean() if not df_filt.empty else 0
total_qty   = df_filt["Quantity"].sum()
pct_disc    = df_filt["HasDiscount"].mean()*100 if not df_filt.empty else 0
c1.metric("🔖 Ventas Totales", f"${total_sales:,.0f}")
c2.metric("🎫 Ticket Promedio", f"${avg_ticket:,.2f}")
c3.metric("📦 Cantidad Vendida", f"{total_qty:,.0f}")
c4.metric("% Con Descuento", f"{pct_disc:.1f}%")

# 6+7. TENDENCIAS TEMPORALES (un gráfico con dropdown)
st.header("1. Tendencias Temporales")
freq_map = {"Diaria":"D","Semanal":"W-MON","Mensual":"M","Anual":"A"}
agg_data = {}
for label,freq in freq_map.items():
    if label=="Anual":
        tmp = (df_filt.groupby(df_filt['Transaction Date'].dt.year)
               .agg({"Total Spent":"sum","Quantity":"sum"})
               .reset_index().rename(columns={'index':'Year'}))
        tmp['Transaction Date'] = pd.to_datetime(tmp['Transaction Date'].astype(int).astype(str)+"-01-01")
        agg_data[label] = tmp[['Transaction Date','Total Spent','Quantity']]
    else:
        tmp = df_filt.resample(freq, on="Transaction Date").agg({"Total Spent":"sum","Quantity":"sum"}).reset_index()
        agg_data[label] = tmp

fig = go.Figure()
for idx,(label,df_agg) in enumerate(agg_data.items()):
    fig.add_trace(go.Scatter(
        x=df_agg["Transaction Date"],
        y=df_agg["Total Spent"],
        name=f"Ventas ({label})",
        visible=(label==agg_option)
    ))

buttons=[]
for idx,label in enumerate(freq_map.keys()):
    vis=[i==idx for i in range(len(freq_map))]
    buttons.append(dict(label=label, method="update",
                        args=[{"visible":vis},
                              {"title":f"Ventas agregadas ({label.lower()})"}]))
fig.update_layout(
    updatemenus=[dict(active=list(freq_map.keys()).index(agg_option),
                      buttons=buttons, x=0,y=1.2,xanchor="left",yanchor="top")],
    title=f"Ventas agregadas ({agg_option.lower()})",
    xaxis_title="Fecha", yaxis_title="Ventas ($)"
)
st.plotly_chart(fig, use_container_width=True)

# 8. Ventas por Categoría
st.header("2. Ventas por Categoría")
df_cat = df_filt.groupby("Category")["Total Spent"].sum().sort_values().reset_index()
fig_cat = px.bar(df_cat, x="Total Spent", y="Category", orientation="h",
                 labels={"Total Spent":"Ventas ($)","Category":"Categoría"})
st.plotly_chart(fig_cat, use_container_width=True)

# Pareto
df_cat['Cumulative']=df_cat['Total Spent'].cumsum()
df_cat['Pareto']=df_cat['Cumulative']/df_cat['Total Spent'].sum()*100
fig_p=go.Figure()
fig_p.add_bar(x=df_cat['Category'], y=df_cat['Total Spent'], name="Ventas")
fig_p.add_scatter(x=df_cat['Category'], y=df_cat['Pareto'], name="Acumulado (%)", yaxis="y2")
fig_p.update_layout(yaxis2=dict(overlaying="y",side="right"), title="Pareto de Categorías")
st.plotly_chart(fig_p, use_container_width=True)

# 9. Canales de Venta
st.header("3. Canales de Venta")
df_ch = df_filt.groupby("Channel")["Total Spent"].sum().reset_index()
fig_ch = px.pie(df_ch, names="Channel", values="Total Spent", title="% Ventas por Canal")
st.plotly_chart(fig_ch, use_container_width=True)

df_ch_t = (df_filt.groupby([pd.Grouper(key="Transaction Date",freq="W-MON"),"Channel"])
           ["Total Spent"].sum().reset_index())
fig_ch_t = px.line(df_ch_t, x="Transaction Date", y="Total Spent", color="Channel",
                   title="Evolución Semanal por Canal")
st.plotly_chart(fig_ch_t, use_container_width=True)

# 10. Métodos de Pago
st.header("4. Métodos de Pago")
df_pay = df_filt.groupby("Payment Method").agg(Transacciones=("Total Spent","size"),
                                              Ventas=("Total Spent","sum")).reset_index()
fig_pay = go.Figure()
fig_pay.add_bar(x=df_pay["Payment Method"], y=df_pay["Transacciones"], name="Transacciones")
fig_pay.add_bar(x=df_pay["Payment Method"], y=df_pay["Ventas"], name="Ventas ($)")
fig_pay.update_layout(barmode="group", title="Transacciones y Ventas por Pago")
st.plotly_chart(fig_pay, use_container_width=True)
fig_box = px.box(df_filt, x="Payment Method", y="Total Spent",
                 title="Dispersión de Gasto por Método")
st.plotly_chart(fig_box, use_container_width=True)

# 11. Impacto de Descuentos
st.header("5. Impacto de Descuentos")
avg_t = df_filt.groupby("HasDiscount")["Total Spent"].mean().reset_index()
avg_t["Label"]=avg_t["HasDiscount"].map({True:"Con",False:"Sin"})
fig_d1 = px.bar(avg_t, x="Label", y="Total Spent",
                title="Ticket Promedio con/sin Descuento")
st.plotly_chart(fig_d1, use_container_width=True)
fig_d2 = px.histogram(df_filt, x="Quantity", color="HasDiscount", barmode="overlay",
                      title="Cantidad comprada con vs sin descuento")
st.plotly_chart(fig_d2, use_container_width=True)

# 12. Carrito y Ticket Medio
st.header("6. Carrito y Ticket Medio")
fig_s = px.scatter(df_filt, x="Price Per Unit", y="Quantity",
                   title="Precio Unitario vs Cantidad")
st.plotly_chart(fig_s, use_container_width=True)
fig_h = px.histogram(df_filt, x="Total Spent", title="Distribución del Ticket")
st.plotly_chart(fig_h, use_container_width=True)

# 13. Botón de descarga
csv = df_filt.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar datos filtrados", data=csv,
                   file_name="ventas_filtradas.csv", mime="text/csv")