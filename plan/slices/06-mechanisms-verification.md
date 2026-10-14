# 06 · 完整消融、H2 结构控制与 H3 联合风险

**F27 在开发阶段冻结代理并供 F20 使用；其余任务在全局冻结后测量。代理相关性不是因果证明。**

继承 `01-foundation.md` 的输入角色、单写者、科学键、重试和资源规则。所有命令均为 **FUTURE**。最终结果无论支持或否定假设，都必须保留。

## F26 · 完整 2^3 组件析因与三种特征对照

### 目标、先决与落点

不再用有限单因素消融冒称全部交互已分离。输入F20冻结reference、F10三特征模式及F17统计；缺真实pretrained时对应研究阻塞，不能以random替代。

落点：`configs/experiments/F26-factorial.json`、`runs/F26/`、`reports/F26/`。配置只由冻结展开器产生；worker不编辑全局reference。

### 实施步骤

1. 展开ASIT on/off×RaS on/off×feature none/pretrained八组合；每个ASIT/RaS组合另加random_frozen，因此共12种完整配置（未跨数据/模型/seed展开）。
2. 每行保存base_config、overrides、compare_to及完整resolved hash；selected_caap不改变reference的存在。
3. 按冻结三域/模型/seed范围训练，统一D评估；配置完全一致时与F24/F25去重，别名不增加独立seed。
4. 估计主效应、两阶及三阶可识别交互，并分别比较none/random/pretrained。
5. 输出各seed点、配对差、cluster区间、成本和多重比较家族；不能只显示显著系数。

### 正负验收与命令

正例：selected已关ASIT/RaS/feature三种情形，12配置仍完整且正确去重。负例：加回模块标“移除”、不同K/更新数混成纯模块对照、缺组合仍输出三阶交互均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F26-factorial.json --dry-run`；矩阵展开断言纳入F20的 `tests/integration/test_freeze.py`，改共享测试须向F20所有者申请。

### 产物、指标、成本与接力

输出 `factorial-effects.json`、全部train/eval产物与配置差。键包含模块、feature权重/随机seed、K、优化和选模；统计同一artifact多个draw不能当独立训练。GPU训练按展开成本预留；宽CI/无增益不追加seed。对应 `R1-2/R2-5/H1/H4`；交接F41真实reference/no_ras打印源和F43完整消融证据。

## F27 · 独立线结构代理开发与设计可识别性

### 目标、先决与落点

在读取测试结果前锁定非victim依赖的结构测量。输入F13几何、F17统计及训练/验证可视样本；没有主线真值只能称代理，不能制造标注。

落点：`src/caap/attack/structure_features.py`、`src/caap/tools/analyze_structure.py`、`configs/protocols/structure.json`、`tests/unit/test_structure_features.py`、`test_structure_design.py`、`reports/F27/`。本任务独占提取器与参数，F28只读。

### 实施步骤

1. 定义候选两尺度六方向零均值L2归一化Gabor组，绝对响应最大值为非负能量；核尺寸/sigma/波长/padding/eps在开发夹具选定。
2. 计算coverage=sum(M*E)/(sum(E)+eps)，保存面积/bbox/周长/方向；平坦图标无信息。
3. 用人工线条、斜线、旋转、强度缩放、空/全mask检验；更换victim权重/标签不影响能量图。
4. 在训练/验证上有限人工核对可解释性并冻结参数，不按test相关性重调滤波器。
5. 冻结样本×artifact×model×seed统计结构，draw先聚合；检查跨度/面积/周长/方向协变量秩和模板/簇数量。
6. 探索性回归保留预注册协变量和身份/共享artifact相关结构；秩不足输出INSUFFICIENT_DESIGN，不删除变量追预期符号。

### 正负验收与命令

正例：线所在区域有较高覆盖，空/全mask约0/1，平坦图无除零。负例：结构图随victim改变、test逐图选最高coverage模板、重复sample/artifact行、完全共线仍给独立拓扑系数都拒绝。

`FUTURE`：`python -m unittest -v tests/unit/test_structure_features.py tests/unit/test_structure_design.py`；`python -m caap.tools.analyze_structure --config configs/protocols/structure.json --development-only --out reports/F27`。

### 产物、指标、成本与接力

输出 `proxy-validation.json`和structure配置，属于开发证据，不包含确认性H2结论。键含原ROI/mask、提取器/统计版本及分组/seed，不依赖victim参数来生成能量。CPU批处理有内存上限，可按域分片；任何测试自适应停止并失效该代理版本。对应 `R1-1/R1-2/H2`；交接F20冻结代理及F28设计可识别边界。

## F28 · H2：同面积、同跨度与预设方向对照

### 目标、先决与落点

排除面积、跨度与亮度遮挡等替代解释，而非预设十字优胜。依赖F20/F27与F13；不可行模板必须在解封前解决，冻结后不得换成更有利形状。

落点：`configs/experiments/F28-h2.json`、`runs/F28/`、`reports/F28/`。模板集合来自冻结配置，worker不能逐图选择位置/方向。

### 实施步骤

1. 第一层比较完整十字/方/圆/三角同面积总体差异，报告未控制的bbox/周长/方向。
2. 第二层加入同面积、尽量同bbox的条带/稀疏控制；逐模板报告残余不匹配，不谎称全部隔离。
3. 第三层使用训练前固定方向模板，各自训练通用纹理；测试时该artifact对所有ROI相同。
4. 每种几何加入训练背景均值灰、白色纸样、固定seed随机与学习纹理，placement/采集条件共享。
5. 固定F27代理在测试ROI只读计算，分析model/seed内同样本配对差、coverage变化关联和共享artifact相关性。
6. 输出三层结果与设计诊断、全散点和身份等权摘要；必要回归只作描述性，不自动因果化。

### 正负验收与命令

正例：同area/bbox对照元数据可复核，调换配对差号反转。负例：只画四个组均值称机制、测试后换方向、无秩仍回归、常数亮度不匹配却全归拓扑，都拒绝相应主张。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F28-h2.json --dry-run`；`python -m caap.tools.analyze_structure --config configs/protocols/structure.json --manifest runs/control/experiment_manifest.json --group F28 --out reports/F28`。

### 产物、指标、成本与接力

输出 `h2-effects.json`、structure/visual逐图记录及模板描述；键含模板、方向、生成/训练seed、代理与协变量规则。GPU训练按模板×域×模型×seed计，分析CPU按cluster计，重复draw不增加artifact样本量。coverage无关联/优势消失如实报告，不加滤波器搜索。对应 `R1-1/R1-2/R1-7/H2`；交接F43支持到哪层、残余混杂和负结果。

## F29 · 大小、位置与软边独立敏感性

### 目标、先决与落点

测清能力范围，不把多个同时变动因素误称单因素。依赖F20/F13/F12/F17；因子水平、训练或仅评估变换的区别在冻结时明确。

落点：`configs/experiments/F29-sensitivity.json`、`runs/F29/`、`reports/F29/`。配置只读，renderer修改不在本任务权限。

### 实施步骤

1. 展开预注册面积等级、固定位置模板和软边等级；主比较仍B784硬边scale1，敏感性单独表。
2. 每个条件声明是否重训纹理或仅变换旧artifact；不同estimand不能混算。
3. 逐级校验完整形状可行性，记录binary/alpha/实际变化面积、bbox、裁剪与物理尺度含义。
4. 对同probe使用共享退化draw，测clean/adv、视觉局部/全图及同eligibility配对差。
5. 输出全部等级与交互（仅当预注册可识别），位置永不按每张test ROI最佳效果选择。

### 正负验收与命令

正例：只改软边时其他resolved字段不动，变化面积被实测；边缘裁剪记录保留。负例：改变位置同时放大却归因位置、软alpha越预算不披露、不可行等级静默删除、用误差区域自适应视觉R均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F29-sensitivity.json --dry-run`；几何与视觉复核复用已验证测试，不临时改断言放行。

### 产物、指标、成本与接力

输出 `sensitivity.json`及逐图三层支撑，键含level、placement、softness、train/eval变换角色。每seed报告全条件，硬边主表与软边表不混。重训成本与派生eval分账；低效果不换等级。技术预算不可行停止该预注册条件并保留缺口，协议改动需要新freeze。对应 `R1-7/R2-1/R2-4/H2`；交接F43稳健范围和未测试范围。

## F30 · H3：分类与验证驱动攻击的联合风险

### 目标、先决与落点

对同一模型和真实掌级凭据比较三种攻击目标，区分分类错、本人拒绝、目标错误接受。依赖F20/F24/F16/F15；F24只提供冻结artifact，不为新目标调参提供最终分数。

落点：`configs/experiments/F30-h3.json`、`runs/F30/`、`reports/F30/`。图库/阈值由共享calibrate节点单写，本任务不得按测试结果重校准。

### 实施步骤

1. 从F20直接读取三objective、模型/目标/seed和匹配计算预算，验证配置早于F24测试解封锁定。
2. 复用F24分类artifact；按F16已开发loss和训练/验证角色生成拒绝/目标接受artifact，不能因F24验证低而新增目标。
3. 每model/gallery/calibration/pair-rule仅校准一次，所有方法共用同threshold hash。
4. 共同probe评价分类与验证，输出2×2、clean/attack FMR/FNMR/TAR及目标接受的全合法pair率和clean原先拒绝条件率。
5. 保存两端身份、pair唯一性、不同掌/同人标签、唯一pair与身份数；固定目标仅抽攻击者，通用pair用双端multiplicity。
6. 报每seed、聚类区间、低FMR支持度与无效工作点；测试EER仅描述，不替换部署阈值。

### 正负验收与命令

正例：所有方法相同校准hash，联合表四格总数等于共同有效集合。负例：target从test选、同人两掌变genuine、将全pair和clean-rejected分母混用、靠共享海量pair宣称10^-5精确保证，都拒绝。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F30-h3.json --dry-run`；`python -m caap.tools.eval_verification --config configs/experiments/F30-h3.json --out runs/F30`，实际执行由子节点配置解析具体只读父引用。

### 产物、指标、成本与接力

输出 `joint-risk.json`、pair_scores、阈值引用、2×2和按seed记录。验证结果键含patch/model/gallery/probe/pair/threshold/渲染/统计；原始分数缓存不含阈值但其其他依赖全校验。训练GPU、pair评分GPU/CPU有上限，共享calibrate去重。低验证风险仅限定当前攻击；缺独立校准或尾部不足保留无效，不补样追显著。对应 `R2-3/R3-3/H3`；交接F43联合风险、分母与适用范围。
