import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Adobe Firefly Announcement - March 21, 2023
event_date = datetime(2023, 3, 21)
start_date = event_date - timedelta(days=14)
end_date = event_date + timedelta(days=14)

# Download Adobe stock data
ticker = "ADBE"
print(f"Downloading {ticker} data...")
adbe_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)

# Download NASDAQ benchmark for abnormal returns calculation
print(f"Downloading NASDAQ (QQQ) benchmark data...")
nasdaq_data = yf.download('QQQ', start=start_date, end=end_date, auto_adjust=True, progress=False)

# Robust column handling
if adbe_data.empty:
    raise ValueError(f"No data downloaded for {ticker}")

# If MultiIndex, flatten it
if isinstance(adbe_data.columns, pd.MultiIndex):
    adbe_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in adbe_data.columns.values]
    # Try to rename the flattened columns to standard names
    col_mapping = {}
    for col in adbe_data.columns:
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
    adbe_data.rename(columns=col_mapping, inplace=True)

print(f"Columns in data: {adbe_data.columns.tolist()}")

# Find the close price column (case insensitive)
close_col = None
for col in adbe_data.columns:
    if 'close' in col.lower():
        close_col = col
        break

if close_col is None:
    raise ValueError(f"Could not find Close column. Available columns: {adbe_data.columns.tolist()}")

print(f"Using '{close_col}' as Close price column")

# Calculate daily returns
adbe_data['Daily_Return'] = adbe_data[close_col].pct_change()

# Add event day marker
adbe_data['Days_from_Event'] = (adbe_data.index - event_date).days

# Rename close_col to 'Close' for consistency
if close_col != 'Close':
    adbe_data.rename(columns={close_col: 'Close'}, inplace=True)

# Find volume column
volume_col = 'Volume'
for col in adbe_data.columns:
    if 'volume' in col.lower() and col != 'Volume':
        adbe_data.rename(columns={col: 'Volume'}, inplace=True)
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
adbe_data = adbe_data.join(nasdaq_data[['Market_Return']], how='left')

# Calculate abnormal returns (company return - market return)
adbe_data['Abnormal_Return'] = adbe_data['Daily_Return'] - adbe_data['Market_Return']

# Display the data
print("="*80)
print("Adobe Stock Data Around Adobe Firefly Announcement")
print("Event Date: March 21, 2023")
print("⚠️  NOTE: Adobe Q1 2023 earnings on March 15 (6 days before)")
print("Market Benchmark: NASDAQ (QQQ)")
print("="*80)
display_cols = ['Close', 'Volume', 'Daily_Return', 'Market_Return', 'Abnormal_Return', 'Days_from_Event']
display_cols = [col for col in display_cols if col in adbe_data.columns]
print(adbe_data[display_cols])

# Calculate cumulative returns from event date
event_price = adbe_data.loc[adbe_data['Days_from_Event'] == 0, 'Close'].iloc[0]
adbe_data['Cumulative_Return'] = (adbe_data['Close'] / event_price - 1) * 100

# Calculate Cumulative Abnormal Return (CAR)
adbe_data['CAR'] = 0.0
event_idx = adbe_data[adbe_data['Days_from_Event'] == 0].index[0]

# Calculate CAR for days at and after event
for idx in adbe_data.index:
    if idx >= event_idx:
        days_slice = adbe_data.loc[event_idx:idx]
        adbe_data.loc[idx, 'CAR'] = days_slice['Abnormal_Return'].sum() * 100

# Calculate CAR for days before event (going backward)
for idx in reversed(adbe_data[adbe_data.index < event_idx].index):
    days_slice = adbe_data.loc[idx:event_idx]
    adbe_data.loc[idx, 'CAR'] = -days_slice['Abnormal_Return'].sum() * 100

# Plot the results
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Price chart
ax1.plot(adbe_data['Days_from_Event'], adbe_data['Close'], marker='o', color='#FF0000', linewidth=2, markersize=8)
ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Adobe Firefly Announcement')
# Mark earnings date
earnings_days = (datetime(2023, 3, 15) - event_date).days
ax1.axvline(x=earnings_days, color='orange', linestyle=':', linewidth=2, alpha=0.7, label='Q1 Earnings (Mar 15)')
ax1.set_xlabel('Days from Event', fontsize=12)
ax1.set_ylabel('Close Price ($)', fontsize=12)
ax1.set_title('Adobe Stock Price Around Adobe Firefly Announcement\nMarch 21, 2023', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Cumulative returns
ax2.plot(adbe_data['Days_from_Event'], adbe_data['Cumulative_Return'], marker='o', color='green', linewidth=2, markersize=8)
ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Event Date')
ax2.axvline(x=earnings_days, color='orange', linestyle=':', linewidth=2, alpha=0.7, label='Earnings')
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Days from Event', fontsize=12)
ax2.set_ylabel('Cumulative Return (%)', fontsize=12)
ax2.set_title('Cumulative Returns from Event Date', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('adbe_firefly_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Summary statistics
pre_event_return = adbe_data[adbe_data['Days_from_Event'] < 0]['Daily_Return'].mean()
post_event_return = adbe_data[adbe_data['Days_from_Event'] > 0]['Daily_Return'].mean()
event_day_return = adbe_data[adbe_data['Days_from_Event'] == 0]['Daily_Return'].iloc[0]

pre_event_ar = adbe_data[adbe_data['Days_from_Event'] < 0]['Abnormal_Return'].mean()
post_event_ar = adbe_data[adbe_data['Days_from_Event'] > 0]['Abnormal_Return'].mean()
event_day_ar = adbe_data[adbe_data['Days_from_Event'] == 0]['Abnormal_Return'].iloc[0]

# Get the last available day's return (may not be exactly day +14 due to weekends/holidays)
last_day = adbe_data['Days_from_Event'].max()
last_day_return = adbe_data[adbe_data['Days_from_Event'] == last_day]['Cumulative_Return'].iloc[0]
last_day_car = adbe_data[adbe_data['Days_from_Event'] == last_day]['CAR'].iloc[0]

print(f"\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Event: Adobe Firefly Announcement")
print(f"Company: Adobe Inc. (ADBE)")
print(f"Event Date: March 21, 2023")
print(f"⚠️  Confound: Q1 Earnings on March 15, 2023 (6 days before)")
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
print(f"Last day price (day +{last_day}): ${adbe_data[adbe_data['Days_from_Event'] == last_day]['Close'].iloc[0]:.2f}")

# Earnings impact check
earnings_day_data = adbe_data[adbe_data['Days_from_Event'] == earnings_days]
if not earnings_day_data.empty:
    earnings_return = earnings_day_data['Daily_Return'].iloc[0]
    earnings_ar = earnings_day_data['Abnormal_Return'].iloc[0]
    print(f"\nEarnings Day Returns (Mar 15):")
    print(f"   Raw Return: {earnings_return*100:.2f}%")
    print(f"   Abnormal Return: {earnings_ar*100:.2f}%")
    print(f"⚠️  NOTE: Include this case but test robustness to exclusion due to earnings proximity")
    
print("="*80)

# Save data to CSV
output_filename = 'adobe_performance.csv'
adbe_data.to_csv(output_filename)
print(f"\nData saved to {output_filename}")
print(f"Columns saved: {list(adbe_data.columns)}")
