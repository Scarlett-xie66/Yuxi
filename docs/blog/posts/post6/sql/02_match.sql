CREATE TABLE father_child_links AS
SELECT c.person_id AS child_id,p.person_id AS father_id,
       c.birth_year AS child_birth_year,p.birth_year AS father_birth_year,
       c.sex AS child_sex
FROM persons c JOIN persons p ON c.father_id=p.person_id
WHERE c.birth_year BETWEEN 1972 AND 1976
  AND 2000-p.birth_year BETWEEN 45 AND 60
  AND c.birth_year-p.birth_year BETWEEN 15 AND 55;
-- One observed income per person-wave; retain positive actual amounts, with topcodes flagged.
CREATE TABLE person_income AS
SELECT r.person_id,r.survey_year,r.survey_year-1 AS income_year,
       r.survey_year-1-p.birth_year AS income_age,r.family_interview_id,
       f.income AS income_nominal,LN(f.income) AS log_income,f.topcoded
FROM roster r JOIN persons p ON p.person_id=r.person_id
JOIN family_income f ON f.survey_year=r.survey_year
                    AND f.family_interview_id=r.family_interview_id
WHERE r.sequence BETWEEN 1 AND 20 AND r.relationship IN (10,20,22)
  AND p.birth_year IS NOT NULL AND f.income>0 AND f.valid_code=1;
CREATE UNIQUE INDEX income_key ON person_income(person_id,survey_year);
CREATE TABLE income_summary AS
SELECT person_id,
       CASE WHEN survey_year IN (1999,2001,2003) THEN 'early' ELSE 'midlife' END AS stage,
       COUNT(*) AS n_obs,AVG(log_income) AS log_multi,
       MAX(CASE WHEN survey_year IN (2001,2017) THEN log_income END) AS log_single,
       MAX(CASE WHEN survey_year IN (2001,2017) THEN income_nominal END) AS income_single,
       SUM(topcoded) AS n_topcoded
FROM person_income
GROUP BY person_id,stage;
CREATE TABLE common_before_household_check AS
SELECT l.*,p.log_multi AS father_log_multi,p.log_single AS father_log_single,
       y.log_multi AS young_log_multi,y.log_single AS young_log_single,
       a.log_multi AS midlife_log_multi,a.log_single AS midlife_log_single,
       p.n_obs AS father_n,y.n_obs AS young_n,a.n_obs AS midlife_n,
       p.income_single AS father_income_2000,
       y.income_single AS child_income_2000,
       a.income_single AS child_income_2016,
       p.n_topcoded+y.n_topcoded+a.n_topcoded AS n_topcoded
FROM father_child_links l
JOIN income_summary p ON p.person_id=l.father_id AND p.stage='early' AND p.n_obs=3
JOIN income_summary y ON y.person_id=l.child_id AND y.stage='early' AND y.n_obs=3
JOIN income_summary a ON a.person_id=l.child_id AND a.stage='midlife' AND a.n_obs=3;
CREATE TABLE matched_income AS
SELECT m.*,
       EXP(father_log_multi) AS father_income_geo,
       EXP(young_log_multi) AS child_young_income_geo,
       EXP(midlife_log_multi) AS child_midlife_income_geo
FROM common_before_household_check m
WHERE NOT EXISTS (
 SELECT 1 FROM person_income c JOIN person_income p
   ON c.survey_year=p.survey_year AND c.family_interview_id=p.family_interview_id
 WHERE c.person_id=m.child_id AND p.person_id=m.father_id
   AND c.survey_year IN (1999,2001,2003));
CREATE UNIQUE INDEX child_key ON matched_income(child_id);
CREATE TABLE selection_counts AS
SELECT '1. Children born 1972–1976' AS step,COUNT(*) AS children
FROM persons WHERE birth_year BETWEEN 1972 AND 1976
UNION ALL SELECT '2. Documented father record found',COUNT(*)
FROM persons c JOIN persons p ON c.father_id=p.person_id
WHERE c.birth_year BETWEEN 1972 AND 1976
UNION ALL SELECT '3. Father age 45–60 in 2000; age gap 15–55',COUNT(*) FROM father_child_links
UNION ALL SELECT '4. Father has all 3 positive early incomes',COUNT(*)
FROM father_child_links l JOIN income_summary s ON s.person_id=l.father_id AND s.stage='early' AND s.n_obs=3
UNION ALL SELECT '5. Also child has all 3 positive early incomes',COUNT(*)
FROM father_child_links l
JOIN income_summary p ON p.person_id=l.father_id AND p.stage='early' AND p.n_obs=3
JOIN income_summary y ON y.person_id=l.child_id AND y.stage='early' AND y.n_obs=3
UNION ALL SELECT '6. Also child has all 3 positive midlife incomes',COUNT(*) FROM common_before_household_check
UNION ALL SELECT '7. Distinct father/child family units in early waves',COUNT(*) FROM matched_income;
