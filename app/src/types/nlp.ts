import type { EmotionKey } from "../config";

export interface NlpKeyword {
  word: string;
  tf: number;
  tfidf: number;
  global_tfidf: number;
  surge: boolean;
  surge_ratio: number;
  pos: string;
}

export interface NlpWeekKeywords {
  status: "ok" | "insufficient_data" | "no_data";
  total_posts: number;
  min_required?: number;
  dominant_emotion?: EmotionKey;
  top_emotions?: EmotionKey[];
  top_keywords?: NlpKeyword[];
  frequent_keywords?: NlpKeyword[];
  surge_keywords?: NlpKeyword[];
  keywords: NlpKeyword[];
}

export interface NlpKeywordsByWeek {
  meta: {
    generated_at: string;
    source_file: string;
    min_posts_per_week: number;
    top_k: number;
    method: string;
    stopwords_source: string;
  };
  weeks: Record<string, NlpWeekKeywords>;
}

export interface NlpEmotionKeyword {
  word: string;
  avg_tfidf: number;
  peak_week: string;
  peak_tfidf: number;
}

export interface NlpEmotionKeywords {
  meta: {
    generated_at: string;
    method: string;
  };
  emotions: Partial<Record<EmotionKey, NlpEmotionKeyword[]>>;
}

export interface NlpGlobalVocabItem {
  word: string;
  total_tf: number;
  avg_tfidf: number;
  peak_week_idx: number;
  peak_tfidf: number;
}

export interface NlpGlobalVocabulary {
  meta: {
    generated_at: string;
    total_terms: number;
  };
  vocabulary: NlpGlobalVocabItem[];
}

export interface NlpData {
  keywordsByWeek: NlpKeywordsByWeek | null;
  emotionKeywords: NlpEmotionKeywords | null;
  globalVocabulary: NlpGlobalVocabulary | null;
}
