import pickle,collections,numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font,Alignment,PatternFill,Border,Side
from openpyxl.utils import get_column_letter
V=pickle.load(open('v2_after.pkl','rb')); CH=V['CH']; Q=V['Q']
wb=Workbook(); thin=Side(style='thin',color='999999'); B=Border(left=thin,right=thin,top=thin,bottom=thin)
HF=PatternFill('solid',fgColor='DDEBF7'); YF=PatternFill('solid',fgColor='FFF2CC')
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
                 c['duct'],c['flex'],c['eq'] or '未移动',c['labels'],'；'.join(c['notes']),''])
sheet(ws,['编号','区域','房间','调整方式','暖通原风口(系统)','原块名','原标注','原X','原Y','对应装饰风口','装饰尺寸','装饰块名','调整后X','调整后Y','移动距离mm','轴向/横向分量mm','形式变化','旋转','风管修改(图层 动作×数量)','软管/连接','风机盘管/水管/设备','标注随动','备注/假设/需复核','Wade修改意见'],rows,
      [7,11,20,20,18,15,16,9,9,16,11,22,9,9,9,12,14,8,48,30,40,16,48,22])
for r in range(2,len(rows)+2): ws.cell(r,24).fill=YF
ws2=wb.create_sheet('待Wade决定')
rows=[[q['id'],q['kind'],q['zone'],q['room'],q['type'],q['block'],q.get('label',''),round(q['c'][0]),round(q['c'][1]),q['note'],''] for q in Q]
sheet(ws2,['编号','问题','区域','房间','风口类型','块名','暖通标注','X','Y','说明/建议','Wade决定'],rows,[7,18,11,22,18,24,16,9,9,60,24])
for r in range(2,len(rows)+2): ws2.cell(r,11).fill=YF
ws3=wb.create_sheet('统计')
npairs=len(V['pairs'])
st=[['暖通风口总数(含4组弧形)',V['nH']],['其中在装饰图范围内',V['nHc']],['装饰风口总数(已剔除厨房排水渠44个，含新增识别的弧形8个、条缝等18个)',V['nDEC']],
    ['暖通-装饰配对数',npairs],['  配对后已重合(≤100mm且形式一致)，未改',npairs-len(CH)],['  已调整(位置和/或形式)',len(CH)]]
for k,v in collections.Counter(how(c) for c in CH).most_common(): st.append(['    '+k,v])
st.append(['  其中形式变化',sum(1 for c in CH if c['form'])])
st.append(['  其中移动>1m',sum(1 for c in CH if c['dist']>1000)])
st.append(['  其中二次配对(1.5–3m)',sum(1 for c in CH if c['stage']==2)])
for k,v in collections.Counter(q['kind'] for q in Q).most_common(): st.append(['待定：'+k,v])
sheet(ws3,['项目','数量'],st,[70,10])
ws4=wb.create_sheet('说明与假设')
notes=[
'1. 坐标为输出DWG模型空间坐标(mm)，与上一版《GF_风口核对》一致；装饰图配准为纯平移(0°,1:1)，残差见上一版配准参数。',
'2. 厨房132m²内原识别为"地面回风口"的44个对象经核实为排水沟盖板(块名含"排水沟盖板")，已从装饰风口及清单中剔除。',
'3. 新增识别：GF-02&03 C-暖通设备图层上的散线弧形条缝风口8个(全日餐厅6个、酒店区2个)；Office图中散线/未命名块的条缝风口(会议室6.5m条缝、Waiting Area/Digital Lab/Innovation Hub等1200×200条缝等)。',
'4. 暖通侧弧形风口：暖通图块A$C124230B8中"天花末端点位"图层的4组弧线(每组16弧+端线)，位于风机盘管静压箱内，按暖通弧形条缝风口处理。',
'5. 不区分送/回/排风：装饰风口只按形式(方形/条形/圆形/喷口/弧形)与位置对应暖通风口。',
'6. 调整规则：①位置偏差：风口中心移至装饰风口中心；②形式不符：更换为暖通图内同类块($风口$00000060方形散流器/$00000105条形/$00000106圆形/$00000103喷口)，外形按装饰尺寸缩放、方向按装饰；弧形按装饰弧线重画；③连接：支管首段沿轴向拉伸(STRETCH)；横向偏差：风机盘管只带此一个风口时风口+支管+风机盘管+凝水/供回水支管末端整体横移，否则支管末端做乙字弯(偏移段≥300mm)；风口在静压箱内的仅移风口；立管不动。',
'7. 未新增暖通风口、未删除暖通风口：新增/取消需风量计算，列入"待Wade决定"。',
'8. 风口规格(尺寸/风量)：形式变化的风口外形按装饰尺寸，规格需暖通复核；同形式但尺寸不一致的已在备注中注明，未改规格。',
'9. 原位置保留在"调整前-暖通风口/调整前-暖通风管/调整前-暖通设备及水管"图层(灰色虚线)，可冻结；修改处有红色云线(调整-修改云线)及编号(调整-编号)；待定项为橙色圆圈(调整-待定)；软管/接驳示意线在"调整-风口连接软管"。',
'10. 建筑、结构底图未改动。',
]
for n in notes: ws4.append([n])
ws4.column_dimensions['A'].width=150
for row in ws4.iter_rows():
    for c in row: c.alignment=Alignment(wrap_text=True)
wb.save('/workspace/GF_align/output_v2/风口调整清单.xlsx'); print('ok',len(CH),len(Q))
