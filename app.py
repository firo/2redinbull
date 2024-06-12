import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit_extras.buy_me_a_coffee import button

# Titolo dell'app
st.title('Indagine su Chiusure Negative Consecutive in Trend Rialzista')

# Avvertimento legale
st.markdown("""
**Disclaimer:**
Questa applicazione è realizzata a scopo didattico per testare le funzionalità di Python e le librerie utilizzate. Non deve essere utilizzata come strumento finanziario su cui basare le proprie strategie di investimento. L'autore non si assume alcuna responsabilità per eventuali decisioni finanziarie prese sulla base delle informazioni fornite da questa applicazione.
""")
button(username="firo", floating=True, width=221)

def load_ticker_group(file):
    df = pd.read_csv(file, header=0)
    return list(df['Ticker'])

# Input per i ticker dei titoli azionari o il caricamento di un file CSV con i ticker
ticker_source = st.radio('Scegli la fonte dei ticker:', ['Inserimento manuale', 'Caricamento da file CSV'])

if ticker_source == 'Inserimento manuale':
    # Inserimento manuale di default
    default_tickers = ['NVDA', 'AAPL', 'MSFT', 'CRM']
    tickers_input = st.text_area('Inserisci i ticker dei titoli azionari separati da virgole o il codice di un indice (separati da virgole)', ', '.join(default_tickers))
    tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]
else:
    ticker_file = st.file_uploader('Carica un file CSV con i ticker. Il file deve contenere un intestazione chiamata "Ticker".', type=['csv'])
    if ticker_file is not None:
        tickers = load_ticker_group(ticker_file)
    else:
        tickers = []

# Funzione per calcolare le variazioni e il trend
def calculate_variation_and_trend(df):
    df['var'] = df['Close'] - df['Close'].shift(+1)
    df['var_percent'] = (df['var'] / df['Close'].shift(1)) * 100
    df['2rc'] = np.where((df['var'] < 0) & (df['var'].shift(+1) < 0), 1, 0)
    df["sma50"] = df["Close"].rolling(window=50).mean()
    df['trend50'] = np.where(df['sma50'] > df['sma50'].shift(1), 1, 0)
    df['buy'] = np.where((df['trend50'] == 1) & (df['2rc'] == 1), 1, 0)
    return df

# Calcolo delle variazioni e del trend per ogni titolo
results = {}
for stock in tickers:
    start_date = datetime.now() - timedelta(days=100)
    data = yf.download(stock, start=start_date, end=datetime.now())
    results[stock] = calculate_variation_and_trend(data)

# Visualizzazione dei risultati
for stock, result in results.items():
    st.subheader(f'Risultati per {stock}')

    # Check the last 'trend50' and '2rc' value
    if result['trend50'].iloc[-1] == 1:
        if result['2rc'].iloc[-1] == 1:
            comment = f"Azione: BUY {stock} - Il trend è rialzista su 50 periodi e per entrambe le due sedute precedenti ha ottenuto un risultato negativo."
        else:
            comment = "Azione: NEUTRAL - Nonostante il trend sia rialzista, non ci sono state due sedute consecutive con risultati negativi."
    elif result['2rc'].iloc[-1] == 0:
        comment = "Azione: NEUTRAL - Il trend non è rialzista e le ultime due sedute non hanno ottenuto risultati negativi."
    else:
        comment = "Azione: NEUTRAL - Non ci sono segnali di un trend rialzista o di risultati negativi nelle ultime due sedute."

    # Print the comment and result dataframe
    st.write(comment)
    #st.write(result)