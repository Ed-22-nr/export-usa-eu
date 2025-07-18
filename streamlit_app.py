import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

st.set_page_config(page_title="US vs EU Car Market Analyzer", page_icon="🚗", layout="wide")

# ------------------------------------------------------------
# FX Rate USD→EUR live (cache 1h)
@st.cache_data(ttl=3600)
def get_live_usd_to_eur() -> float:
    url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return float(data["rates"]["EUR"])
    except Exception:
        return 0.92

# ------------------------------------------------------------
# Simulated US data loader
@st.cache_data(show_spinner=False)
def load_us_data(model_name: str, min_year: int, max_year: int, km_max: int, cond_filter: str, n: int=200) -> pd.DataFrame:
    np.random.seed(42)
    conds = ["scarse", "buone", "ottime"]
    data = {
        "Model": [model_name]*n,
        "Year": np.random.randint(min_year, max_year+1, n),
        "Price_USD": np.random.randint(25000, 90000, n),
        "Mileage_miles": np.random.randint(3000, int(km_max/1.609)+1, n),
        "Condition": np.random.choice(conds, n, p=[0.2, 0.5, 0.3]),
        "Region": np.random.choice(["CA","TX","FL","NY","NJ","IL"], n),
    }
    df = pd.DataFrame(data)
    if cond_filter != "Tutte":
        df = df[df["Condition"] == cond_filter]
    return df

# ------------------------------------------------------------
# Simulated EU data loader
@st.cache_data(show_spinner=False)
def load_eu_data(model_name: str, min_year: int, max_year: int, km_max: int, cond_filter: str, n: int=150) -> pd.DataFrame:
    np.random.seed(123)
    conds = ["scarse", "buone", "ottime"]
    data = {
        "Model": [model_name]*n,
        "Year": np.random.randint(min_year, max_year+1, n),
        "Price_EUR": np.random.randint(23000, 85000, n),
        "Mileage_km": np.random.randint(3000, km_max+1, n),
        "Condition": np.random.choice(conds, n, p=[0.25, 0.5, 0.25]),
        "Country": np.random.choice(["DE","FR","IT","ES","NL","BE"], n),
    }
    df = pd.DataFrame(data)
    if cond_filter != "Tutte":
        df = df[df["Condition"] == cond_filter]
    return df

# ------------------------------------------------------------
# Sidebar filters
st.sidebar.header("Filtri Auto")
model = st.sidebar.text_input("Modello auto (es. BMW M3 E92)", "BMW M3 E92")

# Ora permettiamo anno minimo e massimo anche 0 come valore "auto"
min_year_input = st.sidebar.number_input("Anno minimo (0 = automatico)", min_value=0, max_value=2025, value=0)
max_year_input = st.sidebar.number_input("Anno massimo (0 = automatico)", min_value=0, max_value=2025, value=0)

km_max = st.sidebar.number_input("Chilometraggio massimo (km)", min_value=5000, max_value=300000, value=100000, step=1000)
condition = st.sidebar.selectbox("Condizioni", options=["Tutte", "scarse", "buone", "ottime"])

# ------------------------------------------------------------
# Load full datasets (unfiltered anni) per calcolare anni min/max disponibili
with st.spinner("Calcolo anni disponibili..."):
    df_us_all = load_us_data(model, 1990, 2025, km_max=300000, cond_filter="Tutte", n=1000)
    df_eu_all = load_eu_data(model, 1990, 2025, km_max=300000, cond_filter="Tutte", n=1000)

    us_year_min = int(df_us_all["Year"].min())
    us_year_max = int(df_us_all["Year"].max())
    eu_year_min = int(df_eu_all["Year"].min())
    eu_year_max = int(df_eu_all["Year"].max())

# Usa i valori automatici se l’utente ha messo 0
min_year = min_year_input if min_year_input > 0 else min(us_year_min, eu_year_min)
max_year = max_year_input if max_year_input > 0 else max(us_year_max, eu_year_max)

# ------------------------------------------------------------
# Load filtered data
with st.spinner("Caricamento dati e cambio FX..."):
    fx_usd_eur = get_live_usd_to_eur()
    df_us = load_us_data(model, min_year, max_year, km_max, condition)
    df_eu = load_eu_data(model, min_year, max_year, km_max, condition)

# Convert USD prices to EUR
df_us["Price_EUR"] = df_us["Price_USD"] * fx_usd_eur
# Convert mileage miles → km for US data
df_us["Mileage_km"] = (df_us["Mileage_miles"] * 1.609).round()

# ------------------------------------------------------------
# Title and FX info
st.title("Analisi mercato auto USA vs Europa")
st.markdown(f"Cambio USD→EUR live: **{fx_usd_eur:.4f}**")

# ------------------------------------------------------------
# Show sample data
st.subheader("Campione auto USA")
st.dataframe(df_us.head(10))
st.subheader("Campione auto Europa")
st.dataframe(df_eu.head(10))

# ------------------------------------------------------------
# Price stats + comparison
col1, col2 = st.columns(2)
with col1:
    st.metric("Prezzo medio USA (USD)", f"${df_us['Price_USD'].mean():,.0f}")
    st.metric("Prezzo medio USA (EUR)", f"€{df_us['Price_EUR'].mean():,.0f}")
    st.metric("Chilometraggio medio USA (km)", f"{df_us['Mileage_km'].mean():,.0f} km")
with col2:
    st.metric("Prezzo medio EU (EUR)", f"€{df_eu['Price_EUR'].mean():,.0f}")
    st.metric("Chilometraggio medio EU (km)", f"{df_eu['Mileage_km'].mean():,.0f} km")

# ------------------------------------------------------------
# Price distributions
colA, colB = st.columns(2)
with colA:
    fig_us = px.histogram(df_us, x="Price_EUR", nbins=25, title="Distribuzione prezzi USA (EUR)")
    st.plotly_chart(fig_us, use_container_width=True)
with colB:
    fig_eu = px.histogram(df_eu, x="Price_EUR", nbins=25, title="Distribuzione prezzi Europa (EUR)")
    st.plotly_chart(fig_eu, use_container_width=True)

# ------------------------------------------------------------
# Profitability estimation
st.header("Simulazione di importazione e profitto")

default_purchase_usd = int(df_us["Price_USD"].mean()) if not df_us.empty else 40000
purchase_price_usd = st.number_input("Prezzo di acquisto (USD)", value=default_purchase_usd, step=1000)
purchase_price_eur = purchase_price_usd * fx_usd_eur

st.markdown("### Costi di importazione stimati (in €)")
colc1, colc2, colc3 = st.columns(3)
with colc1:
    shipping = st.number_input("Spedizione (€)", value=2000, step=100)
with colc2:
    duty_pct = st.number_input("Dazi (%)", value=10.0, step=0.5)
with colc3:
    vat_pct = st.number_input("IVA (%)", value=22.0, step=0.5)
colc4, colc5 = st.columns(2)
with colc4:
    omolog = st.number_input("Omologazione & modifiche (€)", value=2500, step=100)
with colc5:
    other_fees = st.number_input("Altre spese (€)", value=1000, step=100)

duty = (duty_pct / 100.0) * purchase_price_eur
vat = (vat_pct / 100.0) * (purchase_price_eur + duty + shipping)
landed_cost = purchase_price_eur + shipping + duty + vat + omolog + other_fees

st.markdown(f"**Costo totale stimato importazione:** €{landed_cost:,.0f}")

sale_price = st.number_input("Prezzo vendita previsto in Europa (€)", value=60000, step=1000)
profit = sale_price - landed_cost

st.markdown(f"**Profitto stimato:** €{profit:,.0f}")

# ------------------------------------------------------------
# Confronto prezzi medi e indicazione profittabilità
avg_us_eur = df_us["Price_EUR"].mean() if not df_us.empty else 0
avg_eu = df_eu["Price_EUR"].mean() if not df_eu.empty else 0

st.subheader("Confronto prezzi medi")
st.write(f"Prezzo medio USA (EUR): €{avg_us_eur:,.0f}")
st.write(f"Prezzo medio Europa (EUR): €{avg_eu:,.0f}")

if avg_us_eur < avg_eu and profit > 0:
    st.success("✅ Importazione potenzialmente profittevole!")
elif avg_us_eur >= avg_eu:
    st.warning("⚠️ Prezzi USA non inferiori ai prezzi Europa. Importazione meno conveniente.")
else:
    st.error("❌ Profitto negativo con i parametri inseriti.")

# ------------------------------------------------------------
# Export dati
st.download_button(
    "Scarica dati USA (CSV)",
    data=df_us.to_csv(index=False).encode("utf-8"),
    file_name="us_car_market_sample.csv",
    mime="text/csv",
)

st.download_button(
    "Scarica dati Europa (CSV)",
    data=df_eu.to_csv(index=False).encode("utf-8"),
    file_name="eu_car_market_sample.csv",
    mime="text/csv",
)
