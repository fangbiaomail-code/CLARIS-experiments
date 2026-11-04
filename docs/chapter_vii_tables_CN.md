# CLARIS 第七章：全矩阵实测表格

数据来源：`results/fullmatrix`，同一构建、同一主机；每个 cell 预热 3 次、正式测量 30 次。执行目标为 x86_64 (AVX2/AES-NI/PCLMUL)，主机为 Apple M1，通过 Rosetta 2 运行。

## 表 1 实验环境

| 项目 | 值 |
|---|---|
| CPU | Apple M1（8 物理核 / 8 逻辑核） |
| 内存 | 8.0 GiB |
| 操作系统 | macOS 15.3 (build 24D60) |
| 编译器 | Apple clang version 16.0.0 (clang-1600.0.26.3) |
| 编译选项 | `-arch x86_64 -O2 -march=x86-64 -mavx2 -maes -mpclmul -DNDEBUG -D_bswap64=__builtin_bswap64 -std=c11 -Wno-ignored-attributes -Wno-unused-value -Wno-incompatible-pointer-types-discards-qualifiers` |
| 执行方式 | x86_64 (AVX2/AES-NI/PCLMUL)，Rosetta 2 翻译 |
| 转录配置 | CLARIS-Q-v2-G-v1 |
| 构建清单 SHA-256 | `534301c2171bfbbea5fe3f62da6a95e5661b6064522894427cebc1a32193119e` |

## 表 2 基础密码运算

| 运算 | 单位 | 中位数 | 平均值 | 标准差 | P95 | 样本数 |
|---|---:|---:|---:|---:|---:|---:|
| AES-256 key schedule | µs | 0.2070 | 0.2137 | 0.0208 | 0.2358 | 50 |
| AES-256 CTR block | µs | 0.0600 | 0.0597 | 0.0027 | 0.0610 | 50 |
| SHAKE256 hash | µs | 1.9245 | 1.9813 | 0.1162 | 2.2293 | 50 |
| rand_bytes 64 | µs | 8.3030 | 8.4053 | 0.3249 | 9.2304 | 50 |
| VOLE sender | µs | 12791.0000 | 13314.5880 | 2385.8586 | 14967.5300 | 50 |
| VOLE receiver | µs | 12733.4000 | 12816.1160 | 469.8041 | 13830.0200 | 50 |

## 表 3 原始报告随环规模

| N | 证明大小 (B) | 报告 payload (B) | 注册表 (B) | 生成中位数 (ms) | 生成标准差 | 验证中位数 (ms) | 验证标准差 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 50,638 | 50,830 | 2,048 | 293.80 | 6.34 | 358.02 | 4.64 |
| 64 | 50,660 | 50,852 | 8,192 | 319.87 | 1.58 | 380.40 | 9.20 |
| 256 | 50,704 | 50,896 | 32,768 | 450.91 | 11.70 | 486.79 | 33.72 |
| 1024 | 50,792 | 50,984 | 131,072 | 896.12 | 19.92 | 834.28 | 23.64 |

## 表 4 认领证明（s=1）

| N | 证明数 | 证明大小 (B) | 生成中位数 (ms) | 验证中位数 (ms) | 原始报告验证中位数 (ms) | 合并中位数 (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1 | 49,208 | 283.51 | 356.98 | 364.75 | 721.73 |
| 64 | 1 | 49,208 | 278.57 | 351.58 | 380.07 | 731.65 |
| 256 | 1 | 49,208 | 292.40 | 366.91 | 489.50 | 856.41 |
| 1024 | 1 | 49,208 | 286.72 | 363.63 | 839.91 | 1203.53 |

## 表 5 Anchor / Bridge 全矩阵

| N | 结构 | s | 证明数 | 证明大小 (B) | 生成中位数 (ms) | 生成标准差 | 验证中位数 (ms) | 原始报告验证 (ms) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 16 | anchor | 2 | 1 | 49,208 | 273.35 | 2.56 | 344.82 | 723.76 |
| 16 | bridge | 2 | 2 | 98,416 | 570.53 | 27.54 | 709.68 | 736.65 |
| 16 | anchor | 3 | 2 | 98,416 | 544.10 | 1.99 | 687.95 | 1069.41 |
| 16 | bridge | 3 | 3 | 147,624 | 815.27 | 6.03 | 1031.29 | 1069.53 |
| 16 | anchor | 5 | 4 | 196,832 | 1087.96 | 6.25 | 1376.86 | 1783.79 |
| 16 | bridge | 5 | 5 | 246,040 | 1358.97 | 4.82 | 1718.61 | 1783.32 |
| 16 | anchor | 10 | 9 | 442,872 | 2447.25 | 7.54 | 3092.17 | 3564.24 |
| 16 | bridge | 10 | 10 | 492,080 | 2719.92 | 10.38 | 3440.20 | 3566.35 |
| 16 | anchor | 20 | 19 | 934,952 | 5170.18 | 11.49 | 6529.83 | 7132.13 |
| 16 | bridge | 20 | 20 | 984,160 | 5439.61 | 9.46 | 6871.02 | 7129.91 |
| 64 | anchor | 2 | 1 | 49,208 | 284.04 | 15.30 | 361.13 | 780.65 |
| 64 | bridge | 2 | 2 | 98,416 | 562.54 | 9.98 | 711.16 | 780.23 |
| 64 | anchor | 3 | 2 | 98,416 | 574.17 | 13.30 | 725.62 | 1193.36 |
| 64 | bridge | 3 | 3 | 147,624 | 863.09 | 21.12 | 1085.52 | 1180.91 |
| 64 | anchor | 5 | 4 | 196,832 | 1161.76 | 14.75 | 1464.66 | 2001.48 |
| 64 | bridge | 5 | 5 | 246,040 | 1476.34 | 34.84 | 1840.67 | 1981.49 |
| 64 | anchor | 10 | 9 | 442,872 | 2625.40 | 72.92 | 3320.30 | 3968.34 |
| 64 | bridge | 10 | 10 | 492,080 | 2889.12 | 93.59 | 3628.19 | 4055.68 |
| 64 | anchor | 20 | 19 | 934,952 | 5529.39 | 50.02 | 6928.16 | 8023.44 |
| 64 | bridge | 20 | 20 | 984,160 | 5826.55 | 61.86 | 7334.73 | 7958.81 |
| 256 | anchor | 2 | 1 | 49,208 | 289.06 | 5.43 | 364.59 | 980.13 |
| 256 | bridge | 2 | 2 | 98,416 | 584.09 | 10.92 | 733.15 | 983.54 |
| 256 | anchor | 3 | 2 | 98,416 | 590.49 | 16.53 | 742.54 | 1463.81 |
| 256 | bridge | 3 | 3 | 147,624 | 872.40 | 16.24 | 1094.47 | 1454.95 |
| 256 | anchor | 5 | 4 | 196,832 | 1163.62 | 19.44 | 1464.60 | 2462.85 |
| 256 | bridge | 5 | 5 | 246,040 | 1449.94 | 25.82 | 1825.76 | 2438.23 |
| 256 | anchor | 10 | 9 | 442,872 | 2625.41 | 32.00 | 3296.73 | 4884.14 |
| 256 | bridge | 10 | 10 | 492,080 | 2916.51 | 31.40 | 3662.26 | 4892.13 |
| 256 | anchor | 20 | 19 | 934,952 | 5499.97 | 107.98 | 6922.84 | 9747.60 |
| 256 | bridge | 20 | 20 | 984,160 | 5829.62 | 98.03 | 7324.45 | 9779.86 |
| 1024 | anchor | 2 | 1 | 49,208 | 287.11 | 4.18 | 362.42 | 1666.00 |
| 1024 | bridge | 2 | 2 | 98,416 | 578.98 | 8.82 | 725.83 | 1674.09 |
| 1024 | anchor | 3 | 2 | 98,416 | 578.80 | 12.67 | 728.15 | 2502.01 |
| 1024 | bridge | 3 | 3 | 147,624 | 871.05 | 19.42 | 1095.57 | 2498.10 |
| 1024 | anchor | 5 | 4 | 196,832 | 1155.68 | 13.68 | 1457.26 | 4184.27 |
| 1024 | bridge | 5 | 5 | 246,040 | 1454.64 | 20.60 | 1824.85 | 4187.88 |
| 1024 | anchor | 10 | 9 | 442,872 | 2597.68 | 45.77 | 3275.17 | 8373.25 |
| 1024 | bridge | 10 | 10 | 492,080 | 2906.29 | 35.09 | 3649.11 | 8396.39 |
| 1024 | anchor | 20 | 19 | 934,952 | 5397.44 | 63.09 | 6772.29 | 16065.64 |
| 1024 | bridge | 20 | 20 | 984,160 | 5584.99 | 36.36 | 6991.57 | 16725.15 |

## 表 6 Anchor 与 Bridge 消融

| N | s | 证明数 A/B | 生成 A/B (ms) | 节省 (%) | 验证 A/B (ms) | 节省 (%) | 大小节省 (B) |
|---:|---:|---|---|---:|---|---:|---:|
| 16 | 2 | 1/2 | 273.35/570.53 | 52.1 | 344.82/709.68 | 51.4 | 49,208 |
| 16 | 3 | 2/3 | 544.10/815.27 | 33.3 | 687.95/1031.29 | 33.3 | 49,208 |
| 16 | 5 | 4/5 | 1087.96/1358.97 | 19.9 | 1376.86/1718.61 | 19.9 | 49,208 |
| 16 | 10 | 9/10 | 2447.25/2719.92 | 10.0 | 3092.17/3440.20 | 10.1 | 49,208 |
| 16 | 20 | 19/20 | 5170.18/5439.61 | 5.0 | 6529.83/6871.02 | 5.0 | 49,208 |
| 64 | 2 | 1/2 | 284.04/562.54 | 49.5 | 361.13/711.16 | 49.2 | 49,208 |
| 64 | 3 | 2/3 | 574.17/863.09 | 33.5 | 725.62/1085.52 | 33.2 | 49,208 |
| 64 | 5 | 4/5 | 1161.76/1476.34 | 21.3 | 1464.66/1840.67 | 20.4 | 49,208 |
| 64 | 10 | 9/10 | 2625.40/2889.12 | 9.1 | 3320.30/3628.19 | 8.5 | 49,208 |
| 64 | 20 | 19/20 | 5529.39/5826.55 | 5.1 | 6928.16/7334.73 | 5.5 | 49,208 |
| 256 | 2 | 1/2 | 289.06/584.09 | 50.5 | 364.59/733.15 | 50.3 | 49,208 |
| 256 | 3 | 2/3 | 590.49/872.40 | 32.3 | 742.54/1094.47 | 32.2 | 49,208 |
| 256 | 5 | 4/5 | 1163.62/1449.94 | 19.7 | 1464.60/1825.76 | 19.8 | 49,208 |
| 256 | 10 | 9/10 | 2625.41/2916.51 | 10.0 | 3296.73/3662.26 | 10.0 | 49,208 |
| 256 | 20 | 19/20 | 5499.97/5829.62 | 5.7 | 6922.84/7324.45 | 5.5 | 49,208 |
| 1024 | 2 | 1/2 | 287.11/578.98 | 50.4 | 362.42/725.83 | 50.1 | 49,208 |
| 1024 | 3 | 2/3 | 578.80/871.05 | 33.6 | 728.15/1095.57 | 33.5 | 49,208 |
| 1024 | 5 | 4/5 | 1155.68/1454.64 | 20.6 | 1457.26/1824.85 | 20.1 | 49,208 |
| 1024 | 10 | 9/10 | 2597.68/2906.29 | 10.6 | 3275.17/3649.11 | 10.2 | 49,208 |
| 1024 | 20 | 19/20 | 5397.44/5584.99 | 3.4 | 6772.29/6991.57 | 3.1 | 49,208 |

## 表 6b 证明数量-时间线性拟合

| N | 生成斜率 (ms/证明) | 生成截距 (ms) | R² | 验证斜率 (ms/证明) | 验证截距 (ms) | R² |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 271.62 | 6.15 | 1.0000 | 343.19 | 6.97 | 1.0000 |
| 64 | 291.61 | -8.33 | 1.0000 | 366.23 | -7.45 | 1.0000 |
| 256 | 290.52 | 3.07 | 1.0000 | 365.29 | 3.32 | 1.0000 |
| 1024 | 281.33 | 28.94 | 0.9997 | 352.48 | 41.56 | 0.9996 |

## 表 7 通信开销（字节核算，非实测网络传输）

| 对象 | 字节 | KiB | 口径 |
|---|---:|---:|---|
| public_parameters | 0 | 0.00 | compile-time parameter tuple; no trusted-setup file |
| user_public_key | 64 | 0.06 | one ring-profile public key |
| user_secret_key | 64 | 0.06 | one ring-profile secret key |
| claim_proof | 49,208 | 48.05 | one ordinary eight-block G proof |
| link_edge_proof | 49,208 | 48.05 | one ordinary link-edge proof |
| claim_certificate_s1 | 49,276 | 48.12 | claim proof + claimant index + report id + context |
| anchor_link_proof_s2 | 49,208 | 48.05 | 1 ordinary proofs |
| bridge_link_proof_s2 | 98,480 | 96.17 | 2 ordinary proofs + 64-byte bridge tuple |
| anchor_link_proof_s3 | 98,416 | 96.11 | 2 ordinary proofs |
| bridge_link_proof_s3 | 147,688 | 144.23 | 3 ordinary proofs + 64-byte bridge tuple |
| anchor_link_proof_s5 | 196,832 | 192.22 | 4 ordinary proofs |
| bridge_link_proof_s5 | 246,104 | 240.34 | 5 ordinary proofs + 64-byte bridge tuple |
| anchor_link_proof_s10 | 442,872 | 432.49 | 9 ordinary proofs |
| bridge_link_proof_s10 | 492,144 | 480.61 | 10 ordinary proofs + 64-byte bridge tuple |
| anchor_link_proof_s20 | 934,952 | 913.04 | 19 ordinary proofs |
| bridge_link_proof_s20 | 984,224 | 961.16 | 20 ordinary proofs + 64-byte bridge tuple |
| anchor_certificate_N16_s2 | 49,308 | 48.15 | proofs + count + s report ids + context |
| bridge_certificate_N16_s2 | 98,580 | 96.27 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N16_s2 | 151,000 | 147.46 | certificate + 2 report payloads (N=16) + 32-byte manifest digest |
| bridge_complete_package_N16_s2 | 200,272 | 195.58 | certificate + 2 report payloads (N=16) + 32-byte manifest digest |
| anchor_certificate_N16_s3 | 98,548 | 96.24 | proofs + count + s report ids + context |
| bridge_certificate_N16_s3 | 147,820 | 144.36 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N16_s3 | 251,070 | 245.19 | certificate + 3 report payloads (N=16) + 32-byte manifest digest |
| bridge_complete_package_N16_s3 | 300,342 | 293.30 | certificate + 3 report payloads (N=16) + 32-byte manifest digest |
| anchor_certificate_N16_s5 | 197,028 | 192.41 | proofs + count + s report ids + context |
| bridge_certificate_N16_s5 | 246,300 | 240.53 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N16_s5 | 451,210 | 440.63 | certificate + 5 report payloads (N=16) + 32-byte manifest digest |
| bridge_complete_package_N16_s5 | 500,482 | 488.75 | certificate + 5 report payloads (N=16) + 32-byte manifest digest |
| anchor_certificate_N16_s10 | 443,228 | 432.84 | proofs + count + s report ids + context |
| bridge_certificate_N16_s10 | 492,500 | 480.96 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N16_s10 | 951,560 | 929.26 | certificate + 10 report payloads (N=16) + 32-byte manifest digest |
| bridge_complete_package_N16_s10 | 1,000,832 | 977.38 | certificate + 10 report payloads (N=16) + 32-byte manifest digest |
| anchor_certificate_N16_s20 | 935,628 | 913.70 | proofs + count + s report ids + context |
| bridge_certificate_N16_s20 | 984,900 | 961.82 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N16_s20 | 1,952,260 | 1906.50 | certificate + 20 report payloads (N=16) + 32-byte manifest digest |
| bridge_complete_package_N16_s20 | 2,001,532 | 1954.62 | certificate + 20 report payloads (N=16) + 32-byte manifest digest |
| anchor_certificate_N64_s2 | 49,308 | 48.15 | proofs + count + s report ids + context |
| bridge_certificate_N64_s2 | 98,580 | 96.27 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N64_s2 | 151,044 | 147.50 | certificate + 2 report payloads (N=64) + 32-byte manifest digest |
| bridge_complete_package_N64_s2 | 200,316 | 195.62 | certificate + 2 report payloads (N=64) + 32-byte manifest digest |
| anchor_certificate_N64_s3 | 98,548 | 96.24 | proofs + count + s report ids + context |
| bridge_certificate_N64_s3 | 147,820 | 144.36 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N64_s3 | 251,136 | 245.25 | certificate + 3 report payloads (N=64) + 32-byte manifest digest |
| bridge_complete_package_N64_s3 | 300,408 | 293.37 | certificate + 3 report payloads (N=64) + 32-byte manifest digest |
| anchor_certificate_N64_s5 | 197,028 | 192.41 | proofs + count + s report ids + context |
| bridge_certificate_N64_s5 | 246,300 | 240.53 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N64_s5 | 451,320 | 440.74 | certificate + 5 report payloads (N=64) + 32-byte manifest digest |
| bridge_complete_package_N64_s5 | 500,592 | 488.86 | certificate + 5 report payloads (N=64) + 32-byte manifest digest |
| anchor_certificate_N64_s10 | 443,228 | 432.84 | proofs + count + s report ids + context |
| bridge_certificate_N64_s10 | 492,500 | 480.96 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N64_s10 | 951,780 | 929.47 | certificate + 10 report payloads (N=64) + 32-byte manifest digest |
| bridge_complete_package_N64_s10 | 1,001,052 | 977.59 | certificate + 10 report payloads (N=64) + 32-byte manifest digest |
| anchor_certificate_N64_s20 | 935,628 | 913.70 | proofs + count + s report ids + context |
| bridge_certificate_N64_s20 | 984,900 | 961.82 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N64_s20 | 1,952,700 | 1906.93 | certificate + 20 report payloads (N=64) + 32-byte manifest digest |
| bridge_complete_package_N64_s20 | 2,001,972 | 1955.05 | certificate + 20 report payloads (N=64) + 32-byte manifest digest |
| anchor_certificate_N256_s2 | 49,308 | 48.15 | proofs + count + s report ids + context |
| bridge_certificate_N256_s2 | 98,580 | 96.27 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N256_s2 | 151,132 | 147.59 | certificate + 2 report payloads (N=256) + 32-byte manifest digest |
| bridge_complete_package_N256_s2 | 200,404 | 195.71 | certificate + 2 report payloads (N=256) + 32-byte manifest digest |
| anchor_certificate_N256_s3 | 98,548 | 96.24 | proofs + count + s report ids + context |
| bridge_certificate_N256_s3 | 147,820 | 144.36 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N256_s3 | 251,268 | 245.38 | certificate + 3 report payloads (N=256) + 32-byte manifest digest |
| bridge_complete_package_N256_s3 | 300,540 | 293.50 | certificate + 3 report payloads (N=256) + 32-byte manifest digest |
| anchor_certificate_N256_s5 | 197,028 | 192.41 | proofs + count + s report ids + context |
| bridge_certificate_N256_s5 | 246,300 | 240.53 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N256_s5 | 451,540 | 440.96 | certificate + 5 report payloads (N=256) + 32-byte manifest digest |
| bridge_complete_package_N256_s5 | 500,812 | 489.07 | certificate + 5 report payloads (N=256) + 32-byte manifest digest |
| anchor_certificate_N256_s10 | 443,228 | 432.84 | proofs + count + s report ids + context |
| bridge_certificate_N256_s10 | 492,500 | 480.96 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N256_s10 | 952,220 | 929.90 | certificate + 10 report payloads (N=256) + 32-byte manifest digest |
| bridge_complete_package_N256_s10 | 1,001,492 | 978.02 | certificate + 10 report payloads (N=256) + 32-byte manifest digest |
| anchor_certificate_N256_s20 | 935,628 | 913.70 | proofs + count + s report ids + context |
| bridge_certificate_N256_s20 | 984,900 | 961.82 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N256_s20 | 1,953,580 | 1907.79 | certificate + 20 report payloads (N=256) + 32-byte manifest digest |
| bridge_complete_package_N256_s20 | 2,002,852 | 1955.91 | certificate + 20 report payloads (N=256) + 32-byte manifest digest |
| anchor_certificate_N1024_s2 | 49,308 | 48.15 | proofs + count + s report ids + context |
| bridge_certificate_N1024_s2 | 98,580 | 96.27 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N1024_s2 | 151,308 | 147.76 | certificate + 2 report payloads (N=1024) + 32-byte manifest digest |
| bridge_complete_package_N1024_s2 | 200,580 | 195.88 | certificate + 2 report payloads (N=1024) + 32-byte manifest digest |
| anchor_certificate_N1024_s3 | 98,548 | 96.24 | proofs + count + s report ids + context |
| bridge_certificate_N1024_s3 | 147,820 | 144.36 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N1024_s3 | 251,532 | 245.64 | certificate + 3 report payloads (N=1024) + 32-byte manifest digest |
| bridge_complete_package_N1024_s3 | 300,804 | 293.75 | certificate + 3 report payloads (N=1024) + 32-byte manifest digest |
| anchor_certificate_N1024_s5 | 197,028 | 192.41 | proofs + count + s report ids + context |
| bridge_certificate_N1024_s5 | 246,300 | 240.53 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N1024_s5 | 451,980 | 441.39 | certificate + 5 report payloads (N=1024) + 32-byte manifest digest |
| bridge_complete_package_N1024_s5 | 501,252 | 489.50 | certificate + 5 report payloads (N=1024) + 32-byte manifest digest |
| anchor_certificate_N1024_s10 | 443,228 | 432.84 | proofs + count + s report ids + context |
| bridge_certificate_N1024_s10 | 492,500 | 480.96 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N1024_s10 | 953,100 | 930.76 | certificate + 10 report payloads (N=1024) + 32-byte manifest digest |
| bridge_complete_package_N1024_s10 | 1,002,372 | 978.88 | certificate + 10 report payloads (N=1024) + 32-byte manifest digest |
| anchor_certificate_N1024_s20 | 935,628 | 913.70 | proofs + count + s report ids + context |
| bridge_certificate_N1024_s20 | 984,900 | 961.82 | proofs + bridge tuple + count + s report ids + context |
| anchor_complete_package_N1024_s20 | 1,955,340 | 1909.51 | certificate + 20 report payloads (N=1024) + 32-byte manifest digest |
| bridge_complete_package_N1024_s20 | 2,004,612 | 1957.63 | certificate + 20 report payloads (N=1024) + 32-byte manifest digest |

## 表 8 功能验证

| N | 联合检查 | 公开验证 | 无身份关联验证 | 结论 |
|---:|---:|---:|---:|---|
| 16 | 53 | 23 | 22 | PASS |
| 64 | 53 | 23 | 22 | PASS |
| 256 | 53 | 23 | 22 | PASS |
| 1024 | 53 | 23 | 22 | PASS |
