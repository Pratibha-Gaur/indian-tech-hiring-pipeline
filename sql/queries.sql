USE tech_hiring_db_v2;

-- ============================================================
-- HIRING
-- ============================================================

-- Top hiring companies (excluding junk/placeholder company names)
SELECT c.company_name, COUNT(*) AS job_count
FROM jobs j
JOIN companies c ON j.company_id = c.company_id
WHERE c.company_name NOT IN ('-', '.', 'Confidential')
GROUP BY c.company_name
ORDER BY job_count DESC
LIMIT 15;

-- Cities with the most job openings
SELECT primary_city, COUNT(*) AS job_count
FROM jobs
WHERE primary_city IS NOT NULL
GROUP BY primary_city
ORDER BY job_count DESC
LIMIT 15;

-- Role categories with the most jobs
SELECT role_category, COUNT(*) AS job_count
FROM jobs
WHERE role_category IS NOT NULL
GROUP BY role_category
ORDER BY job_count DESC
LIMIT 15;

-- ============================================================
-- SKILLS
-- ============================================================

-- Most in-demand skills overall
SELECT s.skill_name, COUNT(*) AS mention_count
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY s.skill_name
ORDER BY mention_count DESC
LIMIT 20;

-- Most in-demand skills in each of the top 5 cities
SELECT j.primary_city, s.skill_name, COUNT(*) AS mention_count
FROM jobs j
JOIN job_skills js ON j.job_id = js.job_id
JOIN skills s ON js.skill_id = s.skill_id
JOIN (
    SELECT primary_city FROM jobs
    WHERE primary_city IS NOT NULL
    GROUP BY primary_city
    ORDER BY COUNT(*) DESC
    LIMIT 5
) AS top_cities ON j.primary_city = top_cities.primary_city
GROUP BY j.primary_city, s.skill_name
ORDER BY j.primary_city, mention_count DESC
LIMIT 100;

-- ============================================================
-- SALARY (only using disclosed/parsed salary records)
-- ============================================================

-- Average salary by experience range
SELECT
    experience_raw,
    ROUND(AVG(salary_midpoint_lpa), 2) AS avg_salary_lpa,
    COUNT(*) AS job_count
FROM jobs
WHERE salary_midpoint_lpa IS NOT NULL
GROUP BY experience_raw
ORDER BY avg_salary_lpa DESC
LIMIT 15;

-- Average salary by city
SELECT
    primary_city,
    ROUND(AVG(salary_midpoint_lpa), 2) AS avg_salary_lpa,
    COUNT(*) AS job_count
FROM jobs
WHERE salary_midpoint_lpa IS NOT NULL AND primary_city IS NOT NULL
GROUP BY primary_city
ORDER BY avg_salary_lpa DESC
LIMIT 15;

-- Average salary by role category
SELECT
    role_category,
    ROUND(AVG(salary_midpoint_lpa), 2) AS avg_salary_lpa,
    COUNT(*) AS job_count
FROM jobs
WHERE salary_midpoint_lpa IS NOT NULL AND role_category IS NOT NULL
GROUP BY role_category
ORDER BY avg_salary_lpa DESC
LIMIT 15;

-- ============================================================
-- WORK MODE
-- ============================================================

SELECT work_mode, COUNT(*) AS job_count
FROM jobs
WHERE work_mode IS NOT NULL
GROUP BY work_mode
ORDER BY job_count DESC;

-- ============================================================
-- TIME TRENDS
-- ============================================================

-- Hiring volume by posted month
SELECT
    DATE_FORMAT(posted_date, '%Y-%m') AS posted_month,
    COUNT(*) AS job_count
FROM jobs
WHERE posted_date IS NOT NULL
GROUP BY posted_month
ORDER BY posted_month;