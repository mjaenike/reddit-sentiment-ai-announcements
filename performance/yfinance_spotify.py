import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Spotify AI DJ Announcement - February 22, 2023
event_date = datetime(2023, 2, 22)
start_date = event_date - timedelta(days=14)
end_date = event_date + timedelta(days=14)

# Download Spotify stock data
ticker = "SPOT"
print(f"Downloading {ticker} data...")
spot_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

# Robust column handling
if spot_data.empty:
    raise ValueError(f"No data downloaded for {ticker}")

# If MultiIndex, flatten it
if isinstance(spot_data.columns, pd.MultiIndex):
    spot_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in spot_data.columns.values]
    # Try to rename the flattened columns to standard names
    col_mapping = {}
    for col in spot_data.columns:
        if 'close' in col.lower():
            col_mapping[col] = 'Close'
        elif 'open' in col.lower():
            col_mapping[col] = 'Open'
        elif 'high' in col.lower():
            col_mapping[col] = 'High'
        elif 'low' in col.lower():
            col_mapping[col] = 'Low'
        elif 'volume' in col.lower():
            col_mapping[col] = 'Volume'
    spot_data.rename(columns=col_mapping, inplace=True)

print(f"Columns in data: {spot_data.columns.tolist()}")

# Find the close price column (case insensitive)
close_col = None
for col in spot_data.columns:
    if 'close' in col.lower():
        close_col = col
        break

if close_col is None:
    raise ValueError(f"Could not find Close column. Available columns: {spot_data.columns.tolist()}")

print(f"Using '{close_col}' as Close price column")

# Calculate daily returns
spot_data['Daily_Return'] = spot_data[close_col].pct_change()

# Add event day marker
spot_data['Days_from_Event'] = (spot_data.index - event_date).days

# Rename close_col to 'Close' for consistency
if close_col != 'Close':
    spot_data.rename(columns={close_col: 'Close'}, inplace=True)

# Find volume column
volume_col = 'Volume'
for col in spot_data.columns:
    if 'volume' in col.lower() and col != 'Volume':
        spot_data.rename(columns={col: 'Volume'}, inplace=True)
        break

# Display the data
print("="*80)
print("Spotify Stock Data Around Spotify AI DJ Announcement")
print("Event Date: February 22, 2023")
print("="*80)
display_cols = ['Close', 'Volume', 'Daily_Return', 'Days_from_Event']
display_cols = [col for col in display_cols if col in spot_data.columns]
print(spot_data[display_cols])

# Calculate cumulative returns from event date
event_price = spot_data.loc[spot_data['Days_from_Event'] == 0, 'Close'].iloc[0]
spot_data['Cumulative_Return'] = (spot_data['Close'] / event_price - 1) * 100

# Plot the results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price chart
ax1.plot(spot_data['Days_from_Event'], spot_data['Close'], marker='o', color='#1DB954', linewidth=2, markersize=8)
ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Spotify AI DJ Announcement')
ax1.set_xlabel('Days from Event', fontsize=12)
ax1.set_ylabel('Close Price ($)', fontsize=12)
ax1.set_title('Spotify Stock Price Around AI DJ Announcement\nFebruary 22, 2023', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Cumulative returns
ax2.plot(spot_data['Days_from_Event'], spot_data['Cumulative_Return'], marker='o', color='green', linewidth=2, markersize=8)
ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event Date')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Days from Event', fontsize=12)
ax2.set_ylabel('Cumulative Return (%)', fontsize=12)
ax2.set_title('Cumulative Returns from Event Date', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('spot_ai_dj_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Summary statistics
pre_event_return = spot_data[spot_data['Days_from_Event'] < 0]['Daily_Return'].mean()
post_event_return = spot_data[spot_data['Days_from_Event'] > 0]['Daily_Return'].mean()
event_day_return = spot_data[spot_data['Days_from_Event'] == 0]['Daily_Return'].iloc[0]

# Get the last available day's return (may not be exactly day +7 due to weekends/holidays)
last_day = spot_data['Days_from_Event'].max()
last_day_return = spot_data[spot_data['Days_from_Event'] == last_day]['Cumulative_Return'].iloc[0]

print(f"\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Event: Spotify AI DJ Announcement")
print(f"Company: Spotify (SPOT)")
print(f"Event Date: February 22, 2023")
print(f"\nAverage daily return 7 days before: {pre_event_return*100:.2f}%")
print(f"Event day return: {event_day_return*100:.2f}%")
print(f"Average daily return 7 days after: {post_event_return*100:.2f}%")
print(f"Cumulative return through day +{last_day}: {last_day_return:.2f}%")
print(f"\nEvent day price: ${event_price:.2f}")
print(f"Last day price (day +{last_day}): ${spot_data[spot_data['Days_from_Event'] == last_day]['Close'].iloc[0]:.2f}")
print("="*80)

# Save data to CSV
output_filename = 'spotify_performance.csv'
spot_data.to_csv(output_filename)
print(f"\nData saved to {output_filename}")
print(f"Columns saved: {list(spot_data.columns)}")
