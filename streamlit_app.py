import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

st.set_page_config(page_title="US vs EU Car Market Analyzer", page_icon="🚗", layout="wide")

# ------------------------------------------------------------
# Cambio USD→EUR live (cache 1h)
@st.cache_data(ttl=3600)
def get_live_usd_to_eur() -> float:
    url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return float(r.json()["rates"]["EUR"])
    except:
        return 0.92  # fallback

# ------------------------------------------------------------
# Dataset simulato USA
@st.cache_data
def load_us_data(model_name, min_year, max_year, km_max, cond_filter, n=150):
    np.random.seed(42)
    conds = ["scarse", "buone", "ottime"]
    df = pd.DataFrame({
        "Model": [model_name]*n,
        "Year": np.random.randint(min_year, max_year+1, n),
        "Price_USD": np.random.randint(25000, 90000, n),
        "Mileage_miles": np.random.randint(3000, int(km_max/1.609), n),
        "Condition": np.random.choice(conds, n, p=[0.2, 0.5, 0.3]),
        "Region": np.random.choice(["CA","TX","FL","NY","NJ","IL"], n)
    })
    if cond_filter != "Tutte":
        df = df[df["Condition"] == cond_filter]
    return df

# ------------------------------------------------------------
# Dataset simulato EU
@st.cache_data
def load_eu_data(model_name, min_year, max_year, km_max, cond_filter, n=120):
    np.random.seed(123)
    conds = ["scarse", "buone", "ottime"]
    df = pd.DataFrame({
        "Model": [model_name]*n,
        "Year": np.random.randint(min_year, max_year+1, n),
        "Price_EUR": np.random.randint(23000, 85000, n),
        "Mileage_km": np.random.randint(3000, km_max, n),
        "Condition": np.random.choice(conds, n, p=[0.25, 0.5, 0.25]),
        "Country": np.random.choice(["DE","FR","IT","ES","NL","BE"], n)
    })
    if cond_filter != "Tutte":
        df = df[df["Condition"] == cond_filter]
    return df

# ------------------------------------------------------------
# Sidebar input
st.sidebar.header("Filtri")
model = st.sidebar.text_input("Modello (es. BMW M3 E92)", "BMW M3 E92")
min_year_in = st.sidebar.number_input("Anno minimo (0 = auto)", 0, 2025, 0)
max_year_in = st.sidebar.number_input("Anno massimo (0 = auto)", 0, 2025, 0)
km_max = st.sidebar.number_input("Chilometraggio max (km)", 5000, 300000, 100000, 1000)
condition = st.sidebar.selectbox("Condizione", ["Tutte", "scarse", "buone", "ottime"])

# ------------------------------------------------------------
# Calcolo anni dinamici
us_all = load_us_data(model, 1990, 2025, 300000, "Tutte", n=200)
eu_all = load_eu_data(model, 1990, 2025, 300000, "Tutte", n=200)
auto_min = min(us_all["Year"].min(), eu_all["Year"].min())
auto_max = max(us_all["Year"].max(), eu_all["Year"].max())
min_year = min_year_in if min_year_in > 0 else auto_min
max_year = max_year_in if max_year_in > 0 else auto_max

# ------------------------------------------------------------
# Caricamento dati filtrati
fx_usd_eur = get_live_usd_to_eur()
df_us = load_us_data(model, min_year, max_year, km_max, condition)
df_eu = load_eu_data(model, min_year, max_year, km_max, condition)

df_us["Price_EUR"] = df_us["Price_USD"] * fx_usd_eur
df_us["Mileage_km"] = (df_us["Mileage_miles"] * 1.609).round()

# ------------------------------------------------------------
st.title("Analisi mercato auto USA vs Europa")
st.caption(f"Cambio USD→EUR: **{fx_usd_eur:.4f}**")

# ------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.metric("Prezzo medio USA (USD)", f"${df_us['Price_USD'].mean():,.0f}")
    st.metric("Prezzo medio USA (EUR)", f"€{df_us['Price_EUR'].mean():,.0f}")
with col2:
    st.metric("Prezzo medio EU (EUR)", f"€{df_eu['Price_EUR'].mean():,.0f}")

# ------------------------------------------------------------
st.subheader("Grafico prezzi")
colA, colB = st.columns(2)
with colA:
    fig1 = px.histogram(df_us, x="Price_EUR", nbins=25, title="Prezzi USA in EUR")
    st.plotly_chart(fig1, use_container_width=True)
with colB:
    fig2 = px.histogram(df_eu, x="Price_EUR", nbins=25, title="Prezzi EU in EUR")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------
st.header("Simulazione Import & Profitto")
purchase_price_usd = st.number_input("Prezzo acquisto (USD)", value=int(df_us['Price_USD'].mean()), step=1000)
purchase_price_eur = purchase_price_usd * fx_usd_eur

colx1, colx2, colx3 = st.columns(3)
with colx1:
    shipping = st.number_input("Spedizione (€)", 2000)
with colx2:
    duty_pct = st.number_input("Dazi (%)", 10.0)
with colx3:
    vat_pct = st.number_input("IVA (%)", 22.0)
colx4, colx5 = st.columns(2)
with colx4:
    omolog = st.number_input("Omologazione (€)", 2500)
with colx5:
    other = st.number_input("Altri costi (€)", 1000)

duty = purchase_price_eur * duty_pct / 100
vat = (purchase_price_eur + duty + shipping) * vat_pct / 100
landed_cost = purchase_price_eur + shipping + duty + vat + omolog + other

st.markdown(f"**Costo totale:** €{landed_cost:,.0f}")
sale_price = st.number_input("Prezzo vendita EU (€)", 60000, step=1000)
profit = sale_price - landed_cost
st.markdown(f"**Profitto stimato:** €{profit:,.0f}")

if profit > 0:
    st.success("✅ Potenzialmente profittevole")
else:
    st.error("❌ Non profittevole")

# Download dati
st.download_button("Scarica USA CSV", df_us.to_csv(index=False).encode(), "us_data.csv")
st.download_button("Scarica EU CSV", df_eu.to_csv(index=False).encode(), "eu_data.csv")
