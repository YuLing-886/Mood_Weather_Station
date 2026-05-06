# NLP 词云模块 QA Report

## 问题 1: echarts-wordcloud dispose 报错

### 报错原因

```
Cannot read properties of undefined (reading 'layoutInstance')
TypeError at echarts-wordcloud dispose
```

**根本原因：**

1. **React StrictMode 双重卸载**：开发环境 StrictMode 会 mount → unmount → mount 组件。第一次 unmount 时 echarts-wordcloud 开始 dispose（异步），第二次 mount 时创建新实例，导致旧实例的 `layoutInstance` 在 dispose 回调中已被 GC。

2. **option 频繁重建**：`selectedWord` 变化时，整个 option 对象被重建，触发 echarts 内部 `setOption` 的 diff，wordCloud 插件重新 layout，旧 layout 被打断时 `this.layoutInstance` 变成 undefined。

3. **缺少错误边界**：一旦 dispose 报错，整个组件树崩溃白屏。

### 修复

- 拆分 baseOption 与 highlight 更新
- 移除 React.StrictMode
- 添加 WordCloudErrorBoundary
- 空数据保护

---

## 问题 2: 筛选按钮不生效

### 报错原因

1. **后端数据不足**：每周只有 Top 30 keywords，且全部标记为 surge=true（SURGE_THRESHOLD=2.0 太低）
2. **前端状态逻辑错误**：
   - viewMode 只有 "all" 和 "surge"，没有 "high_frequency"
   - "all" 模式没有排序，直接返回原始数组
   - 没有使用 nlp_emotion_keywords 数据
   - 标题不随模式变化

### 修复

#### 后端 04b 脚本

1. 每周输出 80 个关键词（原来是 30）
2. 新增分组字段：
   - `top_keywords`: 按 tfidf 排序 Top 30
   - `frequent_keywords`: 按 tf 排序 Top 30
   - `surge_keywords`: 按 surge_ratio 排序 Top 30
   - `keywords`: 全量 Top 80
3. `build_emotion_keywords` 为所有情绪生成关键词（原来只生成 dominant_emotion）

#### 前端 NlpPanel

1. 三个独立 keywordMode: "top" | "frequent" | "surge"
2. emotionFilter: "all" | "current"
3. `displayedKeywords` 根据模式使用不同数据源：
   - frequent → `weekData.frequent_keywords`
   - surge → `weekData.surge_keywords`
   - top → `weekData.top_keywords`
   - current emotion → `nlpEmotionKeywords.emotions[emotion]`
4. 标题和说明文案随模式变化
5. 切换模式时清空 selectedWord

---

## 修改文件列表

| 文件 | 改动 |
|------|------|
| `scripts/04b_nlp_keywords.py` | 输出分组关键词字段，扩大到 80，修复 emotion_keywords |
| `app/src/types/nlp.ts` | NlpWeekKeywords 新增 top_keywords/frequent_keywords/surge_keywords |
| `app/src/components/NlpPanel.tsx` | 重写筛选逻辑，三个模式独立数据源 |
| `app/src/pages/EventTimeline.tsx` | 传递 emotionKeywords 给 NlpPanel |
| `app/src/main.tsx` | 移除 React.StrictMode |

## 依赖版本（未调整）

| 包 | 版本 |
|---|---|
| echarts | ^5.6.0 |
| echarts-for-react | ^3.0.2 |
| echarts-wordcloud | ^2.1.0 |

## npm run build 结果

通过，无 TypeScript 错误。
