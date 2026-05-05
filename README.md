# 情绪气象站 · Mood Weather Station

基于 COVID-19 期间微博数据的省级公众情绪演变分析系统。通过 DeepSeek API 对 76,441 条微博进行 6 维情绪标注，从时间、空间、异常事件和聚类画像四个维度展示情绪变化。

## 功能

- **全国情绪总览** — 周级时序、情绪结构、异常事件、省份排行
- **中国情绪地图** — 34 省气泡图，支持情绪温度 / 6 维情绪 / 主导情绪切换
- **省份详情** — 单省情绪曲线、月度趋势、样本量
- **聚类分析** — 层次聚类 + KMeans，省份画像和演化热力图
- **事件时间线** — rolling z-score 异常检测，贡献省份 Top 5

## 技术栈

| 层 | 技术 |
|---|---|
| 数据处理 | Python 3.12, pandas, scikit-learn, scipy |
| 情绪标注 | DeepSeek API (OpenAI SDK 兼容) |
| 验证基准 | SMP2020-EWECT (Accuracy 73.3%, Macro F1 0.662) |
| 前端 | React 18, TypeScript, ECharts, Framer Motion |
| 构建 | Vite 7, CSS Modules |

## 快速开始

### 前端

```bash
cd app
npm install
npm run dev
```

访问 http://localhost:5173/

### 数据管线

```bash
# 复制 .env.example 为 .env 并填入 DeepSeek API Key
cp .env.example .env

conda activate py312
pip install -r requirements.txt

# 运行聚合管线（需要先完成标注）
python scripts/04_aggregate_emotions.py
python scripts/05_detect_anomalies.py
python scripts/06_cluster_provinces.py
python scripts/07_cluster_evolution.py
python scripts/08_prepare_frontend_assets.py
```

## 项目结构

```
Mood_Weather_Station/
├── app/                    # React 前端
│   ├── src/
│   │   ├── components/     # 地图、图表、卡片组件
│   │   ├── pages/          # 4 个页面：总览/详情/聚类/事件
│   │   ├── data/           # 数据加载和坐标配置
│   │   ├── hooks/          # 数据获取 Hook
│   │   └── utils/          # 日期、分析、指标工具
│   └── public/
│       ├── data/           # 前端静态数据 (CSV/JSON)
│       ├── maps/           # 地图底图和 GeoJSON
│       └── analysis/       # 词云等可视化产物
├── scripts/                # Python 数据管线 (00-08)
├── data/
│   ├── raw/                # 原始数据 (COV-Weibo2.0, SMP2020)
│   └── processed/          # 处理后数据集
├── docs/                   # 方法论文档
└── analysis/               # 验证报告和可视化产物
```

## 数据管线

| 步骤 | 脚本 | 说明 |
|---:|---|---|
| 00 | `00_probe_data_feasibility.py` | 数据可行性探测 |
| 01 | `01_build_mini_dataset.py` | 构建 76,441 条样本集 |
| 02 | `02_label_emotions.py` | DeepSeek 6 维情绪标注 |
| 03 | `03_validate_emotions.py` | SMP2020 外部验证 |
| 04 | `04_aggregate_emotions.py` | 周/月/省聚合 |
| 05 | `05_detect_anomalies.py` | 异常检测 (z-score) |
| 06 | `06_cluster_provinces.py` | 省份聚类 |
| 07 | `07_cluster_evolution.py` | 聚类演化 |
| 08 | `08_prepare_frontend_assets.py` | 前端数据导出 |

## 情绪标注

每条微博标注 6 维情绪分数，总和为 1：

| 情绪 | 标签 | Pilot 3000 均值 |
|---|---|---:|
| joy | 喜悦 | 0.2716 |
| sadness | 悲伤 | 0.0977 |
| anger | 愤怒 | 0.1024 |
| fear | 恐惧 | 0.0371 |
| surprise | 惊讶 | 0.0595 |
| neutral | 中性 | 0.4317 |

验证结果：Accuracy 73.3%, Macro F1 0.662 (2000 SMP2020 样本)

## License

[MIT](LICENSE)
