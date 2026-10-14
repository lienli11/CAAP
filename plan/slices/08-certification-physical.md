# 08 · H5 认证前提与真实物理设计

**F36/F38/F39 是开发或资产准备；F37/F40 必须在 F20 后完成自己的确认冻结。理论认证、经验攻击和真人采集不能相互替代。**

共同合同见 `01-foundation.md`。所有工具命令为 **FUTURE**，未取得真实许可/原实现/打印标定时保留缺口。本 full 计划包含 H5 和多因素物理研究，不沿用旧最小计划的“可选即可略去”。

## F36 · 认证防御原实现与证明前提开发核验

### 目标、先决与落点

先弄清原认证方法实际保证的集合，再设计范围内外试验。依赖F21/F19/F09；PatchCleanser/CertMask原代码、许可证或定理前提缺失时阻塞该方法，不能用自写滑窗标“原认证”。

落点：`src/caap/attack/defenses/certified.py`、`configs/protocols/certified_defenses.json`、`tests/unit/test_certification_preconditions.py`、`runs/F36/`、`reports/F36/`。原实现引用方式遵守license；wrapper单写，不改共享分类器或renderer。

### 实施步骤

1. 从全文与代码逐项锁定威胁集合、支撑/bbox界、mask覆盖族、预处理、base classifier与证书判决前提。
2. 绑定原commit/依赖/权重和参考例，复现原输出或明确差异；不凭摘要猜仅限方形等前提。
3. 用小尺寸可枚举图验证覆盖关系、证书状态和边界点，独立核验adapter是否破坏理论条件。
4. 在development数据检查clean、证书计算成本及adaptive攻击接口，只用于开发，不看确认分数。
5. 固定候选防御参数范围、理论适用检查器、原实现差异，发布 development-freeze 供 F37 认证分支使用；F20 只登记 H5 承诺与待决项，不等待这些资产。该分支开发进程不得访问前批 final 分数，独立确认仍待分支 freeze。

### 正负验收与命令

正例：枚举允许攻击支撑都被定理所需mask覆盖；参考例通过。负例：mask覆盖不足仍发证书、原实现未核却声称认证、改变预处理不更改前提hash、只测四角却称穷尽都失败。

`FUTURE`：`python -m unittest -v tests/unit/test_certification_preconditions.py`。原参考实现具体命令由F21核验后登记并经宿主授权；本文不捏造第三方CLI。

### 产物、指标、成本与接力

输出 `theorem-audit.json`、`development-freeze.json`和certified配置，区分coverage、certified accuracy与未获证比例。键包含原实现/定理版本、前提、mask族、base model、预处理和角色。CPU枚举/GPU开发各有预算，独立方法可分卡，原引用只读。未知前提停止，不退化成启发式却保留认证标签。对应 `R1-1/R2-4/R3-4/H5`；交接F20/F37可验证适用集合与成本。

## F37 · H5：范围内外认证覆盖与自适应攻击

### 目标、先决与落点

测量认证保证的适用范围与实际代价，不将超范围攻击成功叫击破定理。依赖F20/F36；确认数据必须独立于开发，缺确认集或核实原实现则保持阻塞。

落点：`configs/experiments/F37-h5.json`、`tests/integration/test_certification_scope.py`、`runs/F37/`、`reports/F37/`。防御实现只读；若发现实现缺陷，回到F36新版本并统一失效，不能本任务静默改。

### 实施步骤

1. 在development资料上核实预注册adaptive配方、支持集合及有限预算，冻结branch配置/实现/权重/阈值和独立确认manifest。
2. 解封前通过访问门禁；范围内/外按真实支撑包含关系和F36定理检查器分组，不只比二值面积。
3. 对不同bbox覆盖mask设定评价clean accuracy、获证覆盖、certified accuracy与时间/显存/调用数。
4. 在相同能力约束下评分旧补丁和针对防御重新优化的adaptive补丁，随机性与查询预算全部记录。
5. 范围内获证样本若出现破坏，保全输入/证书/支撑/日志，由独立审查核对原前提与实现；不能直接发“推翻认证”结论。
6. 全部范围外结果明确仅为适用边界，结合未获证样本及失败案例解释，不用经验低ASR替代证书。

### 正负验收与命令

正例：相同面积但超bbox的十字被判范围外，合法内支撑判范围内。负例：超范围成功标certification_broken、adaptive预算缺失、无证样本记为已获证失败、先看确认再改mask族均拒绝。

`FUTURE`：`python -m unittest -v tests/integration/test_certification_scope.py`；`python -m caap.tools.run_experiments --config configs/experiments/F37-h5.json --dry-run`。

### 产物、指标、成本与接力

输出 `branch-freeze.json`、`certification-scope.json`、逐样本证书、预测与支撑证明引用。键包括defense/theorem/mask族、攻击能力/支撑/adaptive优化/预算和confirm角色；同面积不等于同威胁集合。GPU/证书枚举成本预留，预算耗尽停止新派发。潜在范围内反例立即停止相关结论并复核；低ASR不重启搜索。对应 `R1-1/R2-4/H5`；交接F43严格范围、认证与经验分离表。

## F38 · 历史真实拍摄原图与逐次映射恢复

### 目标、先决与落点

找回多少就诚实报告多少，不从原稿400张或9/10比例制造记录。依赖F06/F07，输入实际获准原图、capture映射、打印物、模型与顺序；缺失字段unknown并列不可恢复原因。

落点：`src/caap/tools/recover_physical.py`、`tests/unit/test_physical_import.py`、`.local/physical/legacy/`、`reports/F38/`。原文件只读；私密subject对应表不进入公开报告。

### 实施步骤

1. 核对文件hash和可追溯原始数量，保存原稿声明与实际找回数量的差异，不强凑400。
2. 导入capture→匿名subject/palm/attempt/session/patch/model映射，保留缺时间顺序与未知模型版本。
3. 黑白/RGB、不同纸样和attack_mode/target分别绑定artifact；多物体合并只能标pool。
4. 检查重复/错配和是否存在clean_pair，不凭记忆填写success或排序。
5. 输出合法可复算子集与缺口；旧汇总表只作历史参考，未来F42与新采集分表。

### 正负验收与命令

正例：同capture跨模型仅是多个评价，不变多个受试者。负例：9/10反推逐次success、未知顺序按文件名猜、RGB/BW混同一物体、示例CSV标real都失败。

`FUTURE`：`python -m caap.tools.recover_physical --asset-ledger reports/F06/assets.json --out reports/F38`；`python -m unittest -v tests/unit/test_physical_import.py`。

### 产物、指标、成本与接力

输出 `legacy-capture-manifest.json`、`recovery-gaps.json`；键含真实原图/映射/原模型和导入规则，不包含人工补造成功事件。CPU/人工追溯设截止与预算；独立来源可只读并查，清单单写。无原图/许可停止相应导入并通知，不能下载陌生生物样本替换。对应 `R2-2/R3-2`；交接F39/F42可恢复范围及无法修复的证据限制。

## F39 · 打印尺度标定、固定 ROI 与真实评分链

### 目标、先决与落点

建立从冻结 raw 补丁到纸样和真实拍摄评分的链路。依赖 F13/F15/F19/F09 的开发契约，不依赖 F38 历史原图找回；合成夹具可开发导出/ROI/评分设施。真实标定另要求有效模型、设备、材料、许可和合法标定样本，未就绪只阻塞物理分支；不能阻塞 F20 数字主冻结。

落点：`src/caap/tools/export_print.py`、`score_captures.py`、`src/caap/data/physical_roi.py`、`configs/protocols/printing.json`、`tests/unit/test_print_export.py`、`tests/integration/test_capture_scoring.py`、`runs/F39/`、`reports/F39/`。ROI/打印配置本任务单写，F41不因照片效果回改。

### 实施步骤

1. 导出未归一化灰度纹理、mask、DPI/毫米尺寸和校验图，绑定print_variant、设备、材料、色域/灰阶处理及hash。
2. 用允许的非确认标定物测实际打印尺寸、尺度误差、灰阶响应与可制造性，不能把[0,1]/低TV当打印保证。
3. 固定原拍摄→ROI算法、参数和失败规则；不能在physical模式数字重定位或重绘已拍补丁。
4. 接入真实模型与固定图库/校准，success只由模型输出/协议导出；记录clean_pair及preprocess_id。
5. 测重复capture、尺度不符、ROI失败、缺clean和错模型错误路径；分别以 export_print/preprocess_capture/score_capture 类型登记。打印导出物使用 origin=exported_print，保留父学习/控制artifact的原origin和hash，不能标generate_control，也不证明已真实打印。输出部署链供 F40 物理分支冻结，不作为 F20 数字主冻结前置。

### 正负验收与命令

正例：导出尺寸和登记DPI可计算且实际标定达预设容差，真实评分重复可核。负例：把128ROI像素比例当真实掌面积、人工改success、失败照片删除、根据每次分数改ROI均拒绝。

`FUTURE`：`python -m unittest -v tests/unit/test_print_export.py tests/integration/test_capture_scoring.py`；`python -m caap.tools.export_print --config configs/protocols/printing.json --out runs/F39`；真实评分用 `python -m caap.tools.score_captures --config configs/protocols/printing.json --out runs/F39`，具体capture输入由该配置合法引用。

### 产物、指标、成本与接力

输出 `print-calibration.json`、`roi-scoring-contract.json`、打印导出物与失败清单。键含物理artifact、print_variant、设备/材料、ROI/model/gallery/threshold及capture来源；独立源图仍在.local。CPU/打印耗材/人工标定计费，实拍不能数字替代。无clean配对只描述攻击条件，不推净因果效应。对应 `R2-1/R2-2/R3-2/H4`；交接F20/F40物理能力、标定范围与固定评分版本。

## F40 · 许可、精度导向样本量与多因素采集设计

### 目标、先决与落点

让真人采集有可执行、有限且足以解释的问题设计，不把预算充足变无限人数。依赖F20/F39；真实许可、人员、设备和时间未就绪则BLOCKED_PERMISSION/ASSET，Agent不代办同意或开始采集。

落点：`configs/experiments/F40-physical-design.json`、`src/caap/tools/design_capture_schedule.py`、`tests/unit/test_capture_schedule.py`、`.local/consent/`、`reports/F40/`。许可原件私密保存；公开报告只存授权引用，日程冻结后只有经记录的偏离，不自动重排追高结果。

### 实施步骤

1. 定义主要物理终点、目标精度或功效、受试者簇数、重复相关性/脱落率假设；可用独立development可行性资料，不使用确认成绩反算样本量。
2. 至少洁净、同形常数遮挡、匹配固定十字EOT、reference、reference_no_ras五组；selected不同且要宣称其实拍能力则加第六组，纯ASIT消融另有预算。
3. 预设多设备、姿态、距离、光照、位置因子水平和单位，选择完整或预声明平衡分数设计；列别名/不可识别交互，不隐藏未覆盖组合。
4. 计算总尝试量=人×组×模式×条件单元×重复，并单列设备/打印物/会话扩展和无效采集储备；至少2设备的full跨设备问题不得缩成1设备后仍称完成。
5. 生成受试者内随机交错/平衡顺序、clean配对、操作者记录、休息退出和隐私管理；注册实际前k次ASR@1/5/20所需重复，不足20则预声明该终点不可估。
6. 核实许可/材料/人员与全部上限，冻结branch、print/model/ROI版本、分析计划和独立新采集确认日程，才交给真人执行。

### 正负验收与命令

正例：日程各组/设备/条件平衡，重复数与成本相符，顺序可重建。负例：照片数当独立人、遗漏no_ras、不同模块主方法冒充纯RaS消融、未授权开拍、看成绩追加人直到显著，都禁止。

`FUTURE`：`python -m caap.tools.design_capture_schedule --config configs/experiments/F40-physical-design.json --out reports/F40`；`python -m unittest -v tests/unit/test_capture_schedule.py`。

### 产物、指标、成本与接力

输出 `branch-freeze.json`、`power-precision-plan.json`、`capture-schedule.json`与许可引用。科学键含日程/随机seed、组/因子、print/ROI版本、分析与缺失规则；人数功效是事前假设，不是已观察效果。human主成本，采集可以按批准团队分设备执行但每capture唯一。预算/许可不足停止新采集并保留full缺口；不悄悄降范围。对应 `R2-2/R2-5/R3-2/H4`；交接F41清晰操作表、安全/退出规则和全部冻结hash。
