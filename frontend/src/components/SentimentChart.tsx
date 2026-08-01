// components/SentimentChart.tsx
import React, { useEffect, useRef } from 'react';

interface SentimentChartProps {
  value: number;
  label?: string;
}

const SentimentChart: React.FC<SentimentChartProps> = ({ value, label = 'Customer Satisfaction' }) => {
  const needleRef = useRef<HTMLDivElement>(null);
  const scoreRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (needleRef.current) {
      const angle = -90 + (Math.max(0, Math.min(100, value)) / 100) * 180;
      needleRef.current.style.transform = `translateX(-50%) rotate(${angle}deg)`;
    }
    if (scoreRef.current) {
      scoreRef.current.textContent = Math.round(value).toString();
    }
  }, [value]);

  const getColor = (val: number) => {
    if (val <= 33) return '#E85D1F';
    if (val <= 66) return '#F39C12';
    return '#4CAF50';
  };

  const getMouthPath = (val: number) => {
    if (val <= 33) return 'M 35 65 Q 50 80 65 65';
    if (val <= 66) return 'M 35 65 Q 50 72 65 65';
    return 'M 35 65 Q 50 50 65 65';
  };

  const getStatus = (val: number) => {
    if (val <= 33) return 'Needs Improvement';
    if (val <= 66) return 'Average';
    return 'Excellent';
  };

  const getStatusClass = (val: number) => {
    if (val <= 33) return 'poor';
    if (val <= 66) return 'average';
    return 'excellent';
  };

  return (
    <div className="sentiment-chart">
      <h3 className="chart-title">{label}</h3>
      
      <div className="gauge-wrapper">
        <div className="gauge">
          <div className="segment red" />
          <div className="segment yellow" />
          <div className="segment green" />
          
          <div className="hub">
            <svg className="face-svg" viewBox="0 0 100 100">
              <circle 
                className="eye left" 
                cx="35" 
                cy="40" 
                r="6" 
                stroke={getColor(value)}
              />
              <circle 
                className="eye right" 
                cx="65" 
                cy="40" 
                r="6" 
                stroke={getColor(value)}
              />
              <path 
                className="mouth" 
                d={getMouthPath(value)} 
                stroke={getColor(value)}
              />
            </svg>
            <div className="needle" ref={needleRef} />
            <div className="pivot" />
          </div>
          
          <span className="score" ref={scoreRef}>50</span>
        </div>

        <div className="gauge-status">
          <span className="status-value">{Math.round(value)}%</span>
          <span className={`status-label ${getStatusClass(value)}`}>
            {getStatus(value)}
          </span>
        </div>

        <div className="gauge-slider-container">
          <input
            type="range"
            min="0"
            max="100"
            value={value}
            className="gauge-slider"
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              if (window.setMood) {
                window.setMood(val);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default SentimentChart;