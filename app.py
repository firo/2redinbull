import streamlit as st
import yfinance as yf
import pandas as pd
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
    """Carica i ticker da un file CSV e li restituisce come lista."""
    df = pd.read_csv(file)
    return list(df['Ticker'])

def get_tickers(ticker_source):
    """Ottiene la lista di ticker da input manuale o da file CSV."""
    if ticker_source == 'Inserimento manuale':
        default_tickers = ['NVDA', 'AAPL', 'MSFT', 'CRM', 'SBUX', 'ZS']
        tickers_input = st.text_area(
            'Inserisci i ticker dei titoli azionari separati da virgole o il codice di un indice (separati da virgole)', 
            ', '.join(default_tickers)
        )
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]
    else:
        ticker_file = st.file_uploader('Carica un file CSV con i ticker. Il file deve contenere un\'intestazione chiamata "Ticker".', type=['csv'])
        if ticker_file is not None:
            tickers = load_ticker_group(ticker_file)
        else:
            tickers = []
    return tickers

def fetch_data(ticker, start_date, end_date):
    """Scarica i dati di un ticker da Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            st.warning(f"Nessun dato disponibile per {ticker}.")
        return data
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati per {ticker}: {e}")
        return pd.DataFrame()
    
def calculate_variation_and_trend(df, sma_periods):
    """Calcola le variazioni e il trend dei prezzi."""
    if df.empty or len(df) < sma_periods:
        st.warning(f"Non ci sono abbastanza dati per il calcolo della media mobile a {sma_periods} giorni.")
        return pd.DataFrame()

    df['Variazione'] = df['Close'].diff()
    df['% Variazione'] = df['Variazione'] / df['Close'].shift(1) * 100
    df['2ChiusureNegative'] = ((df['Variazione'] < 0) & (df['Variazione'].shift(1) < 0)).astype(int)
    df['SMA'] = df['Close'].rolling(window=sma_periods).mean()
    df['Trend'] = (df['SMA'] > df['SMA'].shift(1)).astype(int)
    df['Compra'] = ((df['Trend'] == 1) & (df['2ChiusureNegative'] == 1)).astype(int)
    df['Guadagno'] = ((df['Compra'] == 1) & (df['Compra'].shift(-1) == 0)).astype(int)
    return df[['Close', 'Variazione', '% Variazione', '2ChiusureNegative', 'SMA', 'Trend', 'Compra', 'Guadagno']]

def analyze_tickers(tickers, sma_periods, df_days):
    """Analizza i ticker e visualizza i risultati."""
    start_date = datetime.now() - timedelta(days=df_days)
    end_date = datetime.now()

    results = {}

    for stock in tickers:
        data = fetch_data(stock, start_date, end_date)
        if not data.empty:
            df = calculate_variation_and_trend(data, sma_periods)
            if not df.empty:
                #last_record = result.iloc[-1]
                #results[stock] = last_record
                st.subheader(f'Risultati per {stock}')
                #comment = generate_comment(result)
                st.write(generate_comment_tomorrow_buy(df), unsafe_allow_html=True)
                st.write(generate_comment_strategy(stock, df), unsafe_allow_html=True)
                st.dataframe(df)
            else:
                st.warning(f"Nessun risultato disponibile per {stock}.")

def generate_comment_tomorrow_buy(df):
    """Genera un commento in base ai risultati."""
    if df.empty:
        return "Dati insufficienti per generare una valutazione."

    if df.tail(1)['Trend'].values[0] == 1:
        if df.tail(1)['2ChiusureNegative'].values[0] == 1:
            return "Valutazione: <b style='color: green;'>COMPRA</b> - Il trend è <b style='color: green;'>rialzista</b> e per entrambe le due sedute precedenti consecutive ha ottenuto un risultato <b style='color: green;'>negativo</b>."
        else:
            return "Valutazione: <b>NEUTRALE</b> - Nonostante il trend sia <b style='color: green;'>rialzista</b>, non ci sono state due sedute precedenti consecutive con risultati negativi."
    else:
        return "Valutazione: <b style='color: red;'>NEUTRALE</b> - Il trend non è rialzista o non ci sono state due sedute precedenti consecutive con risultati negativi."

def generate_comment_strategy(stock, df):
    total_buy = df['Compra'].sum()
    total_gain = df['Guadagno'].sum()
    strategy_efficency_perc = int(100 *(total_gain / total_buy))
    return "Negli ultimi "+ str(df_days) + ", questa strategia con " + stock + " ha funzionato nel <b style='color: green;'>" + str(strategy_efficency_perc) + "%</b>"


# Barra laterale per il numero di giorni per il calcolo della SMA
sma_days = st.sidebar.slider(
    'Numero di giorni per il calcolo della media mobile (SMA)',
    min_value=20,
    max_value=200,
    value=50
)

df_days = st.sidebar.slider(
    'Numero di giorni del periodo temporale di riferimento',
    min_value=180,
    max_value=3650,
    value=365
)

# Input per i ticker dei titoli azionari o il caricamento di un file CSV con i ticker
ticker_source = st.radio('Scegli la fonte dei ticker:', ['Inserimento manuale', 'Caricamento da file CSV'])
tickers = get_tickers(ticker_source)

# Se ci sono dei ticker da analizzare, esegui l'analisi
if tickers:
    analyze_tickers(tickers, sma_days, df_days)
else:
    st.info('Inserisci o carica almeno un ticker per eseguire l\'analisi.')
