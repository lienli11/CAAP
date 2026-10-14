# 02 · 合法资产、角色划分与真实模型

**F06–F10 将真实证据与合成夹具分开；缺模型或许可会阻塞科学矩阵，不会缩减 full 承诺。**

共同控制、科学键与有限重试遵守 `01-foundation.md`。本组所有模块命令均为 **FUTURE**，须实现并获准后执行；以下没有报告已经完成的训练。七模型指当前实际 `CCNet/CompNet/CO3Net/VGG/ResNet/MobileNetV2/ShuffleNetV2` 家族，具体深度、类名、输入头和本地变体由注册表锁定，不能仅凭名字称标准模型。

## F06 · 合法数据、权重、论文与实拍资产台账

### 目标、先决与责任路径

建立可验证来源和许可的资产清单。输入 F01 范围、用户提供的三域数据、模型/辅助权重、旧实拍、论文源码和合法文献；缺失项分别登记，未知许可不能视为同意。

唯一写者落点：`src/caap/tools/audit_assets.py`、`tests/unit/test_asset_audit.py`、`.local/assets/`、`reports/F06/`。`archive/legacy/` 只读，不能为了整理删历史产物；`.local/` 不进 Git。

### 实施步骤

1. 逐项记录匿名 asset_id、source_ref、许可用途、可信来源、内容 hash、大小、类型和保留/公开限制。
2. 不解包执行不可信 pickle；优先安全加载或由授权人提供安全格式副本。
3. 核对数据、权重、稿件、400 张旧实拍声明与实际文件，不从目录名推断内容。
4. 分离私密映射与公开统计，检查公开报告是否含绝对路径、姓名、模板或可识别人脸/掌纹图。
5. 输出可用/缺失/待许可清单，一次集中请求输入，继续不依赖资产的 CPU 开发。

### 正负验收与命令

正例：同内容换路径 hash 不变；有许可的资产可以引用而不复制到公开目录。负例：不可信 pickle、无许可下载、缺权重却生成随机替代、从比例补逐次数据均被拒绝。

`FUTURE`：`python -m caap.tools.audit_assets --profile configs/profiles/full.json --out reports/F06`；`python -m unittest -v tests/unit/test_asset_audit.py`。

### 产物、指标、成本与交接

输出 `assets.json`、`missing-assets.json`；资产内容 hash 是后续科学键输入，私密路径不是。报告资产数量/许可覆盖，不报告攻击效果。CPU 哈希与存储先估算，独立资产可并行只读；同清单单写。格式损坏停止使用，I/O 可有限重试，缺许可不重试联网获取。对应 `R2-2/R2-3/R2-4/R3-4`；交接资产引用、限制、缺口与合法补给方式给 F07/F21/F38。

## F07 · 三域 ROI、掌级标签与角色 manifest

### 目标、先决与责任路径

Tongji、IITD、AISEC 均使用实际元数据，不套用想象的 session 或 6/2/2 比例。输入 F06 合法资产与历史训练来源；subject/session 不明保留 null，类数不足无法支持目标设计时阻塞，不伪造身份。

落点：`src/caap/data/manifests.py`、`roi.py`、`src/caap/tools/build_manifests.py`、`tests/unit/test_data_manifest.py`、`configs/protocols/data_roles.json`、`runs/F07/`、`reports/F07/`。本任务是全局 sample/label 映射唯一写者，后续任务引用不可变快照。

### 实施步骤

1. 导入全局 sample_id/sha256、domain、palm/class、匿名 subject、hand/session、shape/pixel_space 和来源；连续 class_id 保留逆映射。
2. 固定 ROI 算法和失败处理，记录原图→ROI hash；重复原图/裁剪副本不能跨角色绕过查重。
3. 由本任务唯一生成 recognizer_fit/recognizer_val、patch_train 内 msdife_fit/msdife_val、attack_dev/attack_select/attack_confirm、calibration/gallery/final_probe 及角色关系表；recognizer_train 仅历史来源，attack_val/test_probe 必须显式 alias 到 attack_select/final_probe。
4. recognizer_fit/val 不交且均不接触 attack_confirm/calibration/final_probe；patch_train/dev/select/confirm/calibration/final 默认两两不交。dev/select 数据不足复用须预注册同一 attack_search_pool，不能充当独立确认。gallery 与 recognizer_val 及全部验证/确认/校准/final probe 不交，合法训练复用逐项登记。
5. 登记所有学习组件历史曝光和确认分支；相同 sample_id 通过合法角色关系复用，不复制成新图。确认身份不在闭集头时禁用闭集分类，不改标签凑头。
6. 先交付 data-contract.json、角色 schema 和非生物合成隔离测试作为 development_done；真实角色 manifest 另须资产/身份/目标/采样验收才 experiment_done。F08/F10 只能消费本任务冻结 fit/val，不能再自行划分。

### 正负验收与命令

正例：同人双掌保持不同凭据、同 subject cluster；非连续标签可逆重映射。负例：内容重复跨分割、gallery=probe、val_ratio<=0、目标无样本、未知 subject 用除法猜测都失败。

`FUTURE`：`python -m caap.tools.build_manifests --config configs/protocols/data_roles.json --out runs/F07/manifests`；`python -m unittest -v tests/unit/test_data_manifest.py`。

### 产物、指标、成本与交接

输出角色 manifest、label map、ROI provenance、`role-audit.json`。科学键包含实际内容、split 与预处理，不仅数组下标；统计每角色图/掌/人/session 数。CPU 批处理可分域并行，汇总由单写者发布。任何泄漏/类头冲突先停止受影响域并修规则，修复使后代失效，不手改测试名单救指标。对应 `R2-3/R3-3`；交接 F08/F11/F15 角色 hash、允许交集和曝光限制。

## F08 · 真实七识别器训练与保存设施

### 目标、先决与责任路径

提供从合法识别器训练角色产生真实权重的可恢复设施，不把随机初始化用作领域识别器。依赖 F03/F07/F11；真实 GPU/数据缺失时只开发合成测试，真实训练保持阻塞。

落点：`src/caap/tools/train_recognizer.py`、`src/caap/models/training.py`、`configs/experiments/recognizers.json`、`tests/integration/test_recognizer_training.py`、`runs/F08/`、`reports/F08/`。F11 独占 adapter，本任务消费接口，不并行改归一化；架构有缺陷先通过接口提供者协调。

### 实施步骤

1. 为三域七模型登记实际 class/depth、input shape、头、loss、优化器、归一化、seed 和合法训练数据。
2. 只消费 F07 已冻结的 recognizer_fit/recognizer_val 及角色关系表，不自行从 recognizer_train 划分；历史训练可见性另记，禁止 attack_confirm/calibration/final_probe 参与拟合或选 epoch。
3. 编写短训回归，再实现按样本权重更新、尾批、scheduler、checkpoint 与固定 tie-break。
4. 保存网络/头/optimizer/scheduler/RNG/sampler/epoch，绑定外部预处理和代码 hash。
5. 经预算和独立审查后运行真实训练或导入合法参考权重，原始训练曲线和失败尝试全部保存。

### 正负验收与命令

正例：小型训练可恢复到同结果；真实权重有训练来源。负例：错头、缺恢复字段、test-as-val、假来源、训练成功但无曲线都不能过验收。

`FUTURE`：`python -m caap.tools.train_recognizer --config configs/experiments/recognizers.json --out runs/F08`；`python -m unittest -v tests/integration/test_recognizer_training.py`。前者是成本较高的真实训练命令，仅未来授权执行。

### 产物、指标、成本与交接

科学键包括 train/internal-val、架构、预处理、精度、microbatch、更新/选模规则和 seed。输出完整 latest/best、曲线和实际成本；指标为内部验证准确率及损失，不是攻击确认结果。GPU 默认每卡一 job，三域模型可在独立设备并行；训练 OOM 不擅自改 BN/精度/分辨率，需版本化决定。对应 `R2-3/R2-4/R3-3`；交接 F09 所有 checkpoint 与来源。

## F09 · 三域七模型真实权重与洁净性能验收

### 目标、先决与责任路径

**注册表就绪与真实模型有效是两个独立判定。** `development_done` 只要求验证器/夹具通过、三域七模型共 21 个基础条目均有身份、状态和来源说明；缺权重允许 `blocked/null`。F09 的开发完成不意味着 21 个模型全部有效，也不应阻止其他合法模型继续。

真实执行输入为 F08 权重或 F06 获准参考权重、该域 F07 角色及预设洁净标准；没有参考就明确是项目门槛，不冒称领域标准。每个 `dataset/model/weight_variant` 建立独立 `validate_recognizer` 科学节点。

落点：`src/caap/tools/validate_recognizers.py`、`tests/integration/test_real_model_gate.py`、`runs/F09/`、`reports/F09/`。注册表由控制器单写发布版本快照；模型和历史 gate 只读。

### 实施步骤

1. 校验完整 21 项注册表的结构、状态、唯一 entry_id 与必要来源字段；可以先用明确 synthetic 夹具验证工具，输出 `registry-ready.json` 开发证据。缺真实数据时不制造 model-entry 的有效性证明。
2. 为每个已具备合法资产的条目独立校验权重、架构/头、state keys、输入/归一化、许可与 F07 角色内容 hash；未具备的保留 `BLOCKED_ASSET/BLOCKED_PERMISSION`，不删除条目。
3. `validate_recognizer` 只在允许的开发验证角色计算 clean，保存逐样本预测、k/n、掌/人数、类别覆盖与预设门槛判定；与同资产参考比对，不降低标准求通过。
4. 每个有效条目发布不可变的 `model-entry` 内容指纹与 `model-gate.json`，绑定该次验证 run、权重、角色、预处理、验收规则和结果。没有有效 gate 的条目不能成为真实补丁训练/评估的合法父输入。
5. 全注册表快照 hash 用于 provenance；下游科学键只引用真正依赖的条目和 gate 内容 hash。注册表增加另一个域的条目不改变已有条目内容，不使无关结果失效。
6. 将完整条目状态、局部 gate 和缺口交给 F20；后者可冻结原始 full 范围并仅放行真实前提齐全的子图。跨域或跨模型任务必须同时满足所涉及两端及其配方前提，不能因单端有效就执行；F43 仍逐格对完整范围验收。

### 正负验收与命令

正例：验证器与 21 条状态清单通过即可 `registry-ready`，即使所有真实资产均缺失，也允许 F11 等合成开发继续，但不允许任何真实模型实验。

必须构造调度/科学键夹具：Tongji 某模型的合法角色、真实权重、clean gate、所需 feature/源配方/冻结与预算齐全，而 AISEC 缺资产；Tongji 对应训练/评估可领取，AISEC 及涉及 AISEC 的迁移保持阻塞，F43 full 为 INCOMPLETE。随后按预注册流程补齐 AISEC，只放行相关节点；Tongji 原科学键、已完成状态和重试计数不变。只给 `registry-ready` 而无局部 gate 的真实节点必须拒绝。

负例：随机 fallback、多余 key 被吞、归一化不一致、低 clean 伪称饱和、使用全注册表 hash 导致无关模型重训、把缺模型从 21 项清单中删除，均不得通过。

`FUTURE`：`python -m caap.tools.validate_recognizers --config configs/experiments/recognizers.json --role recognizer_val --out "$CAAP_NEW_RUN"`。控制器按具体条目生成解析配置、授权和新的 `runs/F09/<run_id>/`，只评该条目；汇总注册表不再次评分。验收使用 `python -m unittest -v tests/integration/test_real_model_gate.py`，其中夹具不冒充真实权重。

### 产物、指标、成本与交接

输出 `reports/F09/registry-ready.json`、`model-registry.json`、汇总索引 `clean-validation.json` 和 `model-gates/`；实际逐样本 clean 与 gate 由独立 run 产生，索引只引用，不覆盖旧产物。报告中的条目快照按 entry_id/hash 管理，时间戳和缺口显示变化不冒充科学输入变化。

F20 的开发依赖绑定 `registry-ready.json`；具体实验执行前提绑定自身 model-entry/gate、角色、feature、选择配方与分支冻结。GPU eval 只在对应授权设备运行；经逐样本等价验证可减 eval batch，不能改分辨率或删失败类。来源错误只阻塞受影响条目及依赖后代；全范围完成仍要求所有承诺条目有有效真实证据。对应 `R2-3/R3-3`。

## F10 · 辅助特征预训练与三种语义

### 目标、先决与责任路径

建立 `none/random_frozen/pretrained_frozen` 明确对照。依赖 F08 设施，训练与内部验证仅由 F07 的 patch_train 划出；缺真实预训权重不能把 random 更名。

落点：`src/caap/tools/pretrain_ms_dife.py`、`src/caap/models/feature_training.py`、`configs/experiments/feature_pretraining.json`、`tests/unit/test_feature_modes.py`、`runs/F10/`、`reports/F10/`。与 F08 共享设施只读，所需训练接口变更由 F08 所有者审核。

### 实施步骤

1. 冻结辅助结构、头、输入输出、参数量与初始化；只消费 F07 已发布的 msdife_fit/msdife_val，不自行拆分 patch_train，说明预训不等于已证明身份语义。
2. 先测试 mode 行为：none 零加载，random 固定 seed 后冻结，pretrained 必须严格加载。
3. 仅用 msdife_fit 拟合、msdife_val 选模，核验二者为 patch_train 不交子集，保存学习曲线、完整状态、最佳选择和成本。
4. 冻结网络参数但保留输入梯度；禁止读取 attack_dev/attack_select/attack_confirm/calibration/final_probe 的辅助预训信息。
5. 输出三种 mode 注册和互斥校验；未定义 joint/distillation 直接拒绝。

### 正负验收与命令

正例：none 不触发权重读取 sentinel；random 重现；pretrained 来源和梯度可核。负例：全部 train 预训包含 attack_val、冻结时切断输入梯度、缺教师仍启用蒸馏均失败。

`FUTURE`：`python -m caap.tools.pretrain_ms_dife --config configs/experiments/feature_pretraining.json --out runs/F10`；`python -m unittest -v tests/unit/test_feature_modes.py`。

### 产物、指标、成本与交接

输出 `feature-registry.json`、按 seed 权重及 train_feature 产物；键包含内部 manifest、结构、预处理、优化/选模及 seed。预训练成本与攻击训练分账，GPU 租约独占；合法低开发增益不触发追加训练。对应 `R1-2/R1-3/R2-4/R2-5`；交接 F20/F26 真实三模式及缺失影响，不保证特征必然有效。
