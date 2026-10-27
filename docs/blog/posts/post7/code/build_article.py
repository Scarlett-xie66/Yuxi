"""Build the concise English article, linked Plotly views and saved figure objects."""
from pathlib import Path
import base64
import gzip
import hashlib
import io
import json
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt'] = 'blog7'
import matplotlib.pyplot as plt
from file_io import write_text, write_bytes

ROOT = Path(__file__).resolve().parents[1]
TITLE = 'When Economies Shrink, Whose Employment Rate Falls More?'

def build(preview=True):
    out = ROOT / 'result'
    p = pd.read_csv(out / 'analysis_panel.csv'); h = pd.read_csv(out / 'country_history.csv')
    m = pd.read_csv(out / 'model_results.csv')
    s = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
    r = p[p.contraction].copy()
    es = p[p.iso3.eq('ESP')].set_index('year')
    def estimate(label, outcome):
        return m[(m.specification == label) & (m.outcome == outcome) & (m.term == 'depth')].iloc[0]
    f = estimate('National: all years', 'Women'); male = estimate('National: all years', 'Men')
    diff = estimate('National: all years', 'Women minus men')
    pre = estimate('National: before 2020', 'Women minus men')
    modeled = estimate('Modeled: common source sample', 'Women minus men')
    # Replace missing values with JSON null rather than JavaScript NaN tokens.
    def records(frame): return json.loads(frame.to_json(orient='records', double_precision=12))
    countries = p[['iso3', 'country', 'region']].drop_duplicates().sort_values('country')
    payload = {'countries': records(countries), 'recessions': records(r[['iso3', 'country', 'region', 'year',
        'gdp', 'd_female', 'd_male', 'difference']]), 'histories': records(h[['iso3','year','gdp','female_rate','male_rate']].round(4)), 'models': records(m),
        'years': list(range(2001, 2025))}
    write_text(out / 'dashboard_data.json', json.dumps(payload, ensure_ascii=True))
    body = f'''<article id="blog7-report">
<p class="standfirst">Economic downturns do not leave every worker equally exposed. In a comparison of {s['contraction_observations']} downturn country-years, men’s employment rates fell more than women’s on average. But a smaller decline for women did not mean that women’s employment improved.</p>
<p class="question"><mark class="research-question"><strong>When an economy shrinks, do women’s or men’s employment rates fall more?</strong></mark></p>
<p>Consider two hypothetical downturns of the same size: one centred on factory closures, the other on travel and hospitality. The workers affected could differ even when the fall in national output looks similar. For governments planning job placement or income support, the size of the contraction alone is therefore an incomplete guide to who may need help.</p>
<p>The data offer a way to examine the broader pattern. I match women’s and men’s employment-to-population rates with real GDP growth, producing <strong>{s['observations']:,} annual country-year changes from {s['countries']} countries and territories</strong> between 2001 and 2024.<sup><a href="#note1">1</a></sup> The analysis compares changes in the two rates within the same country and year; it does not identify which industries caused those changes.</p>
<p>GDP declined in <strong>{s['contraction_observations']} of those records, from {s['contraction_countries']} of the {s['countries']} countries and territories</strong>. These are country-years, not {s['contraction_observations']} different countries: some places experienced several downturn years. Women and men are paired within each country-year, so the comparison tracks whose employment rate changed more under the same national GDP movement.</p>

<h2>Men’s employment rates fell further</h2>
<p>In the {s['contraction_observations']} downturn country-years, women’s employment rate fell by an average <strong>{abs(s['female_mean']):.2f} percentage points</strong>, compared with <strong>{abs(s['male_mean']):.2f} points for men</strong>. Women’s rate changed more favourably than men’s in <strong>{s['female_better']} cases ({100*s['female_better']/s['contraction_observations']:.0f}%)</strong>: it either fell less or rose more. Yet women’s rate declined in {s['women_fell']} of the {s['contraction_observations']} downturn records overall. Each country-year counts equally, so these figures describe the sample average, not a global total of jobs lost.</p>
<div class="explorer-controls">
<label for="b7-year">Contraction year<select id="b7-year"></select></label>
<label for="b7-region">Region<select id="b7-region"></select></label>
<label for="b7-country">Country / territory<select id="b7-country"></select></label>
<button id="b7-reset" type="button">Reset</button>
</div>
<p id="b7-status" class="explorer-status" role="status" aria-live="polite"></p>
<figure><figcaption><span class="figure-number">Figure 1.</span> Most contraction observations lie above the equal-change line</figcaption>
<div id="b7-scatter" class="plot" aria-label="Paired female and male employment-rate changes in contraction years"></div>
<p class="source">Each dot is one country-year with negative GDP growth. Above the diagonal, women’s employment rate fell less (or rose more) than men’s; below it, men’s rate fell less. When both coordinates are negative, both rates declined. Hover for values; select a country to see its history.</p>
<details id="b7-detail"><summary>Country history: <span id="b7-country-name">Spain</span></summary>
<div id="b7-history" class="plot" aria-label="Selected country employment-rate histories"></div>
<p class="source">Shading marks years of negative GDP growth. Gaps mark unavailable or flagged employment data; lines do not interpolate them.</p></details>
<p class="source">Source: World Bank/ILO national employment estimates and World Bank real GDP growth; <a href="result/analysis_panel.csv">matched observations</a>.</p></figure>

<p>Spain illustrates why the aggregate comparison is only a starting point. In 2009, the employment-rate declines were {abs(es.loc[2009, 'd_female']):.2f} points for women and {abs(es.loc[2009, 'd_male']):.2f} for men. In 2020, the declines were {abs(es.loc[2020, 'd_female']):.2f} and {abs(es.loc[2020, 'd_male']):.2f} points, respectively. Men’s decline was larger in both years, but the difference was much narrower in 2020. The same country can experience downturns with very different distributions of employment-rate changes.</p>
<h2>Deeper contractions bring a wider difference</h2>
<p>The raw averages mix mild and severe downturns across countries and years. They tell us what happened in the selected downturn records, but not whether deeper contractions are associated with a wider difference between women and men. A model uses all {s['observations']:,} country-year changes—including years when GDP grew—to compare deeper with milder contractions. It accounts for persistent country differences and shifts shared across years, while estimating separate relationships for contractions and expansions.<sup><a href="#note2">2</a></sup></p>
<p>When annual GDP growth is 1 percentage point lower—for example, −4% instead of −3%—the model associates that deeper contraction with a further <strong>{abs(f.estimate):.2f}-point fall in women’s employment rate</strong> and a <strong>{abs(male.estimate):.2f}-point fall in men’s</strong>. The estimated male decline is about twice as large. The direct male-minus-female difference is <strong>{diff.estimate:.2f} points</strong> (95% interval: <strong>{diff.ci_low:.2f} to {diff.ci_high:.2f}</strong>), which excludes zero. Both rates fall; the relative difference is not a gain in women’s employment.</p>
<figure><figcaption><span class="figure-number">Figure 2.</span> A deeper contraction is associated with a larger fall for men</figcaption>
<p class="figure-deck">Change in each group’s employment rate associated with GDP growth falling 1 percentage point further. Bars below zero indicate declines.</p>
<label for="b7-model">Same model, different period<select id="b7-model"></select></label>
<p id="b7-model-status" class="explorer-status" role="status" aria-live="polite"></p>
<div id="b7-coefficients" class="plot" aria-label="Additional employment-rate declines for women and men"></div>
<div class="difference-callout" aria-live="polite"><div><span class="callout-label">Men’s additional decline</span><strong id="b7-extra-decline">{diff.estimate:.2f} pp</strong></div><div><span id="b7-extra-interval">95% interval: {diff.ci_low:.2f} to {diff.ci_high:.2f} pp</span><span class="callout-note">Directly estimated difference between the two groups</span></div></div>
<p class="source">Bars: model estimates; capped lines: 95% intervals, clustered by country. The separate comparison reports the additional decline for men per 1 pp deeper contraction; its interval is estimated directly, not obtained by subtracting interval endpoints. These are associations, not predicted total job losses. Filters above Figure 1 do not refit this model. Source: <a href="result/model_results.csv">estimates, intervals and sample sizes</a>.</p></figure>
<p>Figure 2 puts the result in context: both groups’ estimated changes are negative, but the male estimate is further below zero. Unlike the downturn average, this comparison accounts for differences in contraction depth and for country-specific and common year patterns. It therefore adds a measure of how the female–male difference varies with the severity of a downturn. Before 2020, the estimated male-minus-female difference was larger: <strong>{pre.estimate:.2f} points [{pre.ci_low:.2f}, {pre.ci_high:.2f}]</strong>, so the result is not driven by pandemic downturns alone.</p>
<p>A data-source check on the same {int(modeled.n):,} country-years gives a similar direct difference using ILO-modeled employment series: <strong>{modeled.estimate:.2f} points [{modeled.ci_low:.2f}, {modeled.ci_high:.2f}]</strong>. This is a consistency check, not independent proof; modeled series may incorporate macroeconomic information.</p>
<h2>Takeaway</h2>
<p>In the downturns studied, men’s employment rates fell further than women’s: <strong>{abs(s['male_mean']):.2f} percentage points on average, compared with {abs(s['female_mean']):.2f} points for women</strong>. The difference remained after accounting for country and year patterns. For each additional percentage point of GDP contraction, the estimated decline was <strong>{abs(male.estimate):.2f} points for men and {abs(f.estimate):.2f} points for women</strong>. The result points to an uneven distribution of employment-rate declines across the two groups. Yet women’s employment rates also fell in many downturns: <strong>a smaller decline is not the same as a gain.</strong></p>

<h2>Footnotes</h2>
<section class="footnotes"><ol>
<li id="note1"><strong>Employment-to-population rate:</strong> employed people aged 15+ divided by the same-sex population aged 15+. It is not a group’s share of the labor force. <strong>Contraction:</strong> negative annual real GDP growth. Sources: World Bank and ILO.</li>
<li id="note2"><strong>Method:</strong> coefficients are percentage-point changes per 1-point change in GDP growth. Country and year fixed effects account for persistent country differences and common annual movements. Intervals are clustered by country. Estimates are associations, not causal effects.</li>
</ol></section>

<h2>Reproducibility</h2>
<p>The project keeps the article, code, frozen data and results together:</p>
<pre>index.qmd                 # executable entry point
README.md                 # sample, sources and setup
code/                     # fetch, analysis, figures and validation
data/raw/                 # unchanged official API downloads
data/processed/           # matched analysis panel
result/                   # estimates, coverage audit and figures</pre>
<p>Keep the complete project folder together. Install Quarto, R with knitr, and the Python packages in <code>requirements.txt</code>; then open <code>index.qmd</code> in RStudio and click Render. The QMD runs the analysis automatically from the saved raw data and regenerates the matched panel, estimates, figures, interactive charts and article. For Anaconda, set <code>BLOG7_PYTHON</code> to the Python executable as explained in the README. To refresh official data first, run <code>code/fetch_data.py</code>. Sources: World Bank <a href="https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG">real GDP growth</a> and ILO/World Bank national employment series for <a href="https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.FE.NE.ZS">women</a> and <a href="https://data.worldbank.org/indicator/SL.EMP.TOTL.SP.MA.NE.ZS">men</a>; the <a href="data/raw/manifest.json">manifest</a> records the downloaded snapshot.</p>
</article>'''
    # Render the figures into HTML before any JavaScript runs.
    # Interactive Plotly views progressively replace these offline SVG fallbacks.
    def svg_content(fig):
        stream = io.StringIO()
        fig.savefig(stream, format='svg', bbox_inches='tight', facecolor='#ffffff', metadata={'Date': None})
        plt.close(fig)
        svg = stream.getvalue()
        svg = svg[svg.index('<svg'):]
        prefix='b7-'+hashlib.sha256(svg.encode()).hexdigest()[:10]+'-'
        for key in set(re.findall(r'id="([^"]+)"',svg)):
            svg=svg.replace('id="'+key+'"','id="'+prefix+key+'"').replace('#'+key+'"','#'+prefix+key+'"').replace('#'+key+')','#'+prefix+key+')')
        return svg
    colors = ['#247c80', '#b96833', '#8a8196']
    fig, ax = plt.subplots(figsize=(8.8,4.4), facecolor='#ffffff')
    ax.set_facecolor('#ffffff')
    groups = [(r[r.year.isin([2008,2009])], '2008–2009'), (r[r.year.eq(2020)], '2020'), (r[~r.year.isin([2008,2009,2020])], 'Other years')]
    for (a,label),color in zip(groups,colors):
        ax.scatter(a.d_male,a.d_female,s=28,alpha=.8,color=color,label=label)
    ax.plot([-12,12],[-12,12],color='#777',ls=':',lw=1)
    ax.axhline(0,color='#aaa',lw=.6);ax.axvline(0,color='#aaa',lw=.6)
    ax.set(xlim=(-12,12),ylim=(-12,12),xlabel="Change in men's employment rate (pp)",ylabel="Change in women's employment rate (pp)")
    ax.legend(frameon=False,loc='lower right'); fig.tight_layout()
    scatter_svg = svg_content(fig)
    fig, ax = plt.subplots(figsize=(8.8,3.7),facecolor='#ffffff');ax.set_facecolor('#ffffff')
    estimates=[f.estimate,male.estimate]
    ax.bar([0,1],estimates,width=.46,color=['#247c80','#b96833'],zorder=2)
    ax.errorbar([0,1],estimates,yerr=[[f.estimate-f.ci_low,male.estimate-male.ci_low],[f.ci_high-f.estimate,male.ci_high-male.estimate]],fmt='none',ecolor='#333',capsize=6,elinewidth=1.3,zorder=3)
    ax.set(xticks=[0,1],xticklabels=[f'Women\n{f.estimate:.2f} pp',f'Men\n{male.estimate:.2f} pp'],xlim=(-.65,1.65),ylim=(-.68,.04),ylabel='Additional change (pp)')
    ax.xaxis.tick_top();ax.tick_params(axis='x',length=0,labelsize=13,pad=10)
    ax.axhline(0,color='#444',lw=1.2);ax.yaxis.grid(True,color='#eee',zorder=0);ax.set_axisbelow(True)
    for spine in ax.spines.values():spine.set_visible(False)
    fig.tight_layout()
    (out/'figures').mkdir(exist_ok=True)
    png = io.BytesIO()
    fig.savefig(png,format='png',dpi=300,facecolor='white',bbox_inches='tight')
    write_bytes(out/'figures/figure2_adjusted_declines.png',png.getvalue())
    coefficient_svg=svg_content(fig)
    body=body.replace('id="b7-scatter" class="plot" aria-label="Paired female and male employment-rate changes in contraction years"></div>', 'id="b7-scatter" class="plot" aria-label="Paired female and male employment-rate changes in contraction years">'+scatter_svg+'</div>')
    body=body.replace('id="b7-coefficients" class="plot" aria-label="Additional employment-rate declines for women and men"></div>', 'id="b7-coefficients" class="plot" aria-label="Additional employment-rate declines for women and men">'+coefficient_svg+'</div>')
    css = (ROOT / 'code/style.css').read_text(encoding='utf-8')
    css += '\n#blog7-report label[for="b7-model"]{max-width:360px;font:14px Arial,sans-serif}#blog7-report #b7-coefficients{min-height:370px}#blog7-report #b7-history{min-height:330px}\n'
    js = (ROOT / 'code/dashboard.js').read_text(encoding='utf-8')
    runtime = re.sub('[\u3400-\u9fff]', lambda m: '\\u%04x' % ord(m.group()), (ROOT / 'code/vendor/plotly-basic.min.js').read_text(encoding='utf-8'))
    fragment = '<style>' + css + '</style>\n' + body + '\n<script>' + runtime + '</script>\n'
    fragment += '<script id="b7-data" type="application/json">' + json.dumps(payload, ensure_ascii=True).replace('<','\\u003c') + '</script>\n<script>' + js + '</script>'
    write_text(out / '_article_fragment.html', fragment)
    write_text(out / '_article_body.html', body)
    if preview:
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + TITLE + '</title></head><body><main class="preview"><header id="title-block-header"><h1>' + TITLE + '</h1><p class="subtitle">A matched comparison across 85 countries and territories, 2001–2024</p><div class="categories" aria-label="Categories"><span class="category">Plotly</span><span class="category">Python</span><span class="category">Employment</span><span class="category">Economic contractions</span></div><dl class="metadata"><div><dt>Author</dt><dd>Yuxi Xie</dd></div><div><dt>Published</dt><dd><time datetime="2026-10-26">October 26, 2026</time></dd></div></dl></header>' + fragment + '</main></body></html>'
        # The standalone review also carries its CSV/README evidence as download links.
        def embed(match):
            name = match.group(1); path = ROOT / name
            if path.is_file():
                mime = 'text/csv' if path.suffix == '.csv' else 'application/json' if path.suffix == '.json' else 'text/plain'
                raw = path.read_bytes()
                name = path.name
                if len(raw) > 100_000:
                    raw = gzip.compress(raw, mtime=0); mime = 'application/gzip'; name += '.gz'
                return 'href="data:' + mime + ';base64,' + base64.b64encode(raw).decode() + '" download="' + name + '"'
            return match.group(0)
        page = re.sub(r'href="((?:result/|data/)[^"]+|README\.md)"', embed, page)
        write_text(ROOT / 'index.html', page)
    (out / 'figures').mkdir(exist_ok=True)
    fig1 = go.Figure(go.Scatter(x=r.d_male, y=r.d_female, text=r.country + ', ' + r.year.astype(str), mode='markers'))
    fig1.update_layout(xaxis_title="Men's employment-rate change (pp)", yaxis_title="Women's employment-rate change (pp)")
    fig2 = go.Figure(go.Bar(x=['Women','Men'],y=[f.estimate,male.estimate],
        marker_color=['#247c80','#b96833'],width=.46,
        error_y=dict(type='data',symmetric=False,array=[f.ci_high-f.estimate,male.ci_high-male.estimate],arrayminus=[f.estimate-f.ci_low,male.estimate-male.ci_low])))
    fig2.update_layout(yaxis_title='Additional change (pp)',yaxis_range=[-.68,.04],xaxis_side='top')
    write_text(out / 'figures/figure1.json', fig1.to_json()); write_text(out / 'figures/figure2.json', fig2.to_json())
    fig, ax = plt.subplots(figsize=(7,4.5), facecolor='#ffffff'); ax.set_facecolor('#ffffff')
    ax.scatter(r.d_male, r.d_female, s=18, alpha=.6, color='#247c80')
    ax.plot([-12,12],[-12,12],color='#888',ls=':',lw=1); ax.axhline(0,color='#bbb',lw=.6);ax.axvline(0,color='#bbb',lw=.6)
    ax.set(xlim=(-12,12),ylim=(-12,12),xlabel="Men's employment-rate change (pp)",ylabel="Women's employment-rate change (pp)",title='Employment in contraction years\n251 matched country-year observations')
    fig.tight_layout(); stream=io.BytesIO();fig.savefig(stream,format='png',dpi=300);plt.close(fig)
    write_bytes(out/'figures/thumbnail.png',stream.getvalue())
    print('Built the English contraction article and offline interactive HTML.')

if __name__ == '__main__':
    build()
