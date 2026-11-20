import pickle,json,collections,re,openpyxl
from openpyxl.styles import Font,PatternFill,Alignment
R=pickle.load(open('blk.pkl','rb'))
after=json.load(open('cnt_after.json'))['layers'] if __import__('os').path.exists('cnt_after.json') else {}
G={'A$C5E357C2F':('HVAC','暖通-空调水/风管/设备/图例 (绑定外参)'),'A$C124230B8':('HVAC','暖通-送排风/新风/风口/FCU (绑定外参)'),
'A$C4AC52382':('OTHER','给排水-给水/热水 (绑定外参)'),'A$C7CBB6E43':('OTHER','给排水-雨水/排水 (绑定外参)'),'A$C4F55710D':('OTHER','给排水-污废水 (绑定外参)'),
'A$C0DAF4DAC':('OTHER','消防-喷淋/消火栓/灭火器 (绑定外参)'),'A$C552D5B8D':('OTHER','电气-强电桥架/母线 (绑定外参)'),'A$C1C7B7192':('OTHER','电气-强弱电桥架/CCTV (绑定外参)'),
'A$C40F3171B':('STRUC','结构-梁柱板平面 (绑定外参, 位于平面图左上方 ~-300m 处)'),'DSDSAD':('STRUC','结构-夹层结构平面+图框 (位于平面图左侧)'),
'A$C66761927':('ARCH','建筑底图 (绑定外参)'),'dsadasdqwqwqq':('OTHER','天花综合末端: 灯具/报警按钮/检修口 (电气照明为主)'),'A$C7FB758C8':('NEUTRAL','剖面内小构件 (I-XREF, 6处)')}
wb=openpyxl.Workbook(); ws=wb.active; ws.title='分块分类'
H=['图块(外参)','专业分类','说明','处理','图层','展开图元数','示例文字']
ws.append(H)
fill={'HVAC':'C6EFCE','ARCH':'DDEBF7','STRUC':'FCE4D6','OTHER':'F8CBAD','NEUTRAL':'EDEDED'}
for b,(acc,tx) in R.items():
    cat,desc=G.get(b,('NEUTRAL','?'))
    for L,n in acc.most_common():
        act='保留' if cat!='OTHER' else '删除'
        if cat=='HVAC' and L=='EQUIP_地漏': act='删除(给排水地漏)'
        ws.append([b,cat,desc,act,L,n,' | '.join(tx.get(L,[]))[:80]])
        ws.cell(ws.max_row,2).fill=PatternFill('solid',fgColor=fill[cat])
ws2=wb.create_sheet('模型空间直接图元')
ws2.append(['图层','分类','处理','说明'])
MS=[('Misc-Hvac$0$...$MEQUIP / M-ANNO-SYMB / M-ANNO-PATT','HVAC','保留','暖通设备/符号'),('DUCT-送风风口','HVAC','保留','送风口'),('DUCT-新风管端线 / DUCT-新风法兰','HVAC','保留',''),('ACS_COM','HVAC','保留','剖面内暖通构件'),
('TH_DIM','混合','部分保留','剖面标注: CWS/CWR/CD/FAD/FCU/房间名保留; PL/SW(给排水)、EL/ICT/UPS/FA(桥架)删除'),
('TEL_TEXT','混合','部分保留','修改说明: 风管/空调水/新风/净高类保留; 强电/弱电桥架类删除'),('DIM_MODI / TEL_SYMB','混合','部分保留','修改云线/三角号: 按最近修改说明归属, 靠近桥架说明的删除'),
('TEL_DIM / DIM_SYMB','通用','保留','剖面尺寸、标高、楼板标注'),('0 (直接图元)','通用','保留','剖面中的FCU等设备线条'),
('WALL / COLUMN / A-WALL-1 / AR-WALL-CONC-F / MENUISERI1 / PUB_HATCH / S-楼板-截面线 / DOTE / S-BEAM / A-WALL-PATT-6','ARCH/STRUC','保留','剖面中的墙/柱/楼板'),
('支吊架','通用','保留(存疑)','综合支吊架, 暖通风管亦用'),('I-XREF','通用','保留',''),('图层1','通用','保留','范围框'),('00-20260422-REV (DSDSAD)','STRUC','保留','结构图'),
('C-天花轮廓线 (dsadasdqwqwqq)','OTHER','删除','天花综合末端点位(灯具等)'),('桥架 / CABLETRAY / 桥架中心线','OTHER','删除','电缆桥架'),('ASHADE / AR3_INFO','空','保留','渲染设置, 无图元')]
for r in MS:
    ws2.append(list(r)); ws2.cell(ws2.max_row,2).fill=PatternFill('solid',fgColor={'HVAC':'C6EFCE','OTHER':'F8CBAD'}.get(r[1],'EDEDED'))
# layer sheet
ws3=wb.create_sheet('图层汇总')
ws3.append(['图层','出现于(分类)','原图元数','保留后图元数','结论'])
Lc=collections.defaultdict(lambda:[collections.Counter(),0])
for b,(acc,tx) in R.items():
    cat=G.get(b,('NEUTRAL',''))[0]
    for L,n in acc.items(): Lc[L][0][cat]+=n; Lc[L][1]+=n
ACC=pickle.load(open('acc.pkl','rb'))['ent']
for L in set(ACC)-set(Lc): Lc[L][0]['MS直接']+=ACC[L]
for L,(cc,n) in sorted(Lc.items(),key=lambda x:-ACC.get(x[0],0)):
    n=ACC.get(L,0); a=after.get(L,0)
    ws3.append([L,', '.join(f'{k}:{v}' for k,v in cc.most_common()),n,a,'保留' if a==n else ('删除' if a==0 else '部分保留')])
for w in (ws,ws2,ws3):
    for c in w[1]: c.font=Font(bold=True)
    w.freeze_panes='A2'
    for col,wd in zip('ABCDEFG',[16,10,36,16,40,12,60]): w.column_dimensions[col].width=wd
# summary
ws0=wb.create_sheet('汇总',0)
ws0.append(['分类','图块','展开图元数','处理'])
for b,(acc,tx) in R.items():
    cat,desc=G.get(b,('NEUTRAL','?')); ws0.append([cat,b+' '+desc,sum(acc.values()),'删除' if cat=='OTHER' else '保留'])
ws0.column_dimensions['B'].width=70; ws0.column_dimensions['C'].width=14
wb.save('/workspace/GF_hvac/output/图层分类表.xlsx'); print('ok')
