# 04 · 指标、产物、测试隔离与有限搜索冻结

**F16–F19 建立可信测量，F20 只从 development/pilot 证据冻结完整研究；F20 绝不能依赖尚未解封的正式实验结果。**

继承 `01-foundation.md` 的共同合同。以下命令均为 **FUTURE**，不代表当前科学入口已实现。F21 的核验台账、F23 直接基线开发和 F27 是 F20 的数字准备链；F22 原作复现、F36 认证、F39 打印各自成分支，不阻塞其他数字任务，但仍必须在 F43 full 对账中保留。编号较大不表示执行较晚。

## F16 · 验证专用本人拒绝与固定目标接受目标

### 目标、先决与落点

将验证驱动研究作为明确新协议，不把 logit 攻击低验证风险当系统安全证明。输入 F14 更新语义、F15 embedding/模板合同及仅训练角色的合法原型；目标无样本、模型无 embedding 则阻塞相应任务。

落点：`src/caap/attack/verification_objectives.py`、`tests/unit/test_verification_objectives.py`、`configs/protocols/verification_attack.json`、`reports/F16/`。不修改 F14 分类目标或 F15 校准实现。

### 实施步骤

1. 定义 objective_id：classification、genuine_rejection、target_acceptance；明确各自可见信息和固定/通用能力。
2. 本人拒绝最小化对合法训练本人原型的 cosine；目标接受最大化对预设训练目标原型的 cosine，loss 符号写入配置。
3. 训练原型与部署模板分开登记；source_only 只读获准源信息，template_known 可读明确授权的冻结部署模板，但不自动有阈值权限；query_limited 按批准接口逐次记账。
4. 用二维单位向量与有限差分证明梯度方向、raw 范围和冻结模型不更新；threshold_known 才能额外只读 thresholds.json，用 max(0,s(z,g_y)-tau+margin) 或 max(0,tau+margin-s(z,g_t))，未授权时只用无阈值 cosine 目标。
5. 三目标的更新/draw/查询/选模、模板来源、threshold_known 权限和阈值 hash 分别版本化；margin/候选只在 attack_dev/attack_select 有界选择。任何模式都不能读取 calibration 图像/分数或 final_probe 来优化；source_only 不接收目标模型/模板/阈值/评估反馈。

### 正负验收与命令

正例：一步合法更新使目标 cosine 沿预定方向变化。负例：目标等同本人却称冒名、零范数、目标来自 test、用 calibration 挑参数、混用 objective_id 都失败。

`FUTURE`：`python -m unittest -v tests/unit/test_verification_objectives.py`。

### 产物、成本、失败与接力

输出配置、梯度测试和攻击者知识表；科学键含 objective、原型内容、知识能力、loss、优化与选择策略，不能只写 target_id。CPU 数学测试；真实训练在 F30，成本与分类预算匹配并单列。NaN/无原型停止，低目标接受率不是 bug。对应 `R2-3/R2-4/H3`；交接 F20/F30 冻结损失和可见性。

## F17 · 分类退化、聚类统计、视觉和联合指标

### 目标、先决与落点

每个结果都有事件、分母、统计单位和视觉范围。输入 F14 分类事件、F15 pair/threshold、F13 mask；真数据缺失时仅用非生物夹具。

落点：`src/caap/attack/evaluation.py`、`stats.py`、`visual_metrics.py`、`tests/unit/test_metrics.py`、`test_stats.py`、`test_visual_metrics.py`、`reports/F17/`。统计唯一写者；物理任务消费，不复制另一套 bootstrap。

### 实施步骤

1. 保存 sample/condition/draw 的 clean/adv、eligibility、k/n/n_total；n=0 返回 null/INVALID_DENOMINATOR。
2. clean/adv 共用随机 draw，分别输出逐 draw clean-correct 条件池化率与固定标称洁净集合结果；probe macro 另命名。
3. 训练、eval draw、数据拆分和 bootstrap 分离随机流；评估不能推进训练 RNG。
4. 按 subject 整簇 bootstrap 2000 次，未知退到 palm 并警告；验证 pair 两端抽样同一 multiplicity，不同人权重 m_u*m_v、同人 m_u，固定单目标只抽攻击者。
5. 输出分类错/验证拒绝或目标接受的共同有效集合 2×2；保存 cluster 两端、invalid replicate 比例、区间条件及所有 seed 点。
6. 视觉在外部整图退化前的 raw 灰度计算：全图及 bbox 外扩3px的固定 R；MAE/MSE/PSNR、SSIM map 和 mask 内有效邻边 TV。

### 正负验收与命令

正例：分类夹具 y=[0,1,2,1]、clean=[0,1,0,1]、adv=[1,1,2,0] 必为未定向 2/3、t=1 定向 1/1。A 有效 4 成功 4、B 有效 1 成功 0，池化 80%、macro 50%，零有效 probe 不改变率但总数增加。

统计正例：m_A=2,m_B=1,m_C=0 时 AB/AA/AC 权重为 2/2/0；交换配对条件差号反转。负例：错误分母、只抽 probe 端却声称双端、重复 draw 当独立人必须失败。

视觉恒等图 MSE=0、SSIM≈1、PSNR=null/PERFECT_MATCH；SSIM 固定11×11、sigma1.5、K1=.01/K2=.03、population covariance/reflection，与独立参考一致；无 TV 有效边为 null，mask 外填充值不影响 TV。

`FUTURE`：`python -m unittest -v tests/unit/test_metrics.py tests/unit/test_stats.py tests/unit/test_visual_metrics.py`。

### 产物、成本、失败与接力

输出指标合同和手算测试，正式逐样本/视觉记录由下游任务产生。键含事件、eligibility、draw与bootstrap seed、聚类规则、R/SSIM/TV定义；连续指标不强塞 k/n。CPU 内存有上限，bootstrap 按条件分块但共用配对索引。无效复本不足形成区间则 null，不补0；宽区间不扩样。对应 `R1-7/R2-2/R2-3/R2-5/R3-3/H1/H2/H3/H4`；交接准确字段和边界状态。

## F18 · 类型化产物、科学键与确定性恢复

### 目标、先决与落点

区分逻辑 task_id、计算 scientific_key 和尝试 run_id。输入 F05 控制恢复、F16/F17 科学参数与协议任务类型；父内容未定时保持逻辑引用，不能提前伪造最终键。

落点：`src/caap/runtime/artifacts.py`、`scientific_key.py`、`checkpoints.py`、`runner_registry.py`、`src/caap/tools/eval_checkpoint.py`、`tests/unit/test_artifacts.py`、`tests/integration/test_resume.py`、`reports/F18/`。F04 状态接口只读，必要接口变更经所有者协调；每次 run 原子新建，绝不覆盖旧目录。

### 实施步骤

1. 定义公共 resolved_config/provenance/status/events/artifact_manifest；按类型校验必需文件，覆盖 train_recognizer/validate_recognizer/train_defense/train_feature/train_patch、generate_control、calibrate、eval_classification/eval_verification、analyze_structure/analyze_visual、certify、export_print、preprocess_capture/score_capture、run_original_attack、physical_report/collect_report。
2. 实现固定 runner registry：每 task_type 绑定 caap 入口、argv schema、输入/输出 schema、角色权限、owned_paths 和阶段；禁止执行清单内任意 shell。每条开发边使用 parent_id/child_id/requires_stage=development_done/artifact_refs/artifact_hashes；科学节点的 execution_prerequisites 只以 `{task_id,entry_hash}` 引用独立同名 JSON 文件中的对应条目，科学父输出另需 SUCCEEDED/type/hash/role 全匹配。未绑定边或缺该节点真实父资产时拒绝，不用全 registry 的其他未就绪条目阻塞本节点。
3. 规范化科学键，包含角色父hash、协议依赖、实现/环境、数值精度/AMP及适用科学参数/seed；训练与评分的 placement/尺度等科学参数不能排除，磁盘位置/worker/GPU调度 placement 才不入键。禁止 NaN，有序列表不擅自排序。
4. 保存完整训练状态；patch best 用 attack_select，识别器用 recognizer_val，辅助用 msdife_val。tie早epoch、首个合法零分也保存；完整epoch恢复须实测，中途batch未验证不承诺精确续训。
5. eval-only 不构造 optimizer，默认新目录整节点重跑；分片复用须唯一 sample/pair/capture+condition+draw、完整清单与hash校验。export_print 使用 origin=exported_print 并保留父学习/控制 artifact 的 origin/hash，不冒充 generate_control；原能力黑盒保存 query/search 状态，不伪造 optimizer。
6. 父失效传播所有后代；threshold_known 训练明确依赖冻结阈值，因此阈值变更也使该训练失效。无阈值训练不受影响；验证原始分数缓存须核模型/gallery/probe/pair/渲染一致才能复用。

### 正负验收与命令

正例：连续2epoch与1+恢复+1在声明环境相同；calibrate/control/visual无optimizer照样按类型通过。负例：缺阈值或逐样本预测、同键旧父替换、重复分片、半JSON、路径改变导致科学键改变均失败；改变模型/mask/模式/scale/seed/阈值使相关键变化。

`FUTURE`：`python -m unittest -v tests/unit/test_artifacts.py tests/integration/test_resume.py`；`python -m caap.tools.eval_checkpoint --run-dir "$CAAP_INPUT_RUN" --eval-config "$CAAP_FROZEN_EVAL" --out "$CAAP_NEW_RUN"`，参数须由控制器授予只读父引用和新目录。

### 产物、成本、失败与接力

输出 artifact schema、恢复测试、失效影响表。train_patch/feature、generate_control、calibrate、classification/verification、structure/visual、physical_report、collect_report 必需文件按科学合同逐类型定义。CPU测试，GPU容差由F03预声明；train microbatch/BN/精度变化不自动同键。损坏退最近完整checkpoint，无法恢复新尝试；低ASR不重试。对应 `R2-4`；交接F19/F20可验证产物与失效边界。

## F19 · 离线单测、GPU 回归与测试集封闭

### 目标、先决与落点

防止“跑完”掩盖错误与测试泄漏。依赖 F18；GPU 未授权只标对应层未执行，不把 skip 包装成覆盖。

落点：`tests/integration/test_role_firewall.py`、`tests/regression/`、`src/caap/runtime/test_gate.py`、`reports/F19/`。本任务只增加横切测试和访问门禁，业务模块修复交回各所有者，避免大范围竞争写。

### 实施步骤

1. 分层 CPU核心/CPU完整/GPU/slow；核心离线、无下载、无真实生物数据。
2. 为七模型、几何、预算、指标、恢复和历史可追溯缺陷登记回归ID，记录baseline失败而非忽略。
3. 设置角色访问门禁：开发任务不可读test标签/分数，calibration仅阈值节点读，gallery能力显式授权。
4. 运行关键变异：反平移、断梯度、test-as-val、跳权重校验、换分母，要求对应测试确实失败。
5. 输出完整命令、退出码、数量/skip/环境及未覆盖项；独立审查通过才提供 F20 门禁证据。

### 正负验收与命令

正例：所有核心行为断言可离线执行；合法角色访问通过。负例：0 tests collected、所有核心skip、变异未被捕获、隐式test访问均不准冻结。

`EXISTING` 基础回归：`python -m unittest discover -s tests -v`。`FUTURE` 科学分层：`python -m unittest discover -s tests/unit -v`、`python -m unittest discover -s tests/integration -v`、`python -m unittest discover -s tests/regression -v`。GPU/slow 用 unittest 的显式资源条件和 skip 原因，不使用 pytest marker；只有获准设备与有限预算才能解除相应 skip。未来测试包须可导入，单文件示例也可用 `unittest discover -s <directory> -p <filename> -v`。`python -m compileall -q src/caap` 仅语法检查，不替代测试。

### 产物、成本、失败与接力

输出 `test-gate.json`、`mutation-tests.json`，记录代码快照与测试环境，不产科研数字。CPU/GPU时间有界；变异仅隔离测试上下文，不残留生产修改。失败归根因有限修复，门禁不能降格迁就错误；真实历史曝光始终披露。对应 `R2-1/R2-3/R2-4/R3-1/R3-3`；交接 F20 可以解封哪些能力和哪些仍阻塞。

## F20 · 公平预算、有限自动搜索与全局分支冻结

### 目标、先决与落点

**数字主冻结只消费 development/pilot，不等待 F24 等最终结果，也不硬等 F22 原作、F36 认证或 F39 打印。** F09 的开发边绑定 `reports/F09/registry-ready.json`，允许完整 21 项状态表包含 blocked/null；F03/F05/F10/F19/F23/F27 同样按开发契约验收。真实科学节点只绑定自身 model-entry/clean gate、角色、所需 feature、源选择配方、分支冻结与获准资源，不能要求 F09 全体真实模型先完成。

F20 保留原始 full expected_cells，并可只冻结当前前提齐全的科学子图；AISEC 缺资产不阻止已满足其余门禁的 Tongji 单元，所有涉及 AISEC 的节点仍阻塞，full 仍 INCOMPLETE。后来补齐资产按原预注册规则发布新控制快照，不改已经完成节点的局部科学键，也不能消费先前 final 结果来选择新增配方。F36/F39/F40 的真实前提仍在各自分支校验；development_done 绝不是解封许可。

落点：`src/caap/tools/freeze_experiments.py`、`run_experiments.py`、`configs/protocols/full.json`、`configs/experiments/full.json`、`search.json`、`tests/integration/test_freeze.py`、`runs/F20/`、`reports/F20/`。接管F01协议单写权；各分支只能写自己的扩展配置，不反向修改全局冻结。

### 实施步骤

1. 冻结有限搜索空间、objective、调参角色、每候选次数/最大trial、最大更新/EOT/调用数/时长、早停和选择tie规则；候选必须先登记，禁止看结果临时扩域。
2. 消费 F23 已实现直接基线及成本，特定原作候选缺失单列；只在 patch_train/attack_dev/attack_select 上有限搜索，保存全部候选与失败，禁止 calibration 样本/分数及 final 反馈。
3. 分别锁定 selected_caap 与含 ASIT/RaS/pretrained 的 ablation_reference；完整 2^3 与 none/random/pretrained 行独立保留。source-only 实验另锁定 `selected_caap_by_source[source_spec_id]`，或提供事前共享配方 `a_priori_shared` 未消费目标反馈的证据；保存 selection_manifest_hash/selection_visible_sources/selection_evidence_refs 并审计传递闭包。仅在 CCNet 上选出的全局配方不能自动用于“其他源→CCNet”的 source-only 声称。完整配置和合法选择谱系都相同才复用。
4. 展开三域七模型、至少 3 合法目标、seed `{0,1,42}`、H1–H5、原作/迁移/防御/物理全部 expected_cells；缺原作/认证/物理不是删范围理由。冻结主/次/探索终点、比较家族和多重比较策略。
5. 数字作业用实测成本和批准限额预留；认证/实拍未标定成本保持待决，只禁止对应分支。训练/评估/预训/防御/采集与受限重试分别记账，K=4 额外调用不可隐去；超任何批准总额停止，不私降 full。
6. 经控制器单写发布 runs/control/ 下 experiment_manifest.json、runner_registry.json、execution_prerequisites.json、dependency_bindings.json。所有开发边与科学节点须绑定阶段、类型、artifact/hash、允许argv/路径/权限/资源；未绑定或未知runner拒绝。F33/F35/F37/F40 独立分支freeze，开发worker不挂载前批final数据/分数，也不得收到其摘要；曝光已发生则登记并阻塞独立确认声称。
7. `--config ... --dry-run` 只验证模板，`--manifest runs/control/experiment_manifest.json` 才能执行冻结快照。最终数据仅由经门禁的只读evaluator访问；调度器和数据访问层都验证freeze/role，缺任一字段fail closed，不能靠提示词约束。dry-run不读final、不初始化训练、不生成SUCCEEDED。

### 正负验收与命令

正例：F21/F23 开发先于 F20，F22 原作缺失仍能冻结已就绪数字节点；F36/F39 阻塞不拦其他分支，F43 full 仍不 READY。DAG 无环且 phase 不倒退，selected 关闭模块仍保留 reference。负例：用 development_done 放行缺真实资产的执行、缺 runner/阶段绑定、final 目录可被开发 worker 读取、未授权阈值反馈、无限 trial 均拒绝。

`FUTURE`：`python -m caap.tools.freeze_experiments --profile configs/profiles/full.json --search configs/experiments/search.json --out reports/F20`；`python -m caap.tools.run_experiments --manifest runs/control/experiment_manifest.json --dry-run`；`python -m unittest discover -s tests/integration -p "test_freeze.py" -v`。只有冻结快照及预算门禁通过，才可用相同 manifest 加 `--group Fxx` 执行真实节点；模板 config 命令不得直接去掉 dry-run。

### 产物、指标、成本与接力

输出 `freeze.json`、`budget.json`、冻结full矩阵、全部pilot选择台账。搜索策略、实际候选、科学配置和训练选模进入相关键；不能按路径/候选别名重复计结果。预训练/识别器/防御/实拍另账，默认每GPU一个训练job。

若最终测试后发现真实bug，只能证明根因、统一失效重跑所有受影响方法/seed/条件并披露；不能追高调参。若独立确认资产不足，分支为BLOCKED_ASSET，历史测试上的再分析只能明确探索性，不能靠换名字获得独立性。对应 `R1-2/R1-7/R2-4/R2-5/H1/H2/H3/H4/H5`；交接每分支唯一freeze hash、确认访问权限、科学键与剩余预算。
