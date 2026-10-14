# CAAP 大修工作手册

T-IFS-26361-2026。决策日 2026-10-13，修订截止 2026-11-24。
本文只记录已经核对过的事实、已经落地的代码，以及建议写进回复信的文献。合成数据上的冒烟结果不能写入论文。

代码在 `CAAP_code/`，分支 `revision/tifs-major`，相对公开仓库 `6a805f8`。

## 1. 已经改了什么

公开仓库原先 `import models` 就会失败：`models/__init__.py` 引用了不存在的 `vgg19_bn` 和 `densenet`。这两行已删。

| 问题 | 现在的行为 | 位置 |
| --- | --- | --- |
| 补丁按测试集 ASR 挑选 | 默认从训练集按身份留出 `val_ratio=0.1` 做选择，测试集只在结束时评一次 | `data/data.py`，`attack/main.py` |
| 测试期 ASIT 读洁净 ROI | `evaluate(..., mode="deploy")` 把旋转、平移、缩放、增益、偏置全部固定，只做掌心贴放 | `attack/attack.py` |
| 数字评测不施加采集退化 | 训练结束后自动在 deploy 模式下再测 blur / gamma 1.8 / JPEG q=40，这三项都不在训练期 RaS 里 | `robustness_report` |
| 不报告分母和区间 | `metrics.json` 同时写 oracle ASR、deploy ASR、成功次数和 95% Wilson 区间 | `attack/stats.py` |
| MS-DIFE 随机冻结 | 不给 `--ms_dife_ckpt` 会打印警告；预训练入口是 `tools/pretrain_ms_dife.py` | `attack/attack.py` |
| `--patch_shape patch` 实际是三角形 | `patch` 映射为 `square` 并打印警告；未知形状直接报错 | `attack/utils.py` |
| 定向原型取自测试集 | 目标库改从训练集采集，并反归一化到与合成图相同的 [0,1] | `attack/attack.py` |
| 数据路径写死在服务器上 | `--data_path` 可指向任意 `.pth` | `data/data.py` |
| 物理口径只有“20 次里中 1 次” | `tools/physical_report.py` 输出 per-capture ASR、每人成功次数、ASR@1/5/20 | `tools/physical_report.py` |

`mode="oracle"` 保留原稿的测试期 ASIT，用来和 deploy 对照，不再作为主结论。

2026-10-14 在合成数据上跑通 1 个 epoch（CompNet，8 类，CPU）。验证集 16 张、测试集 40 张，与 8×10 训练 / 8×5 测试、`val_ratio=0.2` 一致。ASR 为 0 是因为只训了 1 轮，只说明链路没断。日志在 `caap_revision/smoke/`。

## 2. 在真实数据上怎么跑

数据 `.pth` 仍是原来的结构：`{"train": {"images", "labels"}, "test": {...}}`，图像为 PIL。

```bash
cd CAAP_code

# 1. 先预训练 MS-DIFE。论文 IV-E 声称它是预训练的，这一步不能省。
python tools/pretrain_ms_dife.py \
  --data_path /path/tongji_org_128.pth --num_class 600 \
  --epochs 20 --out ckpt/ms_dife_tongji.pth

# 2. 攻击。选择发生在验证集，测试集的 oracle / deploy / 退化表会写进 metrics.json。
python -m attack.main \
  --dataset tongji --data_path /path/tongji_org_128.pth \
  --net ccnet --model_ckpt ckpt/aug_0.5/tongji/ccnet.pth \
  --ms_dife_ckpt ckpt/ms_dife_tongji.pth \
  --attack_mode untargeted --epochs 50 --val_ratio 0.1 \
  --num_workers 4 --save_dir results/tongji_ccnet
```

主表应报告 `test_asr_deploy`，`test_asr_oracle` 放在附录，并写明二者的差别来自测试期是否允许读取洁净 ROI。基线必须用同一脚本、同一 checkpoint、同一次测试集调用重跑，否则 Table II 里通用 CNN 列的小分母问题还会在。

物理拍摄记成 CSV，列名为 `subject,attempt,success,condition,model`，`success` 为 0 或 1：

```bash
python tools/physical_report.py --csv captures.csv --out physical_report.json
```

尝试次数不足 20 时，脚本不会把截断后的数写成 ASR@20。格式示例见 `caap_revision/physical_example.csv`，里面的数是假的。

## 3. 论文里要改的判断

主结论改成：在固定一张印刷补丁、测试期不做逐样本数字调整时，攻击还剩多少成功率。oracle 列是上界，不是部署结果。

协议改成闭集、同身份。Tongji 的标准用法是 session1 训练、session2 测试，身份相同，见 Zhang 等 2017 的采集说明，以及 CCNet 官方训练列表。不要再写 subject-disjoint。AISEC 的类别数以 checkpoint 为准：代码注释写标签 1–49、分类头 50 类，正文写 52 掌，二者必须先对上再报洁净准确率。

物理实验的主指标是 per-capture ASR 加 Wilson 区间。ASR@20 可以保留，但要明确它是“允许 20 次重试”的操作点，不能单独作为成功率。

MS-DIFE 要么用上面的脚本预训练后重跑消融，要么正文改成“随机初始化并冻结的多尺度池化”，并把它从贡献列表里降级。后一种写法挡不住 R2-5。

## 4. 文献：写相关工作和回复信时用这些

下面卷期和 DOI 在 2026-10-14 核对过。标了“投稿前再核”的，不要直接抄进 `.bib`。

审稿人已经点名、必须正面写差异的：

- Yu Ran, Weijia Wang, Mingjie Li, Lin-Cheng Li, Yuan-Gen Wang, Jin Li. Cross-shaped adversarial patch attack. IEEE TCSVT, 34(4):2289–2303, 2024. doi:10.1109/TCSVT.2023.3307150. 十字拓扑的出处。本文的增量是掌纹纹理上的等面积比较和捕获链路，不是形状本身。
- Jianlong Jin 等. Unified adversarial augmentation for improving palmprint recognition. ICCV 2025, pp. 14141–14151. 同样用可微空间变换加识别器反馈。他们优化的是增广，使识别更稳；CAAP 优化的是补丁，使识别失败。回复 R1-2 时用这一对对照，不要把 ASIT 说成首个掌纹空间变换器。IEEE DOI 投稿前再核。
- Jianlong Jin 等. Diff-Palm: Realistic palmprint generation with polynomial creases and intra-class variation controllable diffusion models. CVPR 2025, pp. 26367–26376. doi:10.1109/CVPR52734.2025.02455.

R3 要求补的近两年掌纹识别：

- Ziyuan Yang, Yingyu Chen, Chengrui Gao, Andrew Beng Jin Teoh, Bob Zhang, Yi Zhang. FedPalm: A general federated learning framework for closed- and open-set palmprint verification. IEEE TIFS, 21:3093–3107, 2026. doi:10.1109/TIFS.2026.3671064. 闭集与开集的定义可直接用来改写 Section V-A。
- Le Su, Lunke Fei, Bob Zhang, Jie Wen, Yong Xu. Complete region of interest for unconstrained palmprint recognition. IEEE TIP, 33:3662–3675, 2024. doi:10.1109/TIP.2024.3407666.
- Huikai Shao, Yuchen Zou, Chengcheng Liu, Qiang Guo, Dexing Zhong. Learning to generalize unseen dataset for cross-dataset palmprint recognition. IEEE TIFS, 19:3788–3799, 2024. doi:10.1109/TIFS.2024.3371257.
- Huikai Shao, Pengxu Li, Dexing Zhong. Generating stylized features for single-source cross-dataset palmprint recognition with unseen target dataset. IEEE TIP, 33:4911–4922, 2024. DOI 检索到 10.1109/TIP.2024.3420000，投稿前再核。
- Yuqi Wang, Bob Zhang. A GAN-based data poisoning backdoor attack method for palmprint recognition CNNs. ICME 2025. doi:10.1109/ICME59968.2025.11209521. 掌纹上的另一种攻击。正文应说明 CAAP 不碰训练数据，威胁模型不同。

评测口径可以引用的：

- ISO/IEC 30107-3:2023. 全系统指标是 IAPAR 与 CAPRR。2017 版的 IAPMR 与 CAPNMR 已被替换，回复里不要混用两套缩写。
- Roberto Casula, Giulia Orrù, Stefano Marrone, Umberto Gagliardini, Gian Luca Marcialis, Carlo Sansone. Realistic fingerprint presentation attacks based on an adversarial approach. IEEE TIFS, 19:863–877, 2024. doi:10.1109/TIFS.2023.3327663. 同期刊里把数字对抗样本做成物理呈现物的流程。
- Alon Zolfi, Shai Avidan, Yuval Elovici, Asaf Shabtai. Adversarial mask: Real-world universal adversarial attack on face recognition models. ECML PKDD 2022, LNCS 13715, pp. 304–320. doi:10.1007/978-3-031-26409-2_19. 30 名受试者、多种对照物、同时报告数字与物理。
- Hui Wei 等. Physical adversarial attack meets computer vision: A decade survey. IEEE TPAMI, 46(12):9797–9817, 2024. doi:10.1109/TPAMI.2024.3430860.
- Xingxing Wei, Ying Guo, Jie Yu, Bo Zhang. Simultaneously optimizing perturbations and positions for black-box adversarial patch attacks. IEEE TPAMI, 45(7):9041–9054, 2023. doi:10.1109/TPAMI.2022.3231886. 位置与扰动联合优化的先例，用来收窄 ASIT 的新颖性表述。
- Steve T. K. Jan, Joseph Messou, Yen-Chen Lin, Jia-Bin Huang, Gang Wang. Connecting the digital and physical world: Improving the robustness of adversarial attacks. AAAI 2019. 用成对的数字图和实拍图学习打印–拍摄变换。RaS 若要升级，应走这条路，而不是再加一组手写的均匀抖动。页码投稿前再核。

2026 年的部署环境，相关工作里至少要点一句，否则“掌纹支付”的动机是过时的：

- 微信刷掌与 Amazon One 都是可见光掌纹加近红外静脉，不是单张灰度 ROI。印刷在皮肤上的补丁默认打不中静脉通道。正文应把威胁模型收成“可见光、接触式或手机 ROI 识别器”，并把双模态列为未覆盖，而不是暗示支付终端已被攻破。
- Jamal Seyedmohammadi 等. X-Palm: Paired multispectral-to-smartphone dataset for cross-domain palmprint authentication. NeurIPS 2025/2026 Evaluations and Datasets Track. arXiv:2606.08437. 103 人、6,006 张，同一身份同时有六光谱和 80 余款手机。12 个模型里包含 CompNet、CCNet、CO3Net、DINOv2、ArcFace、MagFace，协议分闭集跨域和开集跨域。这是比再跑一遍 Tongji 更有信息量的迁移测试，也直接回应“只有 10 个人”的批评。数据需签 EULA。
- Fei Peng, Yu Zhou, Guohui Long 等. AdvDiffusion: Adversarial patches generation for face recognition with high transferability in physical domain. IEEE TPAMI, 48(7):7485–7502, 2026. doi:10.1109/TPAMI.2026.3664842. 人脸侧 2026 年的物理补丁已经用扩散模型做可迁移图案。CAAP 不必改成扩散，但相关工作不能停在 2024 年的 CSPA。
- Xuntao Lyu 等. CertMask: Certifiable defense against adversarial patches via theoretically optimal mask coverage. AAAI 2026. doi:10.1609/aaai.v40i10.37716. 以及 USENIX Security 2026 的 APEX（定位后修复，号称对印刷补丁和光照变化有效）。防御实验若只留对抗训练，审稿人会认为没碰到当前的补丁防御。CertMask 假设补丁落在一个有界方块内，十字形长臂正好是它的边界情形，适合写成“现有可证明防御对细长支撑是否仍成立，留作后续”，不要在这 6 周里实现一个认证防御。

不要为了凑引用去改方法。上面 ICCV 2025 的 UAA 和 TPAMI 2023 的位置优化已经足够说明：新颖性应落在“掌纹上可部署的捕获链路和评测协议”，而不是三个模块名。
