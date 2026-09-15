import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

PROCESSED_DATA_PATH = "data/processed/cleaned_jobs.csv"


def get_connection():
    """
    Opens a MySQL connection using credentials loaded from .env —
    never hardcoded, per the credential-handling setup from Week 2.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Failed to connect to MySQL: {e}")
        raise

def load_companies(conn, df: pd.DataFrame) -> None:
    """
    Inserts one row per unique company into the companies table.
    Uses INSERT IGNORE so re-running this script is safe — if a
    company_name already exists (UNIQUE constraint), MySQL silently
    skips that row instead of throwing a duplicate-key error and
    aborting the whole batch.
    """
    # Dedupe companies from the cleaned DataFrame — one row per unique name,
    # keeping the first occurrence of rating/size_bucket for that company
    companies_df = df.drop_duplicates(subset=["company_name"])[
        ["company_name", "company_rating", "company_size_bucket"]
    ]

    cursor = conn.cursor()
    insert_query = """
        INSERT IGNORE INTO companies (company_name, company_rating, company_size_bucket)
        VALUES (%s, %s, %s)
    """

    rows = [
        (
            row["company_name"] if pd.notnull(row["company_name"]) else None,
            float(row["company_rating"]) if pd.notnull(row["company_rating"]) else None,
            row["company_size_bucket"] if pd.notnull(row["company_size_bucket"]) else None,
        )
        for _, row in companies_df.iterrows()
    ]

    try:
        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"Inserted {cursor.rowcount} new companies (out of {len(rows)} unique company names found).")
    except Error as e:
        conn.rollback()
        print(f"Error loading companies, rolled back: {e}")
        raise
    finally:
        cursor.close()

import ast

def load_skills(conn, df: pd.DataFrame) -> set:
    """
    Extracts every unique skill name across all jobs and inserts into
    the skills table. skills_list was saved to CSV as a string
    representation of a Python list (CSV has no native list type), so
    we use ast.literal_eval to safely parse it back into a real list
    before extracting unique skill names.

    Returns the set of all unique skill names actually inserted, so
    load_job_skills (Step 5) can look up skill_ids without re-parsing.
    """
    def parse_skills_list(raw):
        if not isinstance(raw, str) or raw.strip() == "":
            return []
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return []

    df["skills_list_parsed"] = df["skills_list"].apply(parse_skills_list)

    all_skills = set()
    for skills in df["skills_list_parsed"]:
        all_skills.update(skills)

    cursor = conn.cursor()
    insert_query = "INSERT IGNORE INTO skills (skill_name) VALUES (%s)"
    rows = [(skill,) for skill in all_skills]

    try:
        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"Inserted {cursor.rowcount} new skills (out of {len(all_skills)} unique skill names found).")
    except Error as e:
        conn.rollback()
        print(f"Error loading skills, rolled back: {e}")
        raise
    finally:
        cursor.close()

    return all_skills

def load_jobs(conn, df: pd.DataFrame) -> None:
    """
    Inserts one row per job posting into the jobs table. Requires a
    company_name -> company_id lookup since jobs stores the foreign
    key, not the raw company name — this is the whole point of
    normalizing: company details (rating, size) live in ONE place
    (companies), not repeated across 23,201 job rows.
    """
    cursor = conn.cursor()

    # Build company_name -> company_id lookup from what's already in MySQL.
    # NOTE: this lookup is case-sensitive on the Python side, but MySQL's
    # collation merged some case-variant company names (Step 2) — so a
    # job row with "Bcforward" needs to match whichever spelling MySQL
    # actually kept. We handle this by looking up case-insensitively too.
    cursor.execute("SELECT company_id, company_name FROM companies")
    company_lookup = {name.lower(): cid for cid, name in cursor.fetchall()}

    insert_query = """
        INSERT IGNORE INTO jobs (
            job_id, company_id, job_title, role_category,
            location_raw, scraped_city, primary_city, work_mode,
            experience_raw, experience_min_yrs, experience_max_yrs,
            experience_tier, is_senior, is_fresher_friendly,
            salary_raw, salary_min_lpa, salary_max_lpa, salary_midpoint_lpa,
            salary_tier, salary_disclosed, salary_negotiable,
            job_description, posted_date_raw, posted_date, days_since_posted,
            job_url, data_source, scraped_at, scraped_month
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    def clean_val(val):
        return None if pd.isnull(val) else val

    rows = []
    skipped_no_company = 0

    for _, row in df.iterrows():
        company_name = row["company_name"]
        company_id = None
        if pd.notnull(company_name):
            company_id = company_lookup.get(str(company_name).lower())
            if company_id is None:
                skipped_no_company += 1

        rows.append((
            int(row["job_id"]), company_id, clean_val(row["job_title"]),
            clean_val(row["role_category"]), clean_val(row["location"]),
            clean_val(row["scraped_city"]), clean_val(row["primary_city"]),
            clean_val(row["work_mode"]), clean_val(row["experience_raw"]),
            clean_val(row.get("experience_min_yrs")), clean_val(row.get("experience_max_yrs")),
            None, None, None,  # experience_tier, is_senior, is_fresher_friendly -> Week 4 doesn't compute these yet
            clean_val(row["salary_raw"]), clean_val(row["salary_min_lpa"]),
            clean_val(row["salary_max_lpa"]), clean_val(row["salary_midpoint_lpa"]),
            None,  # salary_tier -> not yet computed
            clean_val(row.get("salary_disclosed")), None,  # salary_negotiable -> not yet computed
            clean_val(row["job_description"]), clean_val(row["posted_date_raw"]),
            clean_val(row["posted_date"]), None,  # days_since_posted -> not yet computed
            clean_val(row["job_url"]), clean_val(row["data_source"]),
            clean_val(row["scraped_at"]), None,  # scraped_month -> not yet computed
        ))

    try:
        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"Inserted {cursor.rowcount} new jobs (out of {len(rows)} rows processed).")
        print(f"Jobs with no matching company_id: {skipped_no_company}")
    except Error as e:
        conn.rollback()
        print(f"Error loading jobs, rolled back: {e}")
        raise
    finally:
        cursor.close()

def load_job_skills(conn, df: pd.DataFrame) -> None:
    """
    Populates the job_skills junction table — one row per (job_id, skill_id)
    pair, representing the many-to-many relationship between jobs and
    skills. Requires skill_name -> skill_id lookup, built the same
    case-insensitive way as the company lookup in load_jobs, since
    MySQL's collation merged some case-variant skill names too.
    """
    cursor = conn.cursor()

    cursor.execute("SELECT skill_id, skill_name FROM skills")
    skill_lookup = {name.lower(): sid for sid, name in cursor.fetchall()}

    insert_query = "INSERT IGNORE INTO job_skills (job_id, skill_id) VALUES (%s, %s)"

    rows = []
    skipped_no_skill = 0

    for _, row in df.iterrows():
        job_id = int(row["job_id"])
        skills = row.get("skills_list_parsed", [])

        if not isinstance(skills, list):
            continue

        for skill_name in skills:
            skill_id = skill_lookup.get(str(skill_name).lower())
            if skill_id is None:
                skipped_no_skill += 1
                continue
            rows.append((job_id, skill_id))

    try:
        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"Inserted {cursor.rowcount} job_skills rows (out of {len(rows)} pairs attempted).")
        print(f"Skill mentions with no matching skill_id: {skipped_no_skill}")
    except Error as e:
        conn.rollback()
        print(f"Error loading job_skills, rolled back: {e}")
        raise
    finally:
        cursor.close()

if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"Loaded {len(df)} rows from processed CSV.")

    conn = get_connection()
    print("Connected to MySQL successfully.")

    load_companies(conn, df)
    load_skills(conn, df)
    load_jobs(conn, df)
    load_job_skills(conn, df)

    conn.close()
    print("Connection closed.")