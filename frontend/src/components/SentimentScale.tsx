import React, { useEffect, useState, useRef } from 'react';
import './SentimentScale.css';

interface SentimentScaleProps {
  sentiment: 'negative' | 'neutral' | 'positive';
  animate: boolean;
  score?: number; // Keep for potential future use, but NOT for bar width
}

const SentimentScale: React.FC<SentimentScaleProps> = ({ 
  sentiment, 
  animate, 
  score = 50 
}) => {
  const [shouldAnimate, setShouldAnimate] = useState(false);
  const [hasReducedMotion, setHasReducedMotion] = useState(false);
  const [barFillWidth, setBarFillWidth] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevSentimentRef = useRef<string>(sentiment);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setHasReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setHasReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Reset bar when sentiment changes
  useEffect(() => {
    if (prevSentimentRef.current !== sentiment) {
      setBarFillWidth(0);
      setIsAnimating(true);
      prevSentimentRef.current = sentiment;
    }
  }, [sentiment]);

  // Handle entrance animation
  useEffect(() => {
    if (animate) {
      if (hasReducedMotion) {
        setShouldAnimate(true);
      } else {
        const timer = setTimeout(() => {
          setShouldAnimate(true);
        }, 50);
        return () => clearTimeout(timer);
      }
    } else {
      setShouldAnimate(false);
    }
  }, [animate, hasReducedMotion]);

  // ✅ FIX: Animate bar to 100% after faces appear
  useEffect(() => {
    if (shouldAnimate) {
      const delay = hasReducedMotion ? 100 : 600;
      const timer = setTimeout(() => {
        // ✅ ALWAYS fill to 100% - NOT the score value
        setBarFillWidth(100);
        setIsAnimating(false);
      }, delay);
      return () => clearTimeout(timer);
    } else {
      setBarFillWidth(0);
      setIsAnimating(false);
    }
  }, [shouldAnimate, hasReducedMotion]);

  // ✅ DYNAMIC BAR COLOR - SINGLE COLOR BASED ON SENTIMENT
  const getFillColor = (): string => {
    switch (sentiment) {
      case 'negative':
        return '#FF4438'; // Red - matches Negative face
      case 'neutral':
        return '#FFD530'; // Yellow - matches Neutral face  
      case 'positive':
        return '#7ED957'; // Green - matches Positive face
      default:
        return '#7ED957'; // Fallback to green
    }
  };

  // Face configurations with exact colors
  const faces = [
    {
      id: 'negative',
      label: 'Negative',
      bgColor: '#FF4438',
      eyeColor: '#B71C1C',
      mouthColor: '#B71C1C',
      mouthPath: 'M 30 65 Q 50 45 70 65',
      isActive: sentiment === 'negative',
      delay: 0,
    },
    {
      id: 'neutral',
      label: 'Neutral',
      bgColor: '#FFD530',
      eyeColor: '#E8890C',
      mouthColor: '#E8890C',
      mouthPath: 'M 32 60 L 68 60',
      isActive: sentiment === 'neutral',
      delay: 120,
    },
    {
      id: 'positive',
      label: 'Positive',
      bgColor: '#7ED957',
      eyeColor: '#4CAF50',
      mouthColor: '#4CAF50',
      mouthPath: 'M 30 55 Q 50 75 70 55',
      isActive: sentiment === 'positive',
      delay: 240,
    },
  ];

  const fillColor = getFillColor();
  const displayWidth = Math.max(0, Math.min(100, barFillWidth));

  return (
    <div className="sentiment-scale" ref={containerRef}>
      {/* Faces Row */}
      <div className="faces-row">
        {faces.map((face) => (
          <div
            key={face.id}
            className={`face-wrapper ${shouldAnimate ? 'animate-in' : ''} ${face.isActive ? 'active' : 'inactive'}`}
            style={{
              animationDelay: hasReducedMotion ? '0ms' : `${face.delay}ms`,
            }}
          >
            <div
              className={`face-circle ${face.isActive ? 'active' : ''}`}
              style={{
                backgroundColor: face.bgColor,
              }}
            >
              <svg viewBox="0 0 100 100" className="face-svg">
                <circle cx="32" cy="42" r="6" fill={face.eyeColor} />
                <circle cx="68" cy="42" r="6" fill={face.eyeColor} />
                {face.id === 'neutral' ? (
                  <rect x="32" y="58" width="36" height="5" rx="2.5" fill={face.mouthColor} />
                ) : (
                  <path 
                    d={face.mouthPath} 
                    stroke={face.mouthColor} 
                    strokeWidth="5" 
                    fill="none" 
                    strokeLinecap="round" 
                  />
                )}
              </svg>
            </div>
            <span className={`face-label ${face.isActive ? 'active' : ''}`}>
              {face.label}
            </span>
          </div>
        ))}
      </div>

      {/* ✅ SINGLE COLOR FILL BAR - ALWAYS 100% WIDTH */}
      <div className="bar-container">
        <div className="bar-track">
          <div
            className="bar-fill"
            style={{
              width: `${displayWidth}%`,
              backgroundColor: fillColor,
              transition: isAnimating ? 'width 1s cubic-bezier(0.34, 1.56, 0.64, 1)' : 'width 0.3s ease',
            }}
          />
        </div>
        <div className="bar-labels">
          <span>Negative</span>
          <span>Neutral</span>
          <span>Positive</span>
        </div>
      </div>
    </div>
  );
};

export default SentimentScale;