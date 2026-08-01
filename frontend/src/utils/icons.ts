// src/utils/icons.ts
import {
  Utensils,
  Handshake,
  Coins,
  Sparkles,
  Bike,
  Smartphone,
  MessageCircle,
  Smile,
  Meh,
  Frown,
  Coffee,
  Star,
} from 'lucide-react';

// Aspect Icons Mapping - SVG icons, no emojis
export const ASPECT_ICONS = {
  food: Utensils,
  service: Handshake,
  price: Coins,
  cleanliness: Sparkles,
  delivery: Bike,
  ambiance: Sparkles,
  app_experience: Smartphone,
  general: MessageCircle,
  none: null,
};

// Sentiment Icons - SVG icons, no emojis
export const SENTIMENT_ICONS = {
  positive: Smile,
  neutral: Meh,
  negative: Frown,
};

// Get icon by aspect name
export const getAspectIcon = (aspect: string) => {
  return ASPECT_ICONS[aspect as keyof typeof ASPECT_ICONS] || MessageCircle;
};

// Get icon by sentiment
export const getSentimentIcon = (sentiment: string) => {
  return SENTIMENT_ICONS[sentiment as keyof typeof SENTIMENT_ICONS] || Meh;
};

// Application icons
export const APP_ICONS = {
  coffee: Coffee,
  star: Star,
};