import re
import pandas as pd


def clean_salary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses salary_raw into salary_min_lpa, salary_max_lpa, salary_midpoint_lpa.
    'Not Disclosed' / 'Unpaid' / unparseable values become NULL, NOT zero —
    a hidden salary is not the same as a ₹0 salary, and letting zeros leak
    into averages would silently corrupt every salary analysis downstream.

    Handles two source units:
      - "X-Y Lacs PA"           -> already in LPA, used as-is
      - "X,XXX PA" / "X,XXX/month" -> raw rupees, converted to LPA
    """
    def to_lpa_from_rupees(rupee_str: str, is_monthly: bool) -> float:
        value = float(rupee_str.replace(",", ""))
        annual = value * 12 if is_monthly else value
        return round(annual / 100000, 2)  # 1 Lac = 100,000

    def parse_salary_range(raw_value):
        if not isinstance(raw_value, str):
            return (None, None)

        text = raw_value.strip()

        # Normalize case so "Not disclosed" / "not Disclosed" etc. all match
        if text.lower() in ("not disclosed", "unpaid"):
            return (None, None)

        # Pattern 1: "15-30 Lacs PA" -> already in LPA
        match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*Lacs", text, re.IGNORECASE)
        if match:
            return (float(match.group(1)), float(match.group(2)))

                # Pattern 1b: single value "5 Lacs PA" or "9.5 Cr PA" -> min == max
        match = re.search(r"^(\d+(?:\.\d+)?)\s*(Lacs|Cr)\s*PA$", text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            if match.group(2).lower().startswith("cr"):
                value *= 100  # 1 Crore = 100 Lacs
            return (value, value)

        # Pattern 1c: mixed-unit range "70 Lacs-1 Cr PA"
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(Lacs|Cr)\s*-\s*(\d+(?:\.\d+)?)\s*(Lacs|Cr)\s*PA",
            text, re.IGNORECASE
        )
        if match:
            low = float(match.group(1))
            if match.group(2).lower().startswith("cr"):
                low *= 100
            high = float(match.group(3))
            if match.group(4).lower().startswith("cr"):
                high *= 100
            return (low, high)

        # Pattern 2: "50,000-90,000 PA" or "50,000-90,000/month" -> raw rupee range
        match = re.search(r"([\d,]+)\s*-\s*([\d,]+)\s*(PA|/month)", text, re.IGNORECASE)
        if match:
            is_monthly = "month" in match.group(3).lower()
            low = to_lpa_from_rupees(match.group(1), is_monthly)
            high = to_lpa_from_rupees(match.group(2), is_monthly)
            return (low, high)

        # Pattern 3: "50,000 PA" or "15,000/month" -> single rupee value
        match = re.search(r"^([\d,]+)\s*(PA|/month)$", text, re.IGNORECASE)
        if match:
            is_monthly = "month" in match.group(2).lower()
            val = to_lpa_from_rupees(match.group(1), is_monthly)
            return (val, val)

        # Anything else unparseable -> NULL (fail loudly via logging, not silently)
        return (None, None)

    parsed = df["salary_raw"].apply(parse_salary_range)
    df["salary_min_lpa"] = parsed.apply(lambda x: x[0])
    df["salary_max_lpa"] = parsed.apply(lambda x: x[1])
    df["salary_midpoint_lpa"] = df.apply(
        lambda row: round((row["salary_min_lpa"] + row["salary_max_lpa"]) / 2, 2)
        if pd.notnull(row["salary_min_lpa"]) and pd.notnull(row["salary_max_lpa"])
        else None,
        axis=1
    )

    return df

# Known acronyms/mixed-case tech terms that .title() would otherwise mangle.
# Keys are lowercase for matching; values are the correct canonical form.
CANONICAL_SKILLS = {
    "sql": "SQL", "mysql": "MySQL", "nosql": "NoSQL", "postgresql": "PostgreSQL",
    "aws": "AWS", "gcp": "GCP", "api": "API", "html": "HTML", "css": "CSS",
    "php": "PHP", "ai": "AI", "ml": "ML", "erp": "ERP", "crm": "CRM",
    "javascript": "JavaScript", "react.js": "React.js", "node.js": "Node.js",
    "vue.js": "Vue.js", "powerbi": "Power BI", "excel": "Excel",
    "vba": "VBA", "etl": "ETL", "bi": "BI", "seo": "SEO", "hr": "HR",
}


CANONICAL_SKILLS = {
    "sql": "SQL", "mysql": "MySQL", "nosql": "NoSQL", "postgresql": "PostgreSQL",
    "aws": "AWS", "gcp": "GCP", "api": "API", "html": "HTML", "css": "CSS",
    "php": "PHP", "ai": "AI", "ml": "ML", "erp": "ERP", "crm": "CRM",
    "javascript": "JavaScript", "react.js": "React.js", "node.js": "Node.js",
    "vue.js": "Vue.js", "powerbi": "Power BI", "excel": "Excel",
    "vba": "VBA", "etl": "ETL", "bi": "BI", "seo": "SEO", "hr": "HR",
    "devops": "DevOps",
}

# Placeholder text that means "no real value" — should never become a skill
MISSING_VALUE_TOKENS = {"not available", "n/a", "na", "none", "-", "unknown"}


def clean_skills(df: pd.DataFrame) -> pd.DataFrame:
    def parse_skills(raw_value):
        if not isinstance(raw_value, str) or raw_value.strip() == "":
            return []

        if raw_value.strip().lower() in MISSING_VALUE_TOKENS:
            return []

        raw_skills = raw_value.split(",")
        cleaned = []
        seen = set()

        for skill in raw_skills:
            skill = skill.strip()
            if not skill or skill.lower() in MISSING_VALUE_TOKENS:
                continue

            lookup_key = skill.lower()

            if lookup_key in CANONICAL_SKILLS:
                normalized = CANONICAL_SKILLS[lookup_key]
            elif skill.isupper() and len(skill) <= 4:
                normalized = skill.upper()
            else:
                normalized = skill.title()

            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                cleaned.append(normalized)

        return cleaned

    df["skills_list"] = df["skills_required"].apply(parse_skills)
    return df

def clean_location(df: pd.DataFrame) -> pd.DataFrame:
    WORK_MODE_PREFIXES = ["hybrid - ", "remote - ", "on-site - ", "onsite - "]

    # Known duplicate spellings of the same city -> canonical name
    CITY_ALIASES = {
        "gurgaon": "Gurugram",
        "bombay": "Mumbai",
        "bangalore": "Bengaluru",
        "bangalore rural": "Bengaluru",
        "delhi / ncr": "Delhi/NCR",
        "delhi ncr": "Delhi/NCR",
        "ncr": "Delhi/NCR",
    }

    def parse_location(raw_value):
        if not isinstance(raw_value, str) or raw_value.strip() == "":
            return (None, False)

        text = raw_value.strip()

        if text.lower() == "remote":
            return ("Remote", False)

        cities = [c.strip() for c in text.split(",") if c.strip()]
        if len(cities) == 0:
            return (None, False)

        primary = cities[0]

        for prefix in WORK_MODE_PREFIXES:
            if primary.lower().startswith(prefix):
                primary = primary[len(prefix):].strip()
                break

        primary = re.sub(r"\s*\(.*?\)", "", primary).strip()
        primary = primary.title()

        if primary.lower() in CITY_ALIASES:
            primary = CITY_ALIASES[primary.lower()]

        is_multi = len(cities) > 1

        return (primary, is_multi)

    parsed = df["location"].apply(parse_location)
    df["primary_city"] = parsed.apply(lambda x: x[0])
    df["is_multi_city"] = parsed.apply(lambda x: x[1])

    return df
    
def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives 'posted_date' (an actual DATE) from posted_date_raw, which is
    relative text like "5 days ago" or "3+ weeks ago". Relative dates need
    an anchor point to become absolute — we use 'scraped_at' (when this
    row was actually scraped), NOT today's date, since scraping happened
    on a specific past date and "5 days ago" means 5 days before THAT
    moment, not 5 days before whenever we happen to run this script.

    "Starts in X months" is a future START date, not a POSTED date — it
    describes an entirely different concept, so we do NOT force it through
    the same "days ago" math. It becomes NULL for posted_date, with the
    original text preserved in posted_date_raw for reference.
    """
    def parse_posted_date(raw_value, scraped_at):
        if not isinstance(raw_value, str) or pd.isnull(scraped_at):
            return None

        text = raw_value.strip().lower()

        if text.startswith("starts in"):
            return None

        if "day" in text:
            match = re.search(r"(\d+)\s*day", text)
            if match:
                days = int(match.group(1))
                return (scraped_at - pd.Timedelta(days=days)).date()

        if "week" in text:
            match = re.search(r"(\d+)\+?\s*week", text)
            if match:
                weeks = int(match.group(1))
                return (scraped_at - pd.Timedelta(weeks=weeks)).date()

        if "month" in text:
            match = re.search(r"(\d+)\+?\s*month", text)
            if match:
                months = int(match.group(1))
                return (scraped_at - pd.Timedelta(days=months * 30)).date()

        return None

    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
    df["posted_date"] = df.apply(
        lambda row: parse_posted_date(row["posted_date_raw"], row["scraped_at"]),
        axis=1
    )

    return df

def save_processed_data(df: pd.DataFrame, path: str = "data/processed/cleaned_jobs.csv") -> None:
    """
    Saves the fully cleaned DataFrame to data/processed/. This becomes
    the input for load_db.py in Week 4 — nothing downstream should ever
    read the raw CSV directly again.
    """
    df.to_csv(path, index=False)
    print(f"\nSaved cleaned data to {path} ({len(df)} rows, {len(df.columns)} columns)")

if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from scripts.ingest import ingest_raw_data

    df = ingest_raw_data()
    df = clean_salary(df)
    df = clean_skills(df)
    df = clean_location(df)
    df = clean_dates(df)

    print(f"Cleaned {len(df)} rows.")
    print(f"Parsed salaries: {df['salary_min_lpa'].notnull().sum()}")
    print(f"Multi-city postings: {df['is_multi_city'].sum()}")
    print(f"Parsed posted_date: {df['posted_date'].notnull().sum()}")

    save_processed_data(df)