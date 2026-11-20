import pickle,openpyxl,json,collections
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
R=pickle.load(open('result.pkl','rb')); ISS=R['ISS']
wb=openpyxl.Workbook(); ws=wb.active; ws.title='风口核对清单'
H=['编号','区域(装饰图)','房间(建筑底图最近房名)','问题类型','偏差距离(mm)','暖通风口类型','暖通尺寸(图块外框mm)','暖通标注(1.5m内)','暖通X','暖通Y','暖通图块','装饰风口类型','装饰尺寸(mm)','装饰X','装饰Y','装饰图块','备注','修改意见']
ws.append(H)
FILL={'位置偏差':'FFF2CC','暖通有装饰无':'DDEBF7','装饰有暖通无':'FCE4D6','类型':'F8CBAD','地面':'EDEDED'}
for s in ISS:
    row=[s['no'],s.get('zone',''),s.get('room',''),s['kind'],round(s['dist']) if s.get('dist') is not None else '',
         s.get('h_type',''),s.get('h_size',''),s.get('h_label',''),round(s['hx']) if 'hx' in s else '',round(s['hy']) if 'hy' in s else '',s.get('h_block',''),
         s.get('d_type',''),s.get('d_size',''),round(s['dx']) if 'dx' in s else '',round(s['dy']) if 'dy' in s else '',s.get('d_block','')[:40],s.get('note',''),'']
    ws.append(row)
    k=s['kind']; f='类型' if '类型' in k else '地面' if '地面' in k else k.split('+')[0]
    ws.cell(ws.max_row,4).fill=PatternFill('solid',fgColor=FILL.get(f,'FFFFFF'))
    ws.cell(ws.max_row,18).fill=PatternFill('solid',fgColor='FFFFE0')
for c in ws[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='305496'); c.alignment=Alignment(wrap_text=True,vertical='center')
for col,w in zip('ABCDEFGHIJKLMNOPQR',[7,11,22,16,10,16,14,24,10,10,16,16,12,10,10,22,36,30]): ws.column_dimensions[col].width=w
ws.freeze_panes='B2'; ws.auto_filter.ref=ws.dimensions
# stats
w2=wb.create_sheet('统计')
w2.append(['分类','数量']); 
for k,v in R['stat'].items(): w2.append([k,v])
w2.append([]); w2.append(['区域','问题类型','数量'])
for (z,k),v in sorted(collections.Counter((s.get('zone',''),s['kind']) for s in ISS).items()): w2.append([z,k,v])
# matched
w3=wb.create_sheet('重合(≤100mm)')
w3.append(['暖通类型','暖通X','暖通Y','装饰类型','装饰X','装饰Y','距离'])
for i,j,dist in R['pairs']:
    if dist<=100: h=R['Hc'][i]; o=R['Dc'][j]; w3.append([h['type'],round(h['x']),round(h['y']),o['type'],round(o['x']),round(o['y']),round(dist)])
w4=wb.create_sheet('不在装饰图范围的暖通风口')
w4.append(['暖通类型','系统','X','Y','图块','说明'])
for h in R['Hn']: w4.append([h['type'],h['sys'],round(h['x']),round(h['y']),h['name'],'3m内无任何装饰天花内容，未参与核对'])
w5=wb.create_sheet('配准参数')
for r in [['装饰图','方法','平移ΔX(mm)','平移ΔY(mm)','旋转','比例','校核'],
 ['Office-F00 plan 1017','97个轴号文字配对(最小二乘)',-151883.20,-20917.26,'0°','1:1','轴号残差<0.001mm；墙线87%点≤1mm'],
 ['1.GF-01-0914 (模型空间框架)','墙线点云FFT互相关+ICP',36446.53,-20917.40,'0°','1:1','墙线75%点≤2mm；与图块A$C3087fbf4框架结果交叉验证，风口位置0mm一致'],
 ['1.GF-01-0914 (图块A$C3087fbf4)','墙线点云FFT互相关+ICP',-56314.20,-23735.08,'0°','1:1','墙线76%点≤2mm'],
 ['1.GF-02&03大平标新位置-0914','墙线点云FFT互相关+ICP',36446.00,-20918.06,'0°','1:1','墙线78%点≤2mm，与图块02-03组框架一致(<1mm)']]: w5.append(r)
for w in (w2,w3,w4,w5):
    for c in w[1]: c.font=Font(bold=True)
    for col in 'ABCDEFG': w.column_dimensions[col].width=22
wb.save('/workspace/GF_align/output/风口核对清单.xlsx'); print('ok',len(ISS))
