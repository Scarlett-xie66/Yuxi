"""Optional standalone preview with system Pandoc; Quarto remains the website renderer."""
from pathlib import Path
import os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
pandoc=os.environ.get('BLOG6_PANDOC') or shutil.which('pandoc')
if not pandoc:raise SystemExit('Install Pandoc or use: quarto render index.qmd --to html')
subprocess.run([pandoc,str(ROOT/'result/_preview.qmd'),'--from=markdown','--to=html5','--standalone','--embed-resources','--mathml','--highlight-style=pygments',f'--include-in-header={ROOT / "code/preview_head.html"}',f'--output={ROOT / "index.html"}'],cwd=ROOT,check=True)
p=ROOT/'index.html'
h=p.read_text(encoding='utf-8').replace('<body>', '<body class="blog6-report"><main class="content">', 1).replace('</body>', '</main></body>', 1)
p.write_text(h,encoding='utf-8')
print('Rendered standalone index.html with embedded figures and MathML.')
