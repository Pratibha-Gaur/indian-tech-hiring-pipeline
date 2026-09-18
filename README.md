# Indian Tech Job Market Analysis & Hiring Trends Pipeline

An end-to-end data engineering pipeline that ingests, cleans, normalizes, and analyzes 23,201 real Indian tech job postings — turning messy scraped data into a queryable relational database, SQL-driven insights, and a published analytics report.

**Live report:** https://pratibha-gaur.github.io/indian-tech-hiring-pipeline/

---

## Overview

Raw job-posting data is rarely clean. This project takes a real-world Naukri.com dataset — full of inconsistent salary formats, messy skill listings, duplicate city spellings, and relative date strings — and builds a complete pipeline around it: ingestion, cleaning, relational database design, SQL analysis, and visualization.

The goal wasn't just to produce charts, but to demonstrate the full data engineering lifecycle end-to-end, with defensible, explainable decisions at every step.

## Problem Statement

Job postings scraped from Naukri.com arrive as a single flat file with inconsistent formats across nearly every field — salaries mixing Lacs/Crores/raw rupees, skills as unstructured comma-separated text, city names with duplicate spellings (Gurgaon/Gurugram, Bangalore/Bengaluru), and dates written as relative text ("3+ weeks ago"). This project transforms that raw data into a structured, analyzable form and answers real questions about the Indian tech hiring market: which skills are in demand, which cities and companies are hiring most, and how compensation varies by role and location.

## Objectives

- Design a normalized relational schema instead of a flat single-table structure
- Build a defensible, explainable data cleaning pipeline that never silently corrupts data (e.g., never converts "undisclosed salary" to ₹0)
- Load cleaned data into MySQL with proper foreign key relationships
- Answer meaningful hiring/skills/salary questions through SQL
- Visualize key findings and publish them as a live, shareable report

## Pipeline Architecture

```
Raw Dataset (naukri_tech_jobs_raw.csv)
     ↓
Ingestion (ingest.py) — validates file, columns, row count, drops untrusted pre-computed fields
     ↓
Exploration (notebooks/exploration.ipynb) — inspect real data before writing cleaning logic
     ↓
Cleaning & Transformation (clean.py) — salary parsing, skill normalization, city cleaning, date parsing
     ↓
Processed Data (data/processed/cleaned_jobs.csv)
     ↓
MySQL (load_db.py) — normalized 4-table schema, transactional loading
     ↓
SQL Analysis (sql/queries.sql) — hiring, skills, salary, work mode, time-trend queries
     ↓
Python Analysis & Visualization (analyze.py) — Matplotlib charts
     ↓
Static Report (docs/index.html) — published via GitHub Pages
```

## Tech Stack

- **Language:** Python
- **Data processing:** Pandas
- **Database:** MySQL
- **Visualization:** Matplotlib
- **Version control:** Git, GitHub
- **Deployment:** GitHub Pages (static report)
- **Environment:** python-dotenv for credential management, virtualenv for dependency isolation

A local Flask + MySQL interactive dashboard was also built (`dashboard/app.py`) but not deployed live — the published report uses a static snapshot instead, avoiding the cost/complexity of hosting a live database for a dataset that isn't continuously updated.

## Database Schema

Normalized into 4 tables (see `sql/schema.sql`):

- **`companies`** — one row per unique company (deduplicated from 23,201 job rows down to ~6,944 companies)
- **`skills`** — one row per unique skill, with `skill_domain` stored at the skill level (not per-job, since a skill's domain doesn't change based on which job mentions it)
- **`jobs`** — one row per job posting, with a foreign key to `companies`
- **`job_skills`** — junction table representing the many-to-many relationship between jobs and skills (176,389 rows)

This replaces an earlier flat single-table design (v1 of this project), where company and skill details were repeated across every row instead of normalized into their own tables.

## Folder Structure

```
indian-tech-hiring-pipeline/
├── data/
│   ├── raw/                  # Original scraped CSV
│   └── processed/            # Cleaned output from clean.py
├── scripts/
│   ├── ingest.py             # File/column/row validation
│   ├── clean.py              # Salary, skills, location, date cleaning
│   ├── load_db.py            # MySQL loading with transactions
│   └── analyze.py            # Chart generation + stats export
├── sql/
│   ├── schema.sql            # Table definitions
│   └── queries.sql           # Analytical queries
├── notebooks/
│   └── exploration.ipynb     # Pre-cleaning data exploration
├── dashboard/
│   ├── app.py                 # Local Flask dashboard (not deployed live)
│   ├── templates/
│   ├── static/
│   └── charts/                 # Generated chart PNGs
├── docs/                      # Static report, published via GitHub Pages
└── README.md
```

## Setup Instructions

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/Pratibha-Gaur/indian-tech-hiring-pipeline.git
   cd indian-tech-hiring-pipeline
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set up MySQL and create a `.env` file in the project root:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=tech_hiring_db_v2
   ```

3. Run the schema:
   ```bash
   mysql -u root -p < sql/schema.sql
   ```

## How to Run the Pipeline

```bash
python scripts/clean.py       # Cleans raw CSV -> data/processed/cleaned_jobs.csv
python scripts/load_db.py     # Loads cleaned data into MySQL
python scripts/analyze.py     # Generates charts + stats snapshot
```

## SQL Analysis

`sql/queries.sql` includes queries covering:
- Top hiring companies and cities
- Most in-demand skills overall and by city
- Average salary by experience, city, and role category (disclosed salaries only)
- Work mode distribution (on-site / hybrid / remote)
- Hiring volume trend over time

## Key Findings

- **Python, Data Analysis, Machine Learning, and SQL** are the four most in-demand skills across all postings
- **On-site roles dominate** (80.6%) over hybrid (10.1%) and remote (9.3%) — remote work is still a minority in Indian tech hiring, at least in this dataset
- **Mumbai leads hiring volume** (3,118 postings), followed by Bengaluru, Chennai, and Pune
- **Data Scientist roles command the highest average disclosed salary** (₹19.03 LPA), while Data Analyst roles average lowest (₹9.95 LPA) among the six role categories tracked
- Only ~10.6% of postings disclosed a salary — most salary analysis in this project is necessarily based on that smaller, disclosed subset
- The dataset's `posted_date` field spans only ~2 months (May–June 2025), so the hiring-trend chart shows a short window, not a full seasonal pattern

## Visualizations

See `dashboard/charts/` or the [live report](https://pratibha-gaur.github.io/indian-tech-hiring-pipeline/) for:
- Top 15 in-demand skills
- Top 15 hiring cities
- Average salary by role category (with sample sizes labeled)
- Work mode distribution
- Hiring volume trend by month

## Live Report

https://pratibha-gaur.github.io/indian-tech-hiring-pipeline/

## Known Limitations

- A small number of company names in the source data are placeholder/junk values (e.g., "-", ".") that were not filtered before loading
- ~2.5% of postings had a date format that couldn't be confidently parsed into `posted_date`
- Multi-city job postings are represented by their first-listed city only (`primary_city`), with an `is_multi_city` flag noting when a posting spans multiple locations
- The dataset's short (~2-month) time window limits the hiring-trend analysis

## Future Improvements

- Filter junk company name placeholders during cleaning
- Add a live cloud-hosted database and deploy the interactive Flask dashboard
- Expand the dataset's time range for a more meaningful trend analysis
- Add city/role/experience filters to the dashboard

## Skills Demonstrated

Data ingestion & validation · Data cleaning & normalization · Relational database design (3NF, foreign keys, junction tables) · SQL analysis · Python/Pandas · Data visualization · Git/GitHub workflow · Environment/credential management · Static site deployment

---

Built by Pratibha Gaur
