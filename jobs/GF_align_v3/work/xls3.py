import pickle,collections,numpy as np,json
from scipy.spatial import cKDTree
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
V=pickle.load(open('v3_after.pkl','rb')); CH=V['CH']; Q=V['Q']; ISS=pickle.load(open('conf.pkl','rb'))
REG=pickle.load(open('reg_d1d2.pkl','rb')); RS=pickle.load(open('reg_struct.pkl','rb')); BL=json.load(open('base_log.json'))
R=pickle.load(open('/workspace/GF_align/work/hv_raw.pkl','rb'))
H0=np.array([(h['x'],h['y']) for h in R if h['kind']=='INSERT' and h['root'] in('A$C5E357C2F','A$C124230B8') and h['name'].startswith('$风口$') and h['layer'].startswith('DUCT-')])
T0=cKDTree(H0)
V2=pickle.load(open('/workspace/GF_align/work/v2_after.pkl','rb')); v2n={r['id']:np.array(r['new']) for r in V2['CH']}; v2old=cKDTree([r['old'] for r in V2['CH']]); v2ids=[r['id'] for r in V2['CH']]
def wade(c):
    dd,_=T0.query(c['old'])
    if '弧形' in c['h_type']: return '—'
    if dd<=1: return '未动(与10.24管综位置相同)'
    return f'已调整过(相对管综移动{dd:.0f}mm)，仍差{c["dist"]:.0f}mm'
def v2ref(c):
    dd,j=v2old.query(c['old'])
    k=[i for i,r in enumerate(V2['CH']) if np.hypot(*(np.array(r['new'])-c['new']))<=100]
    return V2['CH'][k[0]]['id'] if k else '新(v2无)'
wb=Workbook(); thin=Side(style='thin',color='999999'); B=Border(left=thin,right=thin,top=thin,bottom=thin)
HF=PatternFill('solid',fgColor='DDEBF7'); YF=PatternFill('solid',fgColor='FFF2CC'); RF=PatternFill('solid',fgColor='F8CBAD')
def sheet(ws,head,rows,widths):
    ws.append(head)
    for c in ws[1]: c.font=Font(bold=True); c.fill=HF; c.alignment=Alignment(wrap_text=True,vertical='center'); c.border=B
    for r in rows: ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=Alignment(wrap_text=True,vertical='top'); c.border=B
    for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='B2'
def how(c):
    n=' '.join(c['notes'])
    if '弧形' in c['h_type'] or c['form'].endswith('弧形条缝'): return '弧形风口重画+静压箱随动'
    if c['eq'].startswith('风机盘管'): return '风口+支管+风机盘管+水管支管整体横移'
    if '沿主风管' in n: return '支管沿主风管平移'
    if '箱体不变' in n: return '静压箱内移位'
    if '乙字弯' in n: return '支管末端乙字弯'
    if c['flex'].startswith('风口不在'): return '软管/短支管连接'
    return '支管末端拉伸' if c['dist']>100 else '原位改型'
ws=wb.active; ws.title='风口调整清单'
rows=[]
for c in CH:
    rows.append([c['id'],c['zone'],c['room'],how(c),c['h_type'],c['h_block'],c['h_label'],round(c['old'][0]),round(c['old'][1]),
                 c['d_type'],c['d_size'],c['d_block'],round(c['new'][0]),round(c['new'][1]),round(c['dist']),
                 (f"{c.get('axial',0):.0f} / {c.get('lateral',0):.0f}" if 'axial' in c else ''),c['form'] or '—',(f"{c['rot']:+.1f}°" if c['rot'] else ''),
                 c['duct'],c['flex'],c['eq'] or '未移动',c['labels'],'；'.join(c['notes']),wade(c),v2ref(c),''])
sheet(ws,['编号','区域','房间','调整方式','暖通原风口(系统)','原块名','原标注','原X','原Y','对应装饰风口','装饰尺寸','装饰块名','调整后X','调整后Y','移动距离mm','轴向/横向分量mm','形式变化','旋转','风管修改(图层 动作×数量)','软管/连接','风机盘管/水管/设备','标注随动','备注/假设/需复核','Wade上一轮是否已调整','对应v2编号','Wade修改意见'],rows,
      [7,11,20,20,18,15,16,9,9,16,11,22,9,9,9,12,14,8,48,30,40,16,48,24,10,22])
for r in range(2,len(rows)+2): ws.cell(r,26).fill=YF
ws2=wb.create_sheet('待Wade决定')
rows=[[q['id'],q['kind'],q['zone'],q['room'],q['type'],q['block'],q.get('label',''),round(q['c'][0]),round(q['c'][1]),q['note'],''] for q in Q]
sheet(ws2,['编号','问题','区域','房间','风口类型','块名','暖通标注','X','Y','说明/建议','Wade决定'],rows,[7,18,11,22,18,24,16,9,9,60,24])
for r in range(2,len(rows)+2): ws2.cell(r,11).fill=YF
ws5=wb.create_sheet('新底图冲突')
rows=[[s['id'],s['sev'],s['kind'],s['room'],round(s['c'][0]),round(s['c'][1]),s['hv'],s['bg'],s['src'],s['note'],''] for s in ISS]
sheet(ws5,['编号','严重度','冲突类型','房间','X','Y','暖通图元(调整编号/图层/块)','底图图元(图层)','来源','说明/建议','Wade决定'],rows,[7,7,20,22,9,9,40,30,20,60,22])
for i,s in enumerate(ISS,2):
    ws5.cell(i,11).fill=YF
    if s['sev']=='高': ws5.cell(i,2).fill=RF
ws3=wb.create_sheet('统计')
npairs=len(V['pairs']); adopt=pickle.load(open('adopt.pkl','rb'))
st=[['【底图替换】',''],['建筑底图配准(轴号最小二乘, 97/97个轴号)',f"平移 dx={REG['t'][0]:.3f}, dy={REG['t'][1]:.3f} mm, 旋转0°, 比例1:1, 最大残差{REG['res']:.2e} mm"],
    ['墙线复核(d1旧墙点落在新墙线1mm内的比例)','92.0%（其余8%为新底图中已变动的墙体）'],
    ['结构L01梁柱平面叠加(轴线一维配准, X轴13/13、Y轴10/10)',f"平移 dx={RS['t'][0]:.1f}, dy={RS['t'][1]:.1f} mm；201个柱中187个与建筑柱/墙轮廓重合"],
    ['删除的旧底图',f"建筑底图块 A$C76C4695F ×1(28.3万图元) + 散落墙线AR-WALL-PLST 4条；清理无引用块{BL['purged_blocks']}个"],
    ['暖通图元是否改动(底图替换步骤)','未改动(替换前后模型空间非底图图元逐层计数一致，33351个)'],
    ['【风口核对】',''],
    ['暖通风口总数(119个块+1组弧形)',V['nH']],['其中在装饰图范围内',V['nHc']],['装饰风口总数(已剔除厨房排水沟盖板44个；含弧形8个、散线条缝等18个)',V['nDEC']],
    ['暖通-装饰配对数',npairs],['  配对后已重合(≤100mm且形式一致)，未改',npairs-len(CH)],['  已调整(位置和/或形式)',len(CH)]]
for k,v in collections.Counter(how(c) for c in CH).most_common(): st.append(['    '+k,v])
st.append(['  其中形式变化',sum(1 for c in CH if c['form'])])
st.append(['  其中移动>1m',sum(1 for c in CH if c['dist']>1000)])
st.append(['  其中二次配对(1.5–3m)',sum(1 for c in CH if c['stage']==2)])
st.append(['  其中Wade上一轮已调整过但仍未对准',sum(1 for c in CH if wade(c).startswith('已调整'))])
st.append(['  其中Wade上一轮未动',sum(1 for c in CH if wade(c).startswith('未动'))])
for k,v in collections.Counter(q['kind'] for q in Q).most_common(): st.append(['待定：'+k,v])
st.append(['【新底图冲突】',''])
for k,v in collections.Counter((s['sev'],s['kind']) for s in ISS).most_common(): st.append([f'{k[0]}：{k[1]}',v])
st.append(['【与v2对比】',''])
for k,v in adopt.most_common(): st.append(['v2的76处调整在本次暖通图(Wade已对过)中：'+k,v])
sheet(ws3,['项目','数量/结果'],st,[70,60])
ws4=wb.create_sheet('说明与假设')
notes=[
'1. 输入：①《2026.09.23 G层风管图纸(2).dwg》(Wade已对过风口的暖通图，作为暖通内容来源)；②《GF_风口核对.dwg》(其中的建筑底图块A$C66761927、结构L01梁柱平面A$C40F3171B、夹层结构平面+图框DSDSAD作为新底图)；③《Office-F00 plan 1017.dwg》(13/11新版装饰图)。①在聊天附件中无法读取，已从Wade电脑 桌面\\暖通图纸20261112\\GF\\ 同名文件(29.1MB，与附件大小一致)复制，仅读取未改动。',
'2. 楼层：GF(首层)。三张图坐标系一致：建筑底图插入点相同(8046.5,18543.8)，97个轴号逐一对应，配准平移为0；装饰图轴号与上一版完全一致，沿用上一版平移(-151883.20,-20917.26)。',
'3. 底图替换：只删除①中的旧建筑底图块A$C76C4695F和4条散落的AR-WALL-PLST墙线；①中剖面详图内的墙/柱/楼板(WALL/COLUMN/A-WALL-1/PUB_HATCH/S-楼板-截面线等)属于暖通剖面详图，保留未动；①中的旧天花参照(综合末端-天花、C-天花轮廓线、天花末端点位中的*U条缝块、灯具编号等)不属于建筑结构底图，保留未动(可冻结)。',
'4. 新底图图层：新底图-建筑(d2)、新底图-结构L01(d2原位)、新底图-结构M层(d2原位)、新底图-结构L01(配准叠加)，冻结对应图层即可整体隐藏。结构图在原图中位于平面左侧(未叠加)，按原位保留；另按轴线配准叠加一份L01梁柱平面到GF平面上(灰褐色)，仅用于梁柱冲突核对，如不需要可冻结/删除该图层。',
'5. 导入时有46个与其它幕墙线完全重叠的重复图元未重复导入(几何无差异)；497个ACAD_PROXY_OBJECT代理对象(非图形)未导入。',
'6. 厨房内装饰图的排水沟盖板(块名含"排水沟盖板"、F-地面回风口多段线44个)不是风口，已剔除。',
'7. 不区分送/回/排风：装饰风口只按形式(方形/条形/圆形/喷口/弧形)与位置对应暖通风口；"每个暖通送风口都要有装饰风口对应"按全部暖通风口执行。',
'8. 调整规则与v2相同：①位置偏差：风口中心移至装饰风口中心；②形式不符：更换为暖通图内同类块($风口$00000060方形散流器/$00000105条形/$00000106圆形/$00000103喷口)，外形按装饰尺寸缩放、方向按装饰；③连接：支管首段沿轴向拉伸；横向偏差时，风机盘管只带此一个风口则风口+支管+风机盘管+凝水/供回水支管末端整体横移，否则支管末端做乙字弯(偏移段≥300mm)；风口在静压箱内的仅移风口；立管、主管不动。',
'9. 形式判定沿用v2：暖通$风口$00000105按条形/条缝；装饰"百叶/矩形风口"长宽比<2.5按方形/矩形。因此400×200等暖通条形百叶对装饰400×433/544×800百叶会被判为形式不符并改为方形块(外形按装饰尺寸)，规格/风量需复核。',
'10. 弧形风口：①中"天花末端点位"图层只剩1组弧形条缝(16弧，已与装饰重合)；另7处装饰弧形条缝处已有暖通静压箱+风机盘管(Wade上一轮已对位)，但暖通图没有弧形风口图形。本次不自行补画(不臆造)，列入待定"装饰有暖通无(静压箱已就位)"。',
'11. 未新增、未删除暖通风口；新增/取消需风量计算，列入"待Wade决定"。',
'12. 新底图冲突：只核对平面。①风口外形与新建筑墙线/柱截面相交；②风管外轮廓与新底图中新增或移位的墙体交叉(旧底图已有的墙不重复报)；③风管/风机盘管与柱截面相交；④风口与L01梁边线重叠(提示，需核对梁底标高)。墙体"新增/移位"按旧底图墙线30mm内无对应判定。',
'13. 原位置保留在"调整前-暖通风口/调整前-暖通风管/调整前-暖通设备及水管"图层(灰色虚线)；修改处红色云线(调整-修改云线)+编号C###(调整-编号)；待定项橙色圆圈Q###(调整-待定)；新底图冲突紫色三角B###(调整-新底图冲突)；软管/接驳示意线在"调整-风口连接软管"。',
'14. 建筑、结构底图本身未改动。',
]
for n in notes: ws4.append([n])
ws4.column_dimensions['A'].width=150
for row in ws4.iter_rows():
    for c in row: c.alignment=Alignment(wrap_text=True)
wb.save('/workspace/GF_align_v3/output/风口调整清单.xlsx'); print('ok',len(CH),len(Q),len(ISS))
