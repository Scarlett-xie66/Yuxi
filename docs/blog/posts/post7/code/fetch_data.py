"""Acquire official WDI responses; regular renders use the included snapshot offline."""
from pathlib import Path
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
 'countries': 'https://api.worldbank.org/v2/country?format=json&per_page=400',
 'gdp': 'NY.GDP.MKTP.KD.ZG',
 'female_national': 'SL.EMP.TOTL.SP.FE.NE.ZS',
 'male_national': 'SL.EMP.TOTL.SP.MA.NE.ZS',
 'female_modeled': 'SL.EMP.TOTL.SP.FE.ZS',
 'male_modeled': 'SL.EMP.TOTL.SP.MA.ZS',
}

def download(item):
 name, code = item
 url = code if name == 'countries' else 'https://api.worldbank.org/v2/country/all/indicator/' + code + '?format=json&date=2000:2024&per_page=20000&footnote=y'
 with urlopen(Request(url, headers={'User-Agent': 'Blog7 academic data analysis'}), timeout=90) as response:
  data = response.read()
 parsed = json.loads(data)
 assert len(parsed) == 2 and isinstance(parsed[1], list), name
 assert int(parsed[0]['pages']) == 1 and len(parsed[1]) == int(parsed[0]['total']), name
 return name, data, {'file': name + '.json', 'url': url, 'records': len(parsed[1]),
  'last_updated': parsed[0].get('lastupdated'), 'sha256': hashlib.sha256(data).hexdigest()}

if __name__ == '__main__':
 raw = ROOT / 'data/raw'; raw.mkdir(parents=True, exist_ok=True)
 manifest = {'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'sources': []}
 with ThreadPoolExecutor(max_workers=6) as pool:
  for name, data, record in pool.map(download, SOURCES.items()):
   (raw / (name + '.json')).write_bytes(data)
   manifest['sources'].append(record)
   print(name, record['records'], flush=True)
 (raw / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
