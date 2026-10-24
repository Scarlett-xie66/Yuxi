"""SQL processing and diagnostics for the agreed seven-file, balanced-period design."""
from pathlib import Path
import json,math,sqlite3
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'data/wave_mapping.json').read_text())
c=sqlite3.connect(':memory:');c.create_function('LN',1,lambda v:math.log(v) if v and v>0 else None);c.create_function('EXP',1,math.exp)
pd.read_csv(ROOT/'data/selected/individual.csv').to_sql('individual_raw',c,index=False)
for w in m['family']:pd.read_csv(ROOT/f"data/selected/family_{w['survey_year']}.csv").to_sql(f"raw_{w['survey_year']}",c,index=False)
birth=',\n'.join(f'CASE WHEN {v} BETWEEN 1850 AND 2023 THEN {v} END' for v in reversed(m['birthyear_vars']))
prepare=f'''CREATE TABLE persons AS
SELECT ER30001*1000+ER30002 AS person_id,ER30001 AS family1968,ER30002 AS person_number,
       ER32000 AS sex,COALESCE({birth}) AS birth_year,
       CASE WHEN ER32016>0 AND ER32017 BETWEEN 1 AND 399
            THEN ER32016*1000+ER32017 END AS father_id
FROM individual_raw;
CREATE UNIQUE INDEX person_key ON persons(person_id);
CREATE TABLE roster AS\n'''
prepare+='\nUNION ALL\n'.join(f"SELECT ER30001*1000+ER30002 AS person_id,{w['survey_year']} AS survey_year,{w['family_id_var']} AS family_interview_id,{w['sequence_var']} AS sequence,{w['relationship_var']} AS relationship,{w['age_var']} AS survey_age FROM individual_raw WHERE {w['family_id_var']}>0 AND {w['sequence_var']} BETWEEN 1 AND 20" for w in m['individual'])+';\nCREATE UNIQUE INDEX roster_key ON roster(person_id,survey_year);\nCREATE TABLE family_income AS\n'
prepare+='\nUNION ALL\n'.join(f"SELECT {w['survey_year']} AS survey_year,{w['id_var']} AS family_interview_id,{w['income_var']} AS income,{w['release_var']} AS source_release,CASE WHEN {w['income_var']}=9999999 AND {w['survey_year']}<=2003 THEN 1 ELSE 0 END AS topcoded,CASE WHEN {w['income_var']}<={9999999 if w['survey_year']<=2003 else 9999997} THEN 1 ELSE 0 END AS valid_code FROM raw_{w['survey_year']}" for w in m['family'])+';\nCREATE UNIQUE INDEX family_key ON family_income(survey_year,family_interview_id);\n'
(ROOT/'sql/01_prepare.sql').write_text(prepare)
c.executescript(prepare);c.executescript((ROOT/'sql/02_match.sql').read_text())
queries={
 'selection_counts':'SELECT * FROM selection_counts',
 'income_quality':'''SELECT survey_year,COUNT(*) AS families,MIN(source_release) AS source_release,MIN(income) AS minimum,MAX(income) AS maximum,SUM(income<0) AS negative,SUM(income=0) AS zero,SUM(income=1) AS one_dollar,SUM(income>0 AND valid_code=1) AS positive_valid,SUM(topcoded) AS topcoded,SUM(valid_code=0) AS unexpected_codes FROM family_income GROUP BY survey_year''',
 'roster_join_audit':'''SELECT r.survey_year,COUNT(*) AS responding_people,SUM(f.family_interview_id IS NULL) AS unmatched_family_ids,SUM(r.relationship IN (10,20,22)) AS reference_spouse_partner FROM roster r LEFT JOIN family_income f ON f.survey_year=r.survey_year AND f.family_interview_id=r.family_interview_id GROUP BY r.survey_year''',
 'father_link_audit':'''SELECT CASE WHEN c.father_id IS NULL THEN 'Missing/invalid father pointer' WHEN p.person_id IS NULL THEN 'Father not found' WHEN p.birth_year IS NULL THEN 'Father birth year missing' WHEN 2000-p.birth_year NOT BETWEEN 45 AND 60 THEN 'Father outside proposed age range' WHEN c.birth_year-p.birth_year NOT BETWEEN 15 AND 55 THEN 'Age gap outside range' ELSE 'Eligible father link' END AS status,COUNT(*) AS children FROM persons c LEFT JOIN persons p ON c.father_id=p.person_id WHERE c.birth_year BETWEEN 1972 AND 1976 GROUP BY status ORDER BY children DESC''',
 'matched_income':'SELECT * FROM matched_income ORDER BY child_id',
 'matched_preview':'SELECT child_id,father_id,child_birth_year,father_birth_year,father_income_2000,child_income_2000,child_income_2016,father_income_geo,child_young_income_geo,child_midlife_income_geo FROM matched_income ORDER BY child_id LIMIT 5',
 'person_income':'SELECT * FROM person_income ORDER BY person_id,survey_year',
 'father_child_links':'SELECT * FROM father_child_links ORDER BY child_id'
}
for name,sql in queries.items():
 df=pd.read_sql_query(sql,c);df.to_csv(ROOT/f'result/{name}.csv',index=False)
 if name in ['selection_counts','income_quality','roster_join_audit','father_link_audit']:print(name+'\n'+df.to_string(index=False),flush=True)
for t in ['persons','roster','family_income','income_summary']:
 pd.read_sql_query('SELECT * FROM '+t,c).to_csv(ROOT/f'data/processed/{t}.csv',index=False)
assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
# SQLite backup also works with Python versions without the newer serialization API.
with sqlite3.connect(str(ROOT/'data/processed/analysis.sqlite')) as destination:
 c.backup(destination)
print('Final sample:',c.execute('SELECT COUNT(*),COUNT(DISTINCT father_id),SUM(child_sex=2),SUM(n_topcoded>0) FROM matched_income').fetchone(),flush=True)
c.close()
