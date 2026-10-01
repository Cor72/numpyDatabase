"""Exploratory charts; run with the project's virtual environment."""
from pathlib import Path
import re
import json
import html
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from analyze_survey import OPTIONS, normalize
from analyze_chart_styles import ORDER

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs' / 'advanced_review'
BG, INK, MUTED = '#F4F3EF', '#253547', '#657383'
TEAL, ORANGE = '#147D86', '#CF794E'

def indicators(series, options):
    result = pd.DataFrame(index=series.index)
    for option in options:
        pattern = r'(?<![^，；;])' + re.escape(normalize(option)) + r'(?=$|[，；;])'
        result[option] = series.map(lambda v: bool(re.search(pattern, normalize(v))) if pd.notna(v) else False)
    return result.astype(int)

def main():
    source = ROOT / '图片收集（收集结果）.xlsx'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    d = pd.read_excel(source).dropna(axis=1,how='all')
    assert len(d.columns)==17
    OUT.mkdir(parents=True,exist_ok=True)
    fonts={f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update({'font.family':next(f for f in ['Microsoft YaHei','SimHei','Noto Sans CJK SC'] if f in fonts),'axes.unicode_minus':False,'svg.fonttype':'path'})
    assert d.iloc[:,[1,2,3,4,10,15]].notna().all().all(), '本版分析要求所用题目非空，请先核对缺失值'
    pain=indicators(d.iloc[:,4],OPTIONS[4])
    features=indicators(d.iloc[:,10],OPTIONS[10])
    pcount, fcount = pain.sum(axis=1),features.sum(axis=1)
    difficulty=d.iloc[:,2]; interest=d.iloc[:,3]; grade=d.iloc[:,1]
    assert set(difficulty)<=set(ORDER[2]) and set(interest)<=set(ORDER[3])
    assert set(grade)=={'高二','高三'} and set(d.iloc[:,15])<=set(ORDER[15])
    titles=[]; summaries=[]
    def canvas(number,title,subtitle,left=.13,bottom=.19):
        fig,ax=plt.subplots(figsize=(16,9),facecolor=BG)
        ax.set_facecolor(BG)
        fig.subplots_adjust(left=left,right=.89,top=.75,bottom=bottom)
        fig.text(.065,.93,f'探索性分析  /  {number:02d}',color=TEAL,fontsize=13)
        fig.text(.065,.855,title,color=INK,fontsize=27,weight='bold')
        fig.text(.065,.798,subtitle,color=MUTED,fontsize=13)
        ax.tick_params(axis='both',length=0,labelsize=12,pad=10,colors=INK)
        for s in ax.spines.values(): s.set_visible(False)
        return fig,ax
    def finish(fig,num,title,summary,note):
        fig.text(.065,.095,note,color=MUTED,fontsize=10)
        fig.text(.065,.052,'来源：250份物理学习问卷；仅作样本内探索，未进行显著性检验，不推断因果关系。',color=MUTED,fontsize=10)
        fig.savefig(OUT/f'{num:02d}.png',dpi=200,facecolor=BG)
        fig.savefig(OUT/f'{num:02d}.svg',facecolor=BG)
        plt.close(fig)
        titles.append(title); summaries.append(summary)
    rng=np.random.default_rng(20261001)

    title='学习难度不同，功能选择广度有何差异？'
    fig,ax=canvas(1,title,'箱线图 + 个体散点｜每个点是一份答卷，纵轴是勾选的预设功能数量')
    groups=[fcount[difficulty.eq(c)].to_numpy() for c in ORDER[2]]
    bp=ax.boxplot(groups,positions=np.arange(5),widths=.45,patch_artist=True,showfliers=False,
                  medianprops={'color':INK,'linewidth':2},whiskerprops={'color':MUTED},capprops={'color':MUTED})
    for patch in bp['boxes']: patch.set_facecolor('#A6CED0');patch.set_alpha(.7)
    for x,values in enumerate(groups):
        ax.scatter(x+rng.uniform(-.16,.16,len(values)),values,s=22,color=TEAL,alpha=.38,zorder=3,edgecolors='none')
    ax.set_xticks(range(5),[f'{c}\nn={len(v)}' for c,v in zip(ORDER[2],groups)])
    ax.set_yticks(range(9));ax.set_ylim(-.4,8.6);ax.set_ylabel('预设功能勾选数（0—8）',fontsize=13,color=INK)
    ax.yaxis.grid(True,color='#DDE1DF');ax.set_axisbelow(True)
    medians={c:float(np.median(v)) for c,v in zip(ORDER[2],groups)}
    pd.DataFrame([{'难度':c,'样本数':len(v),'中位数':np.median(v),'Q1':np.quantile(v,.25),'Q3':np.quantile(v,.75)} for c,v in zip(ORDER[2],groups)]).to_csv(OUT/'01_box_summary.csv',index=False,encoding='utf-8-sig')
    finish(fig,1,title,'不同难度组的功能勾选中位数：'+'；'.join(f'{c} {v:g}项' for c,v in medians.items())+'。','箱体为第25—75百分位，中线为中位数，须为1.5倍四分位距范围；散点保留全部个体，横向抖动仅避免重叠。')

    title='学习痛点广度与功能需求广度'
    fig,ax=canvas(2,title,'散点图｜两轴均为勾选项数；轻微抖动用于展示重叠答卷')
    for g,color,marker in [('高二',TEAL,'o'),('高三',ORANGE,'^')]:
        mask=grade.eq(g);size=int(mask.sum())
        ax.scatter(pcount[mask]+rng.uniform(-.14,.14,size),fcount[mask]+rng.uniform(-.14,.14,size),s=46,c=color,marker=marker,alpha=.48,label=f'{g} · n={size}',edgecolors='none')
    ax.set_xlim(-.5,7.5);ax.set_ylim(-.5,8.5);ax.set_xticks(range(8));ax.set_yticks(range(9))
    ax.set_xlabel('预设学习困难勾选数（0—7）',fontsize=13,color=INK);ax.set_ylabel('预设功能勾选数（0—8）',fontsize=13,color=INK)
    ax.grid(color='#DDE1DF',alpha=.7);ax.set_axisbelow(True);ax.legend(frameon=False,fontsize=13,loc='upper left')
    corr=float(np.corrcoef(pcount,fcount)[0,1])
    finish(fig,2,title,f'两类勾选数量的样本 Pearson 相关系数为 {corr:.2f}。共同的多选作答倾向也可能影响这一关系。','坐标原值为整数；抖动不改变统计值。数量表示选择广度，不表示困难严重程度或功能重要性。')

    title='困难与兴趣交叉后，学生分布在哪里？'
    table=pd.crosstab(difficulty,interest).reindex(index=ORDER[2],columns=ORDER[3],fill_value=0)
    table.to_csv(OUT/'03_difficulty_interest.csv',encoding='utf-8-sig')
    fig,ax=canvas(3,title,'气泡矩阵｜圆面积与人数成正比，数字为实际人数；保留所有非空组合',left=.16)
    for y in range(5):
        for x in range(5):
            value=int(table.iloc[y,x])
            if value:
                ax.scatter(x,y,s=value*65,color=TEAL,alpha=.78,edgecolors=BG,linewidths=1)
                ax.text(x,y,str(value),ha='center',va='center',color='white' if value>=8 else INK,fontsize=13,weight='bold')
    ax.set_xticks(range(5),ORDER[3]);ax.set_yticks(range(5),[f'{c} (n={int(table.loc[c].sum())})' for c in ORDER[2]])
    ax.set_xlim(-.65,4.65);ax.set_ylim(4.65,-.65);ax.set_xlabel('对物理的兴趣程度',color=INK,fontsize=13)
    ax.grid(color='#DDE1DF',alpha=.6);ax.set_axisbelow(True)
    hard=difficulty.isin(['比较困难','非常困难']);like=interest.isin(['比较喜欢','很喜欢']);hard_like=int((hard&like).sum())
    finish(fig,3,title,f'觉得物理比较或非常困难的 {int(hard.sum())} 人中，仍有 {hard_like} 人（{hard_like/hard.sum():.1%}）比较或很喜欢物理。','气泡是人数而非组内比例；不同难度组样本量不同。空白格表示0人，圆面积采用统一比例。')

    title='哪些功能经常被同一位学生勾选？'
    short=['拍照生成','暂停慢放','受力与轨迹','修改参数','临界时刻','错题演示','课堂分享','自建实验']
    intersections=features.T.dot(features)
    sums=features.sum().to_numpy();union=sums[:,None]+sums[None,:]-intersections.to_numpy()
    jaccard=np.divide(intersections.to_numpy(),union,out=np.zeros_like(union,dtype=float),where=union>0)
    pd.DataFrame(jaccard,index=features.columns,columns=features.columns).to_csv(OUT/'04_feature_jaccard.csv',encoding='utf-8-sig')
    intersections.to_csv(OUT/'04_feature_joint_counts.csv',encoding='utf-8-sig')
    fig,ax=canvas(4,title,'共选热力图｜Jaccard比例 = 同时选择两项的人数 ÷ 至少选择其中一项的人数',left=.17,bottom=.23)
    masked=np.ma.array(jaccard,mask=np.eye(8,dtype=bool))
    im=ax.imshow(masked,cmap='YlGnBu',vmin=0,vmax=1,aspect='auto')
    for y in range(8):
        for x in range(8):
            if x!=y: ax.text(x,y,f'{jaccard[y,x]:.0%}',ha='center',va='center',fontsize=11,color='white' if jaccard[y,x]>.52 else INK)
    ax.set_xticks(range(8),short,rotation=20,ha='right');ax.set_yticks(range(8),short)
    fig.colorbar(im,ax=ax,fraction=.035,pad=.025,format=matplotlib.ticker.PercentFormatter(1))
    pairs=[(jaccard[i,j],i,j) for i in range(8) for j in range(i+1,8)];score,i,j=max(pairs)
    finish(fig,4,title,f'共选重合度最高的是“{short[i]}＋{short[j]}”：Jaccard 为 {score:.1%}，同时勾选 {int(intersections.iloc[i,j])} 人。','对角线不显示；共选反映选择重合，不代表互补性、功能组合的因果效果或实施优先级。')

    title='不同年级的功能偏好，有多大差别？'
    bygrade=features.groupby(grade).mean()*100
    delta=bygrade.loc['高三']-bygrade.loc['高二'];sort=delta.sort_values().index
    grade_export=pd.DataFrame({'高二人数':features[grade.eq('高二')].sum(),'高二比例':bygrade.loc['高二']/100,'高三人数':features[grade.eq('高三')].sum(),'高三比例':bygrade.loc['高三']/100,'高三减高二_百分点':delta})
    grade_export.to_csv(OUT/'05_grade_preferences.csv',encoding='utf-8-sig')
    fig,ax=canvas(5,title,'哑铃图｜同一功能在高二、高三中的选择比例；右侧标出“高三 − 高二”的百分点差',left=.30)
    for y,c in enumerate(sort):
        a,b=bygrade.loc['高二',c],bygrade.loc['高三',c]
        ax.plot([a,b],[y,y],color='#B8C4C6',linewidth=3,zorder=1)
        ax.scatter(a,y,color=TEAL,s=80,label='高二' if y==0 else None,zorder=2)
        ax.scatter(b,y,color=ORANGE,s=80,label='高三' if y==0 else None,zorder=2)
        ax.text(103,y,f'{delta[c]:+.1f} pp',va='center',fontsize=12,color=MUTED)
    ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%']);ax.set_yticks(range(8),sort);ax.invert_yaxis()
    ax.xaxis.grid(True,color='#DDE1DF');ax.set_axisbelow(True);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.14),ncol=2,frameon=False,fontsize=12)
    largest=delta.abs().idxmax()
    finish(fig,5,title,f'年级选择率差异最大的一项是“{largest}”：高二 {bygrade.loc["高二",largest]:.1f}%，高三 {bygrade.loc["高三",largest]:.1f}%。',f'组内分母：高二 n={int(grade.eq("高二").sum())}，高三 n={int(grade.eq("高三").sum())}。pp表示百分点；差异不等于统计显著。')

    title='不同困难程度下，继续使用意愿如何分布？'
    intent_order=ORDER[15]
    intent=pd.crosstab(difficulty,d.iloc[:,15]).reindex(index=ORDER[2],columns=intent_order,fill_value=0)
    rates=intent.div(intent.sum(axis=1),axis=0)
    intent.to_csv(OUT/'06_difficulty_intent_counts.csv',encoding='utf-8-sig');rates.to_csv(OUT/'06_difficulty_intent_rates.csv',encoding='utf-8-sig')
    fig,ax=canvas(6,title,'行内比例热力图｜每行合计100%；格内同时显示百分比和人数',left=.18)
    im=ax.imshow(rates,cmap='PuBuGn',vmin=0,vmax=1,aspect='auto')
    for y in range(5):
        for x in range(5):
            value=rates.iloc[y,x]
            ax.text(x,y,f'{value:.1%}\n{intent.iloc[y,x]}人',ha='center',va='center',fontsize=13,color='white' if value>.53 else INK)
    ax.set_xticks(range(5),intent_order);ax.set_yticks(range(5),[f'{c} (n={int(intent.loc[c].sum())})' for c in ORDER[2]])
    fig.colorbar(im,ax=ax,fraction=.035,pad=.025,format=matplotlib.ticker.PercentFormatter(1))
    willing=intent[['比较愿意','非常愿意']].sum(axis=1)/intent.sum(axis=1)
    finish(fig,6,title,'各困难组“比较／非常愿意”的合计比例：'+'；'.join(f'{k} {v:.1%}' for k,v in willing.items())+'。','题目前提：实际体验后确实帮助理解。此为条件性自报意愿；小样本组比例波动较大，不代表实际留存。')

    derived=pd.DataFrame({'Excel行号':d.index+2,'年级':grade,'学习难度':difficulty,'物理兴趣':interest,'困难勾选数':pcount,'功能勾选数':fcount})
    derived.to_csv(OUT/'respondent_metrics.csv',index=False,encoding='utf-8-sig')
    pd.concat([pd.Series(d.index+2,name='Excel行号'),features.add_prefix('功能_'),pain.add_prefix('困难_')],axis=1).to_csv(OUT/'selection_indicators.csv',index=False,encoding='utf-8-sig')
    evidence={'source_sha256':digest,'records':len(d),'feature_options':len(features.columns),'pain_options':len(pain.columns),'count_pearson_r':corr,'difficult_and_likes':hard_like,'difficult_total':int(hard.sum()),'feature_medians_by_difficulty':medians,'conclusions':summaries}
    (OUT/'analysis.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=''.join(f'<section><span>EXPLORATION {i:02d}</span><h2>{html.escape(title)}</h2><p>{html.escape(summary)}</p><img src="{i:02d}.png" alt="{html.escape(title)}"><p><a href="{i:02d}.png">高清 PNG</a> · <a href="{i:02d}.svg">矢量 SVG</a></p></section>' for i,(title,summary) in enumerate(zip(titles,summaries),1))
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>物理学习 · 探索性分析</title><style>body{background:#F4F3EF;color:#253547;font:17px/1.8 "Microsoft YaHei",sans-serif;margin:0}main{max-width:1200px;margin:50px auto;padding:0 24px}h1{font-size:40px}section{padding:30px 0;border-top:1px solid #ccd6d5;margin:35px 0}img{width:100%;height:auto}span,a{color:#147D86}p{max-width:1050px}aside{background:#e3ece9;padding:24px}</style><main><span>PHYSICS / STUDENT RESEARCH</span><h1>从单题统计，走向交叉关系</h1><p>250份答卷 · 六张探索图 · 保留所有答卷与原始计数</p><aside>阅读口径：这些关系来自同一次自报问卷，不能证明因果或教学效果。多选题勾选数量仅是选择广度，可能受作答风格影响；无新增需求与无困难等自填内容不计入预设选项数。箱线图用于计数数据；类别仍保留原始等级。分析未进行显著性检验，不宣称总体差异成立。</aside>'+cards+'<section><h2>可转化为试点问题</h2><p>把“有兴趣但觉得困难”的学生作为一个待验证的用户群体；探索高共选功能是否适合一起呈现；用真实试用比较学生的理解、独立解题表现与使用体验。上述方向来自描述性观察，需通过后续研究验证。</p></section></main></html>'
    (OUT/'index.html').write_text(page,encoding='utf-8')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    assert int(table.values.sum())==len(d)==int(intent.values.sum())
    assert np.allclose(jaccard,jaccard.T) and np.allclose(np.diag(jaccard),1)
    assert np.allclose(rates.sum(axis=1),1)
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__':
    main()
