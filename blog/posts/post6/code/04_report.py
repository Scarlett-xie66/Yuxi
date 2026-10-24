"""Generate an inspection report, not the Blog6 article, using only computed audit outputs."""
from pathlib import Path
import html,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
v=json.loads((ROOT/'result/validation.json').read_text());manifest=json.loads((ROOT/'data/source_manifest.json').read_text());mapping=json.loads((ROOT/'data/wave_mapping.json').read_text())
def table(name,rounding=None):
 df=pd.read_csv(ROOT/f'result/{name}.csv')
 if rounding is not None:df=df.round(rounding)
 return '<div class="scroll">'+df.to_html(index=False,border=0,classes='data',escape=True)+'</div>'
files=pd.DataFrame([{'文件':a['filename'],'原始记录数':a['source_rows'],'提取字段数':a['selected_columns'],'ZIP完整性':a['crc']} for a in manifest['archives']])
rows=[]
for f in mapping['family']:
 w=next(w for w in mapping['individual'] if w['survey_year']==f['survey_year'])
 rows.append({'调查年份':f['survey_year'],'收入年份':f['survey_year']-1,'个人文件家庭编号':w['family_id_var'],'家庭文件家庭编号':f['id_var'],'家庭收入字段':f['income_var']})
maptable=pd.DataFrame(rows)
ci=v['paired_midlife_minus_young_multi_ci'];diff=v['pilot_estimates'][3]['beta']-v['pilot_estimates'][1]['beta']
body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blog6：PSID 官方原始数据检查</title><style>
body{{max-width:1080px;margin:36px auto;padding:0 22px;font:16px/1.75 Arial,"Microsoft YaHei",sans-serif;color:#242424;background:#fff}}h1{{font-size:29px;line-height:1.35}}h2{{font-size:21px;margin-top:32px;color:#255d63}}p{{max-width:880px}}.lead{{padding:16px 20px;border-left:4px solid #326f72;background:#eef5f3}}.note{{padding:12px 18px;border-left:4px solid #b47748;background:#fcf6ed}}.scroll{{overflow-x:auto;margin:15px 0}}table{{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}}th,td{{padding:9px 11px;border-bottom:1px solid #ddd;text-align:right}}th{{background:#f1f3f3}}th:first-child,td:first-child{{text-align:left}}code{{background:#f4f4f2;padding:2px 4px}}li{{margin:6px 0}}a{{color:#276e78}}.small{{font-size:13px;color:#666}}</style></head><body>
<h1>Blog6：PSID 官方原始数据检查</h1><p class="small">2026-10-23 · 数据检查与试算报告；尚未生成正式 Blog。所有数值来自本次上传的七个官方 ZIP。</p>
<div class="lead"><strong>结论：七个文件支持确认的 SQL 教程与描述性 IGE 分析。</strong>读取 {v['source_individual_rows']:,} 人及 {v['source_family_rows']:,} 条家庭—波次记录；按预设规则得到 {v['matched_children']} 名子女、{v['distinct_fathers']} 位父亲。SQL 与独立 pandas 复算结果一致。统计精度与选择性限制需要保留。</div>
<h2>1. 文件完整性与来源</h2><p>七个 ZIP 均通过内部 CRC 检查，实际 TXT 记录数均与对应 SAS 文件头的 Rows 数一致。原始 ZIP 未修改。只读取用户提供的 PSID 官方文件；本次不读取第三方档案、旧版提取表或外部 CPI。</p>{files.to_html(index=False,border=0)}
<p>源 ZIP 的 SHA-256、文件版本头及原始字段位置分别保存在 <code>data/source_manifest.json</code> 和 <code>data/variable_dictionary.csv</code>。来源渠道由用户上传说明及包内 PSID 元数据确认；未把包内元数据说成另一次独立官网重新下载。</p>
<h2>2. 合并键与字段确实存在</h2><p>稳定个人键为 ER30001 与 ER30002；父亲指针为 ER32016 与 ER32017。SQL 将这两组编号对应，随后以“调查年份＋当年家庭访谈编号”连接家庭收入。三个基础键均通过唯一性检查：个人、个人—波次、家庭—波次。</p>{maptable.to_html(index=False,border=0)}
<p>六个波次的在访个人连接家庭文件时，未匹配家庭编号均为 0。个人文件中的源 sequence 1–20 用于识别在访成员。</p>{table('roster_join_audit')}
<h2>3. 收入内容与编码检查</h2><p>使用家庭总货币收入，包含工资之外的收入，保留 PSID 原有的插补与组成项处理。它不是个人工资，也没有按家庭人数等价化。收入对应调查的上一年。</p>{table('income_quality')}
<p>六个家庭文件共有 42 条负收入、485 条零收入。这些值保留在原始提取表及质量统计中，但不进入对数回归。正的 1 美元是这六个年份的有效金额，不套用 1994 年之前的底部编码规则。1999–2003 的 9,999,999 是顶部编码；实际六个文件均未出现该正顶部值或超出核对正值范围的代码。最终分析样本的最低有效收入为 ${v['minimum_common_sample_income']:,.0f}，没有 1 美元记录或正顶部编码记录。</p>
<h2>4. 预先确定的样本规则</h2><p>子女出生于 1972–1976 年；父亲在 2000 年为 45–60 岁，父子年龄差为 15–55 年。父亲使用 1998、2000、2002 年收入；子女早期使用相同三年，中年使用 2014、2016、2018 年。要求每个窗口完整三次有效正收入，并且本人为参考人、配偶或伴侣。早期三次观察中，父亲与子女的家庭经济单位必须不同。</p>{table('selection_counts')}
<p>最终 {v['matched_children']} 名子女包括 {v['daughters']} 名女性和 {v['sons']} 名男性，来自 {v['distinct_fathers']} 位父亲。完整样本占初始出生队列约 {100*v['matched_children']/v['cohort_children']:.1f}%，不能视为全国代表性估计。没有为增加样本或得到预期斜率而改动范围。</p>
<p>出生年份采用最新有效报告。全个人档案中有 {v['birthyear_fields_conflict_all_people']:,} 人的不同波次有效出生年报告曾变化；这按报告修订处理，不自动解释为数据错误。最终样本相关的 {v['age_records_checked']:,} 条不同个人—年份记录中，调查年份减出生年与报告年龄的差均为 0 或 1，符合生日时点差异。</p>
<h2>5. 合并后的真实前五行</h2><p>下表的单年金额是对应年份的名义美元；geo 列是三次收入的几何平均，不能据此直接比较 2000 与 2016 年的购买力。</p>{table('matched_preview',2)}
<h2>6. 独立复核与初步 IGE</h2><p>从原始选定列重新用 pandas 构造父亲关系、在访家庭收入、完整三次窗口与同家庭排除条件。父子样本、三个单年对数收入和三个多年平均对数收入均与 SQL 一致。四个回归使用同一批 {v['matched_children']} 名子女。置信区间为 1,000 次父亲聚类 bootstrap 的百分位区间，兄弟姐妹一起抽样。</p>{table('pilot_ige',3)}
<div class="note"><strong>解释界限：</strong>中年多年与早期多年的点估计之差为 {diff:.3f}，配对 bootstrap 的 95% 区间为 [{ci[0]:.3f}, {ci[1]:.3f}]，包含零。因此可以展示测量时点的敏感性及方向，不能宣布已经统计证实生命周期偏差。年龄、宏观时期、家庭组成同时变化，不能将差异全部归为年龄因果效应。</div>
<h2>7. 为什么本次不需要外部 CPI</h2><p>每个窗口都使用同样的三个日历年份，每个人的多年指标都是三次自然对数收入的均值，即几何平均收入的对数。统一年度价格指数只会给每个窗口的对数指标减去同一个常数，因此不会改变含截距 OLS 的 IGE 斜率。这个结论依赖完整相同年份及相同权重；不能用于缺失年份各不相同的窗口，也不能直接推广到名义收入算术均值。</p>
<p>因此，多年指标明确叫几何平均收入。图形应比较中心化的对数收入及斜率，不能把名义金额跨期差距直接解读为实际生活水平增长。</p>
<h2>8. 下一步文章能展示什么</h2><p>数据已支持：SELECT 选列；UNION ALL 叠加六个年份；个人表自连接建立父子关系；按复合键 JOIN 附加收入；LEFT JOIN 审计未匹配记录；GROUP BY、COUNT、AVG 汇总收入；HAVING 筛选三次完整窗口；以及 Python 的四种口径回归和可视化。正式 Blog 中可直接使用本报告的真实合并预览与筛选数字。</p><p class="small">此报告只做数据核查与试算，不修改先前文章，也不把旧版第三方样本的 661 人结果沿用于本次数据。</p></body></html>'''
(ROOT/'PSID_official_data_check.html').write_text(body)
print('Wrote PSID_official_data_check.html')
