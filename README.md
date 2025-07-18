# 🚗 US vs EU Car Market Analyzer (Streamlit App)

Questa applicazione Streamlit ti permette di analizzare e confrontare il mercato delle auto usate negli **USA** rispetto all'**Europa**, con cambio valuta live e simulazione dei costi di importazione.

---

## ✅ Funzionalità principali
- Analisi prezzi auto USA ed Europa (dataset simulati)
- Conversione USD → EUR con cambio live da [exchangerate.host](https://exchangerate.host)
- Filtri: modello auto, anni (con rilevamento automatico), condizione, chilometraggio
- Grafici interattivi con **Plotly**
- Calcolo **costo totale import** (spedizione, dazi, IVA, omologazione, altri costi)
- Stima **profitto** e valutazione convenienza
- Download dati in CSV

---

## 🔧 Come eseguire in locale
```bash
# Clona il repository
git clone https://github.com/<tuo-username>/car-market-usa-eu.git
cd car-market-usa-eu

# Crea un ambiente virtuale
python -m venv venv
source venv/bin/activate  # su Mac/Linux
venv\Scripts\activate     # su Windows

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'app Streamlit
streamlit run streamlit_app.py
