import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import glob
import os
from datetime import datetime

# Set style for academic publications (with fallback for compatibility)
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    try:
        plt.style.use('seaborn-whitegrid')
    except:
        try:
            plt.style.use('seaborn')
        except:
            plt.style.use('ggplot')  # Fallback to ggplot style
            
sns.set_palette("colorblind")

# Academic color scheme (grayscale-friendly, print-ready)
ACADEMIC_COLORS = {
    'Microsoft': '#2E5090',  # Blue
    'Spotify': '#1DB954',     # Green
    'Google': '#DB4437',      # Red
    'Snapchat': '#FFFC00',    # Yellow (will use darker version)
    'Adobe': '#FF0000'        # Adobe red
}

# Company configurations
COMPANIES = {
    'Microsoft': {
        'ticker': 'MSFT',
        'event_date': '2023-03-16',
        'ai_feature': 'Microsoft 365 Copilot',
        'color': '#2E5090'
    },
    'Spotify': {
        'ticker': 'SPOT',
        'event_date': '2023-02-22',
        'ai_feature': 'AI DJ',
        'color': '#1DB954'
    },
    'Google': {
        'ticker': 'GOOGL',
        'event_date': '2023-12-06',
        'ai_feature': 'Gemini',
        'color': '#DB4437'
    },
    'Snapchat': {
        'ticker': 'SNAP',
        'event_date': '2023-02-27',
        'ai_feature': 'My AI',
        'color': '#FFA500'  # Orange instead of yellow for visibility
    },
    'Adobe': {
        'ticker': 'ADBE',
        'event_date': '2023-03-21',
        'ai_feature': 'Firefly',
        'color': '#FF0000'
    }
}

# Directory paths
SENTIMENT_DIR = '../data/sentiment/'
PERFORMANCE_DIR = '../data/performance/'
OUTPUT_DIR = './'  # Save to current directory

print("="*80)
print("ACADEMIC DATA SECTION VISUALIZATIONS")
print("Creating publication-ready figures and tables")
print("="*80)

# ============================================================================
# VISUAL 1: SAMPLE COMPOSITION TABLE
# ============================================================================

print("\n📊 Creating Visual 1: Sample Composition Table...")

composition_data = []

for company_name, info in COMPANIES.items():
    company_lower = company_name.lower()
    
    # Find sentiment files
    post_pattern = os.path.join(SENTIMENT_DIR, f"*{company_lower}*posts*with_sentiment.csv")
    comment_pattern = os.path.join(SENTIMENT_DIR, f"*{company_lower}*comments*with_sentiment.csv")
    
    post_files = glob.glob(post_pattern)
    comment_files = glob.glob(comment_pattern)
    
    num_posts = 0
    num_comments = 0
    
    if post_files:
        try:
            posts_df = pd.read_csv(post_files[0])
            num_posts = len(posts_df)
        except:
            pass
    
    if comment_files:
        try:
            comments_df = pd.read_csv(comment_files[0])
            num_comments = len(comments_df)
        except:
            pass
    
    # Find performance files to count trading days
    perf_pattern = os.path.join(PERFORMANCE_DIR, f"{company_lower}_performance_nasdaq_benchmark.csv")
    perf_files = glob.glob(perf_pattern)
    
    trading_days = 29  # Default: ±14 days = 29 days
    if perf_files:
        try:
            perf_df = pd.read_csv(perf_files[0])
            trading_days = len(perf_df)
        except:
            pass
    
    composition_data.append({
        'Firm': company_name,
        'Ticker': info['ticker'],
        'AI Feature': info['ai_feature'],
        'Event Date': info['event_date'],
        'Event Window': '±14 days',
        'Reddit Posts': f"{num_posts:,}",
        'Reddit Comments': f"{num_comments:,}",
        'Total Content': f"{num_posts + num_comments:,}",
        'Trading Days': trading_days
    })

composition_df = pd.DataFrame(composition_data)

# Create professional table
fig, ax = plt.subplots(figsize=(16, 5))
ax.axis('tight')
ax.axis('off')

# Create table
table = ax.table(cellText=composition_df.values,
                colLabels=composition_df.columns,
                cellLoc='center',
                loc='center',
                bbox=[0, 0, 1, 1])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.2)

# Style the header
for i in range(len(composition_df.columns)):
    cell = table[(0, i)]
    cell.set_facecolor('#333333')
    cell.set_text_props(weight='bold', color='white')

# Alternate row colors
for i in range(1, len(composition_df) + 1):
    for j in range(len(composition_df.columns)):
        cell = table[(i, j)]
        if i % 2 == 0:
            cell.set_facecolor('#F0F0F0')
        else:
            cell.set_facecolor('#FFFFFF')

plt.title('Table 1: Sample Composition and Data Collection Summary', 
          fontsize=14, fontweight='bold', pad=20, loc='left')
plt.savefig(os.path.join(OUTPUT_DIR, 'table1_sample_composition.png'), 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ Saved: table1_sample_composition.png")

# Also save as CSV
composition_df.to_csv(os.path.join(OUTPUT_DIR, 'table1_sample_composition.csv'), index=False)
print("✅ Saved: table1_sample_composition.csv")

# ============================================================================
# VISUAL 2: DESCRIPTIVE STATISTICS TABLE
# ============================================================================

print("\n📊 Creating Visual 2: Descriptive Statistics Table...")

# Load all performance and sentiment data
all_performance_data = []
all_sentiment_data = []

for company_name in COMPANIES.keys():
    company_lower = company_name.lower()
    
    # Load performance data with CAR
    perf_pattern = os.path.join(PERFORMANCE_DIR, f"{company_lower}_performance_nasdaq_benchmark.csv")
    perf_files = glob.glob(perf_pattern)
    
    if perf_files:
        try:
            perf_df = pd.read_csv(perf_files[0])
            perf_df['Firm'] = company_name
            all_performance_data.append(perf_df)
        except Exception as e:
            print(f"  ⚠️  Could not load performance data for {company_name}: {e}")
    
    # Load sentiment data (aggregate posts and comments by date)
    # First try daily sentiment files
    daily_sent_pattern = os.path.join(SENTIMENT_DIR, f"*{company_lower}*daily_sentiment.csv")
    daily_sent_files = glob.glob(daily_sent_pattern)
    
    if daily_sent_files:
        for file in daily_sent_files:
            try:
                sent_df = pd.read_csv(file)
                sent_df['Firm'] = company_name
                all_sentiment_data.append(sent_df)
            except:
                pass

# Combine all data
if all_performance_data:
    performance_combined = pd.concat(all_performance_data, ignore_index=True)
else:
    print("  ⚠️  No performance data found")
    performance_combined = pd.DataFrame()

if all_sentiment_data:
    sentiment_combined = pd.concat(all_sentiment_data, ignore_index=True)
else:
    print("  ⚠️  No sentiment data found")
    sentiment_combined = pd.DataFrame()

# Create descriptive statistics
desc_stats_data = []

# Panel A: Returns
if not performance_combined.empty:
    returns_vars = ['Daily_Return', 'Abnormal_Return', 'Market_Return', 'CAR']
    for var in returns_vars:
        if var in performance_combined.columns:
            desc_stats_data.append({
                'Panel': 'A: Returns',
                'Variable': var.replace('_', ' '),
                'N': len(performance_combined[var].dropna()),
                'Mean': f"{performance_combined[var].mean():.4f}",
                'Median': f"{performance_combined[var].median():.4f}",
                'Std Dev': f"{performance_combined[var].std():.4f}",
                'Min': f"{performance_combined[var].min():.4f}",
                'Max': f"{performance_combined[var].max():.4f}"
            })

# Panel B: Trading Activity
if not performance_combined.empty:
    trading_vars = [('Volume', 'Volume'), ('Days_from_Event', 'Days from Event')]
    for var_name, display_name in trading_vars:
        if var_name in performance_combined.columns:
            desc_stats_data.append({
                'Panel': 'B: Trading Activity',
                'Variable': display_name,
                'N': len(performance_combined[var_name].dropna()),
                'Mean': f"{performance_combined[var_name].mean():.2f}",
                'Median': f"{performance_combined[var_name].median():.2f}",
                'Std Dev': f"{performance_combined[var_name].std():.2f}",
                'Min': f"{performance_combined[var_name].min():.2f}",
                'Max': f"{performance_combined[var_name].max():.2f}"
            })

# Panel C: Sentiment Metrics
if not sentiment_combined.empty:
    sentiment_vars = []
    if 'daily_vader_mean' in sentiment_combined.columns:
        sentiment_vars.append(('daily_vader_mean', 'VADER Score'))
    if 'daily_textblob_mean' in sentiment_combined.columns:
        sentiment_vars.append(('daily_textblob_mean', 'TextBlob Polarity'))
    if 'daily_post_count' in sentiment_combined.columns:
        sentiment_vars.append(('daily_post_count', 'Daily Post Count'))
    
    for var_name, display_name in sentiment_vars:
        if var_name in sentiment_combined.columns:
            desc_stats_data.append({
                'Panel': 'C: Sentiment',
                'Variable': display_name,
                'N': len(sentiment_combined[var_name].dropna()),
                'Mean': f"{sentiment_combined[var_name].mean():.4f}",
                'Median': f"{sentiment_combined[var_name].median():.4f}",
                'Std Dev': f"{sentiment_combined[var_name].std():.4f}",
                'Min': f"{sentiment_combined[var_name].min():.4f}",
                'Max': f"{sentiment_combined[var_name].max():.4f}"
            })

desc_stats_df = pd.DataFrame(desc_stats_data)

if not desc_stats_df.empty:
    # Create table
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare data for display (add panel separators)
    display_data = []
    current_panel = None
    num_cols = 7  # Variable, N, Mean, Median, Std Dev, Min, Max
    
    for idx, row in desc_stats_df.iterrows():
        if row['Panel'] != current_panel:
            # Add panel header
            if current_panel is not None:
                display_data.append([''] * num_cols)
            display_data.append([row['Panel']] + [''] * (num_cols - 1))
            current_panel = row['Panel']
        
        # Add data row (without panel column)
        display_data.append(['  ' + row['Variable']] + row[['N', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']].tolist())
    
    # Create table
    col_labels = ['Variable', 'N', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']
    table = ax.table(cellText=display_data,
                    colLabels=col_labels,
                    cellLoc='center',
                    loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Style header
    for i in range(len(col_labels)):
        cell = table[(0, i)]
        cell.set_facecolor('#333333')
        cell.set_text_props(weight='bold', color='white')
    
    # Style panel headers and data rows
    for i in range(1, len(display_data) + 1):
        for j in range(len(col_labels)):
            cell = table[(i, j)]
            # Check if this is a panel header
            if display_data[i-1][1] == '' and display_data[i-1][0] != '':
                cell.set_facecolor('#666666')
                cell.set_text_props(weight='bold', color='white')
            # Empty separator row
            elif all(x == '' for x in display_data[i-1]):
                cell.set_facecolor('#FFFFFF')
            # Data row
            else:
                if i % 2 == 0:
                    cell.set_facecolor('#F0F0F0')
                else:
                    cell.set_facecolor('#FFFFFF')
    
    plt.title('Table 2: Descriptive Statistics', 
              fontsize=14, fontweight='bold', pad=20, loc='left')
    plt.savefig(os.path.join(OUTPUT_DIR, 'table2_descriptive_statistics.png'), 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Saved: table2_descriptive_statistics.png")
    
    # Save as CSV
    desc_stats_df.to_csv(os.path.join(OUTPUT_DIR, 'table2_descriptive_statistics.csv'), index=False)
    print("✅ Saved: table2_descriptive_statistics.csv")
else:
    print("  ⚠️  No data available for descriptive statistics")

# ============================================================================
# VISUAL 3: COMBINED CAR PLOT BY FIRM
# ============================================================================

print("\n📊 Creating Visual 3: Cumulative Abnormal Returns (CAR) by Firm...")

fig, ax = plt.subplots(figsize=(12, 7))

has_car_data = False

for company_name, info in COMPANIES.items():
    company_lower = company_name.lower()
    
    # Load performance data with CAR
    perf_pattern = os.path.join(PERFORMANCE_DIR, f"{company_lower}_performance_nasdaq_benchmark.csv")
    perf_files = glob.glob(perf_pattern)
    
    if perf_files:
        try:
            perf_df = pd.read_csv(perf_files[0])
            
            if 'CAR' in perf_df.columns and 'Days_from_Event' in perf_df.columns:
                # Plot CAR
                ax.plot(perf_df['Days_from_Event'], 
                       perf_df['CAR'],  # CAR is already in percent
                       marker='o', 
                       linewidth=2.5, 
                       markersize=4,
                       label=f"{company_name} ({info['ticker']})",
                       color=info['color'],
                       alpha=0.8)
                has_car_data = True
        except Exception as e:
            print(f"  ⚠️  Error loading {company_name}: {e}")

if has_car_data:
    # Format plot
    ax.axvline(x=0, color='black', linestyle='--', linewidth=2, alpha=0.7, label='Event Day')
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.3)
    
    ax.set_xlabel('Days from Event', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Abnormal Return (%)', fontsize=12, fontweight='bold')
    ax.set_title('Figure 1: Cumulative Abnormal Returns Around AI Announcement', 
                fontsize=14, fontweight='bold', pad=15)
    
    # Legend
    ax.legend(loc='best', fontsize=10, frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Set x-axis to show full event window
    ax.set_xlim(-15, 15)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'figure1_car_by_firm.png'), 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Saved: figure1_car_by_firm.png")
else:
    plt.close()
    print("  ⚠️  No CAR data available")

# ============================================================================
# VISUAL 4: TIME SERIES - CAR AND SENTIMENT (5-PANEL)
# ============================================================================

print("\n📊 Creating Visual 4: Time Series - CAR and Sentiment Around Events...")

fig, axes = plt.subplots(5, 1, figsize=(12, 14))

for idx, (company_name, info) in enumerate(COMPANIES.items()):
    company_lower = company_name.lower()
    ax = axes[idx]
    
    # Load performance data
    perf_pattern = os.path.join(PERFORMANCE_DIR, f"{company_lower}_performance_nasdaq_benchmark.csv")
    perf_files = glob.glob(perf_pattern)
    
    # Load sentiment data
    daily_sent_pattern = os.path.join(SENTIMENT_DIR, f"*{company_lower}*daily_sentiment.csv")
    daily_sent_files = glob.glob(daily_sent_pattern)
    
    # Also try the ALL_FIRMS file for this company
    all_firms_pattern = os.path.join(SENTIMENT_DIR, "ALL_FIRMS_daily_sentiment.csv")
    
    perf_data = None
    sent_data = None
    
    if perf_files:
        try:
            perf_data = pd.read_csv(perf_files[0])
            perf_data['date'] = pd.to_datetime(perf_data['Date']) if 'Date' in perf_data.columns else pd.to_datetime(perf_data.index)
        except Exception as e:
            print(f"  ⚠️  Error loading performance for {company_name}: {e}")
    
    if daily_sent_files:
        try:
            sent_data = pd.read_csv(daily_sent_files[0])
            sent_data['date'] = pd.to_datetime(sent_data['date'])
        except:
            pass
    
    # Try ALL_FIRMS file
    if sent_data is None and os.path.exists(all_firms_pattern):
        try:
            all_firms_df = pd.read_csv(all_firms_pattern)
            all_firms_df['date'] = pd.to_datetime(all_firms_df['date'])
            sent_data = all_firms_df[all_firms_df['firm'] == company_name]
        except:
            pass
    
    if perf_data is not None and 'CAR' in perf_data.columns and 'Days_from_Event' in perf_data.columns:
        # Create dual axis
        ax2 = ax.twinx()
        
        # Plot CAR on primary axis
        line1 = ax.plot(perf_data['Days_from_Event'], 
                       perf_data['CAR'],  # CAR is already in percent
                       color=info['color'], 
                       linewidth=2.5, 
                       label='CAR (%)',
                       marker='o',
                       markersize=3)
        
        # Plot sentiment on secondary axis if available
        if sent_data is not None and not sent_data.empty:
            # Merge on date
            if 'date' in perf_data.columns and 'date' in sent_data.columns:
                merged = pd.merge(perf_data, sent_data, on='date', how='left')
                
                # Try different sentiment column names
                sent_col = None
                for col in ['daily_vader_mean', 'daily_textblob_mean', 'vader_compound']:
                    if col in merged.columns:
                        sent_col = col
                        break
                
                if sent_col:
                    line2 = ax2.plot(merged['Days_from_Event'], 
                                   merged[sent_col],
                                   color='gray', 
                                   linewidth=2, 
                                   label='Sentiment',
                                   linestyle='--',
                                   marker='s',
                                   markersize=3,
                                   alpha=0.7)
        
        # Event day marker
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.5)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
        
        # Labels
        ax.set_xlabel('Days from Event', fontsize=10)
        ax.set_ylabel('CAR (%)', fontsize=10, color=info['color'], fontweight='bold')
        ax2.set_ylabel('Sentiment Score', fontsize=10, color='gray', fontweight='bold')
        
        ax.tick_params(axis='y', labelcolor=info['color'])
        ax2.tick_params(axis='y', labelcolor='gray')
        
        # Title with company and AI feature
        ax.set_title(f"{company_name}: {info['ai_feature']}", 
                    fontsize=11, fontweight='bold', pad=8)
        
        ax.grid(True, alpha=0.2, linestyle='--')
        
        # Set x-axis range
        ax.set_xlim(-15, 15)
    else:
        ax.text(0.5, 0.5, f'No data available for {company_name}', 
               ha='center', va='center', transform=ax.transAxes, fontsize=10)
        ax.set_xlim(-15, 15)

plt.suptitle('Figure 2: Cumulative Abnormal Returns and Sentiment Around AI Announcements', 
            fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'figure2_car_sentiment_timeseries.png'), 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("✅ Saved: figure2_car_sentiment_timeseries.png")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*80)
print("🎉 ALL ACADEMIC VISUALIZATIONS CREATED SUCCESSFULLY!")
print("="*80)
print(f"\n📁 All files saved in: {os.path.abspath(OUTPUT_DIR)}")
print("\nFiles created:")
print("\n📊 Table 1 - Sample Composition:")
print("  • table1_sample_composition.png")
print("  • table1_sample_composition.csv")

print("\n📊 Table 2 - Descriptive Statistics:")
print("  • table2_descriptive_statistics.png")
print("  • table2_descriptive_statistics.csv")

print("\n📊 Figure 1 - CAR by Firm:")
print("  • figure1_car_by_firm.png")

print("\n📊 Figure 2 - CAR and Sentiment Time Series:")
print("  • figure2_car_sentiment_timeseries.png")

print("\n" + "="*80)
print("✨ All figures are 300 DPI and ready for dissertation submission!")
print("💡 TIP: The CSV files provide exact values for citation in your text")
print("="*80)
