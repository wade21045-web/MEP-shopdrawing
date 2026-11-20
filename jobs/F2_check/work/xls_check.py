import pickle,collections,json
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
R=pickle.load(open('check.pkl','rb')); ROWS,DROWS=R['ROWS'],R['DROWS']
VC=json.load(open('vcheck.json')); VM=json.load(open('vmerge.json')); ML=json.load(open('merge_log.json'))
wb=Workbook(); thin=Side(style='thin',color='999999'); B=Border(left=thin,right=thin,top=thin,bottom=thin)
HF=PatternFill('solid',fgColor='DDEBF7'); FILL={'一致':'E2EFDA','位置偏差':'F8CBAD','形式不一致':'FCE4D6','暖通有装饰无':'FFF2CC','待确认':'FFFF99','装饰有暖通无':'DDEBF7'}
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
    rows.append([r['no'],r['zone'],'ACD图' if r['src']=='ACD' else 'B区酒店图',r['room'],r['htype'],r['hform'],r['hsize'],r['hlabel'],r['dtype'],r['dform'],r['dsize'],r['dist'],'；'.join(r['issues']),'；'.join(r['note']),r1(r['hx']),r1(r['hy']),r1(r['dx']),r1(r['dy']),r['hblock'],r.get('dblock','')])
for r in DROWS:
    rows.append([r['no'],r['zone'],'—',r['room'],'—','—','—','',r['dtype'],r['dform'],r['dsize'],f"最近暖通{r['near']}",r['issue'],r['note'],'','',r1(r['dx']),r1(r['dy']),'',r['dblock']])
sheet(ws,['编号','区域','暖通来源图','房间/位置(装饰图房间名)','暖通风口类型(系统)','暖通形式','暖通尺寸(块外形mm)','暖通标注','装饰风口类型','装饰形式','装饰尺寸mm','偏差mm(暖通→装饰中心)','问题类型','说明','暖通X','暖通Y','装饰X','装饰Y','暖通块名','装饰块名'],rows,[7,12,10,22,22,11,12,18,16,11,11,11,22,48,10,10,10,10,16,16],fillcol=12)
ws=wb.create_sheet('统计')
c=collections.Counter(i for r in ROWS for i in r['issues'])
dupn=c['暖通有装饰无(重复图元)']
lst=[['项目','数量','说明'],
['暖通风口总数(2F合并图)',R['nH'],f"ACD图{sum(1 for r in ROWS if r['src']=='ACD')}个 + B区酒店图{sum(1 for r in ROWS if r['src']=='B')}个(两图重叠处完全相同的8个只保留一份)"],
['装饰天花风口总数(L2-大平面-升版9.2)',R['nDEC'],'方形风口221(600×600为主)、$风口$00000092方形散流器符号36、A/E排风符号6组、换气扇3、加压送风口2'],
['已配对',R['npairs'],f"第一轮≤1.5m {R['pairstage'].get(1,0)}对，第二轮1.5–3m {R['pairstage'].get(2,0)}对"],
['— 位置与形式均一致(≤100mm)',c['一致'],''],
['— 位置偏差 >100mm',c['位置偏差'],'图层 核对-位置偏差，含引线 核对-引线'],
['— 形式不一致',c['形式不一致'],'图层 核对-形式不一致；与位置偏差可同时出现'],
['— 待确认(二次配对)',c['待确认(二次配对1.5–3m)'],'图层 核对-待确认'],
['暖通有装饰无',c['暖通有装饰无']+dupn,f"其中重复图元{dupn}个(同一位置两个排风口块完全重叠，均为原图自带，非合并造成)"],
['装饰有暖通无',len(DROWS),'图层 核对-装饰有暖通无'],
['',None,''],['按区域','',''],]
Z=collections.defaultdict(collections.Counter)
for r in ROWS:
    Z[r['zone']]['暖通风口']+=1
    for i in r['issues']: Z[r['zone']][i.split('(')[0]]+=1
for r in DROWS: Z[r['zone']]['装饰有暖通无']+=1
for z in ['ACD-东北','ACD-中部','ACD-西南斜翼','B区-酒店']:
    k=Z[z]; lst.append([z,k['暖通风口'],f"一致{k['一致']}，位置偏差{k['位置偏差']}，形式不一致{k['形式不一致']}，待确认{k['待确认']}，暖通有装饰无{k['暖通有装饰无']}，装饰有暖通无{k['装饰有暖通无']}"])
lst+=[['',None,''],['合并与图元核验','',''],
['ACD图模型空间图元',VM['nA'],f"合并图中逐图元比对(类型+图层+坐标)缺失/改变 {VM['missA']} 个"],
['B区酒店图模型空间图元',VM['nB'],f"平移(+28961.421, +285185.283)后导入{ML['imported']}个，全部逐图元一致；与ACD图完全相同的{ML['imported'] and 4547}个未重复导入；26个ACAD代理对象(TWT_DIM天正标注)无法转换"],
['2F_机电合并.dwg 模型空间图元',VM['nO'],'= ACD 58275 + B 18945；无其他新增图元'],
['核对图中合并图图元缺失/改变',VC['miss'],'DWG回读后逐图元比对'],
['核对图新增图元(只在核对-图层)',sum(VC['newL'].values()),'；'.join(f'{k}:{v}' for k,v in VC['newL'].items())],
]
for r in lst: ws.append(r)
for cc in ws[1]: cc.font=Font(bold=True); cc.fill=HF
ws.column_dimensions['A'].width=40; ws.column_dimensions['B'].width=10; ws.column_dimensions['C'].width=90
ws=wb.create_sheet('图层核验')
sheet(ws,['图层','合并图图元数','核对图中保持一致','暖通相关'],[[L,n,k,'是' if h else ''] for L,n,k,h in VC['rows']]+[[L,0,f'新增 {n}',''] for L,n in VC['newL'].items()],[50,12,16,10])
ws=wb.create_sheet('说明与假设')
for t in ['1. 本版只核对、不修改：两张暖通图的风口、风管、水管、风机盘管及附件全部保持原样；装饰图也未改动。问题只用云线+编号+说明画在“核对-”开头的新图层上。',
'2. 合并：以 2026.08.24 F02-MEP-A C D区 图为基准(坐标不动)；2026.09.28 F02-MEP-B区(酒店部分)_t3 图按轴号配准整体平移 dx=+28961.421, dy=+285185.283(120个轴号全部吻合，残差0，无旋转/缩放)后并入同一模型空间。',
'3. 合并去重：两图在交界处有完全相同的图元(类型、图层、坐标、块名一致)4547个，只保留ACD图那一份；其中包括8个风口、两图共用的建筑底图块 A$C25902DC9 及 C15358-00-AATC-DD-BASE-AR1/AR2(逐图元展开比对完全一致)。同名但内容不同的块导入时自动改名(加数字后缀)，同名同内容的块共用。B图中26个天正标注代理对象(TWT_DIM)无法转换，未带入。',
'4. 装饰图 L2-大平面-升版9.2 无轴号，按结构柱配准：平移 dx=+316546.489, dy=+304548.380(93个装饰柱中80个与机电底图柱中心重合，残差中位0mm)。装饰风口外形复制到图层“核对-装饰风口(参照)”；整张装饰平面以图块“L2装饰平面_升版9.2(参照)”插入在图层“核对-装饰底图(参照)”，默认冻结，需要对照时解冻。',
'5. 装饰风口识别：综合末端-天花/C-暖通设备图层上的“方形风口”块(220个600×600、1个300×300)、$风口$00000092(36个)、属性A/S=A/E的侧墙排风符号(6组)、$轴流风机(换气扇3个)、加压送风口2个。装饰图综合末端-天花层另有6个约569×189的矩形(B区条形风口旁约300mm)未当作风口，请确认。',
'6. 匹配规则同GF：不区分送/回风；第一轮1.5m内全局最优配对，第二轮1.5–3m(标“待确认”)；形式不同加罚分；3m内无装饰天花点位的暖通风口视为不在装饰图范围(本次0个)。',
'7. 偏差为暖通风口外形中心到装饰风口中心距离；方向按图面(上=北)给出，并列dx/dy(mm)。偏差≤100mm视为一致。',
'8. 形式：条形/条缝、方形/矩形、侧墙/加压送风口。暖通块$风口$00000105视为条形(含1个300×300者)；$风口$00000060/00000137/00000097视为方形；装饰方形风口600×600视为方形。条形对方形记“形式不一致”；方形尺寸不同(如排风320×320对600×600)只在说明中提示。',
'9. 编号：H###为暖通风口(全部列出，包括一致的)，D###为装饰有暖通无。图中只对不一致项画云线+编号+说明。',
'10. 区域：图中无A/B/C/D区文字，按位置分为 ACD-东北(约轴5–13)、ACD-中部(约轴1–5)、ACD-西南斜翼(约轴26–32)、B区-酒店(B图，约轴14–25)。房间名取装饰图SPACE-IDEN。',
'11. 本次未做与新底图的墙/柱/梁冲突检查(GF那次因换底图才做)。']:
    ws.append([t])
ws.column_dimensions['A'].width=140
for row in ws.iter_rows():
    for cc in row: cc.alignment=Alignment(wrap_text=True)
wb.save('../output_check/风口核对清单.xlsx'); print('ok')
