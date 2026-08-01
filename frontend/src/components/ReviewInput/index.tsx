import React, { useState, useEffect } from 'react';
import { Star, Send, Mic } from 'lucide-react';

interface ReviewInputProps {
  onPredict: (text: string, starRating?: number | null) => void;
  loading: boolean;
  threshold: number;
}

const ReviewInput: React.FC<ReviewInputProps> = ({ onPredict, loading, threshold }) => {
  const [text, setText] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [hoveredStar, setHoveredStar] = useState<number | null>(null);

  useEffect(() => {
    const handleSetText = (e: CustomEvent<string>) => {
      setText(e.detail);
    };
    window.addEventListener('setReviewText' as any, handleSetText);
    return () => window.removeEventListener('setReviewText' as any, handleSetText);
  }, []);

  const handleSubmit = () => {
    onPredict(text, rating);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isStarActive = (star: number) => {
    if (hoveredStar !== null) return star <= hoveredStar;
    if (rating !== null) return star <= rating;
    return false;
  };

  return (
    <div className="review-input-container">
      <div className="textarea-wrapper">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tell us about your dining experience..."
          className="review-textarea"
          disabled={loading}
          rows={3}
        />
        <button className="mic-btn" title="Voice input">
          <Mic size={18} />
        </button>
      </div>

      <div className="input-actions">
        <div className="rating-section">
          <span className="rating-label">Rate your experience</span>
          <div className="stars-container">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                className={`star-btn ${isStarActive(star) ? 'active' : ''}`}
                onMouseEnter={() => setHoveredStar(star)}
                onMouseLeave={() => setHoveredStar(null)}
                onClick={() => setRating(star === rating ? null : star)}
                disabled={loading}
              >
                <Star 
                  size={22} 
                  fill={isStarActive(star) ? '#FBBF24' : 'none'}
                  color={isStarActive(star) ? '#FBBF24' : '#D4C9B8'}
                />
              </button>
            ))}
          </div>
          {rating && (
            <span className="rating-value">{rating} / 5</span>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !text.trim()}
          className="analyze-btn"
        >
          {loading ? (
            <>
              <span className="spinner" />
              Analyzing...
            </>
          ) : (
            <>
              <Send size={18} />
              Analyze Review
            </>
          )}
        </button>
      </div>

      <div className="input-stats">
        <span>{text.length} characters</span>
        <span>•</span>
        <span>{text.split(/\s+/).filter(Boolean).length} words</span>
        <span>•</span>
        <span>Threshold: {threshold.toFixed(2)}</span>
      </div>
    </div>
  );
};

export default ReviewInput;