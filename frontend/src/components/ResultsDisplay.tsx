// src/components/ResultsDisplay.tsx
import React, { useEffect, useState } from 'react';
import { ReviewResponse } from '../types';
import { Smile, Meh, Frown, Coffee } from 'lucide-react';
import { getAspectIcon } from '../utils/icons';

interface ResultsDisplayProps {
  result: ReviewResponse;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result }) => {
  const { sentiment_counts, aspects, aspect_sentiments } = result;
  const [counts, setCounts] = useState({ positive: 0, negative: 0, neutral: 0 });

  useEffect(() => {
    const target = {
      positive: sentiment_counts?.positive || 0,
      negative: sentiment_counts?.negative || 0,
      neutral: sentiment_counts?.neutral || 0
    };

    const duration = 600;
    const startTime = Date.now();
    const startValues = { positive: 0, negative: 0, neutral: 0 };

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      setCounts({
        positive: Math.round(startValues.positive + (target.positive - startValues.positive) * progress),
        negative: Math.round(startValues.negative + (target.negative - startValues.negative) * progress),
        neutral: Math.round(startValues.neutral + (target.neutral - startValues.neutral) * progress)
      });

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }, [sentiment_counts]);

  const getAspectIconComponent = (aspect: string) => {
    const Icon = getAspectIcon(aspect);
    return Icon ? <Icon size={18} className="aspect-icon-svg" /> : null;
  };

  return (
    <div className="results-display">
      <h3 className="results-title">Results Overview</h3>

      <div className="results-stats">
        <div className="stat-card happy">
          <div className="stat-icon">
            <Smile size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Happy Diners</span>
            <span className="stat-value">{counts.positive}</span>
            <span className="stat-sub">Reviews</span>
          </div>
        </div>

        <div className="stat-card average">
          <div className="stat-icon">
            <Meh size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Average Experience</span>
            <span className="stat-value">{counts.neutral}</span>
            <span className="stat-sub">Reviews</span>
          </div>
        </div>

        <div className="stat-card needs-improvement">
          <div className="stat-icon">
            <Frown size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Needs Improvement</span>
            <span className="stat-value">{counts.negative}</span>
            <span className="stat-sub">Reviews</span>
          </div>
        </div>
      </div>

      {aspects && aspects.length > 0 && (
        <div className="aspect-results">
          <h4 className="aspect-title">Detected Categories</h4>
          <div className="aspect-list">
            {aspects.filter(a => a !== 'none').map((aspect) => {
              const sentiment = aspect_sentiments?.[aspect] || 'neutral';
              return (
                <div key={aspect} className={`aspect-item ${sentiment}`}>
                  <span className="aspect-icon">
                    {getAspectIconComponent(aspect)}
                  </span>
                  <span className="aspect-name">{aspect}</span>
                  <span className={`aspect-sentiment ${sentiment}`}>
                    {sentiment}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {counts.positive === 0 && counts.negative === 0 && counts.neutral === 0 && (
        <div className="no-results">
          <Coffee size={28} />
          <p>No analysis yet. Submit a review to see results.</p>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;