# 分析设计

## 情绪标签体系

采用 6 维情绪分数：

| 字段 | 中文 | Pilot 3000 均值 |
|---|---|---:|
| `joy` | 喜悦 | 0.2716 |
| `sadness` | 悲伤 | 0.0977 |
| `anger` | 愤怒 | 0.1024 |
| `fear` | 恐惧 | 0.0371 |
| `surprise` | 惊讶 | 0.0595 |
| `neutral` | 中性 | 0.4317 |

每条微博的 6 维分数应在 `[0, 1]`，总和接近 1。主导情绪为最高分维度。

### Pilot 3000 主导情绪分布

| 情绪 | 数量 | 占比 |
|---|---:|---:|
| 中性 | 1150 | 38.3% |
| 喜悦 | 1077 | 35.9% |
| 愤怒 | 414 | 13.8% |
| 悲伤 | 245 | 8.2% |
| 恐惧 | 76 | 2.5% |
| 惊讶 | 38 | 1.3% |

## 标注

`scripts/02_label_emotions.py` 使用 DeepSeek API 批量标注微博文本。

关键设计：

- `smoke`：300 条，用于检查 prompt、解析和续跑。
- `pilot`：3,000 条，用于验证和前端联调。
- `full`：完整 mini dataset。
- 支持断点续跑和临时 checkpoint。
- 输出完整数据行 + 情绪分数，而不是只输出分数。

## 验证

`scripts/03_validate_emotions.py` 使用 SMP2020-EWECT 做外部验证。

输出：

- `tmp/03_accuracy_report.json`
- `analysis/emotion_validation/confusion_matrix.csv`
- `analysis/emotion_validation/deepseek_vs_snownlp_sample.csv`
- `analysis/emotion_validation/emotion_distribution_summary.csv`
- `analysis/emotion_validation/dominant_emotion_distribution.csv`

### Pilot 3000 验证结果（2000 SMP2020 样本）

| 情绪 | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| 喜悦 | 0.940 | 0.701 | 0.803 | 923 |
| 愤怒 | 0.779 | 0.863 | 0.819 | 314 |
| 中性 | 0.568 | 0.788 | 0.660 | 476 |
| 悲伤 | 0.570 | 0.667 | 0.615 | 165 |
| 恐惧 | 0.591 | 0.520 | 0.553 | 75 |
| 惊讶 | 0.533 | 0.511 | 0.522 | 47 |
| **总体** | | | **Accuracy** | **0.733** |
| **Macro avg** | 0.664 | 0.675 | **0.662** | 2000 |

验收重点：

- accuracy: **0.733** ✅
- macro F1: **0.662** ✅
- 每类 F1：joy/anger > 0.80，fear/surprise > 0.52

## 聚合

`scripts/04_aggregate_emotions.py` 生成：

- `emotion_panel_weekly.csv`：周×省
- `emotion_panel_monthly.csv`：月×省
- `emotion_national_timeline.csv`：全国周时序
- `province_emotion_vectors.csv`：省份全年特征向量

省级面板使用 34 省白名单过滤噪声值，全国时序使用全部标注样本。

## 异常检测

`scripts/05_detect_anomalies.py` 对全国情绪时序做 rolling z-score：

- 检测维度：fear, anger, joy
- 基线窗口：当前周之前 4 周
- 阈值：`|z| > 2.5`
- 输出每个异常周的贡献省份 Top 5

异常检测用于发现疫情事件或舆论事件对应的情绪波动。

## 省份聚类

`scripts/06_cluster_provinces.py` 使用省份全年情绪特征做聚类。

特征包括：

- 6 维情绪全年均值
- 情绪强度
- 恐惧方差
- 喜悦方差

输出层次聚类树、KMeans 轮廓系数和省份标签。

## 聚类演化

`scripts/07_cluster_evolution.py` 按月独立聚类，并按“负向风险得分”重排 cluster 编号，避免不同月份标签语义错位。

风险得分：

```text
sadness_mean + anger_mean + fear_mean - joy_mean
```

编号越高，代表该月该类越偏负向/高风险。
