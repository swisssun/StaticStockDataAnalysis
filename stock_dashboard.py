import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# Load combined data
folder = 'stock_data/'
csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]

# Load and combine all files
dataframes = []
for file in csv_files:
    try:
        df = pd.read_csv(os.path.join(folder, file))
        df['Ticker'] = file.replace('.csv', '')
        df['Date'] = pd.to_datetime(df['Date'])
        dataframes.append(df)
    except Exception as e:
        st.error(f"Error loading {file}: {e}")

if not dataframes:
    st.error("No data loaded.")
    st.stop()

combined_df = pd.concat(dataframes)

# Sidebar Controls
st.sidebar.title("Stock Dashboard")

tickers = st.sidebar.multiselect(
    "Select Tickers",
    options=combined_df['Ticker'].unique().tolist(),
    default=['AAPL', 'MSFT']
)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2021-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-01-01"))

normalize = st.sidebar.checkbox("Normalize Prices", value=False)
show_volume = st.sidebar.checkbox("Show Volume Plot", value=False)

strategy = st.sidebar.selectbox(
    "Select Strategy",
    options=["None", "SMA Crossover"]
)

short_window = long_window = None
if strategy == "SMA Crossover":
    short_window = st.sidebar.slider("Short SMA Window", 5, 50, 20)
    long_window = st.sidebar.slider("Long SMA Window", 10, 100, 50)

# Filter data
filtered_data = combined_df[
    (combined_df['Ticker'].isin(tickers)) &
    (combined_df['Date'] >= pd.to_datetime(start_date)) &
    (combined_df['Date'] <= pd.to_datetime(end_date))
].copy()

# Normalize prices
if normalize:
    for ticker in tickers:
        mask = filtered_data['Ticker'] == ticker
        initial = filtered_data[mask]['Close'].iloc[0]
        filtered_data.loc[mask, 'Close'] = filtered_data[mask]['Close'] / initial

# Strategy logic
if strategy == "SMA Crossover" and short_window and long_window:
    filtered_data['SMA1'] = filtered_data.groupby('Ticker')['Close'].transform(lambda x: x.rolling(short_window).mean())
    filtered_data['SMA2'] = filtered_data.groupby('Ticker')['Close'].transform(lambda x: x.rolling(long_window).mean())
    
    filtered_data['Signal'] = 0
    filtered_data.loc[
        (filtered_data['SMA1'] > filtered_data['SMA2']) &
        (filtered_data['SMA1'].shift(1) <= filtered_data['SMA2'].shift(1)),
        'Signal'
    ] = 1  # Buy

    filtered_data.loc[
        (filtered_data['SMA1'] < filtered_data['SMA2']) &
        (filtered_data['SMA1'].shift(1) >= filtered_data['SMA2'].shift(1)),
        'Signal'
    ] = -1  # Sell
else:
    filtered_data['Signal'] = 0

# Plotting
st.title("Stock Price Chart")
fig, ax = plt.subplots(figsize=(12, 6))

for ticker in tickers:
    df_plot = filtered_data[filtered_data['Ticker'] == ticker]
    ax.plot(df_plot['Date'], df_plot['Close'], label=f"{ticker} Close")

    if strategy == "SMA Crossover":
        ax.plot(df_plot['Date'], df_plot['SMA1'], linestyle='--', label=f"{ticker} SMA{short_window}", alpha=0.6)
        ax.plot(df_plot['Date'], df_plot['SMA2'], linestyle='--', label=f"{ticker} SMA{long_window}", alpha=0.6)

        buys = df_plot[df_plot['Signal'] == 1]
        sells = df_plot[df_plot['Signal'] == -1]
        ax.plot(buys['Date'], buys['Close'], '^', color='green', label=f"{ticker} Buy", markersize=8)
        ax.plot(sells['Date'], sells['Close'], 'v', color='red', label=f"{ticker} Sell", markersize=8)

ax.set_xlabel("Date")
ax.set_ylabel("Normalized Price" if normalize else "Close Price")
ax.set_title(f"Prices for {', '.join(tickers)}")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# Optional Volume Plot
if show_volume:
    st.subheader("Volume Chart")
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    for ticker in tickers:
        df_vol = filtered_data[filtered_data['Ticker'] == ticker]
        ax2.plot(df_vol['Date'], df_vol['Volume'], label=f"{ticker} Volume")
    ax2.set_ylabel("Volume")
    ax2.set_xlabel("Date")
    ax2.grid(True)
    ax2.legend()
    st.pyplot(fig2)

# Data Table
st.subheader("Filtered Data")
st.dataframe(filtered_data)

# Buy/Sell Signals Table
st.subheader("Buy/Sell Signals")
signals_table = filtered_data[filtered_data['Signal'] != 0][['Date', 'Ticker', 'Close', 'Signal']]
signals_table['Action'] = signals_table['Signal'].map({1: 'Buy', -1: 'Sell'})
st.dataframe(signals_table)

# Download Buttons
csv_filtered = filtered_data.to_csv(index=False).encode('utf-8')
csv_signals = signals_table.to_csv(index=False).encode('utf-8')

st.download_button("Download Filtered Data CSV", csv_filtered, "filtered_stock_data.csv", "text/csv")
st.download_button("Download Signals CSV", csv_signals, "buy_sell_signals.csv", "text/csv")
