# Data

## Included

- `merged_data.dta`: the daily firm-level analysis panel used for the regressions in the paper. It has 97 trading-day rows covering 5 firms, with 19–20 trading days per firm across a ±14 calendar-day window around each announcement. Built by `analysis/load_and_merge.do`.
- `merged_data.csv`: the same data in CSV format, for anyone without Stata.

## Variables

| Variable | Type | Description |
|---|---|---|
| `firm` | string | Company: Adobe, Google, Microsoft, Snapchat, Spotify |
| `date` | date | Trading day |
| `days_from_event` | integer | Calendar days from the AI announcement (0 = announcement day, range −14 to +13) |
| `abnormal_return` | decimal | Daily abnormal return: firm return minus NASDAQ-100 (QQQ) return. For example, 0.01 = 1% |
| `car` | percent | Cumulative abnormal return, summed outward from the announcement day. For example, 5.0 = 5% |
| `cumulative_return` | percent | Cumulative raw return relative to the announcement-day closing price |
| `daily_vader_mean` | −1 to 1 | Mean VADER compound sentiment of that day's Reddit posts and comments about the firm |
| `daily_post_count` | count | Number of Reddit posts and comments scored that day |

**Notes**

- `abnormal_return` is a decimal, while `car` and `cumulative_return` are in percent.
- Each firm's first day has no `abnormal_return`, because the first return needs a prior close. Days with no matching Reddit activity have missing sentiment, which is 5 rows in total.
- Weekend and holiday Reddit activity is matched to the nearest trading day.

## Not included

- **Raw Reddit posts and comments.** Reddit's API terms don't allow redistributing user content, and the raw text isn't needed to reproduce the results. The collectors in `sentiment/` show exactly how it was gathered.
- **Raw price downloads.** These can be regenerated with the scripts in `performance/`.
