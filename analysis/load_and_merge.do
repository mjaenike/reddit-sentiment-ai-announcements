* ==============================================================================
* Load and Merge Sentiment + Performance Data
* ==============================================================================

clear all
set more off

* ==============================================================================
* PART 1: Load Sentiment Data
* ==============================================================================

* Load the ALL_FIRMS daily sentiment file
import delimited "../data/sentiment/ALL_FIRMS_daily_sentiment.csv", clear varnames(1)

* Convert date variable to Stata date format
gen date_temp = date(date, "YMD")
format date_temp %td
drop date
rename date_temp date

* Keep key variables
keep date firm daily_vader_mean daily_post_count

* Label variables
label variable date "Date"
label variable firm "Company (Microsoft/Google/Adobe/Snapchat/Spotify)"
label variable daily_vader_mean "Daily Average Sentiment (VADER)"
label variable daily_post_count "Number of Posts"

* Save as temp file
tempfile sentiment_data
save `sentiment_data'

* ==============================================================================
* PART 2: Load Performance Data (all 5 firms)
* ==============================================================================

* Define firm list (lowercase for filenames)
local firms "microsoft google adobe snapchat spotify"

* Initialize counter
local counter = 0

* Loop through all firms
foreach firm of local firms {
    
    * Load firm performance data
    import delimited "../data/performance/`firm'_performance_nasdaq_benchmark.csv", clear
    
    * Add firm identifier (capitalize first letter)
    gen firm = proper("`firm'")
    
    * Keep observations within ±14 days
    keep if days_from_event >= -14 & days_from_event <= 14
    
    * Convert date
    gen date_temp = date(date, "YMD")
    format date_temp %td
    drop date
    rename date_temp date
    
    * Keep key variables
    keep date firm days_from_event abnormal_return car cumulative_return
    
    * Save or append
    if `counter' == 0 {
        tempfile performance_data
        save `performance_data'
    }
    else {
        append using `performance_data'
        save `performance_data', replace
    }
    
    local counter = `counter' + 1
}

* Load the combined performance data
use `performance_data', clear

* ==============================================================================
* PART 3: Merge Sentiment + Performance
* ==============================================================================

* Start with performance data (has exact event windows we want)
use `performance_data', clear

* Merge with sentiment data
merge 1:1 date firm using `sentiment_data', keep(master match)

* Check merge results
tab _merge
drop _merge

* Label merged variables
label variable days_from_event "Days from Event (0 = announcement)"
label variable abnormal_return "Daily Abnormal Return"
label variable car "Cumulative Abnormal Return"
label variable cumulative_return "Cumulative Raw Return"

* Sort
sort firm date

* ==============================================================================
* PART 4: Save Merged Dataset
* ==============================================================================

save "../data/merged_data.dta", replace

* Quick summary
describe
summarize

* Check for missing sentiment
count if missing(daily_vader_mean)

di "====================================================================="
di "MERGE COMPLETE!"
di "Saved to: ../data/merged_data.dta"
di "====================================================================="
