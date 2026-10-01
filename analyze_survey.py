r"""Run: .\.venv\Scripts\python.exe analyze_survey.py"""
from pathlib import Path
import json
import html
import re
import hashlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'survey_review'
OPTIONS = {
    4: ['知道公式，但想象不出实际过程', '静态示意图不容易理解', '多个物体相互作用时容易混乱', '临界状态或多阶段运动难理解', '受力分析比较困难', '老师讲时能懂，自己做题不会', '题目条件一变化就不会迁移'],
    5: ['直线运动与受力', '斜面与摩擦', '圆周与轨道运动', '碰撞与动量问题', '振动与周期运动', '电磁感应与电路动态过程', '电场磁场中带电粒子运动'],
    10: ['拍照题目，自动生成动态演示', '暂停/慢放/单步观察', '显示受力、速度或运动轨迹', '修改参数后自动重新计算', '显示临界状态发生的时刻', '保存自己的错题演示', '老师分享课堂演示给学生', '自己搭建物理实验'],
    14: ['AI对题目理解错误', '生成的物理过程不准确', '操作太复杂', '生产速度太慢', '支持的题型太少', '容易依赖，减少独立思考', '动画好看，但对做题没帮助', '使用不方便/需要付费'],
}

def normalize(value):
    return re.sub(r'\s+', '', str(value)).replace(',', '，')

def main():
    source = ROOT / '图片收集（收集结果）.xlsx'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    raw = pd.read_excel(source)
    data = raw.dropna(axis=1, how='all').copy()
    assert len(data.columns) == 17, '问卷结构发生变化，请核对字段后再运行。'
    for col in data:
        data[col] = data[col].map(lambda v: v.strip() if isinstance(v, str) else v).replace('', pd.NA)
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(data)
    assert n > 0
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    font = next((f for f in ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC'] if f in fonts), None)
    if font is None:
        raise RuntimeError('请安装中文字体 Microsoft YaHei 或 Noto Sans CJK SC')
    plt.rcParams.update({'font.family': font, 'axes.unicode_minus': False, 'svg.fonttype': 'path'})
    records, residuals, figures = [], [], []

    def summarize(index, options=None):
        series = data.iloc[:, index].dropna()
        base = len(series)
        if options is None:
            counts = series.value_counts()
        else:
            counts = pd.Series(0, index=options, dtype=int)
            for row, value in series.items():
                remaining = normalize(value)
                # Longest first; internal punctuation remains part of the option.
                for option in sorted(options, key=len, reverse=True):
                    token = normalize(option)
                    pattern = r'(?<![^，；;])' + re.escape(token) + r'(?=$|[，；;])'
                    if re.search(pattern, remaining):
                        counts[option] += 1
                        remaining = re.sub(pattern, '', remaining)
                remainder = remaining.strip('，；;')
                if remainder:
                    residuals.append({'Excel行号': int(row) + 2, '题目': data.columns[index], '原回答': value, '未归入预设选项的内容': remainder})
        assert counts.between(0, base).all()
        if options is None:
            assert counts.sum() == base
        for option, count in counts.items():
            records.append({'题目': data.columns[index], '选项': option, '人数': int(count), '分母': base, '比例': float(count / base), '类型': '多选' if options else '单选'})
        return counts, base

    def chart(number, title, subtitle, counts, base, multi=False, sort=True, footnote=''):
        if sort:
            counts = counts.sort_values(ascending=False, kind='stable')
        fig, ax = plt.subplots(figsize=(16, 9), facecolor='#F5F7FB')
        ax.set_facecolor('#F5F7FB')
        fig.subplots_adjust(left=.34, right=.87, top=.75, bottom=.19)
        colors = ['#234C80'] * len(counts)
        if sort:
            colors[0] = '#128B88'
        bars = ax.barh(range(len(counts)), counts.values / base * 100, color=colors, height=.58)
        ax.set_yticks(range(len(counts)), counts.index, fontsize=14)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'], fontsize=11, color='#637184')
        ax.xaxis.grid(True, color='#DEE4ED', linewidth=.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis='both', length=0, pad=12)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for bar, count in zip(bars, counts.values):
            ax.text(bar.get_width()+1.5, bar.get_y()+bar.get_height()/2, f'{count/base:.1%}  |  {count}人', va='center', fontsize=13, color='#18314D')
        fig.text(.065, .92, f'需求调研  /  {number:02d}', fontsize=13, color='#128B88')
        fig.text(.065, .853, title, fontsize=27, weight='bold', color='#18314D')
        fig.text(.065, .795, subtitle, fontsize=14, color='#52647A')
        note = f'本题作答人数 n={base}；' + ('多选题，各选项占作答人数的比例，合计可超过100%。' if multi else '单选题，百分比因四舍五入可能不恰好合计100%。')
        fig.text(.065, .105, note, fontsize=11, color='#637184')
        fig.text(.065, .067, footnote or '来源：物理学习与动态演示工具需求问卷；描述样本内意见，不代表全体高中生。', fontsize=11, color='#637184')
        name = f'{number:02d}'
        fig.savefig(OUT / f'{name}.png', dpi=200, facecolor=fig.get_facecolor())
        fig.savefig(OUT / f'{name}.svg', facecolor=fig.get_facecolor())
        plt.close(fig)
        figures.append((name, title, subtitle))

    pain, base = summarize(4, OPTIONS[4])
    chart(1, '学习痛点：多物体与多阶段过程', f'“多个物体相互作用时容易混乱”获选 {pain.iloc[2]/base:.1%}，是预设痛点中最高的一项。', pain, base, True)
    topics, base = summarize(5, OPTIONS[5])
    top = topics.idxmax()
    chart(2, '动态演示应优先覆盖哪些题型？', f'样本内获选最多：{top}（{topics.max()/base:.1%}）。', topics, base, True)
    features, base = summarize(10, OPTIONS[10])
    chart(3, '功能优先级：学生最期待什么', f'“{features.idxmax()}”获选最多（{features.max()/base:.1%}）。', features, base, True)
    ways, base = summarize(11)
    chart(4, '产品应支持学生先思考、再验证', f'{ways.get("先自己思考，再用动态演示验证",0)/base:.1%} 选择先自己思考，再用动态演示验证。', ways, base)
    intent, base = summarize(15)
    intent = intent.reindex(['非常愿意', '比较愿意', '可以尝试', '不太愿意', '完全不愿意'], fill_value=0)
    chart(5, '继续使用意愿：以确实帮助理解为前提', f'“非常愿意”与“比较愿意”合计 {(intent.iloc[0]+intent.iloc[1])/base:.1%}；这是有条件的自报意愿。', intent, base, sort=False, footnote='题目前提：实际体验后确实能帮你理解物理。此结果不能解释为实际留存率或教学效果。')
    concerns, base = summarize(14, OPTIONS[14])
    chart(6, '推进试点，也要回应学生的担忧', f'获选最多的担忧是“{concerns.idxmax()}”（{concerns.max()/base:.1%}）。', concerns, base, True, footnote='保留原问卷选项措辞（包括“生产速度太慢”）；此图反映担忧，不代表已发生的产品缺陷。')
    for index in [1, 2, 3, 6, 9, 13]:
        summarize(index)
    pd.DataFrame(records).to_csv(OUT / 'statistics.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(residuals, columns=['Excel行号', '题目', '原回答', '未归入预设选项的内容']).to_csv(OUT / 'unmatched_answers.csv', index=False, encoding='utf-8-sig')
    data.to_csv(OUT / 'cleaned_answers.csv', index=False, encoding='utf-8-sig')
    audit = {'source': source.name, 'source_sha256': before, 'records': n, 'removed_empty_columns': int(raw.shape[1]-data.shape[1]), 'missing_after_strip': data.isna().sum().to_dict(), 'duplicate_rows': int(data.duplicated().sum()), 'duplicate_answers_excluding_time': int(data.iloc[:,1:].duplicated().sum()), 'grade_counts': data.iloc[:,1].value_counts().to_dict(), 'multiselect_residual_entries': len(residuals), 'font': font, 'method': '所有记录保留；仅去除全空列与首尾空格。多选按完整选项及分隔边界匹配，每人每选项最多计一次；自填残余单独输出，分母保留该题所有非空作答。未据此判定250份均为有效问卷。'}
    (OUT / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    cards = ''.join(f'<section><h2>{html.escape(title)}</h2><p>{html.escape(sub)}</p><img src="{name}.png" alt="{html.escape(title)}"><p><a href="{name}.png">高清 PNG</a> · <a href="{name}.svg">矢量 SVG</a></p></section>' for name,title,sub in figures)
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>物理动态演示工具 · 需求调研</title><style>body{margin:0;background:#eef2f7;color:#18314d;font:17px/1.8 "Microsoft YaHei",sans-serif}main{max-width:1200px;margin:50px auto;padding:0 24px}h1{font-size:38px}section{background:white;padding:28px;margin:30px 0;border-radius:12px}img{width:100%;height:auto}a{color:#128b88}.note{padding:24px;background:#e0e9f3}h2{margin:0}p{color:#52647a}</style><main><h1>物理动态演示工具：需求调研</h1>'''
    page += f'<p>样本数 {n} · 高二 {audit["grade_counts"].get("高二",0)} 人 / 高三 {audit["grade_counts"].get("高三",0)} 人 · 6 张评审展示图</p>'
    page += '<div class="note">解读口径：全部记录保留，描述样本内意见。多选比例以本题非空作答人数为分母；自填内容未强行并入预设选项。未取得抽样方式、学校分布与真实使用效果信息，因此不推断全体学生需求或教学效果。图表顺序建议：痛点 → 题型 → 功能 → 学习方式 → 条件性意愿 → 风险与试点。</div>'
    page += cards + '<section><h2>评审讲述与下一步验证</h2><p>这些回答为“复杂物理过程的可视化辅助”提供需求依据。建议从高需求题型做试点，支持暂停、观察和自主验证，并检验生成准确性、理解表现与独立解题表现。问卷中的预期不能替代实际效果验证。</p><p>开放题未自动编码成主题占比；不把“无”视为整份问卷无效。完整统计、原始回答对应的清洗表、未匹配内容和审计信息均保存在本目录。</p></section></main></html>'
    (OUT / 'index.html').write_text(page, encoding='utf-8')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before, '原文件发生变化'
    assert len(list(OUT.glob('*.png'))) == 6 and len(list(OUT.glob('*.svg'))) == 6
    print(json.dumps(audit, ensure_ascii=False))
    print('Charts and report saved:', OUT)

if __name__ == '__main__':
    main()
