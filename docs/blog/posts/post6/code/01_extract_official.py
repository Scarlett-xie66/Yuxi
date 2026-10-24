"""Read only the seven user-uploaded official PSID archives; preserve original selected values."""
from pathlib import Path
import argparse,csv,hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--archives-dir',type=Path,default=ROOT/'data/raw');a=p.parse_args()
YEARS=[1999,2001,2003,2015,2017,2019]
def dictionary(s):
 labels=dict(re.findall(r'(\w+)\s+LABEL\s*=\s*"([^"]*)"',s,re.I))
 pos={v:(int(i)-1,int(j)) for v,i,j in re.findall(r'\b(\w+)\s+(\d+)\s*-\s*(\d+)',s)}
 return {v:(*pos[v],label.strip()) for v,label in labels.items() if v in pos}
def read_selected(z,stem,vars,d,out):
 with z.open(stem+'.txt') as inp,out.open('w',newline='') as dest:
  w=csv.writer(dest);w.writerow(vars);n=0
  for line in inp:
   w.writerow([line[d[v][0]:d[v][1]].decode('ascii').strip() for v in vars]);n+=1
 return n
def sha(f):
 digest = hashlib.sha256()
 with f.open('rb') as b:
  for chunk in iter(lambda: b.read(1024 * 1024), b''):
   digest.update(chunk)
 return digest.hexdigest()
manifest={'source':'User supplied the seven ZIP files as downloaded from the official PSID website','official_catalogue':'https://simba.isr.umich.edu/Zips/ZipMain.aspx','third_party_data_used':False,'archives':[]}
meta=[];mapping={}
for filename in ['ind2023er.zip']+[f'fam{y}er.zip' for y in YEARS]:
 f=a.archives_dir/filename
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None,f'CRC failure: {filename}'
  stem='IND2023ER' if filename.startswith('ind') else filename[:-4].upper()
  sas=z.read(stem+'.sas').decode('ascii');d=dictionary(sas)
  expected=int(re.search(r'Rows\s*:\s*(\d+)',sas,re.I)[1]);release={}
  if filename.startswith('ind'):
   vars=['ER30000','ER30001','ER30002','ER32000','ER32016','ER32017']
   birth=[v for v,(_,__,l) in d.items() if l.startswith('YEAR INDIVIDUAL BORN')]
   vars+=birth;mapping['birthyear_vars']=birth;mapping['individual']=[]
   for y in YEARS:
    suf=str(y)[-2:]
    pick=lambda pred:next(v for v,(_,__,l) in d.items() if pred(l))
    fields={'survey_year':y,'family_id_var':pick(lambda l:l==f'{y} INTERVIEW NUMBER'),'sequence_var':pick(lambda l:l.startswith('SEQUENCE NUMBER') and l.endswith(suf)),'relationship_var':pick(lambda l:('RELATION TO HEAD' in l or 'RELATIONSHIP TO HEAD' in l or 'RELATION TO REFERENCE PERSON' in l) and l.endswith(suf)),'age_var':pick(lambda l:l.startswith('AGE OF INDIVIDUAL') and l.endswith(suf))}
    vars +=[fields[k] for k in ['family_id_var','sequence_var','relationship_var','age_var']];mapping['individual'].append(fields)
   vars=list(dict.fromkeys(vars));out=ROOT/'data/selected/individual.csv'
  else:
   y=int(re.search(r'\d{4}',filename)[0]);ids=[v for v,(_,__,l) in d.items() if l.startswith(str(y)) and 'INTERVIEW' in l];inc=[v for v,(_,__,l) in d.items() if l.startswith('TOTAL FAMILY INCOME')]
   assert len(ids)==len(inc)==1,(y,ids,inc)
   relvar=next(v for v,(_,__,l) in d.items() if l=='RELEASE NUMBER');vars=[relvar]+ids+inc
   mapping.setdefault('family',[]).append({'survey_year':y,'id_var':ids[0],'income_var':inc[0],'release_var':relvar})
   out=ROOT/f'data/selected/family_{y}.csv'
  actual=read_selected(z,stem,vars,d,out);assert actual==expected,(filename,actual,expected)
  meta +=[{'source':filename,'variable':v,'label':d[v][2],'start':d[v][0]+1,'end':d[v][1]} for v in vars]
  manifest['archives'].append({'filename':filename,'bytes':f.stat().st_size,'sha256':sha(f),'crc':'passed','source_rows':actual,'selected_columns':len(vars),'source_header':sas[:450].strip(),'data_member':stem+'.txt'})
  print(filename,actual,'records',len(vars),'selected columns',flush=True)
(ROOT/'data/wave_mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
with (ROOT/'data/variable_dictionary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['source','variable','label','start','end']);w.writeheader();w.writerows(meta)
manifest['selected_files']=[{'filename':str(f.relative_to(ROOT/'data')),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted((ROOT/'data/selected').glob('*.csv'))]
(ROOT/'data/source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
