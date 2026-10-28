import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Google Gemini Announcement - December 6, 2023
event_date = datetime(2023, 12, 6)
start_date = event_date - timedelta(days=14)
end_date = event_date + timedelta(days=14)

# Download Google (Alphabet) stock data
# Note: GOOGL is Class A shares (with voting rights), GOOG is Class C (no voting rights)
# GOOGL is more commonly traded and has higher volume
ticker = "GOOGL"
print(f"Downloading {ticker} data...")
googl_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

# Download NASDAQ benchmark for abnormal returns calculation
print(f"Downloading NASDAQ (QQQ) benchmark data...")
nasdaq_data = yf.download('QQQ', start=start_date, end=end_date, auto_adjust=True, progress=False)

# Robust column handling
if googl_data.empty:
    raise ValueError(f"No data downloaded for {ticker}")

# If MultiIndex, flatten it
if isinstance(googl_data.columns, pd.MultiIndex):
    googl_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in googl_data.columns.values]
    # Try to rename the flattened columns to standard names
    col_mapping = {}
    for col in googl_data.columns:
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
    googl_data.rename(columns=col_mapping, inplace=True)

print(f"Columns in data: {googl_data.columns.tolist()}")

# Find the close price column (case insensitive)
close_col = None
for col in googl_data.columns:
    if 'close' in col.lower():
        close_col = col
        break

if close_col is None:
    raise ValueError(f"Could not find Close column. Available columns: {googl_data.columns.tolist()}")

print(f"Using '{close_col}' as Close price column")

# Calculate daily returns
googl_data['Daily_Return'] = googl_data[close_col].pct_change()

# Add event day marker
googl_data['Days_from_Event'] = (googl_data.index - event_date).days

# Rename close_col to 'Close' for consistency
if close_col != 'Close':
    googl_data.rename(columns={close_col: 'Close'}, inplace=True)

# Find volume column
volume_col = 'Volume'
for col in googl_data.columns:
    if 'volume' in col.lower() and col != 'Volume':
        googl_data.rename(columns={col: 'Volume'}, inplace=True)
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
googl_data = googl_data.join(nasdaq_data[['Market_Return']], how='left')

# Calculate abnormal returns (company return - market return)
googl_data['Abnormal_Return'] = googl_data['Daily_Return'] - googl_data['Market_Return']

# Display the data
print("="*80)
print("Google (Alphabet) Stock Data Around Gemini Announcement")
print("Event Date: December 6, 2023")
print("Market Benchmark: NASDAQ (QQQ)")
print("="*80)
display_cols = ['Close', 'Volume', 'Daily_Return', 'Market_Return', 'Abnormal_Return', 'Days_from_Event']
display_cols = [col for col in display_cols if col in googl_data.columns]
print(googl_data[display_cols])

# Calculate cumulative returns from event date
event_price = googl_data.loc[googl_data['Days_from_Event'] == 0, 'Close'].iloc[0]
googl_data['Cumulative_Return'] = (googl_data['Close'] / event_price - 1) * 100

# Calculate Cumulative Abnormal Return (CAR)
googl_data['CAR'] = 0.0
event_idx = googl_data[googl_data['Days_from_Event'] == 0].index[0]

# Calculate CAR for days at and after event
for idx in googl_data.index:
    if idx >= event_idx:
        days_slice = googl_data.loc[event_idx:idx]
        googl_data.loc[idx, 'CAR'] = days_slice['Abnormal_Return'].sum() * 100

# Calculate CAR for days before event (going backward)
for idx in reversed(googl_data[googl_data.index < event_idx].index):
    days_slice = googl_data.loc[idx:event_idx]
    googl_data.loc[idx, 'CAR'] = -days_slice['Abnormal_Return'].sum() * 100

# Plot the results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price chart
ax1.plot(googl_data['Days_from_Event'], googl_data['Close'], marker='o', color='#4285F4', linewidth=2, markersize=8)
ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Google Gemini Announcement')
ax1.set_xlabel('Days from Event', fontsize=12)
ax1.set_ylabel('Close Price ($)', fontsize=12)
ax1.set_title('Google (Alphabet) Stock Price Around Gemini Announcement\nDecember 6, 2023', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Cumulative returns
ax2.plot(googl_data['Days_from_Event'], googl_data['Cumulative_Return'], marker='o', color='green', linewidth=2, markersize=8)
ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event Date')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Days from Event', fontsize=12)
ax2.set_ylabel('Cumulative Return (%)', fontsize=12)
ax2.set_title('Cumulative Returns from Event Date', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('googl_gemini_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Summary statistics
pre_event_return = googl_data[googl_data['Days_from_Event'] < 0]['Daily_Return'].mean()
post_event_return = googl_data[googl_data['Days_from_Event'] > 0]['Daily_Return'].mean()
event_day_return = googl_data[googl_data['Days_from_Event'] == 0]['Daily_Return'].iloc[0]

pre_event_ar = googl_data[googl_data['Days_from_Event'] < 0]['Abnormal_Return'].mean()
post_event_ar = googl_data[googl_data['Days_from_Event'] > 0]['Abnormal_Return'].mean()
event_day_ar = googl_data[googl_data['Days_from_Event'] == 0]['Abnormal_Return'].iloc[0]

# Get the last available day's return (may not be exactly day +7 due to weekends/holidays)
last_day = googl_data['Days_from_Event'].max()
last_day_return = googl_data[googl_data['Days_from_Event'] == last_day]['Cumulative_Return'].iloc[0]
last_day_car = googl_data[googl_data['Days_from_Event'] == last_day]['CAR'].iloc[0]

print(f"\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Event: Google Gemini Announcement")
print(f"Company: Alphabet Inc. (GOOGL)")
print(f"Event Date: December 6, 2023")
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
print(f"Last day price (day +{last_day}): ${googl_data[googl_data['Days_from_Event'] == last_day]['Close'].iloc[0]:.2f}")
print("="*80)

# Save data to CSV
output_filename = 'google_performance.csv'
googl_data.to_csv(output_filename)
print(f"\nData saved to {output_filename}")
print(f"Columns saved: {list(googl_data.columns)}")
