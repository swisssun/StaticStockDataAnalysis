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
ma_window = st.sidebar.selectbox("Moving Average (days)", options=[None, 7, 20, 50], index=0)

# Filter data
filtered_data = combined_df[
    (combined_df['Ticker'].isin(tickers)) &
    (combined_df['Date'] >= pd.to_datetime(start_date)) &
    (combined_df['Date'] <= pd.to_datetime(end_date))
].copy()

# The pasted code starts here
# --- STRATEGY: SMA Crossover ---

# Calculate 20 and 50-day SMAs for each ticker
filtered_data['SMA20'] = filtered_data.groupby('Ticker')['Close'].transform(lambda x: x.rolling(20).mean())
filtered_data['SMA50'] = filtered_data.groupby('Ticker')['Close'].transform(lambda x: x.rolling(50).mean())

# Generate buy/sell signals
filtered_data['Signal'] = 0
filtered_data.loc[
    (filtered_data['SMA20'] > filtered_data['SMA50']) & 
    (filtered_data['SMA20'].shift(1) <= filtered_data['SMA50'].shift(1)),
    'Signal'
] = 1  # Buy

filtered_data.loc[
    (filtered_data['SMA20'] < filtered_data['SMA50']) & 
    (filtered_data['SMA20'].shift(1) >= filtered_data['SMA50'].shift(1)),
    'Signal'
] = -1  # Sell

# The pasted code ends here

# Normalize prices
if normalize:
    for ticker in tickers:
        mask = filtered_data['Ticker'] == ticker
        initial = filtered_data[mask]['Close'].iloc[0]
        filtered_data.loc[mask, 'Close'] = filtered_data[mask]['Close'] / initial

# Apply moving average
if ma_window:
    for ticker in tickers:
        mask = filtered_data['Ticker'] == ticker
        filtered_data.loc[mask, 'SMA'] = filtered_data[mask]['Close'].rolling(ma_window).mean()

# Plotting
st.title("Stock Price Chart")
fig, ax = plt.subplots(figsize=(12, 6))

#for ticker in tickers:
 #   df_plot = filtered_data[filtered_data['Ticker'] == ticker]
 #   ax.plot(df_plot['Date'], df_plot['Close'], label=f"{ticker} Close")
    
# later on, pasted code starts
for ticker in tickers:
    df_plot = filtered_data[filtered_data['Ticker'] == ticker]
    
    # Plot price line
    ax.plot(df_plot['Date'], df_plot['Close'], label=f"{ticker} Close")
    
    # Plot SMA lines (optional)
    ax.plot(df_plot['Date'], df_plot['SMA20'], linestyle='--', label=f"{ticker} SMA20", alpha=0.6)
    ax.plot(df_plot['Date'], df_plot['SMA50'], linestyle='--', label=f"{ticker} SMA50", alpha=0.6)
    
    # Plot buy/sell markers
    buys = df_plot[df_plot['Signal'] == 1]
    sells = df_plot[df_plot['Signal'] == -1]
    
    ax.plot(buys['Date'], buys['Close'], '^', color='green', label=f"{ticker} Buy", markersize=8)
    ax.plot(sells['Date'], sells['Close'], 'v', color='red', label=f"{ticker} Sell", markersize=8)
    
# later on, pasted code ends here
    
    
    if ma_window:
        ax.plot(df_plot['Date'], df_plot['SMA'], linestyle='--', label=f"{ticker} {ma_window}-day SMA")

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

# below is the pasted code for creating table
st.subheader("Buy/Sell Signals")
signals_table = filtered_data[filtered_data['Signal'] != 0][['Date', 'Ticker', 'Close', 'Signal']]
signals_table['Action'] = signals_table['Signal'].map({1: 'Buy', -1: 'Sell'})
st.dataframe(signals_table)

# Download button for signal table
csv_signals = signals_table.to_csv(index=False).encode('utf-8')
st.download_button("Download Signals CSV", csv_signals, "buy_sell_signals.csv", "text/csv")




# Download Button
csv = filtered_data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV",
    data=csv,
    file_name='filtered_stock_data.csv',
    mime='text/csv'
)
