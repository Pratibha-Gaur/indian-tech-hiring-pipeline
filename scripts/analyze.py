import matplotlib
matplotlib.use("Agg")

import pandas as pd
from load_db import get_connection
import matplotlib.pyplot as plt
import os

CHARTS_DIR = "dashboard/charts"


def run_query(query: str) -> pd.DataFrame:
    """
    Runs a SQL query against the MySQL database and returns the
    result as a Pandas DataFrame — the shared entry point every
    chart-building function in this script will use.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


import matplotlib.pyplot as plt
import os

CHARTS_DIR = "dashboard/charts"


def chart_top_skills(top_n: int = 15) -> None:
    """
    Bar chart of the most in-demand skills, by mention count across
    all job postings.
    """
    query = f"""
        SELECT s.skill_name, COUNT(*) AS mention_count
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.skill_id
        GROUP BY s.skill_name
        ORDER BY mention_count DESC
        LIMIT {top_n}
    """
    df = run_query(query)

    os.makedirs(CHARTS_DIR, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.barh(df["skill_name"][::-1], df["mention_count"][::-1], color="#2b6cb0")
    plt.xlabel("Number of job postings mentioning this skill")
    plt.title(f"Top {top_n} In-Demand Skills — Indian Tech Job Market")
    plt.tight_layout()

    output_path = f"{CHARTS_DIR}/top_skills.png"
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved chart: {output_path}")


def chart_top_cities(top_n: int = 15) -> None:
    """
    Bar chart of the cities with the most job postings.
    """
    query = f"""
        SELECT primary_city, COUNT(*) AS job_count
        FROM jobs
        WHERE primary_city IS NOT NULL
        GROUP BY primary_city
        ORDER BY job_count DESC
        LIMIT {top_n}
    """
    df = run_query(query)

    os.makedirs(CHARTS_DIR, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.barh(df["primary_city"][::-1], df["job_count"][::-1], color="#2f855a")
    plt.xlabel("Number of job postings")
    plt.title(f"Top {top_n} Hiring Cities — Indian Tech Job Market")
    plt.tight_layout()

    output_path = f"{CHARTS_DIR}/top_cities.png"
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved chart: {output_path}")


def chart_salary_by_role() -> None:
    """
    Bar chart of average disclosed salary (LPA) by role category.
    Only includes rows with a parsed salary — undisclosed salaries
    are correctly excluded, not treated as zero.
    """
    query = """
        SELECT
            role_category,
            ROUND(AVG(salary_midpoint_lpa), 2) AS avg_salary_lpa,
            COUNT(*) AS job_count
        FROM jobs
        WHERE salary_midpoint_lpa IS NOT NULL AND role_category IS NOT NULL
        GROUP BY role_category
        ORDER BY avg_salary_lpa DESC
    """
    df = run_query(query)

    os.makedirs(CHARTS_DIR, exist_ok=True)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(df["role_category"], df["avg_salary_lpa"], color="#c05621")
    plt.ylabel("Average Salary (LPA)")
    plt.title("Average Salary by Role Category (Disclosed Salaries Only)")
    plt.xticks(rotation=30, ha="right")

    # Label each bar with its job_count, so low-sample-size bars are visible
    for bar, count in zip(bars, df["job_count"]):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                  f"n={count}", ha="center", fontsize=8)

    plt.tight_layout()

    output_path = f"{CHARTS_DIR}/salary_by_role.png"
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved chart: {output_path}")

def chart_work_mode() -> None:
    """
    Pie chart showing the proportion of job postings by work mode
    (On-site / Hybrid / Remote).
    """
    query = """
        SELECT work_mode, COUNT(*) AS job_count
        FROM jobs
        WHERE work_mode IS NOT NULL
        GROUP BY work_mode
        ORDER BY job_count DESC
    """
    df = run_query(query)

    os.makedirs(CHARTS_DIR, exist_ok=True)

    plt.figure(figsize=(7, 7))
    plt.pie(
        df["job_count"],
        labels=df["work_mode"],
        autopct="%1.1f%%",
        colors=["#2b6cb0", "#c05621", "#2f855a"],
        startangle=90,
    )
    plt.title("Work Mode Distribution — Indian Tech Job Postings")
    plt.tight_layout()

    output_path = f"{CHARTS_DIR}/work_mode.png"
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved chart: {output_path}")

def chart_hiring_trend() -> None:
    """
    Line chart of job posting volume over time, by month.
    NOTE: this dataset's posted_date only spans ~2 months (a short
    scraping window), so this chart shows a limited trend, not a
    full seasonal pattern — documented as a known limitation.
    """
    query = """
        SELECT
            DATE_FORMAT(posted_date, '%Y-%m') AS posted_month,
            COUNT(*) AS job_count
        FROM jobs
        WHERE posted_date IS NOT NULL
        GROUP BY posted_month
        ORDER BY posted_month
    """
    df = run_query(query)

    os.makedirs(CHARTS_DIR, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(df["posted_month"], df["job_count"], marker="o", color="#2b6cb0", linewidth=2)
    plt.xlabel("Month")
    plt.ylabel("Number of job postings")
    plt.title("Hiring Volume Trend by Month")
    for x, y in zip(df["posted_month"], df["job_count"]):
        plt.text(x, y + 200, str(y), ha="center", fontsize=9)
    plt.tight_layout()

    output_path = f"{CHARTS_DIR}/hiring_trend.png"
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved chart: {output_path}")


if __name__ == "__main__":

    chart_top_skills()
    chart_top_cities()
    chart_salary_by_role()
    chart_work_mode()
    chart_hiring_trend()
