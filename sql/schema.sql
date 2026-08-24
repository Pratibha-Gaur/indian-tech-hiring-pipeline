-- ============================================================
-- Indian Tech Job Market Hiring Trends Pipeline (v2 - Advanced Rebuild)
-- Normalized schema: companies, jobs, skills, job_skills
-- Migrated from v1 flat table: tech_jobs
-- ============================================================
 
CREATE DATABASE IF NOT EXISTS tech_hiring_db_v2;
USE tech_hiring_db_v2;
 
-- ------------------------------------------------------------
-- companies
-- One row per unique company. Deduped from company_name in v1.
-- ------------------------------------------------------------
CREATE TABLE companies (
    company_id      INT AUTO_INCREMENT PRIMARY KEY,
    company_name    VARCHAR(255) NOT NULL,
    company_rating  FLOAT,
    company_size_bucket VARCHAR(50),
    UNIQUE KEY uq_company_name (company_name)
);
 
-- ------------------------------------------------------------
-- skills
-- One row per unique skill. skill_domain moved here from job-level
-- in v1, since domain (e.g. "Data Engineering") is a property of
-- the skill itself, not of any single job posting.
-- ------------------------------------------------------------
CREATE TABLE skills (
    skill_id        INT AUTO_INCREMENT PRIMARY KEY,
    skill_name      VARCHAR(100) NOT NULL,
    skill_domain    VARCHAR(100),
    UNIQUE KEY uq_skill_name (skill_name)
);
 
-- ------------------------------------------------------------
-- jobs
-- One row per job posting. job_id reused from v1 (already unique,
-- keeps traceability back to raw scraped data).
-- ------------------------------------------------------------
CREATE TABLE jobs (
    job_id                  INT PRIMARY KEY,
    company_id              INT,
    job_title               VARCHAR(255),
    role_category            VARCHAR(100),
 
    -- location
    location_raw            VARCHAR(255),   -- original 'location'
    scraped_city             VARCHAR(100),
    primary_city             VARCHAR(100),
    work_mode                VARCHAR(50),
 
    -- experience
    experience_raw           VARCHAR(100),
    experience_min_yrs       FLOAT,
    experience_max_yrs       FLOAT,
    experience_tier          VARCHAR(50),
    is_senior                 TINYINT(1),
    is_fresher_friendly       TINYINT(1),
 
    -- salary
    salary_raw                VARCHAR(100),
    salary_min_lpa             FLOAT,
    salary_max_lpa             FLOAT,
    salary_midpoint_lpa        FLOAT,
    salary_tier                VARCHAR(50),
    salary_disclosed            TINYINT(1),
    salary_negotiable           TINYINT(1),
 
    -- content
    job_description             TEXT,
 
    -- dates
    posted_date_raw              VARCHAR(100),
    posted_date                   DATE,        -- NEW: parsed date for time-series analysis
    days_since_posted              FLOAT,
 
    -- source metadata
    job_url                        VARCHAR(500),
    data_source                     VARCHAR(100),
    scraped_at                      DATETIME,
    scraped_month                    VARCHAR(20),
 
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE SET NULL,
 
    INDEX idx_posted_date (posted_date),
    INDEX idx_primary_city (primary_city),
    INDEX idx_role_category (role_category)
);
 
-- ------------------------------------------------------------
-- job_skills (junction table for many-to-many jobs <-> skills)
-- Replaces the old raw 'skills_required' text blob and
-- 'skills_count' derived column in v1.
-- ------------------------------------------------------------
CREATE TABLE job_skills (
    job_id      INT NOT NULL,
    skill_id    INT NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    CONSTRAINT fk_jobskills_job
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_jobskills_skill
        FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        ON DELETE CASCADE
);