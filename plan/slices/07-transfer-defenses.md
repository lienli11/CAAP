# 07 · H4、全模型迁移、跨域与防御

**迁移不访问目标模型来选源补丁；防御开发不使用前批最终结果来设计。F33/F35 的两阶段规则是防止后验挑选，不是绕过全局冻结。**

共同输入角色、单写者、科学键与失败规则见 `01-foundation.md`。以下命令全部为 **FUTURE**，全部结果保留未知。每个新架构或防御确认分支都需要未参与其设计/选模的独立确认集合；若没有，输出阻塞或明确探索性再分析，不能虚称独立确认。

## F31 · H4：RaS、K 与留出退化条件

### 目标、先决与落点

区分RaS是否有效、EOT采样是否增加计算，以及留出数字条件是否仍有效。依赖F20范围与F17配对draw指标；缺reference/no_ras真实artifact时先按冻结配方训练，不拿不同模块主方法冒充纯消融。

落点：`configs/experiments/F31-h4.json`、`runs/F31/`、`reports/F31/`。评价变换参数只读，worker不得看到Q40表现差后改主条件。

### 实施步骤

1. 展开有/无RaS与K=1/4，分别登记固定更新和等前后向/查询预算两组比较。
2. 按冻结训练分布生成EOT，K次loss取均值；实际梯度调用、更新与walltime均入账。
3. 冻结标称、分布内新draw seed、留出变换类型、轻/中/重等级和组合；候选包含平均模糊5×5、gamma1.8、JPEG Q40，但实际参数需F20可行性确认。
4. 同一个随机实现同时作用clean/adv；输出draw池化条件率、固定标称洁净集合读数、退化clean准确率及adv准确率。
5. 对同身份/seed比较RaS差，保留所有等级/多重比较家族；与物理证据分开标注。

### 正负验收与命令

正例：同draw clean/adv变换参数相同，K4实际调用更多的成本可见。负例：众数预测冒充期望ASR、相机退化造成clean全错却报100%补丁成功、K4求和隐式放大学习率均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F31-h4.json --dry-run`；基础回归 `python -m unittest -v tests/unit/test_metrics.py tests/unit/test_training_updates.py`。

### 产物、成本、停止与交接

输出 `h4-effects.json`、每draw参数/eligibility、actual calls和训练artifact。键含RaS分布、K、预算视角、留出条件及draw seed；条件名称不能替代具体参数。GPU按独立job租约，已同键训练只复用一次。OOD低ASR或无RaS更强是合法结论；不扩等级/改K重试。对应 `R2-5/R3-1/H4`；交接F41纯no_ras对照及F43数字与实拍尚差什么。

## F32 · 七模型完整非对角迁移

### 目标、先决与落点

对每域完整七模型源→目标迁移，不只选易迁移的目标。输入F24冻结源artifact、F09目标有效模型和F20矩阵；缺模型保留blocked单元，不删行列。

落点：`configs/experiments/F32-transfer.json`、`runs/F32/`、`reports/F32/`。只读artifact和目标权重，不训练新补丁、不修改source选择。

### 实施步骤

1. 每域展开7×6=42非对角模型对，再乘全部预注册方法/seed/目标设置；对角结果引用F24。
2. 校验源训练与选模依赖不含目标输出/梯度/ASR，目标首次只出现在evaluator。
3. 使用目标模型自身预处理和合法标签映射，raw补丁/placement保持冻结。
4. 保存目标clean-correct分母、源分母、可选共同交集及逐sample预测，不静默替换条件集。
5. 对全部单元输出完整矩阵、成本、N/A/blocked原因；缺节点使覆盖不完整。

### 正负验收与命令

正例：同源artifact在不同target有不同eval科学键且不多训练。负例：source/target调换不改键、目标模型参与source调参、只保留高ASR列、极小/空分母填0均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F32-transfer.json --dry-run`。

### 产物、成本、停止与交接

输出 `transfer-matrices.json`与逐样本eval。键含源artifact、target模型/预处理、probe/label map、目标规则、render/draw/eligibility。GPU只付派生评分成本，不重复预训；可按目标模型批量只读，目录仍独立。OOM仅经逐样本等价测试减eval batch；不得删目标或改分辨率。对应 `R2-4/R3-3`；交接F43所有非对角格子和分母限制。

## F33 · 集成留出与代表性新架构外推

### 目标、先决与落点

研究预注册新架构和真正留出模型，而非从已看矩阵挑弱点。依赖F20/F09；至少一个与现有七家族非同构的代表性架构，具体模型/来源在F20锁定并核实许可。未得到真实有效权重保持阻塞。

落点：`src/caap/models/new_architecture.py`、`src/caap/attack/ensemble.py`、`configs/experiments/F33-ensemble.json`、`tests/unit/test_ensemble_holdout.py`、`runs/F33/`、`reports/F33/`。新adapter通过F11接口，不修改已有模型；集成权重和留出名单单写冻结。

### 实施步骤

1. 阶段A从F20读取已锁定架构、ensemble成员/权重规则、训练角色和有限开发预算；只能用该分支development资料实现/核验。
2. 建新架构真实识别器并按F09同等clean门槛验收，记录actual class、预处理、参数量和训练来源。
3. 实现集成loss的尺度/平均规则；留出模型forward/gradient sentinel在训练选模时不可调用。
4. 锁定实现、权重、成员、超参、attack配方、主要终点和独立确认manifest，发布分支freeze；不得参考F24/F32最终矩阵改成员。
5. 阶段B只在冻结后用独立确认集评价集成内/留出/新架构，完整记录全部seed与目标分母。

### 正负验收与命令

正例：ensemble成员和holdout不交，源训练只访问允许成员，mean loss计数正确。负例：目标参与early stop、看完迁移表才选架构、无新确认集却称独立外推、随机新架构权重冒充真实，均拒绝。

`FUTURE`：`python -m unittest -v tests/unit/test_ensemble_holdout.py`；`python -m caap.tools.run_experiments --config configs/experiments/F33-ensemble.json --dry-run`。

### 产物、成本、停止与交接

输出新真实权重、branch-freeze（记录于 `holdout-audit.json`）、集成artifact和独立确认预测。键含架构实际实现、ensemble成员/权重、训练可见性和confirm manifest。新模型训练与攻击预算分别计费；GPU单卡单job。缺确认集则不解封，历史数据再分析另标exploratory不补confirm格。对应 `R1-2/R2-4/R3-3/R3-4`；交接F43新架构范围、留出证据和数据独立性。

## F34 · 三域跨域固定补丁外推

### 目标、先决与落点

补丁从源域迁到目标域有效系统；不是拿源分类头硬解释目标身份。输入F24 artifact、F09每域真实模型和F20预注册组合；未知身份对应不能做定向跨域。

落点：`configs/experiments/F34-cross-domain.json`、`runs/F34/`、`reports/F34/`。只读source artifact，target evaluator独立，不因目标表现重新训练。

### 实施步骤

1. 展开三域3×2=6有向域对，在冻结模型/方法/seed上对账；同家族跨域与跨家族组合分层列清。
2. 使用目标域自有模型、ROI预处理、class map、gallery和独立calibration，保持source补丁不变。
3. 核验source training/selection未查询target输出/梯度；不能用target test修placement或色域。
4. 默认未定向；只有事前合法共同身份映射和目标模板的另行批准协议才允许定向，不以数字class_id相同推同人。
5. 保存target clean性能、k/n、极小分母/域不兼容原因，报告全部域对而不是最优迁移链。

### 正负验收与命令

正例：相同数字class_id跨域仍不合身份，target model hash和label map入键。负例：600类头直接解释另一域460类身份、target clean崩溃仍称强迁移、测试后换目标域均失败。

`FUTURE`：`python -m caap.tools.run_experiments --config configs/experiments/F34-cross-domain.json --dry-run`。

### 产物、成本、停止与交接

输出 `cross-domain.json`、classification/verification父引用和逐样本记录。键含源artifact、目标domain/model/preprocess/manifest/映射/阈值，域名不是足够身份。GPU派生eval，共享目标校准可去重；无足够有效分母保留null，不扩样。对应 `R2-3/R2-4/R3-3`；交接F43域外推范围与不成立条件。

## F35 · 对抗训练防御：旧补丁与自适应独立确认

### 目标、先决与落点

同时评价冻结旧补丁和知道防御的自适应攻击；旧补丁失败不能证明鲁棒。依赖F20/F09/F23，**不依赖F24最终结果设计防御**。缺独立防御development/确认角色时阻塞，不把前批测试改名新验证。

落点：`src/caap/models/adversarial_training.py`、`src/caap/attack/adaptive_defense.py`、`configs/experiments/F35-adversarial-training.json`、`tests/integration/test_adaptive_training.py`、`runs/F35/`、`reports/F35/`。独立分支配置单写，不能回改F20全局主方法。

### 实施步骤

1. 阶段 A 按 F20 预注册防御配方/候选上限，只消费 F07 冻结的 recognizer_fit/recognizer_val 或已批准防御 fit/val 角色，不自行拆分；F23 development 补丁用于实现检查，开发 worker 不获得前批 final 图像/分数及其摘要。
2. 开发匹配威胁集合的adaptive loss/梯度或必要近似，核查梯度遮蔽、不可微处理和实际forward/backward/query计数。
3. 只用分支development资料确定固定超参，冻结防御权重、攻击算法、预算、old patch集合、确认manifest与主终点。
4. 阶段B解封独立确认，先评分未针对防御重新优化的旧补丁，再从合法attack train/val按冻结adaptive配方训练并评分。
5. 同时报告clean性能、经验鲁棒性、旧/自适应差、成本和全部seed；防御如改变embedding分布，独立干净校准生成新阈值。
6. 保留全失败/阴性结果，独立审查能力等价和训练数据来源，不把攻击失败解释成认证保证。

### 正负验收与命令

正例：确认访问在branch-freeze前被sentinel拦截，防御模型未见确认数据，自适应梯度finite且预算可核。负例：读取F24表现挑防御、旧补丁ASR低便省略adaptive、测试上重校准、额外无限restart追高都失败。

`FUTURE`：`python -m unittest -v tests/integration/test_adaptive_training.py`；`python -m caap.tools.run_experiments --config configs/experiments/F35-adversarial-training.json --dry-run`。

### 产物、成本、停止与交接

输出 `branch-freeze.json`、`adversarial-training.json`、防御checkpoint、旧/自适应artifact和独立确认预测。键包含defense实现/权重/训练roles、adaptive能力/优化/预算及confirm manifest；所有模型训练、攻击训练、eval分别计费。无确认集就BLOCKED_ASSET，旧数据仅允许明确探索性重分析。NaN/错误梯度有限修复使受影响父后代失效；低ASR不扩预算。对应 `R2-4/R3-4/H5`；交接F43独立性证据与经验而非认证的结论。
