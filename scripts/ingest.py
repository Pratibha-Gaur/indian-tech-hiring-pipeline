import pandas as pd
import os

RAW_DATA_PATH = "data/raw/naukri_tech_jobs_raw.csv"

# Columns we trust from the source. The pre-computed/derived columns
# (salary_tier, experience_tier, is_senior, primary_city, skill_domain,
# days_since_posted, salary_midpoint_lpa, is_fresher_friendly,
# salary_negotiable) are intentionally excluded — we recompute these
# ourselves in clean.py instead of trusting old derived values.
EXPECTED_COLUMNS = [
    "job_id", "job_title", "company_name", "company_rating", "location",
    "scraped_city", "role_category", "experience_raw", "salary_raw",
    "salary_disclosed", "skills_required", "job_description",
    "posted_date_raw", "work_mode", "company_size_bucket", "job_url",
    "data_source", "scraped_at"
]

MIN_EXPECTED_ROWS = 20000  # sanity threshold — file should have ~23k rows


def ingest_raw_data(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    # 1. Verify the file exists before doing anything else
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found at: {path}")

    # 2. Load the CSV
    df = pd.read_csv(path)

    # 3. Verify all expected columns are present
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")

    # 4. Sanity check row count — fail loudly if the file looks truncated/corrupted
    if len(df) < MIN_EXPECTED_ROWS:
        raise ValueError(
            f"Row count too low: got {len(df)}, expected at least {MIN_EXPECTED_ROWS}. "
            "File may be truncated or corrupted."
        )

    # 5. Verify job_id has no duplicates (it's our primary key downstream)
    duplicate_count = df["job_id"].duplicated().sum()
    if duplicate_count > 0:
        raise ValueError(f"Found {duplicate_count} duplicate job_id values in raw data.")

    # 6. Keep ONLY the trusted raw columns — drop derived/pre-computed ones
    df = df[EXPECTED_COLUMNS].copy()

    return df


if __name__ == "__main__":
    df = ingest_raw_data()
    print(f"Ingested {len(df)} rows.")
    print(f"Columns loaded ({len(df.columns)} total): {list(df.columns)}")