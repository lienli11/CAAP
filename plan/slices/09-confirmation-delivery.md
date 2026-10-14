# 09 · 真人确认、逐次统计、full 对账与稿件交接

**真实拍摄必须由获准人员实施；完整交付指证据和缺口均可追溯，不保证任何假设成立或审稿意见自动解决。**

共同角色、单写者、科学键、预算及有限重试遵守 `01-foundation.md`。以下科学工具命令均为 **FUTURE**；Git只读命令标为EXISTING。无源码不称论文已编译，无真实实验不称结果已完成。

## F41 · 真人实施多设备多条件冻结拍摄

### 目标、先决与落点

按F40日程完成真实、多设备、多姿态/距离/光照/位置采集，不由Agent合成证据。依赖F40许可/冻结，F24/F26/F31预注册方法与reference/no_ras artifact；依赖结果仅用于取固定配方产物，不按最终ASR挑打印物或种子。

落点：`.local/physical/new/`、`runs/F41/`、`reports/F41/`。真实操作者写原始采集记录；导入器只校验和追加，原图不可覆盖。每设备/操作者分配不冲突capture命名空间，公开报告去标识。

### 实施步骤

1. 人核验有效许可、受试者退出选择、设备/照明/材料安全、冻结日程和实际打印物hash。
2. 按批准随机交错顺序采集clean及各对照；登记subject/palm/session/attempt、条件、设备、距离/姿态/光照/位置、print_variant和clean_pair。
3. 保存每次真实原图、时间与操作偏离；失败捕获、遮挡、ROI失败、退出都进入尝试台账，不静默重拍替换。
4. 通过F39固定ROI/模型评分，不数字重画补丁、不让操作者改success；各目标/模式单独登记。
5. 对照日程检查缺失与偏离，允许的技术补采按预注册规则执行并保留原失败；不因结果好坏扩样、换纸或换人。
6. 完成或达到上限后封存原始资产和manifest，输出实际覆盖/退出/偏离交F42分析。

### 正负验收与命令

正例：每次capture可追到许可引用、真实文件、操作者、冻结条件和固定预测。负例：生成照片当real、跨设备拼同capture、删除失败、看ASR后换种子打印物或无限补拍均拒绝。

真人采集无可替代自动命令。`FUTURE`评分命令：`python -m caap.tools.score_captures --config configs/experiments/F40-physical-design.json --manifest reports/F41/capture-manifest.json --out runs/F41`。仅在真实文件与许可齐全后执行；不得把运行此命令称为完成真人拍摄。

### 产物、指标、成本与接力

输出 `capture-manifest.json`、`protocol-deviations.json`、真实评分记录与私密原图。键包含capture内容、print/model/preprocess/threshold、条件与分组规则；同capture多模型不增加人数。human时间/耗材/存储按F40上限，任何许可撤回或安全问题停止对应采集。实际缺口保留，不造比例。对应 `R2-2/R2-5/R3-2/H4`；交接F42完整尝试顺序、失败原因、匿名cluster和资产hash。

## F42 · 真实逐次物理统计与模块消融

### 目标、先决与落点

将真实尝试变成可复核单次/重试/人级结果。输入F41新记录、F38可恢复旧记录、F17统计；旧数据映射不全只能报告可支持部分，新旧分表。

落点：`src/caap/tools/physical_report.py`、`tests/unit/test_physical_report.py`、`runs/F42/`、`reports/F42/`。复用F17统计，不私造独立bootstrap；原始success字段只校验不编辑。

### 实施步骤

1. 校验capture/model/mode唯一键、attack_mode、target、print_variant、condition和二值成功来源；所有无效采集保留。
2. 分别汇总每组单次micro、每人macro、每人k/n、cluster区间，以及条件识别率和全尝试流程率。
3. 按真实时间顺序计算前k次ASR@1/5/20；不足k或无顺序为null，并报告合格人数/缺失原因。
4. 随机无放回子集指标另名random_subset_success_at_k；不能用独立公式从单次率生成观测重试率。
5. 按人、设备、条件、模型、模式、目标和物体分层配对；reference/no_ras必须仅差RaS才称物理消融。
6. 输出新旧结果、缺clean配对限制、全0/1退化区间警告和全部预注册比较/失败案例。

### 正负验收与命令

正例：20次仅最后成功，顺序ASR@1/5=0、@20=1，random_subset@1=.05。负例：4次数据输出@20、按文件名猜顺序、同capture三模型当三人、RGB/BW或跨目标串组均失败。

`FUTURE`：`python -m unittest -v tests/unit/test_physical_report.py`；`python -m caap.tools.physical_report --manifest reports/F41/capture-manifest.json --config configs/experiments/F40-physical-design.json --out reports/F42`；历史输入用单独输出实例，不能覆盖新结果。

### 产物、指标、成本与接力

输出 `physical-results.json`、`physical-coverage.json`、capture审计和逐次引用。科学键含真实manifest/预测、打印物/model/ROI、分组、重试、无效采集和聚类规则；不要求训练checkpoint。CPU有界bootstrap，共享subject整簇保留多条件重复。全0/1不声称零不确定性，缺paired clean不声称净效应。对应 `R2-2/R2-5/R3-2/H4`；交接F43哪几组真实齐全及仍无法回答的问题。

## F43 · full 矩阵、负结果与证据依赖对账

### 目标、先决与落点

所有承诺格子、失效、负结果和预算均可审计，不能仅收集成功目录。依赖 F22 原能力复现、F24–F42 各科学分支与 F20 expected_cells；开发只等父契约，真实 READY 必须验收全部科学产物。有阻塞分支时可生成只读 INCOMPLETE 覆盖预览，不能跳过 F22/认证/物理缺口而宣称 full 完成。

落点：`src/caap/tools/collect_tables.py`、`tests/integration/test_full_evidence.py`、`reports/F43/`。全表由收集器单写，实验worker不手改表或主张；所有上游只读。

### 实施步骤

1. 校验每expected_cell允许的协议/branch freeze、父hash、scientific_key、seed、任务类型、必需产物和真实资产来源。
2. 检查role/预算/能力/阈值/eligibility相容；real取决于评价数据和有效模型，不因随机控制纹理而误判synthetic。
3. 同键多尝试只选验收通过且未失效实例，不按最大ASR；登记复用别名但不增加seed/样本。
4. 生成CSV/JSON/可选LaTeX表、coverage、资源决算和主张引用链；任何数字可追到sample/pair/capture。
5. 保留阴性、null原因、N/A、blocked、technical failure、范围取消及历史表；必要缺口使INCOMPLETE并非零退出。
6. 检查完整full：三域七模型、目标、3seed、H1–H5、原能力/适配、迁移、新架构、防御与多因素物理全部对账；只有完整有效覆盖可READY。

### 正负验收与命令

正例：合法生成控制在真实数据/模型上能入其控制行，calibration无checkpoint照样按类型验收。负例：合成ROI冒充real、缺seed、旧阈值、损坏父artifact、同键重试多计、混预算主表、只存百分数无预测均非零退出且保留coverage。

`FUTURE`：`python -m unittest -v tests/integration/test_full_evidence.py`；`python -m caap.tools.collect_tables --manifest runs/control/experiment_manifest.json --out reports/F43`。

### 产物、指标、成本与接力

输出 `coverage.json`、`tables/`、`claims.json`、`resource-ledger.json`，键含当前冻结矩阵与全部上游结果hash/表格规则。READY只表示证据包达到承诺范围，不自动意味审稿充分解决；full中必需分支取消只能保留缩范围版本，不能继续叫原full全部完成。CPU/存储有上限，预期缺口不是技术重试理由。对应 `R1-1/R1-2/R1-7/R2-1/R2-2/R2-3/R2-4/R2-5/R3-1/R3-2/R3-3/H1/H2/H3/H4/H5`；交接F44每项主张的精确支持与限制。

## F44 · 稿件修订、16 条逐点回复与诚实主张

### 目标、先决与落点

修订由证据驱动，不守住旧高百分比。输入F43报告及缺口、F21核验书目、合法LaTeX/其他稿件源码和投稿规范；没有源码只交可落地修改建议，不假称编译成功。

落点：用户提供并获准的 `paper/revision/`、`reports/F44/`；`paper/sources/` 原始 PDF/来源材料始终只读，不修改、不在该目录编译。论文/回复单写者；生成表只读引用 F43 输出，不手抄数值或修改原始预测。`doc/` 保持不变。

### 实施步骤

1. 为R1-1..7、R2-1..5、R3-1..4逐条建立“问题→修改→证据→页节→限制→真实状态”，共16条不能合并省略。
2. 修正十字归属、ASIT/RaS/EOT组合贡献与形状选择建议；没有优势或机制证据时降为系统比较。
3. 解释phi是权重集合、网络结构/初始化/参数量、c/b预测头/边界/训练分布；图1与公式同步，审稿人式号差异礼貌澄清不改原话。
4. 建独立符号表和缩写首次全称检查；核对分类/验证/物理模式、角色、double-palm、分母、预算、调用数和历史实现差异。
5. 更新已核验相关工作及任务边界，不堆未读引用；引用原始书目状态，未核DOI不入最终BibTeX。
6. 基于实际阴性/正向结果修摘要、结论和限制，插入可追溯表图；有源码才编译、核页数/字体/引用，提交前由人复核。

### 正负验收与命令

正例：16条均有位置和证据状态，任一主张能跳到有效run与原始记录。负例：无实拍no_ras却称R2-5完全解决、分类错称冒名、GP称物理上界、缺源码称已编译、范围外攻击称击破认证都不允许。

`FUTURE`：稿件编译命令从实际 `paper/revision/` 构建配置核验后记录，若存在获准LaTeX入口可执行 `latexmk -pdf -interaction=nonstopmode -halt-on-error "$CAAP_PAPER_MAIN"`。变量必须指向获准真实主文件；不得凭本文假定latexmk已安装或页面限制已经通过。

### 产物、指标、成本与接力

输出 `reviewer-map.json`、`response-letter.md`、`claim-diff.json`及真实稿件修改。状态区分未开始/改代码待验证/已有证据/部分解决/无法补齐并收缩主张；全部意见有回复不等于全部充分解决。报告键绑定F43证据hash和稿件版本，文字变化不强迫重训。CPU编译/人工审阅有上限，未授权不投稿、commit/push。对应所有16条与H1–H5；交接F45可构建版本、最终限制和未解意见。

## F45 · 干净环境重建与可恢复最终交接

### 目标、先决与落点

验证结果不依赖开发者机器私有路径，并留下唯一安全续跑入口。依赖F44/F05及全部来源/锁文件；干净clone不包含.local，缺私有资产应能明确请求合法引用而不伪造。

落点：`src/caap/tools/rebuild_audit.py`、`tests/integration/test_clean_rebuild.py`、`reports/F45/`。新干净工作区必须明确授权，不能擅自在workspace外创建或删除目录；原数据/旧run不删除。

### 实施步骤

1. 记录批准commit与额外未提交补丁hash，指出未推送变更如何合法交接；不自动commit/push。
2. 在获准独立环境恢复精确依赖，验证包导入、CPU核心测试、DAG/schema/path和无个人绝对路径依赖。
3. 按合法资产引用接入只读原始证据；缺.local时输出BLOCKED_ASSET，不能下载受限数据或随机生成替代。
4. 从已有可信逐样本/pair/capture结果重建表格，对比数值、coverage和来源；无需为文档重建无谓重训。
5. 模拟控制器中断与接力，确认无重复GPU任务、正确科学键/预算余额/父失效处理。
6. 输出代码已实现、测试已通过、真实实验已完成、论文已修改四种状态的独立清单，以及负结果、未解决项和下一步唯一入口。

### 正负验收与命令

正例：另一批准环境同来源产物重建相同表格；缺资产产生准确缺口。负例：硬编码用户名/服务器路径、隐藏依赖本地数据、用新seed重训代替可复算、状态全写完成而物理仍缺失均失败。

`EXISTING`：`git status --short`、`git rev-parse HEAD`。`FUTURE`：`python -m caap.tools.rebuild_audit --profile configs/profiles/full.json --manifest runs/control/experiment_manifest.json --out reports/F45`；`python -m unittest -v tests/integration/test_clean_rebuild.py`。

### 产物、指标、成本与最终交接

输出 `rebuild.json`、`handoff.json`、`unresolved.json`；含完整命令/退出码/测试数/skip/环境、有效/失效run、真实预算、所有freeze/hash、16意见与H1–H5状态。重建provenance绑定源码/依赖/数据，不把输出路径纳入科学键。CPU复算有界，新增GPU重训仅真正失效且获预算时执行；依赖安装失败最多获准重试一次，不改全局环境。

对应 `R2-4`。最终明确：负结果也是有效科学交付；缺许可/资产/独立确认或无法完成的矩阵不是负结果，也不是full完成。若无可执行节点则输出缺口并退出，不假装后台持续自主运行。
