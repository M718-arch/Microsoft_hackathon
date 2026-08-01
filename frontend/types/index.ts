// src/types/index.ts
export interface ReviewRequest {
  text: string;
  star_rating?: number | null;
  threshold?: number;
}

export interface ReviewResponse {
  review_id?: number;
  text: string;
  translated?: string;
  aspects: string[];
  aspect_sentiments: Record<string, string>;
  sentiment_counts: {
    positive: number;
    negative: number;
    neutral: number;
  };
  confidence?: Record<string, number>;
  processing_time?: number;
  error?: string;
}

export interface BatchResponse {
  results: ReviewResponse[];
  summary: {
    positive: number;
    negative: number;
    neutral: number;
  };
  total_processed: number;
  errors: Array<{
    index: number;
    text: string;
    error: string;
  }>;
}

export interface ModelInfo {
  model_loaded: boolean;
  model_path?: string;
  threshold: number;
  device: string;
  f1_score?: number;
  mode?: string;
}

// ✅ No emojis - plain text only
export const ASPECT_LABELS: Record<string, string> = {
  food: 'Food',
  service: 'Service',
  price: 'Price',
  cleanliness: 'Cleanliness',
  delivery: 'Delivery',
  ambiance: 'Ambiance',
  app_experience: 'App Experience',
  general: 'General',
  none: '—'
};

// ✅ REMOVED - No emoji mapping
// export const SENTIMENT_EMOJI: Record<string, string> = { ... };

// ✅ Keep color mapping only
export const SENTIMENT_COLORS: Record<string, string> = {
  positive: 'sentiment-positive',
  negative: 'sentiment-negative',
  neutral: 'sentiment-neutral'
};