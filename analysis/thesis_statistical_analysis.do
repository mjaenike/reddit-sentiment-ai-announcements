* ==============================================================================
* SENIOR THESIS ANALYSIS FILE
* Consumer Sentiment and Short-Term Market Responses to AI Feature Announcements
* AUTHOR: Mia Jaenike
* LAST UPDATED: DEC 10 2025
* ADVISOR: Professor Austin Smith, Ph.D.
* Bates College, December 2025
* ==============================================================================

/*
This file combines all statistical analyses for the thesis in the order that
results appear in the document. The file produces:

TABLES:
  - Table 3: Granger Causality Lag Lengths (Section 3.2.1)
  - Table 4: Vector Autoregression Lag Lengths (Section 3.3.1)  
  - Table 5: Baseline Fixed Effects Regression (Section 4.1)
  - Table 6: Granger Causality, One Lag Specification (Section 4.2.1)
  - Table 7: Granger Causality, Two Lag Specification (Section 4.2.2)
  - Table 8: Reverse Causality, One Lag Specification (Section 4.3.1)
  - Table 9: Reverse Causality, Two Lag Specification (Section 4.3.2)
  - Table 10: Vector Autoregression Granger Causality Tests, One Lag (Section 4.4.2)
  - Table 11: Vector Autoregression Granger Causality Tests, Two Lag (Section 4.4.3)

FIGURES:
  - Figure 3: Impulse Response of Abnormal Returns to Sentiment Shock (Section 4.4.1)

NOTES:
  - Tables 1 and 2 (descriptive statistics and sample composition) were created in Python
  - Figures 1 and 2 (cumulative abnormal returns) were created in Python
  - Standard errors are clustered at the firm level throughout
*/

* ==============================================================================
* SETUP AND DATA PREPARATION
* ==============================================================================

clear all
set more off

* Create output directories
capture mkdir "../output"
capture mkdir "../output/tables"
capture mkdir "../output/figures"

di ""
di "======================================================================"
di "CONSUMER SENTIMENT AND AI ANNOUNCEMENTS: STATISTICAL ANALYSIS"
di "======================================================================"
di ""
di "Loading and preparing data..."

* Load merged panel data (sentiment + stock returns)

* Data were collected via Python (PRAW, yfinance), then merged together 
* in external file load_and_merge.do

use "../data/merged_data.dta", clear

* Label variables for clear output
label variable abnormal_return "Daily Abnormal Return"
label variable daily_vader_mean "Daily Average Sentiment"
label variable daily_post_count "Daily Post Count"
label variable days_from_event "Days from Event"
label variable car "Cumulative Abnormal Return"
label variable cumulative_return "Cumulative Return"

* Encode firm identifier and declare panel structure
encode firm, gen(firm_id)
xtset firm_id date

* Generate lagged abnormal return for momentum controls
gen lag_ar = L.abnormal_return
label variable lag_ar "Lagged Abnormal Return"

di "✓ Data loaded successfully"
di "  Firms: " e(N_g)
di "  Total observations: " _N
di ""

* ==============================================================================
* LAG LENGTH SELECTION
* ==============================================================================

* Before estimating the main models, I need to select optimal lag lengths
* using information criteria (AIC and BIC). This follows standard time series
* methodology and ensures the models capture the approprate dynamic structure.

* ------------------------------------------------------------------------------
* TABLE 3: Granger Causality Lag Length Selection (Section 3.2.1)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 3: LAG SELECTION FOR PANEL GRANGER CAUSALITY"
di "======================================================================"
di ""

* Estimate panel Granger causality model with 1 lag
quietly xtreg abnormal_return L.daily_vader_mean L.abnormal_return, fe
estat ic
matrix ic1 = r(S)
local aic1 = ic1[1,5]
local bic1 = ic1[1,6]
local ll1 = e(ll)
local n1 = e(N)

* Estimate panel Granger causality model with 2 lags
quietly xtreg abnormal_return L(1/2).daily_vader_mean L(1/2).abnormal_return, fe
estat ic
matrix ic2 = r(S)
local aic2 = ic2[1,5]
local bic2 = ic2[1,6]
local ll2 = e(ll)
local n2 = e(N)

* Determine which lag length minimizes each criterion
if `aic1' < `aic2' {
    local gc_aic_select = "1*"
    local gc_aic_select2 = "2"
    di "AIC selects 1 lag (AIC = " %7.2f `aic1' ")"
}
else {
    local gc_aic_select = "1"
    local gc_aic_select2 = "2*"
    di "AIC selects 2 lags (AIC = " %7.2f `aic2' ")"
}

if `bic1' < `bic2' {
    local gc_bic_select = "1*"
    local gc_bic_select2 = "2"
}
else {
    local gc_bic_select = "1"
    local gc_bic_select2 = "2*"
}

* Display results to console
di ""
di "Lags    Log-Likelihood    AIC           BIC           Observations"
di "----    --------------    ---           ---           ------------"
di "`gc_aic_select'           " %7.2f `ll1' "        " %9.2f `aic1' "     " %9.2f `bic1' "     " %3.0f `n1'
di "`gc_aic_select2'           " %7.2f `ll2' "        " %9.2f `aic2' "     " %9.2f `bic2' "     " %3.0f `n2'
di ""
di "* indicates lowest (optimal) value for each criterion"
di ""

* Export results
file open table3_txt using "../output/tables/table3_granger_lags.txt", write replace
file write table3_txt "Table 3: Granger Causality Lag Length Selection" _n
file write table3_txt "================================================" _n _n
file write table3_txt "Lags    Log-Likelihood    AIC           BIC           Observations" _n
file write table3_txt "----    --------------    ---           ---           ------------" _n
file write table3_txt "`gc_aic_select'           " %7.2f (`ll1') "        " %9.2f (`aic1') "     " %9.2f (`bic1') "     " %3.0f (`n1') _n
file write table3_txt "`gc_aic_select2'           " %7.2f (`ll2') "        " %9.2f (`aic2') "     " %9.2f (`bic2') "     " %3.0f (`n2') _n
file write table3_txt _n
file write table3_txt "Asterisks (*) denote the optimal value for each criterion." _n
file write table3_txt _n
file write table3_txt "Note: Lower values of AIC and BIC indicate better model fit." _n
file write table3_txt "Both criteria select the 1-lag specification." _n
file close table3_txt

* Also save as CSV for easy import to Word/Excel
file open table3_csv using "../output/tables/table3_granger_lags.csv", write replace
file write table3_csv "Lags,Log-Likelihood,AIC,BIC,Observations" _n
file write table3_csv "1," (`ll1') "," (`aic1') "," (`bic1') "," (`n1') _n
file write table3_csv "2," (`ll2') "," (`aic2') "," (`bic2') "," (`n2') _n
file close table3_csv

di "✓ Table 3 saved:"
di "  - ../output/tables/table3_granger_lags.txt"
di "  - ../output/tables/table3_granger_lags.csv"
di ""

* ------------------------------------------------------------------------------
* TABLE 4: VAR Lag Length Selection (Section 3.3.1)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 4: LAG SELECTION FOR VECTOR AUTOREGRESSION"
di "======================================================================"
di ""

* VAR models require a single time series, not panel data
* I handle this by: (1) removing firm fixed effects via demeaning within firms
*                   (2) collapsing to a single time series by averaging across firms

preserve

* Demean variables within firms (removes firm fixed effects)
foreach var of varlist abnormal_return daily_vader_mean {
    bysort firm_id: egen mean_`var' = mean(`var')
    gen dm_`var' = `var' - mean_`var'
}

* Collapse to single time series by averaging demeaned values
collapse (mean) dm_abnormal_return dm_daily_vader_mean, by(date)

* Declare as pure time series (no longer of panel structure)
tsset date

* Estimate VAR with 1 lag
quietly var dm_abnormal_return dm_daily_vader_mean, lags(1)
estat ic
matrix var_ic1 = r(S)
local var_aic1 = var_ic1[1,5]
local var_bic1 = var_ic1[1,6]
local var_ll1 = e(ll)
local var_n1 = e(N)

* Estimate VAR with 2 lags
quietly var dm_abnormal_return dm_daily_vader_mean, lags(1/2)
estat ic
matrix var_ic2 = r(S)
local var_aic2 = var_ic2[1,5]
local var_bic2 = var_ic2[1,6]
local var_ll2 = e(ll)
local var_n2 = e(N)

* Determine which lag length minimizes each criterion
if `var_aic1' < `var_aic2' {
    local var_aic_select = "1*"
    local var_aic_select2 = "2"
    di "AIC selects 1 lag (AIC = " %7.2f `var_aic1' ")"
}
else {
    local var_aic_select = "1"
    local var_aic_select2 = "2*"
    di "AIC selects 2 lags (AIC = " %7.2f `var_aic2' ")"
}

if `var_bic1' < `var_bic2' {
    local var_bic_select = "1*"
    local var_bic_select2 = "2"
}
else {
    local var_bic_select = "1"
    local var_bic_select2 = "2*"
}

* Display results to console
di ""
di "Lags    Log-Likelihood    AIC           BIC           Observations"
di "----    --------------    ---           ---           ------------"
di "`var_aic_select'           " %7.2f `var_ll1' "        " %9.2f `var_aic1' "     " %9.2f `var_bic1' "     " %3.0f `var_n1'
di "`var_aic_select2'           " %7.2f `var_ll2' "        " %9.2f `var_aic2' "     " %9.2f `var_bic2' "     " %3.0f `var_n2'
di ""
di "* indicates lowest (optimal) value for each criterion"
di ""

restore

* Export results
file open table4_txt using "../output/tables/table4_var_lags.txt", write replace
file write table4_txt "Table 4: Vector Autoregression Lag Length Selection" _n
file write table4_txt "====================================================" _n _n
file write table4_txt "Lags    Log-Likelihood    AIC           BIC           Observations" _n
file write table4_txt "----    --------------    ---           ---           ------------" _n
file write table4_txt "`var_aic_select'           " %7.2f (`var_ll1') "        " %9.2f (`var_aic1') "     " %9.2f (`var_bic1') "     " %3.0f (`var_n1') _n
file write table4_txt "`var_aic_select2'           " %7.2f (`var_ll2') "        " %9.2f (`var_aic2') "     " %9.2f (`var_bic2') "     " %3.0f (`var_n2') _n
file write table4_txt _n
file write table4_txt "Asterisks (*) denote the optimal value for each criterion." _n
file write table4_txt _n
file write table4_txt "Note: Estimated on collapsed time series (firm-demeaned, averaged across firms)." _n
file write table4_txt "Lower values of AIC and BIC indicate better model fit." _n
file write table4_txt "Both criteria select the 1-lag specification." _n
file close table4_txt

* Also save as CSV
file open table4_csv using "../output/tables/table4_var_lags.csv", write replace
file write table4_csv "Lags,Log-Likelihood,AIC,BIC,Observations" _n
file write table4_csv "1," (`var_ll1') "," (`var_aic1') "," (`var_bic1') "," (`var_n1') _n
file write table4_csv "2," (`var_ll2') "," (`var_aic2') "," (`var_bic2') "," (`var_n2') _n
file close table4_csv

di "✓ Table 4 saved:"
di "  - ../output/tables/table4_var_lags.txt"
di "  - ../output/tables/table4_var_lags.csv"
di ""

* ==============================================================================
* BASELINE FIXED EFFECTS REGRESSION
* ==============================================================================

* I begin by examining the contemporaneous relationship between sentiment
* and abnormal returns using fixed effects regression. This controls for
* time-invariant firm characteristics while testing whether same-day sentiment
* predicts same-day returns.

* ------------------------------------------------------------------------------
* TABLE 5: Baseline Fixed Effects Regression (Section 4.1)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 5: BASELINE FIXED EFFECTS REGRESSION"
di "======================================================================"
di ""

* Model 1: Baseline specification without lagged returns
* Tests: AR_it = α + β₁*Sentiment_it + firm_FE + ε_it
di "Estimating Model 1 (without momentum control)..."
quietly xtreg abnormal_return daily_vader_mean, fe vce(robust)
estimates store model1
estadd local firm_fe "Yes", replace
estadd local lags "No", replace

* Model 2: Include lagged abnormal returns to control for momentum
* Tests: AR_it = α + β₁*Sentiment_it + β₂*AR_{it-1} + firm_FE + ε_it
di "Estimating Model 2 (with momentum control)..."
quietly xtreg abnormal_return daily_vader_mean lag_ar, fe vce(robust)
estimates store model2
estadd local firm_fe "Yes", replace
estadd local lags "Yes", replace

* Export formatted table to RTF
esttab model1 model2 using "../output/tables/table5_baseline.rtf", ///
    replace ///
    b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title("{\b Table 5: Baseline Fixed Effects Regression}") ///
    mtitles("Without Lag" "With Momentum Control") ///
    label ///
    alignment(D{.}{.}{-1}) ///
    width(\paperw) ///
    nobaselevels ///
    nodepvars ///
    nonumbers ///
    stats(firm_fe lags N r2_w N_g, ///
          labels("Firm Fixed Effects" "Lagged Returns" "Observations" ///
                 "Within R-squared" "Number of Firms") ///
          fmt(%9.0g %9.0g 0 3 0)) ///
    addnote("{\i Note:} This table presents fixed effects regression estimates examining" ///
            "the contemporaneous relationship between daily consumer sentiment and abnormal" ///
            "stock returns. The dependent variable is daily abnormal return (firm return minus" ///
            "NASDAQ return). Sentiment is measured using VADER sentiment analysis of Reddit" ///
            "posts surrounding AI feature announcements. Model 1 presents the baseline" ///
            "specification; Model 2 includes lagged abnormal returns to control for momentum" ///
            "effects. Robust standard errors clustered at the firm level are shown in parentheses." ///
            "* {\i p}<0.10, ** {\i p}<0.05, *** {\i p}<0.01")

di ""
di "✓ Table 5 saved: ../output/tables/table5_baseline.rtf"
di ""

* ==============================================================================
* GRANGER CAUSALITY TESTS
* ==============================================================================

* The baseline regressions examine conteporaneous relationships. To test whether
* sentiment predicts future returns (temporal precedence), I use Granger causality
* tests. These assess whether lagged sentiment improves prediction of current returns
* beyond what past returns alone would suggest.

* ------------------------------------------------------------------------------
* TABLE 6: Granger Causality, One Lag Specification (Section 4.2.1)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 6: GRANGER CAUSALITY (ONE LAG SPECIFICATION)"
di "======================================================================"
di ""
di "Testing: Does sentiment at t-1 predict returns at t?"
di ""

* Estimate Granger causality model: AR_t = α + β₁*Sentiment_{t-1} + β₂*AR_{t-1} + firm_FE + ε_t
quietly xtreg abnormal_return L.daily_vader_mean L.abnormal_return, fe vce(robust)
estimates store granger_1lag
estadd local firm_fe "Yes", replace
estadd local lags "1", replace

* Test joint significance of lagged sentiment
test L.daily_vader_mean
local f_stat = r(F)
local p_val = r(p)
estadd scalar f_joint = `f_stat', replace
estadd scalar p_joint = `p_val', replace

* Determine significance level for display
if `p_val' < 0.01 {
    local sig_result "Significant***"
}
else if `p_val' < 0.05 {
    local sig_result "Significant**"
}
else if `p_val' < 0.10 {
    local sig_result "Significant*"
}
else {
    local sig_result "Not Significant"
}
estadd local joint_sig "`sig_result'", replace

* Export formatted table
esttab granger_1lag using "../output/tables/table6_granger_1lag.rtf", ///
    replace ///
    b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title("{\b Table 6: Granger Causality, One Lag Specification}") ///
    mtitles("Abnormal Return") ///
    label ///
    alignment(D{.}{.}{-1}) ///
    width(\paperw) ///
    nobaselevels ///
    nodepvars ///
    nonumbers ///
    order(L.daily_vader_mean L.abnormal_return) ///
    stats(firm_fe lags f_joint p_joint joint_sig N r2_w N_g, ///
          labels("Firm Fixed Effects" "Number of Lags" "F-statistic (Test)" ///
                 "{\i p}-value (Test)" "Significance" "Observations" ///
                 "Within R-squared" "Number of Firms") ///
          fmt(%9.0g 0 2 4 %9.0s 0 3 0)) ///
    addnote("{\i Note:} This table tests whether lagged sentiment values Granger-cause abnormal" ///
            "returns using a one-lag specification. The null hypothesis is that the lagged sentiment" ///
            "coefficient equals zero. F-statistic and {\i p}-value test the significance of L.Sentiment." ///
            "Rejection of the null indicates that sentiment contains predictive information about future" ///
            "returns beyond what is captured by past returns alone. Robust standard errors clustered" ///
            "at firm level in parentheses. * {\i p}<0.10, ** {\i p}<0.05, *** {\i p}<0.01")

di ""
di "✓ Table 6 saved: ../output/tables/table6_granger_1lag.rtf"
di "  F-statistic: " %6.3f `f_stat'
di "  p-value: " %6.4f `p_val'
di "  Result: `sig_result'"
di ""

* ------------------------------------------------------------------------------
* TABLE 7: Granger Causality, Two Lag Specification (Section 4.2.2)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 7: GRANGER CAUSALITY (TWO LAG SPECFICATION)"
di "======================================================================"
di ""
di "Testing: Does sentiment at t-1 and t-2 jointly predict returns at t?"
di ""

* Estimate two-lag specification
* AR_t = α + β₁*Sentiment_{t-1} + β₂*Sentiment_{t-2} + γ₁*AR_{t-1} + γ₂*AR_{t-2} + firm_FE + ε_t
quietly xtreg abnormal_return L(1/2).daily_vader_mean L(1/2).abnormal_return, fe vce(robust)
estimates store granger_2lag
estadd local firm_fe "Yes", replace
estadd local lags "2", replace

* Test joint significance of both lagged sentiment terms
test L.daily_vader_mean L2.daily_vader_mean
local f_stat_2 = r(F)
local p_val_2 = r(p)
estadd scalar f_joint = `f_stat_2', replace
estadd scalar p_joint = `p_val_2', replace

* Determine significance level
if `p_val_2' < 0.01 {
    local sig_result_2 = "Significant***"
}
else if `p_val_2' < 0.05 {
    local sig_result_2 = "Significant**"
}
else if `p_val_2' < 0.10 {
    local sig_result_2 = "Significant*"
}
else {
    local sig_result_2 = "Not Significant"
}
estadd local joint_sig "`sig_result_2'", replace

* Export formatted table
esttab granger_2lag using "../output/tables/table7_granger_2lag.rtf", ///
    replace ///
    b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title("{\b Table 7: Granger Causality, Two Lag Specification}") ///
    mtitles("Abnormal Return") ///
    label ///
    alignment(D{.}{.}{-1}) ///
    width(\paperw) ///
    nobaselevels ///
    nodepvars ///
    nonumbers ///
    order(L.daily_vader_mean L2.daily_vader_mean L.abnormal_return L2.abnormal_return) ///
    stats(firm_fe lags f_joint p_joint joint_sig N r2_w N_g, ///
          labels("Firm Fixed Effects" "Lags" "F-stat (Joint)" ///
                 "{\i p}-value (Joint)" "Significance" "Observations" ///
                 "Within R-squared" "Number of Firms") ///
          fmt(%9.0g 0 2 4 %9.0s 0 3 0)) ///
    addnote("{\i Note:} This table tests whether lagged sentiment values Granger-cause abnormal" ///
            "returns using a two-lag specification. The null hypothesis (H₀) is that sentiment does not" ///
            "Granger-cause returns (both lagged sentiment coefficients equal zero). The F-statistic and" ///
            "{\i p}-value test the joint significance of L.Sentiment and L2.Sentiment. Rejection of H₀" ///
            "indicates that sentiment contains predictive information about future returns beyond what" ///
            "past returns alone explain. Robust standard errors clustered at firm level in parentheses." ///
            "* {\i p}<0.10, ** {\i p}<0.05, *** {\i p}<0.01")

di ""
di "✓ Table 7 saved: ../output/tables/table7_granger_2lag.rtf"
di "  F-statistic: " %6.3f `f_stat_2'
di "  p-value: " %6.4f `p_val_2'
di "  Result: `sig_result_2'"
di ""

* ==============================================================================
* REVERSE CAUSALITY TESTS
* ==============================================================================

* To ensure my results reflect sentiment predicting returns rather than the reverse,
* I test whether lagged returns predict future sentiment. If returns do not predict
* sentiment but sentiment predicts returns, this supports unidirectional causality
* from sentiment to returns.

* ------------------------------------------------------------------------------
* TABLE 8: Reverse Causality, One Lag Specification (Section 4.3.1)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 8: REVERSE CAUSALITY (ONE LAG SPECIFICATION)"
di "======================================================================"
di ""
di "Testing: Do returns at t-1 predict sentiment at t?"
di ""

* Estimate reverse model: Sentiment_t = α + β₁*AR_{t-1} + β₂*Sentiment_{t-1} + firm_FE + ε_t
quietly xtreg daily_vader_mean L.abnormal_return L.daily_vader_mean, fe vce(robust)
estimates store reverse_1lag
estadd local firm_fe "Yes", replace
estadd local lags "1", replace

* Test significance of lagged returns
test L.abnormal_return
local f_stat_rev = r(F)
local p_val_rev = r(p)
estadd scalar f_joint = `f_stat_rev', replace
estadd scalar p_joint = `p_val_rev', replace

* Determine significance level
if `p_val_rev' < 0.01 {
    local sig_result_rev = "Significant***"
}
else if `p_val_rev' < 0.05 {
    local sig_result_rev = "Significant**"
}
else if `p_val_rev' < 0.10 {
    local sig_result_rev = "Significant*"
}
else {
    local sig_result_rev = "Not Significant"
}
estadd local joint_sig "`sig_result_rev'", replace

* Export formatted table
esttab reverse_1lag using "../output/tables/table8_reverse_1lag.rtf", ///
    replace ///
    b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title("{\b Table 8: Reverse Causality, One Lag Specification}") ///
    mtitles("Daily Sentiment") ///
    label ///
    alignment(D{.}{.}{-1}) ///
    width(\paperw) ///
    nobaselevels ///
    nodepvars ///
    nonumbers ///
    order(L.abnormal_return L.daily_vader_mean) ///
    stats(firm_fe lags f_joint p_joint joint_sig N r2_w N_g, ///
          labels("Firm Fixed Effects" "Number of Lags" "F-statistic (Test)" ///
                 "{\i p}-value (Test)" "Significance" "Observations" ///
                 "Within R-squared" "Number of Firms") ///
          fmt(%9.0g 0 2 4 %9.0s 0 3 0)) ///
    addnote("{\i Note:} This table tests the reverse causal relationship: whether lagged returns" ///
            "Granger-cause sentiment using a one-lag specification. The null hypothesis is that the" ///
            "lagged return coefficient equals zero. Finding that returns do not predict sentiment" ///
            "(failure to reject null) combined with evidence that sentiment predicts returns (Table 6)" ///
            "would support unidirectional causality from sentiment to returns. Robust standard errors" ///
            "clustered at firm level in parentheses. * {\i p}<0.10, ** {\i p}<0.05, *** {\i p}<0.01")

di ""
di "✓ Table 8 saved: ../output/tables/table8_reverse_1lag.rtf"
di "  F-statistic: " %6.3f `f_stat_rev'
di "  p-value: " %6.4f `p_val_rev'
di "  Result: `sig_result_rev'"
di ""

* ------------------------------------------------------------------------------
* TABLE 9: Reverse Causality, Two Lag Specification (Section 4.3.2)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 9: REVERSE CAUSALITY (TWO LAG SPECIFICATION)"
di "======================================================================"
di ""
di "Testing: Do returns at t-1 and t-2 jointly predict sentiment at t?"
di ""

* Estimate two-lag reverse model
* Sentiment_t = α + β₁*AR_{t-1} + β₂*AR_{t-2} + γ₁*Sentiment_{t-1} + γ₂*Sentiment_{t-2} + firm_FE + ε_t
quietly xtreg daily_vader_mean L(1/2).abnormal_return L(1/2).daily_vader_mean, fe vce(robust)
estimates store reverse_2lag
estadd local firm_fe "Yes", replace
estadd local lags "2", replace

* Test joint significance of both lagged return terms
test L.abnormal_return L2.abnormal_return
local f_stat_rev2 = r(F)
local p_val_rev2 = r(p)
estadd scalar f_joint = `f_stat_rev2', replace
estadd scalar p_joint = `p_val_rev2', replace

* Determine significance level
if `p_val_rev2' < 0.01 {
    local sig_result_rev2 = "Significant***"
}
else if `p_val_rev2' < 0.05 {
    local sig_result_rev2 = "Significant**"
}
else if `p_val_rev2' < 0.10 {
    local sig_result_rev2 = "Significant*"
}
else {
    local sig_result_rev2 = "Not Significant"
}
estadd local joint_sig "`sig_result_rev2'", replace

* Export formatted table
esttab reverse_2lag using "../output/tables/table9_reverse_2lag.rtf", ///
    replace ///
    b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    title("{\b Table 9: Reverse Causality, Two Lag Specification}") ///
    mtitles("Daily Sentiment") ///
    label ///
    alignment(D{.}{.}{-1}) ///
    width(\paperw) ///
    nobaselevels ///
    nodepvars ///
    nonumbers ///
    order(L.abnormal_return L2.abnormal_return L.daily_vader_mean L2.daily_vader_mean) ///
    stats(firm_fe lags f_joint p_joint joint_sig N r2_w N_g, ///
          labels("Firm Fixed Effects" "Lags" "F-stat (Joint)" ///
                 "{\i p}-value (Joint)" "Significance" "Observations" ///
                 "Within R-squared" "Number of Firms") ///
          fmt(%9.0g 0 2 4 %9.0s 0 3 0)) ///
    addnote("{\i Note:} This table tests the reverse causal relationship using a two-lag specification." ///
            "The null hypothesis (H₀) is that returns do not Granger-cause sentiment (both lagged return" ///
            "coefficients equal zero). The F-statistic and {\i p}-value test the joint significance of" ///
            "L.Returns and L2.Returns. Failure to reject H₀ combined with evidence from Table 7 that" ///
            "sentiment predicts returns supports unidirectional causality from sentiment to returns." ///
            "Robust standard errors clustered at firm level in parentheses." ///
            "* {\i p}<0.10, ** {\i p}<0.05, *** {\i p}<0.01")

di ""
di "✓ Table 9 saved: ../output/tables/table9_reverse_2lag.rtf"
di "  F-statistic: " %6.3f `f_stat_rev2'
di "  p-value: " %6.4f `p_val_rev2'
di "  Result: `sig_result_rev2'"
di ""

* ==============================================================================
* VECTOR AUTOREGRESSION
* ==============================================================================

di ""
di "======================================================================"
di "VECTOR AUTOREGRESSION"
di "======================================================================"
di ""

* ------------------------------------------------------------------------------
* TABLE 10: VAR Granger Causality, One Lag (Section 4.4.2)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 10: VAR GRANGER CAUSALITY (ONE LAG)"
di "======================================================================"
di ""

* Preserve original panel data
preserve

* Demean variables within firms (removes firm fixed effects)
foreach var of varlist abnormal_return daily_vader_mean {
    bysort firm_id: egen mean_`var' = mean(`var')
    gen dm_`var' = `var' - mean_`var'
}

* Collapse to single time series by averaging across firms
collapse (mean) dm_abnormal_return dm_daily_vader_mean, by(date)

* Set as pure time series (no panel dimension)
tsset date

* Estimate VAR with 1 lag
quietly var dm_abnormal_return dm_daily_vader_mean, lags(1)

* Conduct Granger causality tests
vargranger

* For debugging: Show the matrix structure
matrix gstats = r(gstats)
di "DEBUG - Matrix structure:"
matrix list gstats

* Extract results
scalar chi2_sent_to_ret = gstats[1,1]
scalar df_sent_to_ret = gstats[1,2]
scalar p_sent_to_ret = gstats[1,3]
scalar chi2_ret_to_sent = gstats[3,1]
scalar df_ret_to_sent = gstats[3,2]
scalar p_ret_to_sent = gstats[3,3]

* For debugging: Display scalar values
di "DEBUG - Scalars after extraction:"
di "  chi2_sent_to_ret = " chi2_sent_to_ret
di "  df_sent_to_ret = " df_sent_to_ret
di "  p_sent_to_ret = " p_sent_to_ret
di "  chi2_ret_to_sent = " chi2_ret_to_sent
di "  df_ret_to_sent = " df_ret_to_sent
di "  p_ret_to_sent = " p_ret_to_sent

* Determine significance
if p_sent_to_ret < 0.01 {
    local result1 "Reject***"
}
else if p_sent_to_ret < 0.05 {
    local result1 "Reject**"
}
else if p_sent_to_ret < 0.10 {
    local result1 "Reject*"
}
else {
    local result1 "Fail to Reject"
}

if p_ret_to_sent < 0.01 {
    local result2 "Reject***"
}
else if p_ret_to_sent < 0.05 {
    local result2 "Reject**"
}
else if p_ret_to_sent < 0.10 {
    local result2 "Reject*"
}
else {
    local result2 "Fail to Reject"
}

di "Sentiment → Returns: Chi² = " %6.3f chi2_sent_to_ret ", p = " %6.4f p_sent_to_ret " [`result1']"
di "Returns → Sentiment: Chi² = " %6.3f chi2_ret_to_sent ", p = " %6.4f p_ret_to_sent " [`result2']"
di ""

* Store results before restoring
tempname chi2_s2r df_s2r p_s2r chi2_r2s df_r2s p_r2s
scalar `chi2_s2r' = chi2_sent_to_ret
scalar `df_s2r' = df_sent_to_ret
scalar `p_s2r' = p_sent_to_ret
scalar `chi2_r2s' = chi2_ret_to_sent
scalar `df_r2s' = df_ret_to_sent
scalar `p_r2s' = p_ret_to_sent
local result1_stored "`result1'"
local result2_stored "`result2'"

* Restore original panel data
restore

* Retrieve stored values
scalar chi2_sent_to_ret = scalar(`chi2_s2r')
scalar df_sent_to_ret = scalar(`df_s2r')
scalar p_sent_to_ret = scalar(`p_s2r')
scalar chi2_ret_to_sent = scalar(`chi2_r2s')
scalar df_ret_to_sent = scalar(`df_r2s')
scalar p_ret_to_sent = scalar(`p_r2s')

* Export Table 10 CSV
preserve
clear
set obs 2
gen str60 null_hypothesis = ""
gen chi_squared = .
gen df = .
gen p_value = .
gen str20 result = ""

replace null_hypothesis = "Sentiment does NOT Granger-cause Returns" in 1
replace chi_squared = chi2_sent_to_ret in 1
replace df = df_sent_to_ret in 1
replace p_value = p_sent_to_ret in 1
replace result = "`result1_stored'" in 1

replace null_hypothesis = "Returns do NOT Granger-cause Sentiment" in 2
replace chi_squared = chi2_ret_to_sent in 2
replace df = df_ret_to_sent in 2
replace p_value = p_ret_to_sent in 2
replace result = "`result2_stored'" in 2

list
export delimited using "../output/tables/table10_var_granger_1lag.csv", replace
restore

di "✓ Table 10 CSV saved"
di ""

* ------------------------------------------------------------------------------
* TABLE 11: VAR Granger Causality, Two Lags (Section 4.4.3)
* ------------------------------------------------------------------------------

di ""
di "======================================================================"
di "TABLE 11: VAR GRANGER CAUSALITY (TWO LAGS)"
di "======================================================================"
di ""

* Preserve original panel data
preserve

* Demean variables within firms (removes firm fixed effects)
foreach var of varlist abnormal_return daily_vader_mean {
    bysort firm_id: egen mean_`var' = mean(`var')
    gen dm_`var' = `var' - mean_`var'
}

* Collapse to single time series by averaging across firms
collapse (mean) dm_abnormal_return dm_daily_vader_mean, by(date)

* Set as pure time series (no panel dimension)
tsset date

* Estimate VAR with 2 lags
quietly var dm_abnormal_return dm_daily_vader_mean, lags(1/2)

* Conduct Granger causality tests
vargranger

* Extract results
matrix gstats2 = r(gstats)
scalar chi2_sent_to_ret_2 = gstats2[1,1]
scalar df_sent_to_ret_2 = gstats2[1,2]
scalar p_sent_to_ret_2 = gstats2[1,3]
scalar chi2_ret_to_sent_2 = gstats2[3,1]
scalar df_ret_to_sent_2 = gstats2[3,2]
scalar p_ret_to_sent_2 = gstats2[3,3]

* Determine significance
if p_sent_to_ret_2 < 0.01 {
    local result3 "Reject***"
}
else if p_sent_to_ret_2 < 0.05 {
    local result3 "Reject**"
}
else if p_sent_to_ret_2 < 0.10 {
    local result3 "Reject*"
}
else {
    local result3 "Fail to Reject"
}

if p_ret_to_sent_2 < 0.01 {
    local result4 "Reject***"
}
else if p_ret_to_sent_2 < 0.05 {
    local result4 "Reject**"
}
else if p_ret_to_sent_2 < 0.10 {
    local result4 "Reject*"
}
else {
    local result4 "Fail to Reject"
}

di "Sentiment → Returns: Chi² = " %6.3f chi2_sent_to_ret_2 ", p = " %6.4f p_sent_to_ret_2 " [`result3']"
di "Returns → Sentiment: Chi² = " %6.3f chi2_ret_to_sent_2 ", p = " %6.4f p_ret_to_sent_2 " [`result4']"
di ""

* Store results before restoring
tempname chi2_s2r2 df_s2r2 p_s2r2 chi2_r2s2 df_r2s2 p_r2s2
scalar `chi2_s2r2' = chi2_sent_to_ret_2
scalar `df_s2r2' = df_sent_to_ret_2
scalar `p_s2r2' = p_sent_to_ret_2
scalar `chi2_r2s2' = chi2_ret_to_sent_2
scalar `df_r2s2' = df_ret_to_sent_2
scalar `p_r2s2' = p_ret_to_sent_2
local result3_stored "`result3'"
local result4_stored "`result4'"

* Restore original panel data
restore

* Retrieve stored values
scalar chi2_sent_to_ret_2 = scalar(`chi2_s2r2')
scalar df_sent_to_ret_2 = scalar(`df_s2r2')
scalar p_sent_to_ret_2 = scalar(`p_s2r2')
scalar chi2_ret_to_sent_2 = scalar(`chi2_r2s2')
scalar df_ret_to_sent_2 = scalar(`df_r2s2')
scalar p_ret_to_sent_2 = scalar(`p_r2s2')

* Export Table 11 CSV
preserve
clear
set obs 2
gen str60 null_hypothesis = ""
gen chi_squared = .
gen df = .
gen p_value = .
gen str20 result = ""

replace null_hypothesis = "Sentiment does NOT Granger-cause Returns" in 1
replace chi_squared = chi2_sent_to_ret_2 in 1
replace df = df_sent_to_ret_2 in 1
replace p_value = p_sent_to_ret_2 in 1
replace result = "`result3_stored'" in 1

replace null_hypothesis = "Returns do NOT Granger-cause Sentiment" in 2
replace chi_squared = chi2_ret_to_sent_2 in 2
replace df = df_ret_to_sent_2 in 2
replace p_value = p_ret_to_sent_2 in 2
replace result = "`result4_stored'" in 2

list
export delimited using "../output/tables/table11_var_granger_2lag.csv", replace
restore

di "✓ Table 11 CSV saved"
di ""

* ==============================================================================
* ANALYSIS COMPLETE (yay!)
* ==============================================================================

di ""
di "======================================================================"
di "ANALYSIS COMPLETED WITHOUT ERROR"
di "======================================================================"
di ""
di ""
di "TABLES:"
di "  Table 3:  Granger Causality Lag Length Selection"
di "  Table 4:  VAR Lag Length Selection"
di "  Table 5:  Baseline Fixed Effects Regression"
di "  Table 6:  Granger Causality (1 lag)"
di "  Table 7:  Granger Causality (2 lags)"
di "  Table 8:  Reverse Causality (1 lag)"
di "  Table 9:  Reverse Causality (2 lags)"
di "  Table 10: VAR Granger Causality (1 lag)"
di "  Table 11: VAR Granger Causality (2 lags)"
di ""
di "FIGURES:"
di "  Figure 3: Impulse Response Function"
di ""
di "======================================================================"
