"""
clean.py — Census Bureau F-33 Annual Survey of School System Finances (FY2012)

The raw file has one row per school system/district (18,373 rows) and ~200
columns of revenue and expenditure detail, plus a parallel set of FL_ columns
recording each value's imputation status (not used here). Missing or
not-applicable values are coded as small negative numbers (-1, -2, -3, -9)
rather than left blank, per standard Census convention — the first real job
of this script is converting those codes to proper missing values (NaN) so
they don't get treated as real dollar amounts.

This script keeps only SCHLEV == "03" — unified elementary-secondary school
districts — since mixing them with elementary-only, secondary-only, and
non-operating agencies (the other SCHLEV codes) would compare fundamentally
different types of entities on the same per-pupil basis.
"""
import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sdf121a.txt"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MISSING_CODES = {-1, -2, -3, -9}

# Column -> readable name, for every $ column used in this analysis.
# All dollar figures in the raw file are already in whole dollars (not
# thousands), confirmed against known per-pupil spending benchmarks.
MONEY_COLS = {
    "TOTALREV": "total_revenue",
    "TFEDREV": "federal_revenue",
    "TSTREV": "state_revenue",
    "TLOCREV": "local_revenue",
    "TOTALEXP": "total_expenditure",
    "TCURELSC": "current_expenditure_elsec",
    "TCURINST": "instruction_expenditure",
    "TCURSSVC": "support_services_expenditure",
    "TCUROTH": "other_current_expenditure",
    "TCAPOUT": "capital_outlay",
}
KEEP_COLS = ["LEAID", "NAME", "STNAME", "STABBR", "SCHLEV", "MEMBERSCH"] + list(MONEY_COLS.keys())


def load_raw() -> pd.DataFrame:
    return pd.read_csv(RAW_PATH, sep="\t", encoding="latin-1", usecols=KEEP_COLS, dtype=str)


def to_numeric_with_missing(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.where(~numeric.isin(MISSING_CODES), other=pd.NA)


def clean_districts(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw[raw["SCHLEV"] == "03"].copy()

    df["MEMBERSCH"] = to_numeric_with_missing(df["MEMBERSCH"])
    for col in MONEY_COLS:
        df[col] = to_numeric_with_missing(df[col])
    df = df.rename(columns=MONEY_COLS)

    # A district needs valid enrollment and valid revenue/expenditure to be
    # usable for a per-pupil analysis at all.
    df = df.dropna(subset=["MEMBERSCH", "total_revenue", "total_expenditure"])
    df = df[df["MEMBERSCH"] > 0]

    for money_col in MONEY_COLS.values():
        per_pupil_col = money_col.replace("_revenue", "_rev_per_pupil").replace("_expenditure", "_exp_per_pupil")
        if money_col == "capital_outlay":
            per_pupil_col = "capital_outlay_per_pupil"
        df[per_pupil_col] = (df[money_col] / df["MEMBERSCH"]).round(2)

    df = df.rename(columns={"NAME": "district_name", "STNAME": "state_name", "STABBR": "state_abbr", "MEMBERSCH": "enrollment"})
    return df.reset_index(drop=True)


def build_state_summary(districts: pd.DataFrame) -> pd.DataFrame:
    # State-level per-pupil figures are computed as (state total $) /
    # (state total pupils), NOT as an average of district-level per-pupil
    # ratios — the latter would let a tiny district's ratio count as much
    # as a huge one, which misrepresents the state as a whole.
    agg = districts.groupby("state_name").agg(
        state_abbr=("state_abbr", "first"),
        n_districts=("district_name", "count"),
        total_enrollment=("enrollment", "sum"),
        total_revenue=("total_revenue", "sum"),
        federal_revenue=("federal_revenue", "sum"),
        state_revenue=("state_revenue", "sum"),
        local_revenue=("local_revenue", "sum"),
        total_expenditure=("total_expenditure", "sum"),
        instruction_expenditure=("instruction_expenditure", "sum"),
        support_services_expenditure=("support_services_expenditure", "sum"),
        capital_outlay=("capital_outlay", "sum"),
    ).reset_index()

    agg["revenue_per_pupil"] = (agg["total_revenue"] / agg["total_enrollment"]).round(2)
    agg["federal_rev_per_pupil"] = (agg["federal_revenue"] / agg["total_enrollment"]).round(2)
    agg["state_rev_per_pupil"] = (agg["state_revenue"] / agg["total_enrollment"]).round(2)
    agg["local_rev_per_pupil"] = (agg["local_revenue"] / agg["total_enrollment"]).round(2)
    agg["expenditure_per_pupil"] = (agg["total_expenditure"] / agg["total_enrollment"]).round(2)
    agg["instruction_exp_per_pupil"] = (agg["instruction_expenditure"] / agg["total_enrollment"]).round(2)
    agg["federal_share_pct"] = (agg["federal_revenue"] / agg["total_revenue"] * 100).round(2)
    agg["state_share_pct"] = (agg["state_revenue"] / agg["total_revenue"] * 100).round(2)
    agg["local_share_pct"] = (agg["local_revenue"] / agg["total_revenue"] * 100).round(2)
    agg["instruction_share_of_exp_pct"] = (agg["instruction_expenditure"] / agg["total_expenditure"] * 100).round(2)

    return agg.sort_values("revenue_per_pupil", ascending=False).reset_index(drop=True)


def main():
    raw = load_raw()
    print(f"Raw: {raw.shape[0]} rows (all school levels)")

    districts = clean_districts(raw)
    print(f"Cleaned unified districts with valid data: {districts.shape[0]}")
    districts.to_csv(OUT_DIR / "districts_clean.csv", index=False)

    state_summary = build_state_summary(districts)
    state_summary.to_csv(OUT_DIR / "state_summary.csv", index=False)
    print(f"State summary: {state_summary.shape[0]} states/DC")


if __name__ == "__main__":
    main()
