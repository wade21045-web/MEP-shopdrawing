# MEP 图纸处理脚本

本仓库保存暖通施工图处理脚本，按作业放在 `jobs/` 下。这些文件是历次实际运行的记录，相对路径和内容保持原样，没有重构。图纸和中间数据（DWG、DXF、pickle、PNG、压缩包、`output/`）不入库。

## 用途

用 Python（[ezdxf](https://ezdxf.readthedocs.io/)）处理暖通 DXF：按实体 handle 增补或移动风机盘管、缩短风管并把风口对齐到装饰风口、清理首层底图、把首层暖通风口与装饰图对齐或只做核对、把二层两张机电图合并后再与装饰风口核对。改图一律另存新文件，说明和标记画在新建图层上。

## 总体工作流程

1. **DWG → DXF**。用 ODA File Converter。`jobs/GF_align_v3/work/oda.sh` 在虚拟显示（`xvfb-run`）下调用本机的 `ODAFileConverter`，命令行参数原样传给转换器。
2. **按 handle 编辑或核对**。`ezdxf.readfile` 读入后，用 `entitydb[handle]`，或按图层、块名、包围盒筛出实体，再复制、平移、拉伸、删除，或只加标注。
3. **逐实体核对**。`verify*.py` 对比输入与输出的实体签名：日志里删除的 handle 应不在结果中，未改动的实体签名保持不变，新增实体落在日志记录的 handle 或新建图层上。结果写入 json。
4. **改前 / 改后出图**。`render*.py`、`plan.py` 等用 matplotlib 按窗口把图元画成 PNG。
5. **DXF → DWG**。仍用 ODA File Converter 转回。

脚本里的做法：

- 写出用 `saveas` 新文件名（如 `out_after.dxf`、`v3_after.dxf`、`check.dxf`），不覆盖读入的原图。
- 说明和核对标记建在新图层上：`修改-…`、`调整-…`、`核对-…`、`装饰-风口` 等。
- 后一步读上一步写出的文件。`hvac_sad1000` 的链是：`build.py` → `out_after.dxf` → `build_v2.py` → `out_v2.dxf` → `v3/build.py` → `v2_shop.dxf` → `v3/build_v3.py` → `v3/v3.dxf`。

脚本里的 DXF、pickle、PNG 路径是当时机器上的工作路径，本仓库没有这些数据文件。

## 各作业

### `jobs/hvac_azone` — A 区风机盘管增补（参照做法）

以 FLOUR 房间已有的风机盘管为样板，在 STOR、OFF 两间按同一做法增补。

`region.py` 在固定世界窗口里为模型空间实体做包围盒索引（`region.pkl`）。`arch.py` 从图块 `1054E9` 抽出墙线。`find.py` 搜 FLOUR / STORAGE / OFFICE 等文字。`a1.py`–`a4.py` 查看指定 INSERT，以及三间房间在旋转后的局部坐标里的图元差异。`common.py` 放三间房间的原点和 handle 列表（送风、阀门、立管、新风）。`plan.py` 抽出 FLOUR 侧图层 `EQ-风机盘管` 上的线段，并画出三房间对照图。

`build.py` 读 `out/input.dxf`：删掉 STOR、OFF 的旧盘管组（按图层聚类加固定 handle），把去重后的 FLOUR 盘管线、送风、阀门链、立管和新风按房间平移复制过去，移动阵列块，在图层 `修改-风机盘管调整20261118` 写上「同FLOUR STORAGE做法」，另存 `out_after.dxf` 和 `build_log.json`。`clash.py` 检查新增线段是否穿过 `AR-WALL*` / `墙体完成面`。`verify.py` 用实体签名对照 `rt_out/rt.dxf`。`render.py` 按窗口把任意 DXF 画成 PNG。

### `jobs/hvac_shop` — SHOP 风机盘管移位

SHOP 左右两间（装饰风口 D050/D043、D044/D045）把标注为 FCU-06 的风机盘管移到回风口（兼检修口）上方，送风口与装饰风口重合。

`common.py` 用约 18.41° 的局部坐标系和四个装饰风口的世界坐标。`region.py`、`arch.py`、`find.py`、`dump.py`、`a4.py`、`plan.py` 做窗口索引、墙线、文字检索、图层清单和平面对照，不改图。

`build.py` 对左右两间：在局部窗口里选出盘管、送风管、FCU-06 文字、阀组、冷凝水符号和立管，按回风口与盘管中心的差值计算平移；复制后删除原实体，把送风管端拉到新的末端 X，在送风装饰风口处复制 600×600 风口块（原型 handle `DA072`），冷水供、冷水回和冷凝水立管用乙字弯改接到新阀组。说明写在图层 `修改-风机盘管调整20261119`，另存 `out_after.dxf`。`clash0.py` 统计被删线段在原图上与其他管线的交叉，`clash.py` 统计新线段与墙、既有管线的交叉。`verify.py` 对照 `rt_out/rt.dxf`。`render.py` 出 PNG。

### `jobs/hvac_sad1000` — 三个会议厅风管缩短与风口对齐

三个厅在代码里是 `top`、`mid`、`bot`。说明文字里称为「三个会议厅」。读入路径写在脚本中（`build.py` 读 `/workspace/hvac_shop/out/input.dxf`）。

- `build.py`：用暖通风口 handle `CCEC8` 与装饰风口 `1083AA` 的 X 差，把窗口内 SAD1000×250 直管缩短，下游送风管、支管、风口、机组、回风管整体左移，使 SAD∅300 与装饰圆形风口对齐；跨过窗口边界的 LINE / LWPOLYLINE 只拉伸落在窗内的端点。说明层 `修改-风管缩短20261119`，另存 `out_after.dxf`。
- `build_v2.py`：读 `out_after.dxf`。中厅、下厅做同样的缩短和左移；三个厅中部左上的 SAD∅300 移到装饰风口中心，删掉直管短节，弯头随风口改位置。另存 `out_v2.dxf`。
- `v3/build.py`：在 `out_v2.dxf` 上按 `hvac_shop` 的同一规则做左右两间 FCU-06 移位，另存 `v2_shop.dxf`。`v3/vshop.py` 用删除/新增签名对照 SHOP 作业的结果。
- `v3/build_v3.py`：读 `v2_shop.dxf`。三个厅左下 SAD∅300 侧送风口、墙边右上圆形风口与装饰风口同心（调弯头、缩短直管），并保留 SHOP 盘管修改。另存 `v3/v3.dxf`。

`verify.py`、`verify_v2.py`、`v3/verify_v3.py` 按日志中的 moved / stretched / deleted / modified 做指纹核对。`region.py`、`region2.py`、`dump.py`、`dump2.py`、`dump3.py`、`arch.py`、`arch_all.py`、`find.py`、`render.py`、`vdiag.py` 做索引、转储、墙线提取、风管尺寸文字查找和出图。

### `jobs/GF_hvac` — 首层暖通图清理

对象是 `dxf_out/GF.dxf`。

`an.py`–`an7.py` 从模型空间清点做到按图块展开：图层和类型、外部参照、代理实体、文字样本、图块包围盒，以及若干指定图块（含天花综合末端）的内容。`an2.py`、`an4.py` 把展开结果写入 pickle，供后面的分类表使用。

`clean.py` 从模型空间删掉给排水、消防、电气桥架和天花综合末端（灯具、报警按钮等）图块，以及桥架图层；删掉剖面里非暖通的管线标注和靠近这些标注的修改标记；暖通图块 `A$C5E357C2F`、`A$C124230B8` 只去掉块内图层 `EQUIP_地漏`。然后清理无引用图块和未使用图层，另存 `GF_clean.dxf`，并写 `clean_log.json`。`count.py` 统计清理后的图层和类型。`xls.py` 按专业（暖通 / 建筑 / 结构 / 其他）写出 `图层分类表.xlsx`。`render.py`、`render2.py` 出全图和局部 PNG。`c0.py`、`near.py`、`near2.py` 在指定坐标附近查看圆、弧和文字。

### `jobs/GF_align` — 首层风口与装饰对齐（第一轮）

把三张装饰图（GF-01、GF-02&03、Office-F00）的天花风口对齐到暖通底图 `GF_暖通+建筑结构底图.dxf`（路径指向 `GF_hvac` 的输出）。

配准和提取（只读）：`grids.py`、`g23.py`、`pts.py`、`fpts.py` 收集轴号和墙线点；`reg.py` 用轴号做二维相似变换并写出平移；`rreg.py` 用墙点的 FFT 卷积搜索旋转和平移，再做 ICP。`dec.py`、`q12.py`、`dec3.py`、`loose.py`、`clus.py`、`geo1.py` 从装饰图抽出风口块、散线和可复制的外形。`hv.py`、`hv2.py`、`hvzoom.py` 从两个暖通根图块抽出风口和管线。`compare.py` 按中心距（上限 1500 mm，匈牙利算法）配对，并记下形式和位置差异。

`build.py` 不移动暖通风口，只把装饰外形和核对圆圈、编号画进新文件 `GF_风口核对.dxf`（图层 `装饰-风口`、`风口核对-标记`、`风口核对-编号`、`风口核对-连线`）。

`v2.py` 才改暖通几何，参数为 `before` 或 `after`。两段配对距离是 1500 mm 和 3000 mm，形式不一致（方形/条缝/圆形/喷口/弧形）加距离惩罚。`after` 在根图块 `A$C5E357C2F`、`A$C124230B8` 内把 `$风口$` 块移到装饰中心（可换块、改比例和转角），弧形风口改画装饰轮廓，风管按局部坐标做相当于 AutoCAD STRETCH 的拉伸（横偏时加乙字弯），风机盘管组可随动；原位置留在 `调整前-暖通风口`、`调整前-暖通风管`、`调整前-暖通设备及水管`，修改处画 `调整-修改云线` 和编号。`before` 叠装饰参照、不做这些移动。分别另存 `v2_before.dxf`、`v2_after.dxf`。

`q.py`、`q2.py`–`q13.py`、`an.py`、`an2.py`、`cand.py`、`term.py`、`ftext.py`、`dz.py`、`zr.py`、`thumbs.py` 是当时的探查和局部出图。`xls.py`、`xls2.py` 出核对清单和调整清单。`render_any.py`、`render3.py`、`render_v2.py` 按窗口出 PNG。`lib.py` 是嵌套图块遍历。

### `jobs/GF_align_v3` — 首层换底图、风口对齐，以及只核对

这一轮先换建筑/结构底图，再在新底图上对齐；另有一条只标注、不改暖通的核对路径。

- `flat.py`、`gp.py`、`grids.py`、`reg.py`、`regst.py`、`regst2.py`、`regst3.py`、`st.py` 从新旧底图抽墙线和轴号并求平移（结构相对建筑的最终平移由 `regst3.py` 写入）。
- `build_base.py` 用 `Importer` 把新建筑、结构图块按上述平移放进旧图，去掉旧建筑底图和抹灰层，新底图使用 `新底图-建筑(d2)`、`新底图-结构L01(d2原位)` 等图层，并检查非「新底图」的模型空间实体未变。另存 `base.dxf`。
- `dec.py`、`q12.py`、`decbuild.py`、`dec3.py`、`geo1.py`、`lab.py` 提取装饰风口、房间文字，供对齐和核对共用。
- `v3.py` 在 `base.dxf` 上做与 `GF_align/work/v2.py` 同类的配对和 `before` / `after` 修改（移动风口、拉伸风管、风机盘管随动、云线和软管示意），另存 `v3_before.dxf`、`v3_after.dxf`。
- `conf_prep.py` 对比新旧墙、柱、梁；`conf.py` 在调整后的图上把风口和风管与这些构件做相交检查，冲突画在图层 `调整-新底图冲突`。
- `check.py`（`check_head.py` 与 `check_tail.py` 是同一流程拆成的前半和后半）配对后只在 `核对-*` 图层上加云线、编号、引线、装饰风口参照，以及与新底图冲突的标记，不改暖通风口位置。另存 `check.dxf`。`purge.py` 去掉无引用图块得到 `check_p.dxf`，`fixapp.py` 补回缺失的 APPID，`verify.py` 按图层签名确认暖通图层相对原图未变。
- `pickv.py` 按核对标记聚成四个视口，写入 `views.json`（会议中心、办公北区、工具间、全日餐厅/酒店区）。`render_v3.py`、`render_check.py` 用这些窗口出 PNG。`xls3.py`、`xls_check.py` 出调整清单和核对清单。
- `layers.py`、`blks.py`、`sz.py`、`h1.py`、`quick.py`、`rtcheck.py` 是清点和快照。`oda.sh` 是上一节的 ODA 转换封装。`lib.py` 是图块遍历。

### `jobs/F2_check` — 二层两张机电图合并，风口只核对、不改位

- `merge.py` 以 `dxf/F02-MEP-ACD.dxf` 为底，用 `Importer` 导入 `dxf/F02-MEP-B_hotel.dxf`。图块内容相同则沿用原名，不同则在导入时改名。模型空间里签名已存在的实体跳过；新导入的实体再平移一个固定偏移，使 B 区与 ACD 对齐。与 ACD 底图版本不同的底图块改到图层 `合并-B图自带底图(与ACD图底图版本不同)`。另存 `merged.dxf`。`verify_merge.py` 用实体签名检查 A、B 两侧是否都进入合并结果、有无多余实体。
- `cols.py`、`regdec.py` 用结构柱中心把装饰图 `L2-大平面-升版9.2` 配到机电坐标（装饰图没有轴号）。`grids.py`、`rooms.py`、`exdec.py`、`exdec2.py`、`exdec3.py`、`exdecT.py`、`exmep.py`、`exmepT.py`、`prep.py` 提取轴号、房间、装饰风口、暖通风口和天花覆盖范围。`layers.py`、`big.py`、`basecmp.py`、`ov.py`、`ovl.py` 是图层、大图块和两图重叠的探查。
- `check.py` 只处理合并图里图层 `DUCT-*`、块名含「风口」的 INSERT，与装饰风口按距离和形式配对（1.5 m 内，其次 1.5–3 m 标为待确认）。位置偏差、形式或条缝方向不一致、一侧有另一侧无，都只新增云线、文字和引线，图层为 `核对-装饰风口(参照)`、`核对-位置偏差`、`核对-形式不一致`、`核对-装饰有暖通无`、`核对-暖通有装饰无`、`核对-待确认`、`核对-引线`、`核对-编号`。整张装饰平面作为一个图块插在 `核对-装饰底图(参照)` 上，该图层冻结。不修改风口、风管、水管和风机盘管的位置。另存 `check.dxf`。`xls_check.py` 的说明页写明：本版只核对、不修改。
- `verify_check.py` 对比合并底图与核对图的实体签名，多出来的实体应只在核对图层上。`render_check.py` 按 `views.json` 的五个窗口（全层、ACD 东北/中部/西南、B 区酒店）出 PNG。`sigs.py`、`lib.py` 是签名和图块遍历。

## 依赖

第三方包见 `requirements.txt`（均为脚本中的 import）：`ezdxf`、`numpy`、`scipy`、`matplotlib`、`openpyxl`、`shapely`。其余用的是 Python 标准库（`json`、`pickle`、`math`、`re`、`collections`、`hashlib`、`sys`、`time`）。

`.gitignore` 排除 `*.dwg`、`*.dxf`、`*.pkl`、`*.png`、`*.zip`、`*.xz`、`output/` 和 `__pycache__/`。
