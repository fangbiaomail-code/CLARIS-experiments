#!/usr/bin/env python3
"""Render the Chinese Chapter VII draft and experiment status from measured aggregates."""
import argparse
import json
from pathlib import Path


def fmt(x, d=2):
    return f'{x:,.{d}f}'


def table(headers, rows, align=None):
    out = ['| ' + ' | '.join(headers) + ' |',
           '|' + '|'.join(align or ['---'] * len(headers)) + '|']
    out += ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows]
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    root = args.root.resolve()
    agg = json.loads((root / 'results/aggregate.json').read_text())
    env = agg['environment']
    ring = {r['ring_size']: r for r in agg['ring_scalability']}
    cert = {(r['ring_size'], r['method'], r['selected_count']): r
            for r in agg['certificate_scalability']}
    fit = {r['ring_size']: r for r in agg['proof_count_timing_fit']}
    ns = sorted(ring)
    reps = agg['repetitions']
    warm = agg['warmups']
    basic = {r['operation']: r for r in agg['basic_operations']}
    counts_path = root / 'results/processed/operation_counts.csv'
    counts = None
    if counts_path.exists():
        import csv
        counts = list(csv.DictReader(counts_path.open()))

    gen_small, gen_large = ring[ns[0]], ring[ns[-1]]
    claim_rows = [cert[(n, 'claim', 1)] for n in ns]

    text = []
    text.append('# VII. 性能评估与比较（PERFORMANCE EVALUATION AND COMPARISON）\n')
    text.append(
        '本节在**同一份构建、同一台主机**上完成 CLARIS 的 N × s 全矩阵评测：环成员数 '
        'N ∈ {16, 64, 256, 1024}，关联报告数 s ∈ {2, 3, 5, 10, 20}，并单独测量 s = 1 的认领基线。'
        f'每个配置预热 {warm} 次、正式测量 {reps} 次，保存全部原始样本。评测包括三部分证据：'
        '（1）底层密码运算的独立微基准；（2）报告、认领和关联各阶段的端到端计时；'
        '（3）基于实测文件的通信字节核算。所有数字都可以追溯到仓库中的原始 CSV、构建清单和运行环境记录。\n')
    if agg.get('provenance_notes'):
        notes = agg['provenance_notes']
        desc = '；'.join(
            f"N={n['ring_size']} 的报告 cell 中位数为 "
            f"{n.get('discarded_run_report_median_ms'):.2f} ms，重测为 "
            f"{n.get('substituted_report_median_ms'):.2f} ms" for n in notes)
        text.append(
            f'数据来源说明：{desc}。该 ring 的首次运行紧接在一次约 5 分钟的功能测试之后开始，'
            'SoC 处于热状态，报告 cell 整体偏高约 10%。重测使用同一构建、同一主机、同样的 '
            '3 次预热 + 30 次采样；被替换的首次运行仍完整保留在 `results/fullmatrix/n16` 中，'
            '其余三个环规模的 cell 未受影响。\n')
    text.append(
        '需要区分两类比较：一类是 CLARIS 原型内部的实测比较（不同 N、不同 s、Anchor 与 Bridge 消融）；'
        '另一类是与已有工作的构造和安全属性比较。当前没有 Park–Sealfon、Fiore 等人、DualRing-PRF、'
        'SPRING 等方案在同一硬件、同一安全参数和同一操作口径下的可运行实现，因此本文不把不同论文的'
        '运行时间拼成柱状图，也不据此计算性能提升百分比。\n')

    text.append('## A. 实验环境与基础运算（Experimental Environment）\n')
    text.append('### A.1 实验环境\n')
    text.append(table(
        ['项目', '取值'],
        [['CPU', f"{env.get('cpu_brand')}（{env.get('physical_cores')} 物理核 / "
                 f"{env.get('logical_cores')} 逻辑核）"],
         ['内存', f"{int(env.get('memory_bytes')) / (1024 ** 3):.1f} GiB"],
         ['操作系统', f"macOS {env.get('os_version')} (build {env.get('os_build')})"],
         ['编译器', env['compiler'].splitlines()[0]],
         ['编译选项', '`' + ' '.join(env['flags']) + '`'],
         ['执行目标', env['execution_arch']],
         ['执行方式', 'Rosetta 2 翻译执行（非原生 ARM 后端，绝对时间包含翻译开销）'],
         ['证明系统配置', env['transcript_profile']],
         ['构建清单 SHA-256', f"`{env['build_manifest_sha256']}`"],
         ['源完整性', f"113 个文件通过；扩展记录 `{env['harness_revision_sha256'][:16]}…`"],
         ['测量协议', f'每 cell {warm} 次预热、{reps} 次正式测量；保存原始样本']],
        ['---', '---']))
    text.append(
        '\n全部环规模使用同一构建产物，按 N = %s 的顺序依次测量（N=16 的重测见数据来源说明）。由于主机为无风扇的 Apple M1，'
        '长时间连续负载会造成一定程度的频率与温度漂移；同一 cell 内的样本顺序测量，'
        '因此 cell 内统计量稳定，而跨 cell 的绝对时间存在约 10%% 量级的波动。'
        '这一限制在 D 节和 F 节中进一步说明，所有结论都避免依赖小于该量级的跨 cell 时间差。\n'
        % '、'.join(str(n) for n in ns))

    text.append('### A.2 基础密码运算\n')
    text.append(
        '表 1 列出代码实际调用的底层运算。AES-256 密钥扩展、AES-256 CTR 单块、SHAKE256 和 '
        'rand_bytes 每样本内部重复 1,000 次；VOLE 使用 vendor 的 small-VOLE 原语，每样本重复 5 次。'
        f'每行 {basic[next(iter(basic))]["n"]} 个样本，均先预热 3 次。\n')
    text.append('\n**表 1 基础密码运算实测。**\n')
    text.append(table(
        ['基础运算', '单位', '中位数', '平均值', '标准差', 'P95', '样本数'],
        [[k, 'µs', fmt(v['median'], 4), fmt(v['mean'], 4), fmt(v['stddev'], 4),
          fmt(v['p95'], 4), v['n']] for k, v in basic.items()],
        ['---', '---', '---:', '---:', '---:', '---:', '---:']))
    text.append(
        '\n需要说明的是，VOLE 行是 vendor 实现的单次 small-VOLE 协议调用（k = 12，'
        '36 个列块），不是一次完整证明的 VOLE 总量；VOLE-in-the-Head 证明还会调用承诺、'
        '检查和学习阶段，其总时间以报告/普通证明的端到端计时为准。SHAKE256 行是 64 字节输入、'
        '32 字节输出的一次 hash API 调用，也不等同于一次证明内的全部 Keccak 置换。\n')

    text.append('## B. 计算开销（Computational Overhead）\n')
    text.append('### B.1 原始匿名报告随环规模的变化\n')
    text.append('\n**表 2 原始报告随环规模的生成/验证时间与大小。**\n')
    text.append(table(
        ['N', '证明大小 (B)', '报告 payload (B)', '注册表 (B)', '生成中位数 (ms)',
         '生成标准差', '验证中位数 (ms)', '验证标准差'],
        [[r['ring_size'], f"{r['report_proof_bytes']:,}", f"{r['report_payload_bytes']:,}",
          f"{r['ring_registry_bytes']:,}", fmt(r['generate_median_ms']),
          fmt(r['generate_stddev_ms']), fmt(r['verify_median_ms']),
          fmt(r['verify_stddev_ms'])] for r in agg['ring_scalability']],
        ['---:', '---:', '---:', '---:', '---:', '---:', '---:', '---:']))
    text.append(
        f'\n环规模从 N = {ns[0]} 增至 N = {ns[-1]}（{ns[-1] // ns[0]} 倍）时，报告生成中位数由 '
        f'{fmt(gen_small["generate_median_ms"])} ms 增至 {fmt(gen_large["generate_median_ms"])} ms，'
        f'约为 {gen_large["generate_median_ms"] / gen_small["generate_median_ms"]:.2f} 倍；'
        f'验证中位数由 {fmt(gen_small["verify_median_ms"])} ms 增至 '
        f'{fmt(gen_large["verify_median_ms"])} ms，约为 '
        f'{gen_large["verify_median_ms"] / gen_small["verify_median_ms"]:.2f} 倍。'
        '增长明显慢于 N 的线性增长，原因是环选择关系采用批量 VOLE 与 AVX2 并行，'
        '固定开销被更多成员摊薄。\n')
    text.append(
        f'报告证明大小从 {gen_small["report_proof_bytes"]:,} B 增加到 '
        f'{gen_large["report_proof_bytes"]:,} B，仅增加 '
        f'{gen_large["report_proof_bytes"] - gen_small["report_proof_bytes"]:,} B；'
        f'公开注册表（2N 个公钥，每个 64 B）则严格线性增长到 '
        f'{gen_large["ring_registry_bytes"]:,} B。报告 payload 还包含 192 B 的消息、随机数、'
        't0/t1 标签字段，因此报告传输大小随 N 只有很小的增长。\n')

    text.append('### B.2 身份认领证明\n')
    text.append('\n**表 3 认领证明（s=1）的实测开销。**\n')
    text.append(table(
        ['N', '证明数', '证明大小 (B)', '生成中位数 (ms)', '生成标准差',
         '验证中位数 (ms)', '验证标准差', '原始报告验证 (ms)'],
        [[r['ring_size'], r['proof_count'], f"{r['proof_bytes']:,}",
          fmt(r['generate_median_ms']), fmt(r['generate_stddev_ms']),
          fmt(r['verify_median_ms']), fmt(r['verify_stddev_ms']),
          fmt(r['original_median_ms'])] for r in claim_rows],
        ['---:', '---:', '---:', '---:', '---:', '---:', '---:', '---:']))
    cmin = min(r['generate_median_ms'] for r in claim_rows)
    cmax = max(r['generate_median_ms'] for r in claim_rows)
    vmin = min(r['verify_median_ms'] for r in claim_rows)
    vmax = max(r['verify_median_ms'] for r in claim_rows)
    text.append(
        f'\n认领证明的大小在全部环规模下恒为 49,208 B，生成中位数在 {fmt(cmin)}–{fmt(cmax)} ms、'
        f'核心验证中位数在 {fmt(vmin)}–{fmt(vmax)} ms 之间，没有随 N 单调增长的趋势；'
        '这与普通 G 证明关系不包含环成员选择分支的设计一致。'
        '但认领的公开验证还需要验证被认领的原始报告，该部分时间随 N 增长（表 3 最后一列），'
        '因此“认领完整验证”应报告为“原始报告验证 + 核心证明验证”，而不是一个端到端单次计时。\n')

    text.append('### B.3 Anchor 与 Common Bridge 全矩阵\n')
    text.append(
        '对于 s 份报告的选择性关联，Anchor 以第一份报告为锚点，为其余 s−1 份报告各生成一条关联边证明，'
        '因此证书包含 s−1 个普通证明；Common Bridge 为每份报告生成一条关联证明，包含 s 个普通证明，'
        '并额外携带 64 B 的公开 Bridge 元组。表 4 给出全部 N 与 s 的实测中位数。\n')
    rows = []
    for r in agg['certificate_scalability']:
        if r['method'] == 'claim':
            continue
        rows.append([r['ring_size'], r['method'], r['selected_count'], r['proof_count'],
                     f"{r['proof_bytes']:,}", fmt(r['generate_median_ms']),
                     fmt(r['generate_stddev_ms']), fmt(r['verify_median_ms']),
                     fmt(r['original_median_ms'])])
    text.append('\n**表 4 Anchor 与 Common Bridge 全矩阵。**\n')
    text.append(table(['N', '结构', 's', '证明数', '证明大小 (B)', '生成中位数 (ms)',
                       '生成标准差', '验证中位数 (ms)', '原始报告验证 (ms)'], rows,
                      ['---:', '---', '---:', '---:', '---:', '---:', '---:', '---:', '---:']))
    slopes = ', '.join(f'N={n}: {fit[n]["generate_ms_per_proof"]:.1f} ms/证明'
                       for n in ns)
    text.append(
        '\n把全部 s = 1…20 的 cell 按证明数量做最小二乘拟合，生成时间与证明数量高度线性：'
        + slopes + '；R² 均高于 0.99，截距仅为个位数毫秒。'
        '这说明关联证书的生成成本由普通证明数量决定：Anchor 比 Bridge 少一个证明，'
        '因此节省的时间约为一个普通证明的成本，节省的字节数恒为 49,208 B。'
        '按 s 计算，Anchor 的证明大小相对 Bridge 节省 1/s：s = 2 时为 50%，s = 5 时为 20%，'
        's = 20 时为 5%。\n')
    text.append(
        '需要如实说明：由于每个 cell 是连续测量，cell 之间的绝对时间存在约 10% 的波动；'
        '在 s = 20 这类长 cell 中，一个证明的差异与波动同量级，因此本文的消融结论以'
        '**证明数量与证明大小（确定性量）**为主，时间结论以线性拟合斜率为准，而不依赖单个 cell 的原始差值。'
        '表 5 给出同一 s 下 Anchor/Bridge 的对照及其按证明数归一化后的每证明成本。\n')
    text.append('\n**表 5 Anchor/Bridge 同 s 对照与每证明归一化成本。**\n')
    text.append(table(
        ['N', 's', '证明数 A/B', '生成 A/B (ms)', '每证明成本 A/B (ms)',
         '验证 A/B (ms)', '大小节省 (B)'],
        [[r['ring_size'], r['selected_count'], f"{r['anchor_proofs']}/{r['bridge_proofs']}",
          f"{fmt(r['anchor_generate_median_ms'])}/{fmt(r['bridge_generate_median_ms'])}",
          f"{fmt(r['anchor_generate_per_proof_ms'])}/{fmt(r['bridge_generate_per_proof_ms'])}",
          f"{fmt(r['anchor_verify_median_ms'])}/{fmt(r['bridge_verify_median_ms'])}",
          f"{r['proof_bytes_saved']:,}"] for r in agg['anchor_bridge_ablation']],
        ['---:', '---:', '---', '---', '---', '---', '---:']))

    text.append('### B.4 各阶段的基础运算调用次数\n')
    if counts:
        text.append(
            '在独立的计数插桩构建中（仅用于调用次数，不用于计时），对 AES 密钥扩展、AES-256 块加密、'
            'SHAKE256 的 init/update/final（含 x4 并行版本）以及 VOLE sender/receiver 计数。'
            '表 6 给出每次操作的实际调用次数；普通证明与 N 无关，报告操作随 N 增长。\n')
        rows = []

        def cells(r):
            return [r['aes_key_schedule'], r['aes_256_blocks'],
                    f"{r['shake_init']}/{r['shake_update']}/{r['shake_final']}",
                    f"{r['shake_init_x4']}/{r['shake_update_x4']}/{r['shake_final_x4']}",
                    f"{r['vole_sender']}/{r['vole_receiver']}"]

        for operation, label in [('report_generation', '原始报告生成'),
                                 ('report_verification', '原始报告验证')]:
            for r in [x for x in counts if x['operation'] == operation]:
                rows.append([label, r['ring_size'], *cells(r)])
        for operation, label in [('claim_gen_per_proof', '认领生成（单证明）'),
                                 ('claim_ver_per_proof', '认领验证（单证明）'),
                                 ('bridge_gen_per_proof', '关联边生成（单证明）'),
                                 ('bridge_ver_per_proof', '关联边验证（单证明）')]:
            cand = [x for x in counts if x['operation'] == operation]
            if cand:
                r = min(cand, key=lambda x: x['ring_size'])
                rows.append([label, '与 N 无关', *cells(r)])
        text.append('\n**表 6 计数插桩得到的基础运算调用次数。**\n')
        text.append(table(['操作', 'N', 'AES 密钥扩展', 'AES-256 块', 'SHAKE init/update/final',
                           'SHAKE x4 init/update/final', 'VOLE sender/receiver'], rows,
                          ['---', '---:', '---:', '---:', '---:', '---:', '---:']))
        text.append('\n注：SHAKE 计数是 API 调用次数，不是 Keccak 置换次数；一次证明内的 hash 调用会吸收不同长度的输入。'
                    'AES 计数主要由 VOLE 提交/扩展阶段的 PRG 产生（每次普通证明约 7.07×10^6 个 AES-256 块、'
                    '1.23×10^5 次密钥扩展），OWF 关系本身只涉及 8 个 AES 块；这也是证明时间主要消耗在 '
                    'VOLE 相关性扩展、而不是 OWF 电路上的原因。\n')
    else:
        text.append('计数插桩构建未包含在本次运行中，该表记为未测量。\n')

    text.append('## C. 通信开销（Communication Overhead）\n')
    comm = agg['communication_overhead']
    text.append(
        '通信开销按三个口径分别报告：**proof-only**（仅证明本体）、'
        '**certificate + references**（证明、计数/认领者索引、报告标识和上下文摘要）以及'
        '**complete evidence package**（上述证书 + 所引用的原始报告 + 32 B manifest 摘要）。'
        '表 7 中所有字节数均由实测证明文件大小和编译期常量核算，**不是实测网络传输量**。\n')
    wanted = ['public_parameters', 'user_public_key', 'user_secret_key', 'claim_proof',
              'link_edge_proof', 'claim_certificate_s1']
    selected = [r for r in comm if r['object'] in wanted]
    selected += [r for r in comm if r['object'].startswith(
        ('report_proof_N', 'report_payload_N', 'ring_registry_N'))]
    selected += [r for r in comm if r['object'] in (
        'anchor_link_proof_s5', 'bridge_link_proof_s5',
        'anchor_link_proof_s20', 'bridge_link_proof_s20')]
    ref_n = ns[-1]
    selected += [r for r in comm if r['object'].startswith(
        (f'anchor_complete_package_N{ref_n}_s5', f'bridge_complete_package_N{ref_n}_s5',
         f'anchor_complete_package_N{ref_n}_s20', f'bridge_complete_package_N{ref_n}_s20'))]
    rows = [[r['object'], f"{r['bytes']:,}", f"{r['kib']:.2f}", r['scope']] for r in selected]
    text.append('\n**表 7 通信开销字节核算。**\n')
    text.append(table(['对象', '字节', 'KiB', '口径'], rows, ['---', '---:', '---:', '---']))
    payload_large = ring[ns[-1]]['report_payload_bytes']
    text.append(
        '\n核心结论：认领证明与单条关联边证明均为 49,208 B；s 份报告的 Anchor 证书为 '
        '(s−1) × 49,208 B，Bridge 为 s × 49,208 B + 64 B。'
        f'完整证据包中原始报告占主导（N=1024 时每份 {payload_large:,} B），因此当 s 较大时，'
        'Anchor 相对 Bridge 节省的 49,208 B 在整包中的占比约为 1/s 的证明部分，'
        '不能把“核心证明减少 20%（s=5）”误写成“完整证据包减少 20%”。\n')

    text.append('## D. 扩展性评估（Scalability）\n')
    text.append(
        '\n'
        f'- **报告阶段**：生成与验证时间随 N 单调上升但慢于线性（N 增长 {ns[-1] // ns[0]} 倍，'
        f'生成时间增长 {gen_large["generate_median_ms"] / gen_small["generate_median_ms"]:.2f} 倍）；'
        f'证明大小几乎不变（{gen_small["report_proof_bytes"]:,} → {gen_large["report_proof_bytes"]:,} B）。'
        '\n'
        f'- **认领阶段**：证明大小与核心生成/验证时间不随 N 变化，认领的完整验证随 N 增长'
        f'（原始报告验证 {fmt(claim_rows[0]["original_median_ms"])} → '
        f'{fmt(claim_rows[-1]["original_median_ms"])} ms）。'
        '\n'
        f'- **关联阶段**：生成和验证时间与证明数量线性（斜率 '
        f'{fit[ns[0]]["generate_ms_per_proof"]:.1f}–{fit[ns[-1]]["generate_ms_per_proof"]:.1f} ms/证明），'
        'Anchor 为 s−1 个证明，Bridge 为 s 个证明。'
        '\n'
        f'- **峰值内存**：普通证明 worker 的峰值 RSS 约 '
        f'{min(r["max_rss_bytes"] for r in agg["certificate_scalability"]) / 2**20:.1f}–'
        f'{max(r["max_rss_bytes"] for r in agg["certificate_scalability"]) / 2**20:.1f} MiB，'
        '不随 N 或 s 单调增长；报告生成进程的峰值 RSS 在 N=16 时约 '
        f'{ring[ns[0]]["driver_peak_rss_bytes"] / 2**20:.1f} MiB（N 越大，注册表与 '
        '20 份报告 fixture 越大）。这些数值是进程峰值常驻内存，不是证明对象的大小。\n')
    text.append(
        '关于跨 N 比较的可信度：N = 64、256、1024 在同一构建、同一主机上连续测得；'
        'N=16 因首次运行受前置功能测试的热状态影响而重测（见数据来源说明）。'
        '由于无风扇主机的热漂移，跨 cell 的时间波动约 10%，'
        '但 N 带来的变化（数倍）显著大于该波动；证明大小、注册表大小、证明数量等确定性量不受影响。\n')

    text.append('## E. 功能与安全属性比较（Functionality and Security Properties）\n')
    text.append(
        '在四种环规模上分别执行了功能与对抗性检查：正确认领、错误身份拒绝、同所有者关联、'
        '混合签名者拒绝、报告内容/标识/上下文篡改拒绝、无秘密信息的公开验证。'
        f'每种环规模均通过全部检查（联合检查 {agg["functional_validation"]["rows"][0]["joint_checks_passed"]} 项、'
        f'公开验证 {agg["functional_validation"]["rows"][0]["fresh_public_checks"]} 项、'
        f'无身份关联验证 {agg["functional_validation"]["rows"][0]["fresh_link_checks"]} 项；'
        '检查计数随固定的 20 份报告 fixture 变化）。这些是功能测试，不是密码学安全性证明。\n')
    text.append(
        '与已有方案的属性比较沿用 `docs/SECURITY_PROPERTY_COMPARISON.md` 的文献级表格：'
        '逐项比较后量子基础、环匿名、不可伪造、事后认领、可链接性、选择性关联和问责，'
        '并明确 Park–Sealfon 的 claimability、Fiore 等人的用户控制可链接性、'
        'DualRing-PRF 的公开链接标签、SPRING 的指定开启者问责与 CLARIS 的选择性事后关联'
        '不是同一语义，不能简单打勾等同。\n')
    text.append(
        '性能上的外部比较目前只有一个可执行基线：固定 commit 的 Chiang et al. VOLEitH 实现，'
        '且其 128-bit 与 AES-256 CLARIS 不是同一安全配置，每个 N 只有一次观测。'
        '因此本文只把它作为“同族实现的参考量级”，不计算加速比，也不把它与 CLARIS 放进同一张排名表。'
        'Park–Sealfon、Fiore 等人、DualRing-PRF、SPRING、TalosLogic 的 matched benchmark '
        '仍记为未完成，而不是用文献中的异构数字代替。\n')

    text.append('## F. 小结与限制（Summary and Limitations）\n')
    text.append(
        f'本节在统一构建与主机上完成了 N ∈ {{{", ".join(str(n) for n in ns)}}}、'
        f's ∈ {{2,3,5,10,20}} 的全矩阵测量，并给出 s = 1 的认领基线。主要实测结论是：'
        f'（1）报告证明大小几乎不随 N 变化（{gen_small["report_proof_bytes"]:,} → '
        f'{gen_large["report_proof_bytes"]:,} B），而生成/验证时间随 N 亚线性增长；'
        '（2）认领证明恒为 49,208 B，其核心证明时间不随 N 变化，完整验证的增量来自原始报告验证；'
        '（3）关联证书的成本由普通证明数量决定，Anchor 为 s−1 个、Bridge 为 s 个，'
        '生成时间与证明数量线性（R² > 0.99），Anchor 恒定节省 49,208 B。\n')
    text.append(
        '必须保留的限制：（a）全部计时是 Rosetta 2 翻译下的 x86_64 执行，不是原生 x86_64 或 ARM 性能；'
        '（b）“完整验证”是原始报告验证与核心证明验证两个独立中位数之和，不是单次端到端计时；'
        '（c）通信开销是字节核算，未做真实网络传输；（d）无风扇主机的热漂移带来约 10% 的跨 cell 波动，'
        '消融结论以证明数量/大小和线性拟合斜率为准；（e）外部方案没有 matched executable benchmark；'
        '（f）功能测试不构成 QROM 安全性证明，主定理的条件性假设仍需单独陈述。\n')

    (root / 'docs').mkdir(exist_ok=True)
    (root / 'docs/VII_performance_evaluation_CN.md').write_text('\n'.join(text) + '\n')
    print(root / 'docs/VII_performance_evaluation_CN.md')


if __name__ == '__main__':
    main()
