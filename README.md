# CAAP：可复现掌纹鲁棒性研究工作区

**一个入口理解项目，一份任务图驱动后续开发与实验；原始证据、运行结果和科学结论分开管理。**

本仓库用于授权离线的可见光掌纹鲁棒性研究。它不验证或宣称攻破完整支付系统、活体检测或多模态认证。

## 1. 从哪里开始

- 理解论文、16 条审稿意见和 H1–H5：[doc/README.md](doc/README.md)。
- 新 Agent 开始执行：[plan/README.md](plan/README.md)，机器任务索引为 [plan/tasks.json](plan/tasks.json)。
- 修改文件前先读：[AGENTS.md](AGENTS.md)。
- 远程拉取、GPU 探测、并行与恢复：[远程运行规范](plan/05-远程启动与资源调度.md)。

当前版本提供**完成包化的旧研究代码、可用的环境探测/计划校验工具、迁移回归及详细 full 计划**。正式实验队列、完整数据协议和 P0 算法修正仍是待实现任务，不能仅凭本次重构把实验状态标为通过。

## 2. 目录只有一个职责

| **位置** | **放什么** | **不放什么** |
| --- | --- | --- |
| `src/caap/` | 可安装 Python 源码、命令实现 | 数据集、输出、临时脚本 |
| `tests/` | unit/integration/regression 测试及小型夹具 | 真实私密生物样本 |
| `doc/` | 便于人理解的论文与研究说明 | 运行日志、自动生成报表 |
| `plan/` | 规范、任务图、详细分片与交接规则 | 伪造的任务完成状态 |
| `configs/` | 版本化模板、profile、目录治理规则 | 机器密码、绝对私密路径 |
| `paper/sources/` | 原始论文、审稿信 PDF | 覆盖后的修订稿 |
| `archive/legacy/` | 冻结历史配置、合成 smoke、上游材料与来源映射 | 新实验结果 |
| `.local/` | 本机数据、权重、许可材料和原上游 checkout，Git 忽略 | 可移植源码 |
| `runs/`、`reports/` | 新任务状态、运行产物、派生报表，Git 忽略 | 作为源码提交的巨大目录 |

根目录仅保留项目入口与构建声明。新增目录角色须更新 [目录登记](configs/repository-layout.json) 及治理测试；新命令在 `caap` 下注册，不在根目录放第二套执行脚本。

## 3. 当前确实可用的命令

需要 Python 3.9 或更新版本。建议在获准机器的独立虚拟环境中使用 Python 3.11/3.12；不要搬运本机 `.venv` 到 Linux。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m caap --help
.venv/bin/python -m caap doctor
.venv/bin/python -m caap plan-check --manifest plan/tasks.json
.venv/bin/python -m unittest discover -s tests/unit -t . -v
```

`doctor` 只做环境清点，不分配 GPU；显存空闲不代表获得资源使用权。`plan-check` 验证 45 个计划节点、依赖和覆盖，不运行实验，也不声称计划中的代码已经实现。

研究依赖独立安装：先依据驱动和平台选择兼容 PyTorch/torchvision 构建，再安装 `.[research]`，导出精确环境锁。`pyproject.toml` 的范围约束不是已经验证所有组合的跨平台锁文件。

```bash
.venv/bin/python -m pip install -e '.[research]'
.venv/bin/python -m unittest discover -s tests -t . -v
```

没有研究依赖时部分回归测试会显式 skip；跳过不是通过。真实训练仅在 F 任务的实现、测试、资产、资源和协议门禁通过后执行。

### 旧入口不是正式 v2 引擎

`legacy-attack`、`legacy-pretrain`、`legacy-physical-report` 保留研究原型，须显式承认 legacy 协议。它们尚有计划列出的几何、统计、数据角色等限制，不准用于填充新论文主表。

`make-synthetic` 只生成明确标记的非真实测试纹理；训练合成识别器需要额外显式开关。任何合成结果都不能替代真实实验。

**当前没有可直接运行的 `run-all-experiments` 或正式 GPU worker。** 新 Agent 应先实现和验收对应 F 任务，不自行猜一个不存在的命令。

## 4. 重构与证据保留

原 `CAAP_code/` 的源码迁到 `src/caap/`；完整的原嵌套工作树在本机 `.local/upstream/CAAP_code/` 原样保留，不进入新 clone。

原 `caap_revision/` 已移到 `archive/legacy/caap_revision/`，两份 PDF 移到 `paper/sources/`。所有冻结文件的原路径、SHA-256 和新位置见 [迁移清单](archive/legacy/migration.json)。原始配置中的旧路径不被改写，它们是历史记录，不是可直接执行的新配置。

历史提交 `278e371` 可用于核对旧布局。远程启动必须固定实际包含 `src/caap/` 和 `plan/tasks.json` 的重构提交，并记录 `git rev-parse HEAD`；不能只靠仓库 URL 或分支名判断运行版本。

## 5. 研究完成意味着什么

默认 full-profile 覆盖完整分类/验证、几何机制、迁移、防御与物理证据分支，不再受旧三周预算限制。

“充分预算”不等于无限 GPU 时间或人体采集许可。成功与失败实验都要决算；缺资产/许可是阻塞，负结果是可成立的研究结果。不能为了出现显著优势无限追加 seed、目标或最终测试调参。

正式证据必须能由冻结配置、数据/模型指纹、逐样本记录和统计规则重建；全部审稿意见有状态、证据和限制，不将缩减范围冒充完整完成。

## 6. 来源与许可

研究源码来源于 [ryliu68/CAAP](https://github.com/ryliu68/CAAP)，上游参考提交与本地修订状态见迁移清单，代码许可见 [LICENSE](LICENSE)。

源码许可不等于论文、审稿信、数据集或受试者图像可任意公开。保持仓库私有；公开任何证据前单独核查授权与去标识范围。不要自动将 `.local/`、`runs/` 或整份实拍数据上传 GitHub。
