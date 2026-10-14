# Agent 自治、纠错与恢复

**让 Agent 自动处理工程故障，把人的注意力留给科学主张、资源和许可；不能把自主执行变成自主改协议。**

## 1. 授权边界

**本轮仅迁移与自检；本文件的科研队列、租约、自动恢复是 future 合同。** 后续实现并通过门禁，且收到用户明确执行任务后，在已批准工作区、依赖环境和资源预算内，Agent 可自行：

- 读取和修改切片允许的源码与测试。
- 生成匿名合成测试夹具、执行离线单测与集成测试。
- 根据真实异常定位根因、加回归断言、最小修复、复测。
- 调度已冻结的实验单元、从合法 checkpoint 恢复、重跑受影响评估。
- 汇总有效结果、标记负结果、生成缺口和证据报告。

不可自行：改变训练/测试角色、扩大预算/攻击能力、按最终测试选参数、下载受限数据、申请云服务或付费 GPU、开展新采集、公开生物数据、提交/推送 Git、删用户产物。

遵守宿主工具审批。若读取文档中的命令需要确认，集中提交一组拟执行命令与作用；不借子 Agent 绕过权限，也不把每个已批准循环变成一次询问。

## 2. 可恢复状态与日志

未来控制状态位于 `runs/control/`，运行产物位于 `runs/<F任务ID>/<run_id>/`，报告位于 `reports/`。F ID 只用于 owner/group 与写入权限分组，task_id/scientific_key 标识具体科学节点；当前自检可写自身报告，但不伪造科研任务完成台账。

`state.json` 至少包含：`plan_version,protocol_hash,workspace_snapshot,active_slice,tasks,runs,budget,open_decisions,last_verified_artifact,controller_epoch,allocation_snapshot`。

开发任务至少包含 `id,development_status,owner,dependencies,allowed_paths,attempt_count,evidence_paths,last_error,next_action`。计算节点另外使用 `execution_status,task_type,input_refs,scientific_key,expected_outputs,lease_id,fencing_token`；每次尝试有不同 run_id。`plan/tasks.json` 保持严格 `caap.tasks.v2` schema：F DAG 表达开发/证据组织关系，不是已经展开和获准的科学执行 DAG。

F18/F20 在 `runs/control/` 生成并审查三个 **future** 文件，当前不伪造它们已实现：

| **文件** | **必要绑定** | **执行门禁** |
| --- | --- | --- |
| `runner_registry.json` | registry版本/hash；每 task_type 的固定 entrypoint/argv 模板、输入/输出 schema、状态/恢复合同、所需能力和允许路径 | 所有科学节点必须有经过代码审查的类型映射；未知/未映射类型拒执行 |
| `execution_prerequisites.json` | 按科学 task_id 登记 F owner、development 证据 hash、对应数据/model-entry、角色/clean gate、feature/recipe/branch freeze、许可/预算；科学父输出绑定 task_id/output_name/type/hash/role 且要求 SUCCEEDED | 科学节点字段固定为 `execution_prerequisites={task_id,entry_hash}`，仅引用本文件同 task_id 的条目及其内容 hash；不内嵌第二份前提；缺项只阻塞该节点及依赖后代 |
| `dependency_bindings.json` | 每 F 开发边固定字段 `parent_id/child_id/requires_stage/artifact_refs/artifact_hashes`，`requires_stage=development_done` | 静态 depends_on 统一是开发验收依赖；不能凭 development_done 推断真实实验通过，科学前提另由上一文件校验 |

冻结的 `experiment_manifest.json` 引用三文件 hash 与具体科学节点/expected_cells。dry-run 检查绑定完整、无环、类型相容、目标反馈闭包和前提，但不执行任意配置代码、不生成 SUCCEEDED。F20 不依赖认证/旧实拍恢复才能做数字冻结；原法/物理缺口依然进入 full 最终 evidence gate。

实现验收通过只提升 development 状态，真实资产、洁净基线、冻结协议、权限/预算全部通过后才可进入计算 `PENDING`。计算完成也不能自动把论文写作/采集条目改为完成。

训练、校准、评估、分析、物理报告与汇总均纳入同一依赖图和状态机。无 ASIT 等预声明能力缺失为 NOT_APPLICABLE；数据暂缺为 BLOCKED_ASSET。只有已校验、未失效且科学键匹配的输出可以复用。运行预算按真实尝试累加，统计 seed 数按科学单元计算，重试不增加独立样本。

追加 `events.jsonl` 记录：开始、命令及退出码、修复原因、测试摘要、状态转换、重试、失效传播、决策。日志不含令牌、真实姓名、邮件或不必要的图像内容。

状态原子写入，任务领取使用互斥/租约。控制 Agent 重启先核查活动进程、Slurm job、租约和已有产物，不把过期 RUNNING 直接当失败重开，不双重占用同 GPU。

future 状态机的正常链路为 `PENDING → READY → LEASED → RUNNING → VALIDATING → SUCCEEDED`。失败转 `RETRYABLE/FAILED_TECHNICAL/BLOCKED_ASSET/BLOCKED_PERMISSION`；受影响节点转 `INVALIDATED`，范围变更转 `CANCELLED_SCOPE`，经审计不适用转 `NOT_APPLICABLE`。ready 要求父输出类型/hash、门禁、预算均通过；进程退出 0 仅进入 VALIDATING，不能直接 SUCCEEDED。

同一状态转换以 task 版本的 compare-and-swap/事务完成。run 创建、占用预算和领取资源须可审计，恢复时处理尚未完成的事务；原子重命名只保证单文件发布，不等于多资源事务或多 writer 安全。

每个物理 GPU 或获准 MIG 实例独占租约：`resource_id,owner,task_id,run_id,parent_hashes,allocation_id,issued_at,expires_at,heartbeat_at,fencing_token`。领取时递增 token；TTL 过期只表示需核验，先确认旧进程结束或隔离，再转交。过期 worker 的旧 token 禁止发布 checkpoint/status/结果。物理 GPU 与其 MIG 子资源不能重叠授予；多个不同 MIG 实例只在 scheduler 明确授权时可并发。

### 2.1 命令与多写入者安全

- 执行器仅接受 `runner_registry.json` 中经过源码审查的 `task_type → caap.* 入口 → argv` 映射；registry 必须绑定已审查实现 hash，不允许实验配置自定义入口/脚本或修改 registry。每项登记 `entrypoint_id,argv_template,input_schema,output_schema,state_contract,capabilities,allowed_paths`。
- `export_print` 的 future 固定映射为 `caap.tools.export_print`，`run_original_attack` 为 F22 拥有的 `caap.attack.baselines.original`；两者 argv 模板均为 `[approved_python,-m,fixed_module,--config,resolved_config,--out,new_run_dir]`。前者只导出文件、不自动调用物理打印机；后者只调用锁定版本原法 wrapper，查询/网络权限与预算单独授权。接口实现和对应验收前，这两项均不可执行。
- `validate_recognizer` 的 future 固定映射为 F09 的 `caap.tools.validate_recognizers`，argv 为 `[approved_python,-m,fixed_module,--config,resolved_entry_config,--role,recognizer_val,--out,new_run_dir]`；配置只含该条目的真实权重/角色/标准与批准上下文，不由 worker 扫完整 registry 自选目标。输出逐样本 clean、metrics 和 model-gate；无 patch、无 optimizer。缺局部前提时只阻塞该条目和后代。
- 其他 task_type 同样必须有明确已审查映射，不能只登记以上几种类型就开放全队列。配置是数据，不接受任意 shell、动态 import、eval/exec 或未经审查脚本路径；参数类型/范围/路径校验后用 argv 调用，不用 `shell=True` 拼接。
- 配置路径 resolve 后必须在授权根；拒绝路径穿越、逃逸 symlink、覆盖原始数据和旧 run。未知键直接拒绝，不吞掉后按默认值运行。
- F 任务派发前绑定允许文件/子包、owner 与验收；热点文件串行。新文件先过落位门禁，声明用途、调用方、测试和父目录，不在根目录堆 helper，不复制出第二套 runtime。
- 文件锁与资源租约分开：源码写入锁防止覆盖他人改动，GPU/task 租约防止重复执行。多 writer 状态需真实竞争、过期 token、崩溃/恢复测试，单机“试过一次”不算通过。
- LLM 提出代码补丁必须走开发审查、测试和语义失效分析后再执行；不能让实验配置携带代码在 worker 上即时运行。

## 3. 自主工作循环

1. 读取协议与最新状态，选择依赖已通过的最小切片。
2. 核对该文件当前内容和用户新增变更，不用旧上下文覆盖新代码。
3. 为预期行为建立失败断言；对既有缺陷记录 baseline failure。
4. 只修改责任路径，运行最小相关测试，再运行受影响回归层。
5. 独立审查实现、错误处理与实验口径；不能只读“测试通过”一句话。
6. 不通过时按故障表做有限修复；通过后将证据落盘、释放所有权、继续下一切片。
7. 遇到资产/许可阻塞，标记状态并选择不依赖它的任务，不无限空转等待。

一次实现至少返回：变更摘要、文件、精确测试命令、退出码、测试数量与 skip、环境、证据路径、未解决问题、下一任务。只在关键点向用户发送摘要。

搜索/训练是另外一条受限循环：在已批准候选域、次数、更新与 GPU-hours 内观察 attack_dev/attack_select，完整记录所有候选，达到停止条件就冻结或说明不足。attack_confirm 仅按预注册规则消费；final 不参与下一候选决策。source-only 任务不能接收目标模型输出、目标 ASR 或阈值作为方法反馈。

开发门禁测试可以使用合成夹具，计算门禁必须使用真实有效资产与来源。真实识别器权重缺失时，若数据/许可/预算足够则推进 train_recognizer；缺数据才阻塞。不支持 embedding/认证的模型先做能力审计与合法适配，不以暂未实现为由从 full 中消失。

## 4. 故障分类与自动动作

默认同一根因最多 **2 次自动修复/重试**；累计第 3 次仍失败即升级通知。相同错误指纹不能通过换目录重置计数。

| **故障** | **可自动做** | **不可自动做/升级条件** |
| --- | --- | --- |
| 类型、形状、device、导入错误 | 定位栈、复现小例、修复并加回归 | 不能绕过断言或改标签凑 shape |
| 临时 worker/I/O 中断 | 从完整 checkpoint 重试；保留中断日志 | 数据校验失败不能当临时 I/O 忽略 |
| eval OOM | 减 eval batch，确认逐样本结果不变，记录配置 | 改分辨率、删样本或改指标不允许 |
| train OOM | 停止当前 run，分析峰值；仅使用已批准的等价策略 | microbatch/BN、精度、有效 batch 改变会改变算法，需版本化和 D1 类决策 |
| loss/gradient NaN | 在夹具复现数值边界；检查输入/分母/AMP；最小修复 | 不能把 NaN 替换 0 后继续报结果 |
| 结果字段缺失 | 若原预测齐全，修导出器并新建派生 eval | 缺预测不能从百分数反填样本结果 |
| checkpoint 不完整/损坏 | 退回最近校验通过的完整 checkpoint，说明重算 | 无法恢复就从头新 run；不称精确续训 |
| 依赖安装失败 | 使用已获准独立环境和锁定源重试一次 | 不降级安全限制、不改全局环境、不换未经验证框架 |
| 缺数据/真实权重/同意书 | 标记 BLOCKED_ASSET，继续离线切片 | 不生成随机权重冒充真实、不采集新人体数据 |
| 低 ASR/模块无增益 | 记录有效阴性结果，按预设解释继续矩阵 | 不能归为技术失败、自动调参重跑 |
| CI 宽/不显著 | 报效应和不确定性 | 不自动追加 seed/人直到显著 |
| 文献 URL 失效 | 查 DOI/正式会议页，标核验状态 | 不编 DOI 或绕过访问验证 |

修复循环不包含大规模重构。若最小修复需要改共享接口，先给影响分析和测试计划，再由控制 Agent 决定是否属已批准范围。

## 5. 结果失效与重跑传播

科学依赖链：**数据/权重 → 预处理/训练实现 → 补丁 checkpoint → 评估协议/阈值 → 原始预测 → 指标 → 表格/主张**。

| **变更** | **必须失效的产物** | **通常无需重做** |
| --- | --- | --- |
| 训练数据、损失、合成几何、训练归一化修正 | 相关补丁与全部下游评估；受影响基线同样失效 | 无关数据集/模型且依赖未变的 run |
| 纯评估分母或阈值实现修正 | 相关指标/表格；原分数足够则重新派生；threshold_known 训练若依赖该阈值也失效 | 未以错误指标选模、未使用该阈值的训练 |
| 被修正指标曾用于选模 | 最佳 checkpoint 选择及下游；没有所有候选 checkpoint 时可能重训 | 不能假定只重算最终一轮就够 |
| 实拍 grouping/retry 逻辑修正 | 物理指标与稿件结论 | 原始照片和可信逐次输出 |
| 图例、错别字、无语义注释 | 相关文档 | 算法实验 |
| 权重/manifest 来源不可信 | 所有依赖结果 | 无关且来源完整的结果 |

每项旧结果写 `invalidated_by` 与原因，新结果写 `replaces_run_id`；不覆盖旧文件。若源码 dirty diff 指纹变化但语义只影响注释，控制 Agent 记录证据豁免，不能只靠 hash 不同盲目烧卡。

最终测试阶段发现真实 bug 时允许修复，但必须把所有受影响方法/seed/条件一致重跑，并披露重分析；不只修对主方法有利的格子。

迁移阶段的数学模块 bytehash 相等证明的是“机械搬迁未改算法”，不是后续永久恢复旧 bug 的要求。F14/F17 语义升级先登记新协议和独立行为/负例断言，再将受改维护模块的不变性检查转换为新版本验收，保留变更理由和证据；归档原hash与migration manifest不改，未受改模块仍受旧迁移约束。不得简单删测试或改预期数值凑绿，也不把合法新语义差异送入无限自动回退。

## 6. 只在关键点通知用户

### D0：输入、许可与资源

一次集中说明缺数据、权重、安装/下载权限、scheduler allocation、显式总 GPU-hours/存储/时长、实拍授权和论文源码。用户暂未回复时继续离线开发。初始 observational phase 在已有读取权限内审计环境/metadata，不要求先获训练许可；但不以观察名义训练或读取 final 评分。

### D1：协议冻结或实质改变

通知内容：推荐配置、候选差异、验证集证据、实际时长/显存、主矩阵数量、预计成本、未解决限制。

D1 后改变预算、模块、K、分割、目标策略、主终点、数据域或采集范围，均需新版本和相同级别决策，不能称“普通重试”。

### D2：影响论文主张的发现

只发送有证据的新发现，例如：数据协议与原稿不一致、关键权重不可追溯、几何假设未获支持、部署与原稿明显不同、物理原图无法恢复。

不把单个 seed 小波动包装成重大结论。通知同时给替代解释和区间，避免只报告一个百分数。

### D3：自动修复耗尽或安全/资源越界

同根因两次修复仍失败、资源上限将超、需要工作区外修改、需要未批准安装/下载/采集时通知。

标准通知包含四项：**发现 → 证据 → 影响 → 推荐动作与需要选择的范围**。同类事件聚合，不逐 job 刷屏。

## 7. 资源与退出规则

- 正式训练无显式预算则不启动；CPU 测试也遵守批准的时长和内存上限。
- 每个 job 有最大更新数、最长时长、设备、存储上限和重试余额。
- 在启动前预留输出空间；清理仅限本次拥有且可重建的临时文件，不删除 `.codebuddy/`、原数据、旧日志或可追溯失败结果。
- 预算不足时停止新派发，保留完整 checkpoint；不擅自借用其他设备。
- 没有可执行任务且全部被阻塞时，输出简短缺口清单并结束当前执行；以后可从状态恢复，不能假装在后台持续工作。

本计划不自动创建定时任务或远程运行环境。用户未来从获准提交后的根仓自行 clone；未提交/未推送的本地重构不能声称远端已更新，Agent 不自动 commit/push。

future 调度遵守 Slurm/srun 的实际 allocation 与 CUDA 可见性，空闲显存不是资源授权；详见 05。默认独立任务单 GPU/MIG，DDP 未经数值/恢复/吞吐实测不得启用。先实测资源再核算总 GPU-hours，预算足够仍有明确上限。

`tmux`、nohup 或 scheduler 保活只保证对应进程，不保证 LLM Agent 持续在线。会话中断后，已经实现且获准的受限执行器可以完成已冻结 argv；需新决策、修代码或扩权限时等待 Agent/用户恢复。当前并未交付该执行器，不声称无限后台自治。

无可执行任务时写交接并退出，区分 `full_scope_complete/execution_exhausted/partial_blocked`；后两者绝非科研全量完成。范围取消保留原 full 缺口，不能通过重算分母变成 complete。

## 8. 独立审查检查表

- 是否真的加载正确识别器？加载失败会不会继续？
- recognizer_fit/val、MS-DIFE 内层、patch_train、attack_dev/select/confirm、calibration/gallery/final 的交集和历史曝光是否合规？
- deploy 是否任何情况下都不调用测试输入条件模块？
- 面积、缩放、插值与位置是否满足已声明的合同？
- k/n、分母过滤、空分母、目标策略和退化 clean 对照是否一致？
- 训练、恢复和随机流是否真实验证，而非仅记录 seed？
- 方法/基线的计算与调参预算是否透明？
- 物理重复、双掌和配对身份相关性是否被正确处理？
- 合成、示例、失败、失效和真实结果能否被收集器区分？
- 所有主张能否指向证据，缺失证据是否仍被标记未完成？
- 原/匹配基线、source-only/target-informed、分类/验证专用目标是否分名，模板/阈值权限是否真实？
- 每个新任务类型是否有独立产物 schema、恢复与失效规则，精度入键而 GPU placement 不入键？
- 设备是否属于实际 allocation，TTL/fencing/父 hash/多 writer 锁是否覆盖真实竞争？
- 取消范围或技术重试是否错误地提高 full 完成率，是否把 execution_exhausted 冒充 full_scope_complete？

审查发现不改变契约来“适配”错误实现。契约确实不可行时由控制 Agent 提出修订并经相应决策点确认。

## 9. 最终交接格式

交接应包含：已完成切片及测试证据、完整/部分完成矩阵、有效与失效 run 清单、主张变化、未解审稿条目、预算消耗、下一步唯一入口。

明确区分：**代码已实现、测试已通过、真实实验已完成、论文已修改**。四种状态不能互相替代。低成功率、宽区间和失败案例都可以是高质量研究交付的一部分。
