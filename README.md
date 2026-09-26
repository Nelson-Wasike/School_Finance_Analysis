# U.S. School District Finance, FY2012 - Revenue, Spending, and Funding Source Equity

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**A cleaning pipeline and per-pupil finance analysis built from the U.S. Census
Bureau's F-33 Annual Survey of School System Finances - 18,373 school districts,
FY2012.**

## The question

How much do U.S. school districts spend per student, how does that vary by
state, and does *where the money comes from* (local, state, or federal) predict
*how much* a district ultimately has to spend?

## Headline findings

- **Per-pupil revenue ranges from $7,321 (Idaho) to $28,197 (District of
  Columbia)** across states - a nearly 4x gap between the best- and
  least-resourced states in this dataset.
- **States that rely more on local funding spend significantly more per pupil**
  (r = 0.36), while **states relying more on federal funding spend significantly
  less** (r = -0.45). This is a well-documented pattern in U.S. education
  finance: federal funding (Title I, IDEA, etc.) is largely compensatory aid
  targeted at lower-resource districts, so a high federal share is a symptom of
  low overall resources, not a cause of high spending.
- **A small number of tiny special-education cooperative districts (7-57
  students) report per-pupil figures in the hundreds of thousands of dollars**
  - a real data-comparability issue, not an error, caught and handled explicitly
  (see "Data quality" below) rather than silently left in every chart.

## What's in this repo

```
schoolfinance-analysis/
├── data/
│   ├── raw/
│   │   └── sdf121a.txt                  # original Census F-33 export, 18,373 rows
│   └── processed/
│       ├── districts_clean.csv          # 11,173 unified districts, all with valid data
│       ├── districts_comparable.csv     # same, restricted to 100+ enrollment (10,929 districts)
│       └── state_summary.csv            # 51 states/DC, aggregated correctly (see below)
├── src/
│   └── clean.py                         # missing-code handling, filtering, per-pupil calculations
├── notebooks/
│   └── school_finance_analysis.ipynb  # full walkthrough with executed outputs
├── images/                              # 3 charts
├── reports/
│   ├── SchoolFinance_FY2012_Report.docx        # full written report
│   └── SchoolFinance_FY2012_Presentation.pptx  # slide deck
├── requirements.txt
└── README.md
```

## How the cleaning works

1. **Missing-value codes.** Census codes missing or not-applicable values as
   small negative numbers (-1, -2, -3, -9) rather than leaving cells blank -
   left as-is, these would be silently averaged in as real dollar amounts.
   Every negative code in a dollar or enrollment column is converted to a
   proper missing value before any calculation happens.
2. **Restricted to unified school districts** (`SCHLEV == "03"`) - the raw file
   also includes elementary-only, secondary-only, and non-operating education
   agencies, which aren't comparable to a full K-12 district on a per-pupil
   basis and would distort any ranking if mixed in.
3. **State-level per-pupil figures are (state total $) / (state total pupils),
   not an average of each district's own ratio.** Averaging district ratios
   would let a tiny district's number count exactly as much as a huge city
   district's - summing first, then dividing, weights every dollar and every
   student correctly.

## Data quality: the tiny-district outlier problem

A handful of special-education service cooperatives serve very small
enrollments (as few as 7 students) while reporting substantial regional
service budgets, which produces per-pupil figures over $1,000,000 -
mathematically correct, but meaningless for comparison against a normal
school district. `districts_comparable.csv` restricts to districts with 100+
enrolled students (10,929 of the original 11,173) specifically for
district-level comparisons and charts; the full, unrestricted file is kept
separately so nothing is silently discarded from the raw data.

**Data source:** [U.S. Census Bureau — Annual Survey of School System Finances (F-33)](https://www.census.gov/programs-surveys/school-finances.html)
