# Retail Store Sales Dashboard

Una aplicación interactiva desarrollada con **Streamlit** para explorar y visualizar las ventas de una tienda minorista. Permite filtrar por fechas, categorías, métodos de pago y ubicaciones, y muestra KPIs y gráficos dinámicos.

## 📋 Tabla de contenidos

- [Demo](#-demo)  
- [Características](#-características)  
- [Instalación](#-instalación)  
- [Uso](#-uso)  
- [Estructura del proyecto](#-estructura-del-proyecto)  
- [Datos](#-datos)  
- [Tecnologías](#-tecnologías)  
- [Contribuir](#-contribuir)  
- [Licencia](#-licencia)  

---

## 🚀 Demo

Puedes interactuar con el dashboard desplegado en Streamlit aquí:  
https://dashboardretail-store-sales-dqotitdrvjlwy5uggusien.streamlit.app

---

## ✨ Características

- Filtrado dinámico por:
  - Rango de fechas  
  - Categoría de producto  
  - Método de pago (Online / In-Store)  
  - Ubicación  
- KPIs en tiempo real:
  - Ventas totales  
  - Ticket promedio  
  - Cantidad vendida  
- Gráficos interactivos (Plotly):
  - Evolución diaria de ventas  
  - Distribución de métodos de pago  
  - Ventas por categoría  
- Descarga de datos filtrados en CSV

---

## 📦 Instalación

1. Clona este repositorio:  
   git clone https://github.com/DaniDCC/Dashboard_Retail-Store-Sales.git
   cd Dashboard_Retail-Store-Sales

2. Crea y activa un entorno virtual (opcional pero recomendado):  
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows

3. Instala las dependencias:
   pip install -r requirements.txt

---

## ▶️ Uso
   streamlit run App.py

---

🗂️ Estructura del proyecto
bash
Copiar
Editar
├── App.py
├── requirements.txt
├── retail_store_sales.csv           # Datos crudos originales
├── retail_store_sales_clean.csv     # Datos depurados para el dashboard
└── README.md                        

---

🔢 Datos

retail_store_sales.csv:
Dataset original con transacciones, incluye columnas como ID de transacción, categoría, precio, cantidad, total, método de pago, ubicación y fecha.

retail_store_sales_clean.csv:
Versión filtrada y limpia (sin valores nulos, formato de fechas homogéneo) que consume la aplicación.

---

🛠️ Tecnologías
- Streamlit
- Pandas
- Plotly
- Python 3.7+
