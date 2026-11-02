# CLARIS 实验计划与完成标准

本文档明确 CLARIS 第七章需要完成的实验范围、实验矩阵、外部方案比较要求、数据记录规范和最终交付物。实验目标不只是测出 CLARIS 自身的运行时间，而是回答：

1. CLARIS 的报告生成、认领和关联分别需要多少计算与通信开销？
2. 这些开销如何随环成员数量和待关联报告数量变化？
3. Anchor 与 Bridge 两种设计分别带来什么性能影响？
4. 与已有可认领环签名、用户控制可链接环签名及后量子环签名方案相比，CLARIS 的功能差异和性能代价是什么？

> **数据真实性要求**
> - **Measured（实测）**：由当前代码实际运行得到，必须保留原始样本、实验环境和代码 commit。
> - **Calculated（计算）**：由明确公式和输入参数推导得到。
> - **Reported（文献报告）**：摘录自已有论文，必须注明来源、参数和原论文实验环境。
> - **Not measured / N/A（未测/不适用）**：没有实现、没有测量或方案不支持该操作。不得用估计值填充，也不得把 N/A 写成 0。
>
> 不同机器、不同安全参数或不同实现环境下的文献数据，不得与本机实测结果混在一起，直接据此宣称性能领先。

---

## 1. 最终需要交付什么

实验完成时，仓库应包含以下内容：

- [ ] 可编译、可运行的 CLARIS 实验代码，以及必要的补丁和依赖版本说明。
- [ ] 可重复执行的构建、功能测试和 benchmark 脚本。
- [ ] 实验配置文件和参数说明。
- [ ] 每次运行的原始计时样本（CSV/JSON），不能只保留平均值。
- [ ] 自动生成的汇总表、统计结果和论文用图（PDF/SVG/PNG）。
- [ ] 实验环境记录：CPU、核心数、内存、操作系统、编译器、依赖版本、编译选项和 Git commit。
- [ ] 与已有方案的功能/安全属性比较表。
- [ ] 在可比条件下完成的外部方案性能比较；无法公平比较的方案应说明原因。
- [ ] 一份结果说明，区分实测、理论计算和文献报告。

建议目录：

```text
CLARIS-experiments/
├── README.md
├── EXPERIMENT_PLAN.md
├── docs/
│   ├── REPRODUCIBILITY.md
│   ├── BASELINES.md
│   └── RESULTS_NOTES.md
├── src/                       # CLARIS 实现及必要补丁
├── third_party/               # 上游依赖的固定版本和获取说明
├── configs/                   # 参数及 benchmark 配置
├── scripts/                   # build / test / benchmark / plot
├── tests/
│   ├── functional/
│   └── adversarial/
└── benchmarks/
    ├── raw/                   # 原始数据，不覆盖
    ├── processed/             # 汇总数据
    └── figures/               # 论文图表
```

若上游代码受许可证或体积限制，不直接复制全部源码；应记录仓库地址、固定 commit、补丁和获取步骤。

---

## 2. CLARIS 必须完成的核心实验

### 2.1 正确性与功能测试

需要覆盖：

- 密钥/注册表生成；
- 环签名报告生成；
- 原始报告验证；
- 单条报告 Claim 生成与验证；
- 两条及多条报告 Link 生成与验证；
- 错误报告、错误身份、错误上下文、错误报告引用和混合签名者报告的拒绝；
- 验证端不需要加载签名私钥；
- 编码、解析及报告引用的一致性检查。

除正常输入外，还要构造负向测试：修改公开输入字段、替换报告引用、混用不同上下文或提交错误证明，验证程序是否拒绝。不要只用简单的字节篡改代替完整的语句级负向测试。

**完成标准：** 从干净构建可运行测试命令；记录通过/失败用例数、失败原因和对应代码 commit。测试通过仅说明实现行为符合测试预期，不等同于密码学安全证明。

### 2.2 证明大小与通信开销

分别测量：

1. 原始环报告完整编码大小；
2. 单条 Claim 证明和证书大小；
3. 单条 Link edge 证明大小；
4. 多报告 Link 的证明核心大小；
5. Link wrapper、报告引用和 manifest 的编码大小；
6. 完整证据包大小（原始报告、manifest、应用消息/附件，以及适用时的 Claim/Link 证书）。

每个对象同时记录 bytes 和 KiB，并明确区分：

- **Proof-only**：仅证明本体；
- **Certificate + references**：证明、证书封装和报告引用；
- **Complete evidence package**：完整传输证据包。

实际序列化长度必须通过程序测量；公式推算值单独标为 Calculated。

**已有稿件中记录、需要用当前代码复核的参考值（不是本次新测结果）：**

- 普通 Claim / 单条 Link edge proof：49,208 bytes；
- 三报告 Link 的两条 edge proof 合计：98,416 bytes；
- 稿件报告上述大小在 N=64 和 N=1024 时相同。

复跑后若结果不同，保留差异并分析参数、编码或实现变化，不要为了符合旧数值而修改实验结果。

### 2.3 计算时间

不要只给一个总运行时间。必须分别计时：

| 操作 | 记录内容 |
|---|---|
| KeyGen / registry setup | 密钥或注册表生成时间 |
| Report signing | 单份报告生成时间 |
| Report verification | 单份原始报告验证时间 |
| Claim generation | 认领证明生成时间 |
| Claim verification | 仅验证 Claim 证明的时间 |
| Claim full verification | 包含原始报告验证的完整时间 |
| Link generation | 关联证明生成时间 |
| Link core verification | 仅验证额外 Link proof 的时间 |
| Link full verification | 包含全部原始报告验证的完整时间 |

每个配置至少进行 1 次 warm-up 和 30 次有效测量。保存每次原始耗时，并报告：

- 样本数；
- mean；
- median；
- standard deviation；
- p95。

使用单调时钟计时，计时区间不应包含编译、依赖下载等无关操作。

对于 full verification，分别测试：

- **Cold path**：不复用原始报告验证结果；
- **Cached path**：原始报告和 manifest 已验证并缓存。

需要说明缓存键如何绑定报告标识、manifest 和参数集，避免把不同语句或报告的验证结果错误复用。

### 2.4 可扩展性实验矩阵

环成员数量：

[
N \in \{16, 64, 256, 1024\}
]

选择报告数量：

[
s \in \{2, 3, 5, 10, 20\}
]

对每个支持的组合测量：

- 报告生成时间；
- 原始报告验证时间；
- Link 生成时间；
- Link core verification 时间；
- Link full verification 时间；
- proof bytes；
- certificate bytes；
- complete evidence package bytes；
- 峰值内存（peak RSS，MiB）。

每个配置至少 1 次 warm-up + 30 次有效测量。若某个组合不支持或因资源限制无法完成，记录配置、错误信息和机器状态，不得静默删掉该配置。

需要通过数据检验、而不是预先假定以下关系：

- 普通 Claim / 单条 Link edge 的额外证明大小是否与 N 无关；
- Anchor 结构的额外证明大小是否随 s 按 edge 数增长；
- full verification 时间如何随 N、s 变化；
- 缓存对 full verification 时间的影响。

### 2.5 Anchor 与 Bridge 消融实验

在相同报告集合、相同证明系统、相同参数、相同编译选项和相同硬件下，对 Anchor 与 Bridge 进行 matched ablation。

至少测量：

- 证明生成时间；
- core verification 时间；
- full verification 时间；
- proof bytes；
- peak RSS。

建议配置：

[
N \in \{64,1024\},\qquad s \in \{2,3,5\}
]

每格至少 1 次 warm-up + 30 次有效测量。

如果复现稿件中已有的三次测量旧结果，应单独标注为历史数据，不能与新的 30 次样本混合统计。Anchor/Bridge 消融用于隔离内部设计选择的影响，不应被描述为完整外部方案比较。

---

## 3. 与已有方案比较：第七章必须完成的部分

第七章必须回答 CLARIS 相比已有方案改进了什么。不能只展示 CLARIS 自身的柱状图，也不能把功能、参数、安全级别和硬件完全不同的论文数据拼在一起排名。

### 3.1 优先研究的对比对象

| 方案/方向 | 主要比较价值 | 比较要求 |
|---|---|---|
| Park–Sealfon claimability transformation | 通用可认领机制 | 核对其 Claim 接口、密钥/状态需求，并尽可能在相同基础环签名上实例化 |
| Fiore et al. RS-UCL / RS-UCAL / AKRS compiler | 用户控制的关联机制 | 区分 UCL 与 UCAL 的功能，优先做相同底层环签名的 matched comparison |
| Chiang et al. AES/VOLE threshold ring signatures | 与 CLARIS 接近的 AES/VOLE 环签名底层路线 | 比较原始报告生成/验证和底层证明开销；不能把原生 tag/link 直接等同于事后选择性关联 |
| DualRing-PRF | 对称密码路线的后量子环签名/可链接方向 | 先做功能与构造比较；取得可运行实现并匹配安全参数后再测性能 |
| SPRING | 格基环签名及指定开启者问责 | 做功能和构造比较；没有统一平台实现时，不做不公平的耗时排名 |
| TalosLogic | VOLE 环签名工程实现参考 | 核实实际版本、实现功能和复现条件后再决定是否纳入性能表 |

这些方案的功能并不完全相同。Claimability、user-controlled linkability、public linkability 和 selective post-hoc association 不能当成同一个功能。

### 3.2 外部方案比较分两层完成

**A. Matched implementation comparison（优先）**

在同一台机器、相同编译器和尽可能一致的安全参数下，对兼容方案进行本机重跑。优先顺序：

1. CLARIS 当前实现；
2. Park–Sealfon claimability transformation；
3. Fiore AKRS / user-controlled linking compiler；
4. Chiang AES/VOLE 基础环报告路径。

对双方均支持的操作，比较：

- 报告生成；
- 报告验证；
- Claim 生成/验证；
- Link 生成/验证；
- 证明大小和完整证据包大小。

若某方案原生不支持某项操作，标记 N/A，并在功能表解释，不能自行给它补一个虚构耗时。

**B. Literature-reported comparison（补充）**

可以引用其他论文公布的运行时间和证明大小，但必须注明：

- 原论文引用；
- 原论文硬件和软件环境；
- 安全参数；
- 环规模和消息长度；
- 测量方法；
- 该数值属于文献报告而非本机实测。

文献报告数据不得与本机实测数据混成一个排行榜，也不能据此直接计算 CLARIS 的速度提升百分比。

**完成标准：**

- 至少完成 2 个最相关方案的细粒度功能/构造比较；
- 尽可能完成 1–2 个外部实现的 matched benchmark；
- 对无法运行或不具可比性的方案，保留文献比较并明确限制；
- 不得伪造缺失数据或用理论估计冒充实测。

### 3.3 功能与安全属性比较表

建议至少比较：

- Post-quantum security；
- Ring anonymity；
- Claimability / identity opening；
- User-controlled linkability；
- Public linkability；
- Selective post-hoc association；
- Separate linking/opening secret；
- 是否需要保留签名随机数或用户状态；
- 额外披露证明是否依赖环成员数量 N；
- 证明大小是否随被选报告数 s 增长；
- 注册表或可信初始化假设。

采用 ✓、✗、Conditional、N/A 四种状态。每个判断应能追溯到论文定义、定理或具体算法；条件性结论要写明条件，不能只标 ✓。

---

## 4. 实验环境与数据记录规范

每次正式 benchmark 自动记录：

- timestamp；
- repository commit SHA；
- working tree 是否 clean；
- CPU 型号、物理/逻辑核心数；
- RAM；
- OS/kernel；
- compiler 及版本；
- 编译 flags；
- 依赖版本和上游 commit；
- 参数配置；
- warm-up 次数和有效重复次数；
- 每次原始耗时；
- peak RSS；
- 输出对象字节数。

建议每个配置独立进程运行，或明确记录进程复用策略。不同实现的测量顺序应交替或随机化，以减少运行顺序、温度和 CPU 频率变化带来的偏差。异常值要保留并解释，不得只删除不利样本。

推荐原始 CSV 字段：

```text
timestamp,git_commit,build_id,operation,variant,N,s,run_index,warmup,elapsed_ms,proof_bytes,certificate_bytes,package_bytes,peak_rss_bytes,success,cpu,os,compiler,flags,notes
```

---

## 5. 第七章应生成的图表和表格

至少完成：

1. Report signing time vs. N；
2. Report verification time vs. N；
3. Claim generation / verification time；
4. Link generation time vs. s；
5. Link core verification vs. (N, s)；
6. Link full verification vs. (N, s)，cold 与 cached 分开；
7. Proof / certificate / complete package size vs. s；
8. Peak memory vs. N、s；
9. Anchor vs. Bridge 的时间和证明大小对比；
10. 外部方案 matched comparison（仅展示真正可比的数据）。

此外必须提供：

- 一张外部方案功能与安全属性比较表；
- 一张通信开销比较表；
- 一张计算开销比较表；
- 一张实验参数和环境表。

所有图表注明单位、参数、样本数和数据来源。差异跨度较大时可以使用对数轴，但应在图注中明确说明。

---

## 6. 论文第七章的完成判定

只有同时满足以下条件，才可认为性能评估章节的实验主体完成：

- [ ] CLARIS 功能测试全部有记录，正向和负向用例均覆盖；
- [ ] 报告、Claim、Link 的生成和验证时间分别测量；
- [ ] N 与 s 的扩展性矩阵已运行，未完成的格子有明确原因；
- [ ] proof、certificate 和完整证据包大小分别统计；
- [ ] peak RSS 已测量；
- [ ] Anchor/Bridge 消融实验完成；
- [ ] 至少 2 个相关外部方案完成功能与构造层面的逐项比较；
- [ ] 尽可能完成 1–2 个可公平复现的外部实现性能比较；
- [ ] 原始样本、汇总脚本、图表和环境信息均已归档；
- [ ] 论文中的每个性能数字都能追溯到原始 CSV、计算公式或明确的文献来源；
- [ ] 结论没有将不同安全级别、不同机器或不同功能的方案不公平地比较。

**最重要的原则：宁可明确写出某项实验尚未测量，也不要用推测数字填表。第七章的说服力来自可复现的对比证据，而不是图表数量。**
