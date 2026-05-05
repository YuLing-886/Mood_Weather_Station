# 脚本流水线

## 当前运行策略

不重跑 `00` 和 `01`。从 `02` 开始按 province-level V1 继续推进。

## 脚本清单

| Step | 脚本 | 状态 | 输入 | 主要输出 |
|---:|---|---|---|---|
| 00 | `scripts/00_probe_data_feasibility.py` | 已被人工复核修正 | raw 数据 | `tmp/00_feasibility_report.json` |
| 01 | `scripts/01_build_mini_dataset.py` | ✅ 已完成 | raw CSV + users.db | `data/processed/mini_dataset.csv` (76,441 rows) |
| 02 | `scripts/02_label_emotions.py` | ✅ pilot 3000 条 | `mini_dataset.csv` | `labeled_dataset.csv` (3000 rows) |
| 02b | `scripts/02b_build_stratified_relabel_plan.py` | ✅ dry-run 就绪 | mini + labeled | 补标计划 CSV + summary JSON |
| 02c | `scripts/02c_merge_labeled_datasets.py` | ✅ 就绪 | old + new labeled | 合并后 CSV + summary JSON |
| 03 | `scripts/03_validate_emotions.py` | ✅ 2000 SMP 样本 | SMP2020 + labeled | accuracy=73.3%, macro F1=0.662 |
| 04 | `scripts/04_aggregate_emotions.py` | ✅ 已完成 | `labeled_dataset.csv` | 1,055 周行, 372 月行, 34 省向量 |
| 05 | `scripts/05_detect_anomalies.py` | ✅ 已修复 | national + weekly panel | `anomaly_detection.json` |
| 06 | `scripts/06_cluster_provinces.py` | ✅ 已完成 | province vectors | 18 省 6 聚类, silhouette=0.2708 |
| 07 | `scripts/07_cluster_evolution.py` | ✅ 已完成 | monthly panel | 月度聚类演化 CSV |
| 08 | `scripts/08_prepare_frontend_assets.py` | ✅ 已完成 | processed + analysis | `app/public/` 15 个静态资产 |

## 推荐运行顺序

```powershell
conda activate py312

# 先估算 token 与成本
python scripts/02_label_emotions.py --mode smoke --dry-run

# 小样本标注
python scripts/02_label_emotions.py --mode smoke

# SMP2020 验证，可先少量样本试跑
python scripts/03_validate_emotions.py --max-samples 120

# 如果 smoke 与验证正常，再进入 pilot/full
python scripts/02_label_emotions.py --mode pilot
python scripts/03_validate_emotions.py --max-samples 2000

# 聚合与分析（无需传参数，自动读取 labeled_dataset.csv）
python scripts/04_aggregate_emotions.py
python scripts/05_detect_anomalies.py
python scripts/06_cluster_provinces.py
python scripts/07_cluster_evolution.py
python scripts/08_prepare_frontend_assets.py

# 前端构建与启动
cd app
npm install
npm run prepare:data
npm run build
npx vite --host
```

## 分层补标流程

```powershell
conda activate py312

# 1. 生成补标计划（dry-run，不调用 API）
python scripts/02b_build_stratified_relabel_plan.py --cap 30 --seed 42 --output data/processed/stratified_label_plan_cap30.csv --summary tmp/02b_stratified_label_plan_cap30_summary.json

# 2. 执行补标（会调用 DeepSeek API，产生费用）
python scripts/02_label_emotions.py --input data/processed/stratified_label_plan_cap30.csv --output data/processed/labeled_dataset_stratified_new_cap30.csv

# 3. 合并新旧标注
python scripts/02c_merge_labeled_datasets.py --old data/processed/labeled_dataset.csv --new data/processed/labeled_dataset_stratified_new_cap30.csv --output data/processed/labeled_dataset_merged_cap30.csv

# 4. 用合并后的数据集重新运行聚合（需要临时替换 labeled_dataset.csv）
python scripts/04_aggregate_emotions.py
python scripts/05_detect_anomalies.py
python scripts/06_cluster_provinces.py
python scripts/07_cluster_evolution.py
python scripts/08_prepare_frontend_assets.py
```

## 300 条 smoke 跑法

```powershell
.\scripts\run_smoke_pipeline.ps1
```

smoke 运行会临时把：

- `MIN_POSTS_RELIABLE=1`
- `MIN_CLUSTER_POSTS=1`
- `MIN_MONTHLY_CLUSTER_POSTS=1`

这样 300 条样本也能把整条省级 V1 链路跑完，方便看图和页面效果。

## 输出依赖

```text
mini_dataset.csv
  -> 02 labeled_dataset.csv
      -> 03 validation reports
      -> 04 aggregate panels
          -> 05 anomaly_detection.json
          -> 06 cluster_labels.csv
          -> 07 monthly_cluster_labels.csv
              -> 08 frontend assets
```

## 关键注意事项

- `.env` 只放本地，不提交 API key。
- `02` 输出必须保留 `post_id/date_week/date_month/province/content_clean/word_count` 等原始字段。
- 省级面板只使用 34 标准省份。
- 22 条噪声省份值会在聚合阶段过滤，不影响 V1。
- `08` 如果缺少关键文件会返回非零退出码，方便发现链路断点。
