# 03 · 像素、几何、预算与判决正确性

**F11–F15 是未来必须真正修复并验证的 P0 基础，不属于本轮机械迁移已经完成的工作。**

遵守 `01-foundation.md` 的单写者、预算、失败与科学键规则。所有命令为 **FUTURE**；先建立合成数学夹具，不要求先拥有真实数据，真实验收由 F09/F20 接入。本组不访问最终测试。

## F11 · 模型适配、像素空间与输入梯度正确性

### 目标、先决与落点

唯一图像链为 raw `[0,1]` ROI → 合成 → 模型边界归一化 → logits/embedding。输入 F02 已验收源码/交接契约与 F07 的 `reports/F07/data-contract.json`（requires_stage=development_done），不等待真实三域 manifest。真实权重/数据未就绪仍可运行明确 synthetic 夹具，但不得把开发通过写成真实模型或实验通过。

落点：`src/caap/utils/model_adapter.py`、`src/caap/data/data.py`、`tests/unit/test_model_contract.py`、`test_pixel_space.py`、`reports/F11/`。本任务独占 adapter/data 修改；F08/F14/F15 只消费已发布接口。

### 实施步骤

1. 先断言原像素与模型输入分离，归一化只执行一次；枚举 none、aug_0.5、实际可支持的逐 ROI 标准化。
2. 保留 raw 图像；不能把标准化后数据贴补丁再 clamp 当原图，aug_org 无法安全实现则拒绝。
3. 实现严格结构/头/尺寸/通道/有限值检查，正式模式加载失败不能退回随机模型。
4. 冻结模型参数并设 eval，保留输入梯度；检查 running buffers 不变。
5. 为七模型离线小 batch 前向、反向、错维度和非法输入建立测试，输出实际类和支持能力。

### 正负验收与命令

正例：aug_0.5 往返恢复 raw，none 不变；模型前向与参考一致，patch 输入梯度 finite。负例：重复归一化、NaN、错通道/类头、全局 no_grad 切梯度均失败；外部整图变换前 alpha=0 区必须完全不变。

`FUTURE`：`python -m unittest -v tests/unit/test_model_contract.py tests/unit/test_pixel_space.py`。

### 产物、指标、成本与接力

输出接口和测试报告；关键 provenance 包含 actual class、checkpoint hash、训练归一化、代码与输入 shape。CPU 七模型测试可标 slow 但不能全跳过；不自动下载预训练。错误在夹具复现后最小修复，最多 2 次同根因循环；无法支持的接口明确阻塞。对应 `R1-3/R2-3/R2-4/R3-3`；交接 F08/F12/F15 输入输出签名、支持表与严格错误码。

## F12 · 正向几何、alpha 与固定部署能力隔离

### 目标、先决与落点

外部几何必须可解释，内部显式转逆采样，固定部署不能隐含读取当前图像来适配。输入 F11 raw ROI；模型资产缺失不影响标记图测试。

落点：`src/caap/attack/synthesizer.py`、`placement.py`、`tests/unit/test_geometry.py`、`test_composite.py`、`reports/F12/`。与 F14 的训练器边界分离，只有本任务修改 renderer。

### 实施步骤

1. 用单点、棋盘和非对称标记图断言 tx>0 向右、ty>0 向下、scale>1 放大以及固定旋转方向。
2. 固定 align_corners、插值、边界和中心；统一 placement，坐标不能在画布和 affine 中重复应用。
3. 验证预乘方案 `W(M*clip(cP+b))+(1-W(M))*x` 或等价方案；不能预乘后再乘 alpha。
4. 实现 D/G/P/GP 能力开关；非零位移/非单位光度 stub 证明禁用分支不泄漏。
5. deploy-fixed 只读纹理/mask/冻结 placement，不调用 ASIT/attention/标签定位；记录支持模式与 scale_policy。
6. 保存真实渲染位移、尺度、光度、支撑、裁剪和有限梯度诊断，旧几何仅显式版本转换。

### 正负验收与命令

正例：恒等与直接贴图一致，四角/出界方向正确，白纹理软边无额外暗边。负例：反向平移、双偏移、alpha 双乘、deploy 调用 sentinel 都失败；无 ASIT 直接请求条件模式报 `UNSUPPORTED_MODE`，队列预声明组合为 N/A。

`FUTURE`：`python -m unittest -v tests/unit/test_geometry.py tests/unit/test_composite.py`。

### 产物、指标、成本与接力

输出 `render-contract.json`、测试证据与 ASIT 五类头/六标量说明；c/b 是预测量和范围，不编全局最终常量。几何/alpha/scale 参数都进入科学键。CPU 可并行测试、共享 renderer 单写；非有限梯度停止，不以 nan_to_num 掩盖。对应 `R1-4/R2-1/R2-4/R3-1/H1`；交接 F13/F25 精确模式能力及几何版本。

## F13 · 完整形状面积可行性和三层支撑预算

### 目标、先决与落点

先判离散形状能否满足共同预算，再训练。输入 F12 渲染和候选 `B=784`、不超预算、2% 公差；不可行须在 F20 前改共同协议或阻塞，不能悄悄改形状。

落点：`src/caap/attack/geometry_budget.py`、`controls.py`、`tests/unit/test_mask_budget.py`、`configs/protocols/geometry.json`、`runs/F13/`、`reports/F13/`。几何规范由本任务写、F20 冻结引用。

### 实施步骤

1. 回归 legacy 十字 L40/w11 面积759、L30旧形状459；保留 patch→square 的显式兼容警告。
2. 定义完整方/圆/三角/十字离散栅格，确定性枚举：误差最小、面积较小、固定参数排序。
3. 对拟入主表形状逐项校验 `[0.98B,B]`，不能删角/随机挖孔仍叫完整方形。
4. 输出 binary_area、bbox_w/h、周长方法、alpha_sum、alpha>1e-6 支撑、abs(adv-clean)>1e-6 支撑、可见比例。
5. 创建同 mask/placement 的训练背景均值灰、白纸样和固定 seed 随机纹理；生成控制不要求 optimizer/训练 seed。
6. 主比较硬边/scale1，软边与 legacy759 独立条件；整图采集改变可见面积时测量，不反向缩回伪造过程。

### 正负验收与命令

正例：metadata 重建相同二值 mask，主预算所有形状可行。负例：`B=759,square,tolerance=.02,no_exceed=true` 返回 `BUDGET_INFEASIBLE`；空、越界、未知形状失败；不同 alpha/实际支撑不得仅用 mask.sum 冒充。

`FUTURE`：`python -m unittest -v tests/unit/test_mask_budget.py`；几何枚举由配置 dry-run 调用，不先训练试错。

### 产物、指标、成本与接力

输出 `feasibility.json`、geometry 配置、控制 artifact。科学键含完整栅格定义/阈值/插值/生成 seed；常数 train_seed=null。CPU 枚举有参数上界，控制可并行独立目录。不可行是协议状态，不自动松公差。对应 `R1-1/R1-7/R2-4/H2/H5`；交接 F14/F27/F39 可重建模板与未匹配描述量。

## F14 · 分类攻击目标、有效样本及更新语义

### 目标、先决与落点

修正分类损失与优化账本，不能只证明 loss 会下降。输入 F11 模型、F13 mask 和 F07 标签；不存在真实目标类时阻塞该目标。

落点：`src/caap/attack/attack.py`、`losses.py`、`classification.py`、`tests/unit/test_classification_objectives.py`、`test_training_updates.py`、`reports/F14/`。renderer/adapter 单写者仍为 F12/F11；F16 增目标须使用独立模块。

### 实施步骤

1. 固定未定向 loss 符号和定向 loss 定义，以可手算 logits 和有限差分检查梯度方向。
2. 分类有效集合取 clean-correct；定向另排 y=t，非法 t、无样本和越界标签直接失败。
3. 训练样本筛选与增广后动态有效性显式建模，零有效 batch 不伪造 optimizer step。
4. EOT K 次 loss 取均值；累积按实际有效样本权重，尾批必须更新，scheduler 与真实 step 对齐。
5. 冻结 recognizer 参数与 buffer；patch 仅合法支撑/[0,1] 内更新，保存实际 calls/draws/updates。

### 正负验收与命令

正例：手算梯度方向、不同有效数量尾批与无 BN 等效大 batch 梯度一致。负例：K 次求和、漏尾批、用测试选目标、scheduler 空步、训练改识别器参数均失败。有效 batch 相同不自动证明 microbatch/BN 等价。

`FUTURE`：`python -m unittest -v tests/unit/test_classification_objectives.py tests/unit/test_training_updates.py`。

### 产物、指标、成本与接力

输出 objective/update 合同及 budget tests；loss/优化器/EOT/选模/累积语义入科学键。CPU 小例，真实 pilot 留给 F23/F20。NaN 先核输入/分母，不置零继续；合法零 ASR 首个 checkpoint 仍保存，不追高重试。对应 `R2-3/R2-4/R3-3`；交接 F16/F17/F23 正确事件、权重与更新计数。

## F15 · 固定图库、干净校准与验证判决

### 目标、先决与落点

从干净 calibration 固定阈值，与 patch 独立；不能从测试 ROC 选部署工作点。输入 F07 gallery/calibration 与 F11 稳定 embedding；不支持 embedding 直接 `UNSUPPORTED_MODEL`，不拿 logits 兜底。

落点：`src/caap/attack/verification.py`、`src/caap/tools/calibrate.py`、`eval_verification.py`、`tests/unit/test_verification.py`、`test_calibration_isolation.py`、`configs/protocols/verification.json`、`reports/F15/`。模板/阈值由共享 calibrate 节点单写，各方法复用。

### 实施步骤

1. 冻结干净模板平均/L2 规则，校验 gallery 与 probe 不同图；掌为凭据，同人另一掌标记但不是 genuine。
2. 固定 genuine/impostor 对、去重、采样 seed、同人双掌排除策略和两端 cluster ID。
3. 定义 cosine `score>=tau` 接受；实现 tau_eer_cal 与经验 FMR 上限的最低满足阈值，冻结 tie 规则。
4. 包含全接受/全拒绝端点，用 decision_rule 与 tau=null 序列化；全拒绝唯一解标退化，不算有效工作点。
5. 输出阈值 hash 与校准分数；test EER 仅描述，低 FMR 支持度另列，缺样本不插值出极低尾部保证。
6. 以二维单位向量和读 test 即抛错 sentinel 测试校准，不读取 patch、test 分数或 attack_val 来选阈值。

### 正负验收与命令

正例：cosine 与手工接受计数一致，改测试分数阈值不动。负例：gallery=probe、重复 pair、零范数/NaN、无 impostor、自动合双掌、未知目标都确定失败或明确无效；不写 NaN/Infinity。

`FUTURE`：`python -m unittest -v tests/unit/test_verification.py tests/unit/test_calibration_isolation.py`。本任务只交付校准实现、配置和夹具证据；真实共享 calibrate 节点在 F20 冻结矩阵后于 F30 等消费任务的获准 run 目录实例化，不临时越过本任务 owned_paths 写结果。

### 产物、指标、成本与接力

开发交付 `calibration-tests.json` 与配置；真实共享校准产物由冻结矩阵单独实例化，不假装本组已完成。calibrate 键含模型/gallery/calibration/pair/阈值算法，不含 patch。FMR/FNMR/TAR 与分类 ASR 分离。CPU 数学测试，可在获准 GPU 只读评分；校准泄漏立即使阈值与后代失效。对应 `R2-3/R3-3/H3`；交接 F16/F17 工作点状态、两端身份与独立阈值引用。
