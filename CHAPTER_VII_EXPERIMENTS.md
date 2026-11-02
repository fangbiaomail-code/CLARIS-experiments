# CLARIS 第七章：性能评估与比较——实验内容与执行清单

本文件根据论文参考范文第七章的组织方式，明确 CLARIS 性能评估章节需要完成的实验。整体沿用范文的论证顺序：**实验环境与基础运算 → 通信开销比较 → 计算开销比较 → 扩展性分析 → 安全属性比较**。

本章的核心目标是回答：CLARIS 在报告生成、身份认领和选择性关联方面需要多少计算与通信开销？这些开销如何随环规模和关联报告数量变化？与已有环签名、可认领环签名、可链接环签名及后量子方案相比，CLARIS 的功能和性能优势、代价分别是什么？

## A. 实验环境与基础运算测试（Experimental Environment）

### A.1 实验环境

记录并在论文中报告：

- CPU 型号、主频、物理核心数和逻辑核心数；
- 内存容量；
- 操作系统及版本；
- 编译器及版本；
- 密码学库/证明系统及版本；
- 编译优化参数；
- 实验代码的 Git commit。

所有性能结果都应能追溯到具体代码版本和实验环境。

### A.2 基础密码运算测试

参考范文先测量底层运算时间，再用于分析上层协议操作。CLARIS 应测量代码实际使用的基础运算，例如：

| 基础运算 | 需要记录的指标 |
|---|---|
| SHA3 哈希 | 单次运行时间 |
| AES 运算 | 单次运行时间 |
| VOLE 证明生成 | 单次运行时间 |
| VOLE 证明验证 | 单次运行时间 |
| 承诺生成 | 单次运行时间 |
| 承诺验证 | 单次运行时间 |
| 随机数生成 | 单次运行时间 |

**执行要求：**

1. 先检查 CLARIS 源码，确认实际调用了哪些运算；未使用的运算不纳入表格。
2. 每项基础运算至少进行 50 次测量。
3. 记录原始样本，并报告平均时间；建议同时报告中位数和标准差。
4. 明确计时单位，统一使用 ms 或 μs。

表格中的运算次数和运行时间必须来自实际代码与实验，不得预先假定。

## B. 通信开销比较（Communication Overhead Comparison）

参考范文比较公钥和密文大小。CLARIS 应根据自己的数据结构，比较公共参数、密钥、报告证明、Claim/Link 证明及完整证据包大小。

### B.1 需要测量的数据

| 数据对象 | 记录内容 |
|---|---|
| Public Parameters | 公共参数大小 |
| User Keys | 公钥、秘密密钥大小 |
| Ring Report | 原始环签名报告大小 |
| Claim Proof | 身份认领证明大小 |
| Link Proof | 单条关联证明大小 |
| Multi-report Link Proof | 多报告关联证明大小 |
| Complete Evidence Package | 报告、证明、引用、manifest 等完整传输大小 |

每项同时记录 bytes 和 KiB，并区分：

- Proof-only：仅证明本体；
- Certificate + references：证明、证书封装及报告引用；
- Complete evidence package：完整证据包。

### B.2 环规模与报告数量

测试环成员数量：

[
N\in\{16,64,256,1024\}
]

测试关联报告数量：

[
s\in\{2,3,5,10,20\}
]

重点回答：

1. 原始报告大小是否随环成员数量 N 增长；
2. Claim 证明大小是否随 N 变化；
3. 单条 Link edge proof 大小是否随 N 变化；
4. 多报告关联证明大小如何随 s 变化；
5. 完整证据包大小如何随 N 和 s 变化。

**本节应至少形成：**

- 表：不同方案的通信开销比较；
- 图：不同 N 下的报告/证明大小；
- 图：不同 s 下的关联证明及完整证据包大小。

注意：以上是待验证的实验问题，不应在运行实验前将预期关系写成实验结论。

## C. 计算开销比较（Computational Overhead Comparison）

这是第七章最重要的部分之一。参考范文的做法，先统计底层运算开销，再分析每个协议阶段的计算量，并与已有方案比较。

### C.1 CLARIS 各阶段运行时间

必须分别测量：

| 操作 | 测量内容 |
|---|---|
| Report Generation | 报告生成时间 |
| Report Verification | 原始报告验证时间 |
| Claim Generation | 认领证明生成时间 |
| Claim Verification | 认领证明验证时间 |
| Link Generation | 关联证明生成时间 |
| Link Verification | 关联证明验证时间 |

Link Verification 还应拆分为：

- Link core verification：仅验证额外关联证明；
- Link full verification：包含相关原始报告验证的完整流程。

Claim Verification 同样应区分仅验证 Claim 证明和包含原始报告验证的完整流程。

### C.2 基础运算次数统计

仿照范文的计算开销表，逐项统计每个操作调用的 SHA3、AES、VOLE prove、VOLE verify、承诺和其他实际运算次数。

| 协议操作 | SHA3 | AES | VOLE Prove | VOLE Verify | 其他 |
|---|---:|---:|---:|---:|---:|
| Report Generation | 从代码统计 | 从代码统计 | 从代码统计 | — | 从代码统计 |
| Report Verification | 从代码统计 | 从代码统计 | — | 从代码统计 | 从代码统计 |
| Claim Generation | 从代码统计 | 从代码统计 | 从代码统计 | — | 从代码统计 |
| Claim Verification | 从代码统计 | 从代码统计 | — | 从代码统计 | 从代码统计 |
| Link Generation | 从代码统计 | 从代码统计 | 从代码统计 | — | 从代码统计 |
| Link Verification | 从代码统计 | 从代码统计 | — | 从代码统计 | 从代码统计 |

这里的“从代码统计”是待完成工作，不是已经得到的运算次数。应通过代码调用路径、计数器或 profiler 核验。

### C.3 运行时间分析

依据基础运算基准和上层操作的实际计时，给出各阶段开销。若使用运算次数乘以单次运算时间的方式计算，应明确公式，并与端到端实测结果分开报告。

可报告：

[
T_{\mathrm{Total}} =
T_{\mathrm{Report}}+
T_{\mathrm{Claim}}+
T_{\mathrm{Link}}.
]

该总时间只代表论文明确界定的工作流程。应说明是否包含原始报告验证、数据传输、序列化和缓存处理，避免重复计时或漏计。

### C.4 与已有方案的计算开销比较

优先研究以下工作：

| 对比对象 | 主要比较方向 |
|---|---|
| Park–Sealfon | 可认领环签名及 Claim 机制开销 |
| Fiore et al. | 用户控制可链接环签名/关联机制开销 |
| Chiang et al. | AES/VOLE 环签名的报告生成和验证开销 |
| DualRing-PRF | 后量子可链接环签名方向 |
| SPRING | 格基环签名及问责机制 |
| TalosLogic | VOLE 环签名工程实现参考 |

对比时应遵循：

1. 优先在同一机器、相同编译环境和可匹配参数下重跑公开实现。
2. 至少对两个最相关方案进行深入的功能和构造比较。
3. 尽可能对 1–2 个外部实现完成 matched benchmark。
4. 某方案不支持 Claim 或 Link 时标记 N/A，不得人为添加操作或估算耗时。
5. 无法本机复现的方案，可引用原论文报告值，但必须单独标注硬件、参数和数据来源。
6. 不得将不同硬件、不同安全级别的论文数据直接混合成速度排名，也不得据此计算不公平的性能提升百分比。

本节至少形成一张计算开销比较表，并在可比条件下生成报告生成/验证、认领和关联的时间对比图。

## D. 扩展性评估（Scalability Evaluation）

扩展性实验使用前述参数：

[
N\in\{16,64,256,1024\},\qquad
s\in\{2,3,5,10,20\}.
]

分别考察：

- Report Generation / Verification 随 N 的变化；
- Claim Generation / Verification 随 N 的变化；
- Link Generation / Verification 随 N、s 的变化；
- Proof、certificate 和完整证据包大小随 N、s 的变化；
- Peak RSS（峰值内存）随 N、s 的变化。

每组配置至少进行 1 次 warm-up 和 30 次有效测量，保存每次原始耗时。报告 mean、median、standard deviation、p95 和样本数。

对无法运行的配置，保留配置及失败原因，不得静默删除。

### D.1 Anchor 与 Bridge 消融实验

在相同硬件、参数、报告集合和编译选项下比较 Anchor 与 Bridge：

- 证明生成时间；
- core verification 时间；
- full verification 时间；
- 证明大小；
- 峰值内存。

建议优先使用 N ∈ {64, 1024}、s ∈ {2, 3, 5}。消融实验用于分析 CLARIS 内部设计选择的影响，不能替代外部方案比较。

## E. 安全属性与功能比较（Security and Property Comparison）

参考范文的安全属性比较表，CLARIS 应与已有工作比较：

| 属性 | 比较内容 |
|---|---|
| Post-Quantum Security | 是否有后量子安全论证 |
| Ring Anonymity | 是否提供环匿名性 |
| Unforgeability | 是否满足不可伪造性 |
| Claimability | 是否支持事后身份认领 |
| Linkability | 是否支持可链接性 |
| Selective Association | 是否支持选择性关联 |
| Accountability | 是否支持问责 |

可使用 ✓、✗、Conditional、N/A。每项判断都应依据对应论文的安全定义、定理或算法；条件性结论必须说明条件。不能仅凭方案使用 AES、VOLE 或格就直接认定其满足某项安全属性。

功能不同的方案应明确指出其功能边界。例如，Claimability、user-controlled linkability、public linkability 和 selective post-hoc association 并非同一概念。

## F. 第七章需要形成的最终结果

完成后，至少应有以下表格和图：

### 表格

1. 实验环境与软件配置；
2. 基础密码运算时间；
3. CLARIS 各阶段的基础运算次数；
4. CLARIS 各阶段的运行时间；
5. 通信开销比较；
6. 计算开销比较；
7. Anchor 与 Bridge 消融比较；
8. 已有方案安全属性与功能比较。

### 图

1. Report Generation 时间随 N 变化；
2. Report Verification 时间随 N 变化；
3. Claim 生成和验证时间；
4. Link Generation 时间随 s 变化；
5. Link core / full verification 随 N、s 变化；
6. 证明大小随 N、s 变化；
7. 完整证据包大小随 N、s 变化；
8. Peak RSS 随 N、s 变化；
9. Anchor 与 Bridge 的时间和大小比较；
10. 与可公平复现的外部方案进行性能比较。

图表必须标注单位、参数、样本数和数据来源。

## G. 实验完成判定

- [ ] 实验环境记录完整；
- [ ] 实际使用的基础密码运算完成基准测试；
- [ ] Report、Claim、Link 各阶段生成和验证时间均已测量；
- [ ] 基础运算调用次数已从代码核验；
- [ ] 公共参数、密钥、报告、Claim、Link 和完整证据包大小已统计；
- [ ] N 与 s 的扩展性实验已完成，未完成项有明确说明；
- [ ] Anchor 与 Bridge 消融实验已完成；
- [ ] Peak RSS 已测量；
- [ ] 至少两个相关外部方案已完成深入功能/构造比较；
- [ ] 尽可能完成 1–2 个外部实现的 matched benchmark；
- [ ] 安全属性比较表中的判断均有文献依据；
- [ ] 原始样本、汇总脚本、图表和环境信息均已归档；
- [ ] 论文中的每个性能数字均可追溯到实测数据、计算公式或明确文献来源。

**原则：** 第七章应按照参考范文的方式，以基础运算、计算开销、通信开销和方案间比较构成证据链。扩展性和消融实验用于进一步解释设计特性。宁可标记某项数据尚未测量或 N/A，也不能用估算值冒充实测值。
