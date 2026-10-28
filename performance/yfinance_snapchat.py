import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Snapchat My AI Announcement - February 27, 2023
event_date = datetime(2023, 2, 27)
start_date = event_date - timedelta(days=14)
end_date = event_date + timedelta(days=14)

# Download Snap stock data
ticker = "SNAP"
print(f"Downloading {ticker} data...")
snap_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

# Download NASDAQ benchmark for abnormal returns calculation
print(f"Downloading NASDAQ (QQQ) benchmark data...")
nasdaq_data = yf.download('QQQ', start=start_date, end=end_date, auto_adjust=True, progress=False)

# Robust column handling
if snap_data.empty:
    raise ValueError(f"No data downloaded for {ticker}")

# If MultiIndex, flatten it
if isinstance(snap_data.columns, pd.MultiIndex):
    snap_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in snap_data.columns.values]
    # Try to rename the flattened columns to standard names
    col_mapping = {}
    for col in snap_data.columns:
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
    snap_data.rename(columns=col_mapping, inplace=True)

print(f"Columns in data: {snap_data.columns.tolist()}")

# Find the close price column (case insensitive)
close_col = None
for col in snap_data.columns:
    if 'close' in col.lower():
        close_col = col
        break

if close_col is None:
    raise ValueError(f"Could not find Close column. Available columns: {snap_data.columns.tolist()}")

print(f"Using '{close_col}' as Close price column")

# Calculate daily returns
snap_data['Daily_Return'] = snap_data[close_col].pct_change()

# Add event day marker
snap_data['Days_from_Event'] = (snap_data.index - event_date).days

# Rename close_col to 'Close' for consistency
if close_col != 'Close':
    snap_data.rename(columns={close_col: 'Close'}, inplace=True)

# Find volume column
volume_col = 'Volume'
for col in snap_data.columns:
    if 'volume' in col.lower() and col != 'Volume':
        snap_data.rename(columns={col: 'Volume'}, inplace=True)
        break

# Process NASDAQ data
if isinstance(nasdaq_data.columns, pd.MultiIndex):
    nasdaq_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in nasdaq_data.columns.values]
nasdaq_close_col = None
for col in nasdaq_data.columns:
    if 'close' in col.lower():
        nasdaq_close_col = col
        break
if nasdaq_close_col:
    nasdaq_data.rename(columns={nasdaq_close_col: 'Close'}, inplace=True)

# Calculate market returns
nasdaq_data['Market_Return'] = nasdaq_data['Close'].pct_change()

# Merge market returns with company data
snap_data = snap_data.join(nasdaq_data[['Market_Return']], how='left')

# Calculate abnormal returns (company return - market return)
snap_data['Abnormal_Return'] = snap_data['Daily_Return'] - snap_data['Market_Return']

# Display the data
print("="*80)
print("Snap Stock Data Around Snapchat My AI Announcement")
print("Event Date: February 27, 2023")
print("Market Benchmark: NASDAQ (QQQ)")
print("="*80)
display_cols = ['Close', 'Volume', 'Daily_Return', 'Market_Return', 'Abnormal_Return', 'Days_from_Event']
display_cols = [col for col in display_cols if col in snap_data.columns]
print(snap_data[display_cols])

# Calculate cumulative returns from event date
event_price = snap_data.loc[snap_data['Days_from_Event'] == 0, 'Close'].iloc[0]
snap_data['Cumulative_Return'] = (snap_data['Close'] / event_price - 1) * 100

# Calculate Cumulative Abnormal Return (CAR)
snap_data['CAR'] = 0.0
event_idx = snap_data[snap_data['Days_from_Event'] == 0].index[0]

# Calculate CAR for days at and after event
for idx in snap_data.index:
    if idx >= event_idx:
        days_slice = snap_data.loc[event_idx:idx]
        snap_data.loc[idx, 'CAR'] = days_slice['Abnormal_Return'].sum() * 100

# Calculate CAR for days before event (going backward)
for idx in reversed(snap_data[snap_data.index < event_idx].index):
    days_slice = snap_data.loc[idx:event_idx]
    snap_data.loc[idx, 'CAR'] = -days_slice['Abnormal_Return'].sum() * 100

# Plot the results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price chart
ax1.plot(snap_data['Days_from_Event'], snap_data['Close'], marker='o', color='#FFFC00', linewidth=2, markersize=8)
ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Snapchat My AI Announcement')
ax1.set_xlabel('Days from Event', fontsize=12)
ax1.set_ylabel('Close Price ($)', fontsize=12)
ax1.set_title('Snap Stock Price Around Snapchat My AI Announcement\nFebruary 27, 2023', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Cumulative returns
ax2.plot(snap_data['Days_from_Event'], snap_data['Cumulative_Return'], marker='o', color='green', linewidth=2, markersize=8)
ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event Date')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Days from Event', fontsize=12)
ax2.set_ylabel('Cumulative Return (%)', fontsize=12)
ax2.set_title('Cumulative Returns from Event Date', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('snap_myai_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Summary statistics
pre_event_return = snap_data[snap_data['Days_from_Event'] < 0]['Daily_Return'].mean()
post_event_return = snap_data[snap_data['Days_from_Event'] > 0]['Daily_Return'].mean()
event_day_return = snap_data[snap_data['Days_from_Event'] == 0]['Daily_Return'].iloc[0]

pre_event_ar = snap_data[snap_data['Days_from_Event'] < 0]['Abnormal_Return'].mean()
post_event_ar = snap_data[snap_data['Days_from_Event'] > 0]['Abnormal_Return'].mean()
event_day_ar = snap_data[snap_data['Days_from_Event'] == 0]['Abnormal_Return'].iloc[0]

# Get the last available day's return (may not be exactly day +14 due to weekends/holidays)
last_day = snap_data['Days_from_Event'].max()
last_day_return = snap_data[snap_data['Days_from_Event'] == last_day]['Cumulative_Return'].iloc[0]
last_day_car = snap_data[snap_data['Days_from_Event'] == last_day]['CAR'].iloc[0]

print(f"\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Event: Snapchat My AI Announcement")
print(f"Company: Snap Inc. (SNAP)")
print(f"Event Date: February 27, 2023")
print(f"Market Benchmark: NASDAQ-100 (QQQ)")
print(f"\nRAW RETURNS:")
print(f"Average daily return 14 days before: {pre_event_return*100:.2f}%")
print(f"Event day return: {event_day_return*100:.2f}%")
print(f"Average daily return 14 days after: {post_event_return*100:.2f}%")
print(f"Cumulative return through day +{last_day}: {last_day_return:.2f}%")
print(f"\nABNORMAL RETURNS (Market-Adjusted):")
print(f"Average abnormal return before event: {pre_event_ar*100:.2f}%")
print(f"Event day abnormal return: {event_day_ar*100:.2f}%")
print(f"Average abnormal return after event: {post_event_ar*100:.2f}%")
print(f"Cumulative Abnormal Return (CAR) through day +{last_day}: {last_day_car:.2f}%")
print(f"\nEvent day price: ${event_price:.2f}")
print(f"Last day price (day +{last_day}): ${snap_data[snap_data['Days_from_Event'] == last_day]['Close'].iloc[0]:.2f}")
print("="*80)

# Save data to CSV
output_filename = 'snapchat_performance.csv'
snap_data.to_csv(output_filename)
print(f"\nData saved to {output_filename}")
print(f"Columns saved: {list(snap_data.columns)}")
