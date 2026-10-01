r"""Generate circle_review and line_review: .\.venv\Scripts\python.exe analyze_chart_styles.py"""
from pathlib import Path
import hashlib
import html
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / '图片收集（收集结果）.xlsx'
ORDER = {
    2: ['很轻松', '比较轻松', '一般', '比较困难', '非常困难'],
    3: ['很不喜欢', '比较不喜欢', '一般', '比较喜欢', '很喜欢'],
    6: ['从不', '很少', '偶尔', '比较多', '经常'],
    9: ['帮助不大', '一般', '比较有帮助', '非常有帮助'],
    13: ['偶尔', '每周1-2次', '每周3-5次', '几乎每天'],
    15: ['完全不愿意', '不太愿意', '可以尝试', '比较愿意', '非常愿意'],
}
TITLES = {1:'受访学生的年级构成', 2:'物理学习的难度感受', 3:'对物理学科的兴趣', 6:'多阶段运动状态的混淆频率', 9:'对动态工具帮助程度的预期', 11:'面对难题时偏好的学习方式', 13:'预计每周使用频率', 15:'有条件的继续使用意愿'}
PALETTE = ['#BA604A', '#E2A15F', '#567D73', '#7398AA', '#ACA2BD']

def counts(series, order=None):
    valid = series.dropna()
    result = valid.value_counts()
    if order:
        assert set(result.index).issubset(order), f'存在未识别选项：{set(result.index)-set(order)}'
        result = result.reindex(order, fill_value=0)
    assert int(result.sum()) == len(valid) and len(valid) > 0
    return result, len(valid)

def save(fig, folder, name):
    fig.savefig(folder / f'{name}.png', dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(folder / f'{name}.svg', facecolor=fig.get_facecolor())
    plt.close(fig)

def gallery(folder, titles, description, bg, fg):
    cards = ''.join(f'<section><h2>{html.escape(title)}</h2><img src="{i:02d}.png" alt="{html.escape(title)}"><p><a href="{i:02d}.png">高清 PNG</a> · <a href="{i:02d}.svg">矢量 SVG</a></p></section>' for i,title in enumerate(titles,1))
    page = f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{folder.name}</title><style>body{{background:{bg};color:{fg};font:17px/1.8 "Microsoft YaHei",sans-serif;margin:0}}main{{max-width:1200px;margin:48px auto;padding:0 24px}}h1{{font-size:38px}}section{{margin:36px 0}}img{{width:100%;height:auto;border-radius:12px}}a{{color:{fg}}}</style><main><h1>{folder.name}</h1><p>{description}</p>{cards}<p>来源：物理学习与动态演示工具需求问卷，250份记录全部保留。结果仅描述本样本。原始Excel未修改。</p></main></html>'
    (folder / 'index.html').write_text(page, encoding='utf-8')

def main():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    data = pd.read_excel(SOURCE).dropna(axis=1, how='all')
    assert len(data.columns) == 17
    for col in data:
        data[col] = data[col].map(lambda x:x.strip() if isinstance(x,str) else x).replace('', pd.NA)
    available = {f.name for f in font_manager.fontManager.ttflist}
    font = next(f for f in ['Microsoft YaHei','SimHei','Noto Sans CJK SC'] if f in available)
    plt.rcParams.update({'font.family':font, 'axes.unicode_minus':False,'svg.fonttype':'path'})
    circle = ROOT / 'outputs' / 'circle_review'
    line = ROOT / 'outputs' / 'line_review'
    circle.mkdir(parents=True, exist_ok=True)
    line.mkdir(parents=True, exist_ok=True)
    circle_rows, line_rows = [], []
    circle_indices = [1,2,9,11,13,15]
    for number,index in enumerate(circle_indices,1):
        result,base = counts(data.iloc[:,index], ORDER.get(index))
        fig = plt.figure(figsize=(16,9),facecolor='#FBF7EF')
        fig.text(.065,.92,f'学生需求调研  /  构成 {number:02d}',color='#BA604A',fontsize=13)
        fig.text(.065,.845,TITLES[index],color='#382F2B',fontsize=29,weight='bold')
        fig.text(.065,.79,'单选题 · 每个扇区表示该选项占本题作答人数的比例',color='#74695F',fontsize=14)
        ax = fig.add_axes([.06,.17,.46,.56])
        # Alternate traditional pies and rings within the same warm editorial style.
        ring = number % 2 == 1
        wedges,_ = ax.pie(result.values, startangle=90,counterclock=False, colors=PALETTE[:len(result)],
                          wedgeprops={'width':.30 if ring else 1,'edgecolor':'#FBF7EF','linewidth':2})
        if ring:
            ax.text(0,.06,str(base),ha='center',va='center',fontsize=40,weight='bold',color='#382F2B')
            ax.text(0,-.20,'本题作答人数',ha='center',fontsize=13,color='#74695F')
        ax.set_aspect('equal')
        for j,(label,count) in enumerate(result.items()):
            y = .67-j*.082
            fig.text(.56,y,'●',color=PALETTE[j],fontsize=22,va='center')
            fig.text(.59,y,label,color='#382F2B',fontsize=15,va='center')
            fig.text(.93,y-.032,f'{count} 人   /   {count/base:.1%}',ha='right',color='#74695F',fontsize=13)
            circle_rows.append({'题目':data.columns[index],'选项':label,'人数':int(count),'分母':base,'比例':count/base})
        fig.text(.065,.105,f'本题 n={base} · 人数与比例见右侧完整标注；比例四舍五入后合计可能不恰好为100%。',fontsize=11,color='#74695F')
        note = '题目前提：实际体验后确实帮助理解物理；自报意愿不代表实际留存率。' if index==15 else '来源：物理学习与动态演示工具需求问卷；结果仅描述本样本，不代表全体高中生。'
        fig.text(.065,.06,note,fontsize=11,color='#74695F')
        save(fig,circle,f'{number:02d}')

    assert set(data.iloc[:,1].dropna()) == {'高二','高三'}, '年级发生变化，请调整比较设计'
    for number,(index,order) in enumerate(ORDER.items(),1):
        fig,ax = plt.subplots(figsize=(16,9),facecolor='#111D30')
        ax.set_facecolor('#111D30')
        fig.subplots_adjust(left=.095,right=.91,top=.70,bottom=.23)
        fig.text(.065,.92,f'学生需求调研  /  年级对比 {number:02d}',color='#60DBC8',fontsize=13)
        fig.text(.065,.845,TITLES[index],color='#F2F5FB',fontsize=29,weight='bold')
        fig.text(.065,.79,'按等级顺序连接的分布折线 · 比较各年级内部比例，不是时间变化趋势',color='#ACBCD2',fontsize=14)
        for grade,color,marker in [('高二','#60DBC8','o'),('高三','#FFB779','D')]:
            selected = data.loc[data.iloc[:,1].eq(grade)].iloc[:,index]
            result,base = counts(selected,order)
            ax.plot(range(len(order)),result.values/base*100,color=color,marker=marker,markersize=9,
                    linewidth=3,label=f'{grade}  ·  n={base}')
            for label,count in result.items():
                line_rows.append({'题目':data.columns[index],'年级':grade,'选项':label,'人数':int(count),'分母':base,'比例':count/base})
        ax.set_ylim(0,100)
        ax.set_yticks([0,20,40,60,80,100],['0%','20%','40%','60%','80%','100%'],color='#ACBCD2',fontsize=12)
        ax.set_xticks(range(len(order)),order,color='#E9EFF9',fontsize=14)
        ax.tick_params(axis='both',length=0,pad=15)
        ax.grid(axis='y',color='#2A3A51',linewidth=.8)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.legend(loc='upper right',facecolor='#111D30',edgecolor='none',labelcolor='#E9EFF9',fontsize=14,ncol=2)
        fig.text(.065,.125,'口径：选项人数 ÷ 该年级本题非空作答人数。横轴为有序类别，类别间距不代表数值差距。',color='#ACBCD2',fontsize=11)
        note = '题目前提：实际体验后确实帮助理解物理；此图不代表实际留存率。' if index==15 else '仅作样本内描述性比较，未进行显著性检验；连线只辅助阅读，不表示因果关系。'
        fig.text(.065,.078,note,color='#ACBCD2',fontsize=11)
        fig.text(.065,.04,'来源：物理学习与动态演示工具需求问卷。',color='#8294AD',fontsize=10)
        save(fig,line,f'{number:02d}')
    pd.DataFrame(circle_rows).to_csv(circle/'statistics.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(line_rows).to_csv(line/'statistics.csv',index=False,encoding='utf-8-sig')
    gallery(circle,[TITLES[i] for i in circle_indices],'暖白纸感 · 陶土色系 · 3张饼图与3张圆环图。仅使用单选题，保留全部选项。','#FBF7EF','#382F2B')
    gallery(line,[TITLES[i] for i in ORDER],'深蓝背景 · 薄荷绿与杏色 · 6张年级分布对比图。横轴是有序回答等级，并非时间或连续数值。','#111D30','#E9EFF9')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    audit = {'records':len(data),'source_sha256':before,'source_unchanged':True,'circle_charts':6,'line_charts':6,'line_denominator':'每个年级每题非空作答人数','circle_denominator':'每题非空作答人数','font':font}
    for folder in [circle,line]:
        assert len(list(folder.glob('*.png')))==6 and len(list(folder.glob('*.svg')))==6
        (folder/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':
    main()
