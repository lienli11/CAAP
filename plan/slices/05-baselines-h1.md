# 05 · 原能力基线、共同约束与 H1

**F21 核验台账与 F23 直接基线 development 供 F20 冻结；F22 原能力复现是独立必需分支，缺原代码不能阻塞直接 EOT/PGD。F24–F25 才是冻结后的确认性研究。**

继承 `01-foundation.md` 的角色、科学键、单写者和有限成本合同。以下 Python 科学命令均为 **FUTURE**；训练、网络获取与真实评分另需授权。科学结果仍未知。

## F21 · 相关工作全文、许可证和原实现能力核验

### 目标、先决与落点

从原文和原代码核实方法，而不是用题名或摘要猜。输入 F06 资产规则、`doc/03-创新点.md` 候选书目及获准全文/代码；取不到全文、源码、许可证时登记缺口，不能捏造 DOI 或实现。

落点：`reports/F21/`、`.local/literature/`。本任务只写可公开核验摘要和私有合法文献缓存，不改 `doc/`，不复制无许可代码进源码树。

### 实施步骤

1. 核对 CSPA、经典 patch/EOT、近期掌纹识别/ROI/验证/跨域、统一评测以及 PatchCleanser/CertMask 的书目和正式发表状态。
2. 按书目、摘要、全文、实现四级记录来源、访问日期、版本、license、原页面和章节定位。
3. 从全文/代码抽取白盒/黑盒、单图/通用、目标、placement、面积/跨度、query/EOT和训练测试角色。
4. 核对原稿与实现差异、十字归属、已有EOT/变换器工作；不以移植领域自动宣称发明。
5. 生成 F22 原能力复现与 F23 共同约束适配的差异表，提供 F36 认证前提候选。

### 正负验收与命令

正例：每项技术断言指向全文页/代码版本；只有元数据的条目只用于书目。负例：凭摘要写查询预算、无许可集成、未核 DOI 入最终 BibTeX、把预印本称已录用均拒绝。

`FUTURE` 的通用证据校验由 F43 收集器实施；F21 不为填命令强造下载脚本。可使用已获准浏览/检索能力人工核验，网络命令须由执行者按真实来源登记，禁止本文虚构一个原实现 URL 或下载命令。

### 产物、成本、停止与交接

输出 `literature-ledger.json`、`original-capabilities.json`，包括 unknown 和来源引用。代码/全文内容 hash 在后续 baseline provenance 中绑定，检索结果不等于实验数据。网络/人工时间设上限，独立文献可并行核对，汇总单写。访问验证或许可不足即停止该获取路径，不绕过限制。对应 `R1-1/R1-2/R2-4/R3-4/H5`；交接已确认事实、不可确认事项和允许的复现方式。

## F22 · 原能力协议下的独立基线复现

### 目标、先决与落点

先核验原算法本来能做什么，再讨论统一比较。依赖 F21/F09/F19；缺原实现或关键参数时该复现阻塞，不用自写白盒 EOT 偷换 CSPA。

落点：`src/caap/attack/baselines/original.py`、`configs/experiments/original_baselines.json`、`tests/integration/test_original_baselines.py`、`runs/F22/`、`reports/F22/`。原代码只在许可允许的方式引用，wrapper 单写且版本固定；不改共享 evaluator。

### 实施步骤

1. 登记原方法 commit、依赖、许可证、权重、原参考例与能力集合。
2. 在安全隔离的获准环境复核原公开参考输出或最小原能力例；无法取得时保留限制。
3. 用本项目 development 数据做域迁入检查，只保留原能力，不添加通用化/EOT后继续用原名。
4. 对原查询/梯度/更新/输入访问做实际计数，区分原文上限与本次实际消耗。
5. 输出与参考差异、无法复现原因和能力不相容项，提交独立审查后供 F23 使用。

### 正负验收与命令

正例：锁版本参考例在声明容差内一致；单图/黑盒标签保留。负例：把原单图改通用、未知query填固定数、读取本项目test调参数、只挑复现成功样本均失败。

`FUTURE`：`python -m unittest -v tests/integration/test_original_baselines.py`。原实现命令必须来自获准且核验后的版本，并经宿主确认后写入 run provenance；此时不提前编造第三方 CLI。

### 产物、成本、停止与交接

以 run_original_attack 输出 `original_result_manifest.json`、`attack_records.jsonl`、`query_ledger.json`、`state_contract.json` 及 `reproduction-delta.json`。仅原算法确有 optimizer/checkpoint 时才要求它们；黑盒原法保存实际 query/search/RNG 状态和明确恢复边界，不能强造训练字段。科学键包含原实现 commit、能力、输入角色、模型、真实 query/更新配置和 seed；原能力结果不直接并入共同约束主表。GPU租约与参考例预算有上限。实现故障有限修复；无法核实关键能力停止原复现，full保留缺口。对应 `R1-1/R2-4`；交接 F23 何处可适配、适配后必须如何命名。

## F23 · 共同约束下基线适配与 development pilot

### 目标、先决与落点

提供公平、简明的共同约束基线和 F20 所需成本测量。依赖 F21 核验台账及 F10/F13/F14/F18/F19，不硬依赖 F22 原实现复现成功；仅用 patch_train/attack_dev/attack_select。原 CSPA 缺失只阻塞其特定适配，不阻塞独立定义的匹配十字 EOT/局部 PGD；原能力复现仍由 F22 在 full 最终单独交账。

落点：`src/caap/attack/baselines/matched.py`、`configs/experiments/development_baselines.json`、`tests/unit/test_matched_baselines.py`、`runs/F23/`、`reports/F23/`。共享 renderer/loss/evaluator 不复制；必要修复交原所有者。

### 实施步骤

1. 独立实现固定通用十字 EOT（无 ASIT/辅助项）与固定支撑 universal patch PGD；只有 F21 已核实所需能力与许可时才启用 CSPA-shape-matched adaptation。缺第三方原实现只给对应候选 BLOCKED_ASSET，不拦直接基线，也不将直接基线冒名原作。
2. 统一数据、mask/placement、raw范围、目标、模型边界、评价事件；PGD明确每步更新和[0,1]投影，不叫全图L∞PGD。
3. 测试同seed重现、支撑外不变、K损失平均、目标和预算接口一致。
4. 在事前小型development清单中有限训练/测时；候选数和最大更新在运行前写入，不等待F20正式冻结也不开放无限搜索。
5. 输出每种方法的实际updates/draws/forward/backward/queries、walltime/peak memory、调参次数及全部失败记录。
6. 给 F20 推荐可比较协议而非“保证某方法获胜”；F20可以在批准有限空间内选择，但不能删除不利baseline。

### 正负验收与命令

正例：不同方法都走同 evaluator，移除模块只有声明字段变化。负例：不同面积混表、只对CAAP加EOT算同成本、用随机教师称预训、补丁越支撑更新都失败。

`FUTURE`：`python -m unittest -v tests/unit/test_matched_baselines.py`；`python -m caap.attack.baselines.matched --config configs/experiments/development_baselines.json --out runs/F23`。本任务在其拥有的 matched 模块提供 development 入口，复用 F14/F18 训练与类型化产物接口；不等待 F20 的通用调度入口，因而没有 F23→F20→F23 的启动环。

### 产物、成本、停止与交接

输出 `method-registry.json`、`pilot-costs.json`及development训练/验证产物。键含适配能力、loss、模型、几何、角色、优化/EOT/选模和seed。固定更新不等于固定计算，两个预算视角分开。每卡一训练job；超批准development预算即停止。低验证表现如实入候选台账，不自动增trial。对应 `R1-1/R1-2/R2-4/R2-5`；交接 F20 可运行且成本可核的方法全集。

## F24 · 三域七模型未定向与多目标分类主矩阵

### 目标、先决与落点

全量测量，而非只跑容易成功的域/模型。依赖 F20全局freeze及其真实模型/角色父证据；三域或任一七模型资产缺失保留blocked单元，full不可冒充完成。

落点：`configs/experiments/F24-classification.json`、`runs/F24/`、`reports/F24/`。配置是F20冻结矩阵的不可变展开；实验worker仅写独立run目录，不能改源码或全局协议。

### 实施步骤

1. 展开 Tongji/IITD/AISEC×七模型×冻结方法×seed{0,1,42} 的未定向和至少3个合法固定目标。
2. 目标仅由训练/注册角色和冻结seed选，真实目标类排除于定向eligibility，不能为提高结果更换目标。
3. 训练只读patch_train/attack_val，best按预声明deploy指标；测试集独立只读节点评分。
4. 主数字结果deploy-fixed；保存clean/adv逐样本、k/n、class map、mask面积/支撑、walltime/calls和全部seed。
5. 生成expected_cells对账、真实/无效/阻塞说明和预声明比较，不替换阴性run。

### 正负验收与命令

正例：3域×7模型的所有方法/seed/目标都有独立科学键及对应证据；合法0成功是SUCCEEDED。负例：无目标样本、从GP高分替换D、缺seed填均值、按test挑epoch/目标、随机权重real标志均拒绝。

`FUTURE` 模板校验：`python -m caap.tools.run_experiments --config configs/experiments/F24-classification.json --dry-run`。授权正式执行：`python -m caap.tools.run_experiments --manifest runs/control/experiment_manifest.json --group F24`；后者须核freeze/角色/预算/父hash，不能直接去掉模板命令的dry-run。

### 产物、指标、成本、停止与接力

输出训练artifact、predictions/metrics和 `classification-cells.json/coverage.json`。训练/评估分别建键，源模型、target、objective、模式、probe、eligibility必须入键。每seed报k/n和均值/SD，身份cluster区间条件于固定artifact。资源按实测展开，非空分母不足保留null，不额外采样。技术错误统一失效受影响格子；低ASR继续矩阵。对应 `R1-7/R2-1/R2-3/R2-4/R3-3`；交接 F30/F32/F34冻结artifact，不向后续设计者提供选参数权限。

## F25 · H1：D/G/P/GP 与 ASIT 训练测试拆分

### 目标、先决与落点

区分测试输入适应与训练期ASIT的贡献，结果方向不预设。依赖 F20reference与F12模式实现、F17配对统计；含ASIT reference缺失时阻塞H1，不能把主方法无ASIT解释为整个问题N/A。

落点：`configs/experiments/F25-h1.json`、`runs/F25/`、`reports/F25/`。只消费renderer，不能看测试结果后改变范围或c/b边界。

### 实施步骤

1. 冻结含ASIT reference的训练artifact和共同probe/draw/eligibility，四路径仅改变声明的几何/光度开关。
2. 同artifact测D/G/P/GP；分别运行scale=fixed_one和predicted，记录位移、光度、alpha/支撑、裁剪。
3. 计算G-D、P-D、GP-D及交互GP-G-P+D；不同面积结果不称严格等预算。
4. 另训有/无ASIT版本，全部走D，比较训练工具作用；同键artifact可与F26复用，不能复算当新seed。
5. 输出全部seed与配对cluster区间；无ASIT artifact的G/P/GP为预登记N/A，直接非法请求仍报错。

### 正负验收与命令

正例：stub只开G时光度不变、只开P时几何不变；D调用ASIT sentinel永不触发。负例：fixed_one仍放大、GP读标签定位、对各模式选择不同最佳probe、删除负差均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F25-h1.json --dry-run`；`python -m unittest -v tests/unit/test_geometry.py tests/unit/test_metrics.py`。

### 产物、指标、成本、停止与接力

输出 `h1-effects.json`及逐样本渲染参数，键包含artifact/mode/scale/draw/共同eligibility。派生评估不另训同artifact，训练因素另建train_patch键；单GPU有限并发。D强于GP为合法负/反方向结果，不调参“恢复上界”。对应 `R2-1/R2-5/R3-1/H1`；交接F43输入条件差、训练差、面积混杂与明确结论限制。
