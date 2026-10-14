# 历史材料：只读，不是当前运行入口

`legacy/migration.json` 记录重构前提交、来源仓库、原路径、新路径、冻结文件 SHA-256 和历史产物适用边界。

`legacy/upstream/` 保留原 README、Linux 环境导出、Shell 示例和忽略规则；这里的命令不是新布局的执行指南。

`legacy/caap_revision/` 保留历史合成数据、模型、smoke、示例 CSV 与旧工作手册。目录名含 `tongji` 不代表真实 Tongji 实验；旧 `config.json` 是输出记录，不是新版配置。

新运行必须写到 `runs/`。原始文件不能为了修路径、改指标或补 seed 而覆写；转换和重分析新建派生产物，引用来源 hash。

原完整上游 Git 工作树本机保存在 `.local/upstream/CAAP_code/`，不会出现在远程 clone。远端历史仍可通过根仓库提交 `278e371` 核对；不要依赖本机备份才能运行新包或测试。
