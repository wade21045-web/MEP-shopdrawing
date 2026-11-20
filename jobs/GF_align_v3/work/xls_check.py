import pickle,collections,json
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
R=pickle.load(open('check.pkl','rb')); ROWS,DROWS,ISS=R['ROWS'],R['DROWS'],R['ISS']
VJ=json.load(open('verify.json'))
wb=Workbook(); thin=Side(style='thin',color='999999'); B=Border(left=thin,right=thin,top=thin,bottom=thin)
HF=PatternFill('solid',fgColor='DDEBF7'); FILL={'一致':'E2EFDA','位置偏差':'F8CBAD','形式不一致':'FCE4D6','暖通有装饰无':'FFF2CC','待确认':'FFFF99','装饰有暖通无':'DDEBF7','弧形':'E4DFEC'}
def sheet(ws,head,rows,widths,fillcol=None):
    ws.append(head)
    for c in ws[1]: c.font=Font(bold=True); c.fill=HF; c.alignment=Alignment(wrap_text=True,vertical='center'); c.border=B
    for r in rows: ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='top'); c.border=B
        if fillcol is not None:
            v=str(row[fillcol].value)
            for k,f in FILL.items():
                if k in v: row[fillcol].fill=PatternFill('solid',fgColor=f)
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='B2'; ws.auto_filter.ref=ws.dimensions
r1=lambda v: round(float(v)) if v!='' else ''
ws=wb.active; ws.title='风口核对清单'
rows=[]
for r in ROWS:
    rows.append([r['no'],r['zone'],r['room'],r['htype'],r['hform'],r['hsize'],r['hlabel'],r['dtype'],r['dform'],r['dsize'],r['dist'],'；'.join(r['issues']),'；'.join(r['note']),r1(r['hx']),r1(r['hy']),r1(r['dx']),r1(r['dy']),r['hblock'],r.get('dblock','')])
for r in DROWS:
    rows.append([r['no'],r['zone'],r['room'],'—','—','—','',r['dtype'],r['dform'],r['dsize'],f"最近暖通{r['near']}",r['issue'],r['note'],'','',r1(r['dx']),r1(r['dy']),'',r['dblock']])
sheet(ws,['编号','装饰分区','房间/位置','暖通风口类型(系统)','暖通形式','暖通尺寸(块外形mm)','暖通标注','装饰风口类型','装饰形式','装饰尺寸mm','偏差mm(暖通→装饰中心)','问题类型','说明','暖通X','暖通Y','装饰X','装饰Y','暖通块名','装饰块名'],rows,[7,11,24,20,11,12,18,16,11,11,11,22,48,10,10,10,10,16,16],fillcol=11)
ws=wb.create_sheet('新底图冲突')
sheet(ws,['编号','严重程度','冲突类型','房间/位置','暖通对象','底图对象(图层)','来源','说明','X','Y'],
      [[s['id'],s['sev'],s['kind'],s['room'],s['hv'],s['bg'],s['src'],s['note'],round(s['c'][0]),round(s['c'][1])] for s in ISS],[7,8,22,24,34,30,20,40,10,10])
ws=wb.create_sheet('统计')
c=collections.Counter(i for r in ROWS for i in r['issues'])
lst=[['项目','数量','说明'],
['暖通风口总数(G层平面内)',R['nH'],'含弧形风口组1组；块风口119个'],
['装饰天花风口总数',R['nDEC'],'Office-F00用最新装饰图(d3)；GF-01、GF-02&03沿用上一轮装饰图'],
['已配对',R['npairs'],'第一轮≤1.5m 103对，第二轮1.5–3m 4对'],
['— 位置与形式均一致(≤100mm)',c['一致'],''],
['— 位置偏差 >100mm',c['位置偏差'],'图层 核对-位置偏差，含引线 核对-引线'],
['— 形式不一致',c['形式不一致'],'图层 核对-形式不一致；与位置偏差可同时出现'],
['— 待确认(二次配对)',c['待确认(二次配对1.5–3m)'],'图层 核对-待确认'],
['暖通有装饰无',c['暖通有装饰无']+c['暖通有装饰无(重复图元)'],f"其中重复图元{c['暖通有装饰无(重复图元)']}个、不在装饰图范围1个"],
['装饰有暖通无',sum(1 for r in DROWS if r['issue'].startswith('装饰有暖通无')),'图层 核对-装饰有暖通无(弧形者在 核对-弧形风口)'],
['弧形风口：装饰有、暖通仅静压箱',sum(1 for r in DROWS if r['issue'].startswith('弧形')),'全日餐厅等：暖通静压箱+风机盘管已就位但无弧形风口图形；图层 核对-弧形风口'],
['新底图冲突 B###',len(ISS),'；'.join(f'{k}:{v}' for k,v in collections.Counter(s['kind'] for s in ISS).items())],
['',None,''],
['暖通图元核验','',''],
['Wade原图(d1)模型空间图层数',len(VJ['rows']),''],
['逐图层逐图元完全一致的图层',sum(1 for r in VJ['rows'] if r[3]),'按类型+坐标+块名比对，DWG回读后'],
['暖通相关图层(DUCT-/EQ-/管道/VANNE/M_/Misc-Hvac等)',sum(1 for r in VJ['rows'] if r[4]),f"共{sum(r[1] for r in VJ['rows'] if r[4])}个图元，全部一致"],
['删除的原底图图元',len(VJ['removed']),'旧建筑底图块A$C76C4695F(0层)1个 + AR-WALL-PLST 墙面抹灰 4条线'],
]
for r in lst: ws.append(r)
for cc in ws[1]: cc.font=Font(bold=True); cc.fill=HF
ws.column_dimensions['A'].width=40; ws.column_dimensions['B'].width=10; ws.column_dimensions['C'].width=80
ws=wb.create_sheet('图层核验')
sheet(ws,['图层','原图图元数','输出图元数','完全一致','暖通相关'],[[a,b,c_,'是' if s else '否(底图删除)',('是' if h else '')] for a,b,c_,s,h in VJ['rows']]+[[L,0,n,'新增核对/底图图层',''] for L,n in VJ['newL']],[50,12,12,18,10])
ws=wb.create_sheet('说明与假设')
for t in ['1. 本版只核对、不修改：暖通风口、风管、空调水管、风机盘管及附件全部保持Wade原图(2026.09.23 G层风管图纸(2).dwg)不动，无“调整前”图层。',
'2. 底图：删除原建筑底图块A$C76C4695F及AR-WALL-PLST墙面抹灰；插入图2建筑块(同坐标，配准偏差0)和结构L01(按轴线配准叠加)，另保留结构L01/M层在图2原位。图2文件与我方v1输出GF_风口核对.dwg完全相同，仅取其建筑和结构块——如有更新的纯建筑/结构底图需重做。',
'3. 装饰：Office-F00区用最新装饰图Office-F00 plan 1017.dwg；GF-01、GF-02&03区未提供新图，沿用上一轮装饰风口。装饰风口外形复制在图层“核对-装饰风口(参照)”供对照。',
'4. 匹配规则同v2：不区分送/回风；厨房排水渠不算风口；第一轮1.5m内全局最优配对，第二轮1.5–3m(标“待确认”)；形式不同加罚分；弧形风口按弧线点集距离匹配；装饰图范围外(3m内无装饰点位)的暖通风口不核对。',
'5. 偏差为暖通风口外形中心到装饰风口中心距离；方向按图面(上=北)给出，并列dx/dy(mm)。偏差≤100mm视为一致。',
'6. 形式：条形/条缝、方形/矩形、圆形、喷口、弧形条缝。暖通块名$风口$00000105视为条形；装饰百叶/矩形风口长宽比≥2.5视为条形，否则方形。',
'7. 编号：H###为暖通风口(全部列出，包括一致的)，D###为装饰有暖通无，B###为新底图冲突。图中只对不一致项画云线+编号+说明。',
'8. 新底图冲突在Wade原始暖通位置上检查：风口与墙/柱重叠、风口与梁边线重叠(平面，低)、风管穿新增/移位墙体、风机盘管与柱/新墙。',
'9. DWG为减小体积，清理了图中未被任何图块/布局/对象引用的块定义(1258个，原图中即未使用，不影响任何可见内容)；动态块主定义、标注箭头块、被对象句柄引用的块均保留。清单见同目录 清理的未引用块清单.txt。']:
    ws.append([t])
ws.column_dimensions['A'].width=140
for row in ws.iter_rows():
    for cc in row: cc.alignment=Alignment(wrap_text=True)
wb.save('../output_check/风口核对清单.xlsx'); print('ok')
