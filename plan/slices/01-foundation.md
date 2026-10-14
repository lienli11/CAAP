# 01 · Full 范围、远程交接与多 Agent 控制

**本组 F01–F05 只建立可信执行基础；目录迁移、计划通过或 GPU 可见都不等于算法已修复或实验已完成。**

## 共同执行合同

- 机器索引为 `plan/tasks.json`，版本 `caap.tasks.v2 / caap-full-v2`，严格保持原字段。它是开发/责任 DAG，不是 45 个训练作业；`depends_on` 统一等待父任务已验收的 `development_done` 契约证据，不默认等待父任务的真实实验。静态 `status=planned` 不保存运行状态。
- F04/F18/F20 必须在 `runs/control/dependency_bindings.json` 将每条开发边展开为 `parent_id/child_id/requires_stage/artifact_refs/artifact_hashes`，唯一阶段值为 `requires_stage=development_done`。真实科学前提集中登记在独立的 `runs/control/execution_prerequisites.json`；科学节点字段 `execution_prerequisites` 仅是 `{task_id,entry_hash}` 引用，不内嵌第二份前提。条目记录真实资产、角色、权限、预算、freeze 和科学父输出的 `task_id/output_name/type/hash/role`，父计算必须 SUCCEEDED。结构精确定义以自治规范 §2 为准；缺引用、条目或 hash 不符均拒绝对应阶段，不能只凭提示词或笼统 completed 放行。
- F01 预算 null 可形成草案/缺口清单并完成开发契约，但 execution 未授权仍阻塞。F06 缺资产台账、F07 `data-contract.json` 与合成角色校验可完成开发，供 F11/F15 使用；真实 manifest 未到不影响这些 CPU 开发，绝不能通过 F08/F09/F10 的真实执行门禁。`development_done` 与 `experiment_done` 分开验收和记录，F43 READY 仍要求所有承诺科学节点的有效真实证据。
- 配置模板在 `configs/experiments/`；唯一冻结科学运行快照为 `runs/control/experiment_manifest.json`，引用同目录 `runner_registry.json/execution_prerequisites.json/dependency_bindings.json` 的 hash。`run_experiments --config <模板> --dry-run` 仅编排校验；真实执行用 `--manifest runs/control/experiment_manifest.json --group Fxx`，不能直接删掉模板命令的 dry-run。单独工具的样本 manifest/配置不得替代该冻结节点引用，不能维护第二套科学键/状态。
- 运行状态只在 `runs/control/`；一次尝试写 `runs/<F任务ID>/<run_id>/`。F 只是 owner/group，不能代替科学节点 task_id/scientific_key；报告写 `reports/Fxx/`。
- 源码落 `src/caap/{attack,data,models,utils,tools,runtime}`；机器配置落 `configs/{profiles,protocols,experiments}`；测试落 `tests/{unit,integration,regression}`；原论文 `paper/sources/` 始终只读，修订仅写获准的 `paper/revision/`；旧资产只读 `archive/legacy/`；隐私资产落被忽略的 `.local/`。本组 worker 不修改 `doc/`，不更改 IDE 私有目录。
- canonical 角色为 `recognizer_fit/recognizer_val/patch_train/msdife_fit/msdife_val/attack_dev/attack_select/attack_confirm/calibration/gallery/final_probe`。下文旧 `attack_val/test_probe` 只能通过 F07 版本化 alias 映射到 `attack_select/final_probe`；未登记映射即拒绝。`recognizer_train` 只保留历史来源含义，新训练不得自行重划角色。
- 本轮仅机械迁移及基础自检，旧 P0 缺陷由 F11–F19 未来修复。`EXISTING`：`caap doctor [--output PATH] [--probe-torch] [--timeout SECONDS]` 和 `caap plan-check [--manifest plan/tasks.json] [--repo-root PATH]` 仅体检/静态图校验，不是执行器。其他标 `FUTURE` 的入口只在实现、测试和授权后运行。
- 开发先写能失败的标准库 `unittest` 行为测试，再最小实现；记录命令、退出码、测试数、skip、环境与证据。不引入 pytest 依赖；未来测试采用可导入测试模块或 unittest discover，GPU/slow 通过显式获准资源条件与 skip 原因分层。编译不代替行为测试，运行 0 个测试不算通过。
- 全部科研分支都遵守 `plan/01-协议与产物契约.md`：角色隔离、掌级 genuine、subject 统计聚类、raw `[0,1]`、三层面积、独立校准、类型化产物、测试封闭。旧目录名由本组目标布局替换，其科学语义不变。
- 科学键为规范化 `task_type + 协议依赖子集 + 实现/环境依赖 + 科学参数 + 按角色父内容 hash + 适用 seed`。路径、日志时间和 worker 名不入键；完整协议 hash 与工作树快照仍保留。开发任务报告不伪造实验科学键，未知父输出保持 pending。
- 运行必须预设更新数、时长、设备、磁盘及重试余额。同一根因最多 2 次自动修复/重试；低 ASR、宽区间、假设不支持、合法 null/N/A 不属于技术故障。缺资产和许可分别阻塞，不以 synthetic 替代真实。
- 多 Agent 以 DAG 拓扑和路径租约调度，编号不是执行顺序。公共接口的提供者是唯一写者；消费者只读或先请求有版本的接口变更。`runs/control/` 由控制器单写，worker 通过事件接口提交；不同任务也不得争写共享配置。

## F01 · 冻结 full 研究范围与授权边界

### 目标、输入与落点

目标是将完整研究承诺与可付出的资源分开登记，不沿用旧三周最小矩阵的删减默认值。输入为本 DAG、16 条意见、H1–H5、现有科学合同及用户授权；缺预算数字、许可或账户权限时输出待决项，不能把“预算充足”解释成无限资源。

落点：`configs/profiles/full.json`、`configs/protocols/full.json`、`reports/F01/`。F01 只写草案；F20 取得租约后成为全局协议最终冻结写者，F01 不再并行改同文件。

### 实施顺序

1. 逐项登记三域七模型、多目标、机制、迁移、防御、认证和物理分支，建立 16 条意见与 H1–H5 的覆盖清单。
2. 记录数据/模型/采集合法性和 CPU/GPU/存储/人次授权；将未提供的限额标未决。
3. 列出既有结果的历史曝光和不可追溯项，明确新测试不自动成为“从未见过”。
4. 分别登记开发、全局 freeze、分支 freeze 与确认性访问边界；记录范围变更必须新版本。
5. 输出完整范围审计和需用户一次集中决策的清单，不启动科学训练。

### 验收与命令

正例：45 个任务、16 个意见、5 个假设有去向；预算币种/小时/字节/人次有单位，未知值保持 null 的草案可验收 development_done。负例：full 漏 H5 的草案失败；无总上限或缺审批却标 execution_ready/可训练必须失败，但不能因此禁止只读盘点或已批准 CPU 合成开发。

`EXISTING`：`git status --short`、`git rev-parse HEAD`，只读快照。`FUTURE`：`python -m caap.tools.freeze_experiments --scope-only --profile configs/profiles/full.json --out reports/F01`，入口由 F20 实现；F01 初始阶段由结构校验和人工审查出草案，不能等待 F20 才成为 DAG 父节点。

### 产物、成本与接力

输出 `scope-audit.json`、授权引用及协议草案 hash，暂无真实科学测量。CPU 小预算；许可由人批准，写配置串行。校验冲突先修索引，不删科学问题；权限不足停止相应动作并集中通知。对应 `R2-4`；交接 F02/F06：快照、全部范围、限额、缺口、下一步可执行任务。

## F02 · 远程 clone 与准确版本交接

### 目标、输入与落点

远端必须拿到批准的准确代码，而不是“同一仓库的某个版本”。输入为获准仓库 URL、commit、远程工作区和本地迁移快照；缺远程参数仍可输出本地源码/迁移契约及缺口并 development_done，供离线开发使用；只有远端身份、版本和权限实际核验后才能执行远程任务，不猜服务器或凭据。

落点：`src/caap/tools/handoff.py`、`tests/unit/test_handoff.py`、`reports/F02/`。远程目录必须显式批准；本任务不 commit/push，也不修改私有 Git 配置。

### 实施顺序

1. 记录 HEAD、tracked/untracked/dirty 状态；列出未进入 commit 的必要文件，不能谎称 clone 会包含它们。
2. 输出机械迁移映射与校验清单，确认旧算法逻辑未被顺便重写。
3. 经宿主批准后在指定目标 clone；既有非空目录拒绝覆盖，已有仓库仅核验，不强制 reset。
4. 核对远端 commit、源码树 hash、包入口和配置路径；额外交接补丁须独立获批并记录 hash。
5. 建立不含用户名、凭据或私有路径的公开摘要及远端未满足项。

### 验收与命令

正例：同 commit、同交接补丁得到相同源码快照。负例：本地 dirty 文件缺失、错误 commit、目标非空或来源不在允许清单均阻塞，不能默默取最新 main。

`EXISTING`：`git rev-parse HEAD`、`git diff --stat`。`EXISTING，须授权`：`git clone "$CAAP_REPOSITORY_URL" "$CAAP_REMOTE_WORKDIR"`；变量必填且命令在目标主机的批准上下文执行，不能将本地路径当远端路径。`FUTURE`：`python -m caap.tools.handoff --verify --out reports/F02`。

### 产物、成本与接力

输出 `handoff.json`、`remote-version-check.json`、机械差异和未交接清单。源码 hash 是 provenance，不构造攻击结果。CPU/网络成本设上限；同一目标目录单写。网络故障最多 2 次，权限/主机身份异常立即停止；不得绕过 SSH 校验。无直接 reviewer 科学证据；交接 F03/F04/F11 精确版本和可用入口。

## F03 · 环境与 GPU 能力和成本标定

### 目标、输入与落点

基于实际获准设备标定，不由显卡型号估算吞吐。输入 F02 快照、依赖锁、独立环境和设备清单；CUDA、驱动或权限缺失时保留 CPU 结果，GPU 部分为阻塞。

落点：复用已实现的 `src/caap/runtime/doctor.py`，新增 `src/caap/runtime/benchmark.py`、`configs/profiles/hardware.json`、`tests/unit/test_environment_probe.py`、`reports/F03/`。doctor 保持唯一探测入口，benchmark 只消费其结果并测受批准成本；不再创建 tools/probe_environment.py。共享 doctor 修改须串行回归现有 unittest，F20 只引用已验收环境 hash。

### 实施顺序

1. 记录 OS、Python、依赖版本与来源、CPU/RAM、Torch/CUDA/driver、设备 UUID 和可用显存。
2. 在授权环境内检查依赖一致性；安装需另获准，不能改用户全局环境或随意升级。
3. 用非生物合成张量分别测 CPU 与获准 GPU 的前向、输入梯度、保存读取，先 warm-up 再统计。
4. 记录 precision、batch、同步方式、p50/p95 时长和峰值显存；真实模型成本后由开发 pilot 更新估计，不混为已测。
5. 输出每卡建议并发及资源安全余量；默认一张卡一个训练 job。

### 验收与命令

正例：同一测例的输出有限且设备归属准确。负例：伪 GPU 标志、不可分配设备、缺驱动、无预算均不能报告 GPU 通过；dry probe 不读取测试标签。

`EXISTING`：`python --version`；`caap doctor --output reports/F03/environment.json`（只读环境信息，可输出报告），获准后可加 `--probe-torch --timeout 15`。`FUTURE`：`python -m caap.runtime.benchmark --profile configs/profiles/full.json --doctor-report reports/F03/environment.json --out reports/F03/benchmark.json`；`python -m unittest discover -s tests/unit -p "test_environment_probe.py" -v`。现有 doctor 不运行 benchmark、不训练，也不承诺已取得 GPU 授权。

### 产物、成本与接力

输出 `environment.json`、`benchmark.json`、硬件配置及原始测时。环境/精度进入相关科学键，机器昵称不入键。资源时长上限先从 F01 扣除；实测超限停止，不借未授权 GPU。对应 `R2-4`；交接 F08/F20 每配置成本的测量范围与尚未测量的部分。

## F04 · 多 Agent 路径所有权与设备租约

### 目标、输入与落点

允许并行开发和评估，但禁止两个写者同时修改同一路径或发布同一科学节点。输入机器 DAG、F02 快照和 F01 资源；父任务未知、协议无效或能力不足不能领取。

落点：`src/caap/runtime/leases.py`、`scheduler.py`、对应单测/集成测试、`runs/control/`、`reports/F04/`。控制器是状态、预算和租约唯一写者；worker 只能使用领取到的 `owned_paths` 和独立 run 目录。

### 实施顺序

1. 验证唯一 ID、依赖存在、无环、phase 不倒退、路径合法；同 phase 允许有向依赖。
2. 为任务、重叠路径和设备建立原子领取、续租、释放及 fencing token。
3. 开发领取只核每条 depends_on 的 development_done 和绑定契约证据；真实执行另核 execution_prerequisites/runner/权限/预算/freeze/真实父hash。F07 data-contract 已验收而真实数据缺失时允许 F11 合成开发，禁止 F08 真实训练；未知绑定一律不派发。
4. Worker 启动前核查令牌、预算预留和目录；提交结果时再次校验，拒绝过期 worker。
5. 构建双进程竞争、控制器崩溃、续租延迟和同卡竞争测试；独立路径任务应能并行。

### 验收与命令

正例：不冲突的两个 CPU 任务可并行，7→3 的非数字依赖按拓扑正确执行。负例：双领取仅一方成功；过期令牌不可发布；有活进程的超时租约不立即派新 GPU job。

`FUTURE`：`python -m unittest -v tests/unit/test_leases.py tests/integration/test_scheduler.py`。若仓库已提供基础 `caap.runtime` 入口，先读当前 `--help` 核对语法；不得由本文推断尚未实现的自动派发能力。

### 产物、成本与接力

输出竞争测试证据、状态和事件 schema；没有科研成功率。CPU 测试有限并发，保留死锁超时和进程清理证据。锁失效停止发布而非容忍双写；不删除已有 run。对应 `R2-4`；交接 F05/F18 领取令牌、单写接口及错误语义。

## F05 · 观察、检查点接力和有限失败恢复

### 目标、输入与落点

控制器中断后能安全续跑；观察界面不能误把“进程结束”当科学验收成功。输入 F04 状态、租约、事件和预算；旧状态缺关键字段时进入需审查状态，不猜恢复点。

落点：`src/caap/runtime/observer.py`、`recovery.py`、`tests/integration/test_control_recovery.py`、`reports/F05/`。观察者只读；状态修订仍经 F04 单写接口，日志追加不覆写。

### 实施顺序

1. 展示任务、父依赖、worker、心跳、资源余额、当前尝试和最后有效产物，不泄漏原始生物数据。
2. 控制器重启核查实际进程、租约和磁盘产物，区分仍运行、可重试、资产/权限阻塞及已失效。
3. 按错误根因指纹累计重试，最多 2 次；同 run 与新 run 都计实际成本。
4. 输出接力摘要：快照、有效父输入、最后确认点、未决项、下一命令和权限，不能只写“继续”。
5. 按状态机测试 worker 被杀、半文件、预算不足、低 ASR、全阻塞和重复通知聚合。

### 验收与命令

正例：中断后只恢复一个实例、旧日志完整、预算不回退。负例：低 ASR 或 CI 宽不会触发重训；第三次同根因自动重试被拒；全阻塞后退出而不是忙等。

`FUTURE`：`python -m unittest -v tests/integration/test_control_recovery.py`。未来观察/恢复入口须先经当前 CLI 帮助核验，再将实际命令写入接力记录。

### 产物、成本与接力

输出 `recovery-tests.json`、`handoff-schema.json`；不声称已经实现任意 batch 精确续训，训练恢复由 F18 独立证明。CPU/日志空间计预算，控制状态串行。权限或数据完整性异常立即停止相关分支；其他就绪任务可以继续。无直接 reviewer 证据；交接 F18/F45 恢复边界和全部待决根因。
