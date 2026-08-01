import React from 'react';

interface CategoryCardProps {
  category: string;
  sentiment: string;
}

const CategoryCard: React.FC<CategoryCardProps> = ({ category, sentiment }) => {
  const getEmoji = (cat: string) => {
    const emojis: Record<string, string> = {
      food: '🍽️',
      service: '🤝',
      price: '💰',
      cleanliness: '🧹',
      delivery: '🛵',
      ambiance: '✨',
      app_experience: '📱',
      general: '💬'
    };
    return emojis[cat] || '📌';
  };

  const getSentimentColor = (sent: string) => {
    if (sent === 'positive') return 'positive';
    if (sent === 'negative') return 'negative';
    return 'neutral';
  };

  return (
    <div className="category-card">
      <span className="category-icon">{getEmoji(category)}</span>
      <span className="category-name">{category}</span>
      <span className={`category-sentiment ${getSentimentColor(sentiment)}`}>
        {sentiment}
      </span>
    </div>
  );
};

export default CategoryCard;