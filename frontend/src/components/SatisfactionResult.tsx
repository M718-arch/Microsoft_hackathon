// src/components/SatisfactionResult.tsx
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Smile, Meh, Frown } from 'lucide-react';

interface SatisfactionResultProps {
  sentiment: 'Positive' | 'Neutral' | 'Negative';
  score: number;
  label: string;
  description: string;
}

// SVG Face Components - 3D style, NO EMOJIS
const NegativeFace3D: React.FC<{ active: boolean }> = ({ active }) => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <ellipse cx="60" cy="80" rx="44" ry="8" fill="rgba(0,0,0,0.06)" />
    <defs>
      <radialGradient id="negGrad" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stopColor="#FEE2E2" />
        <stop offset="100%" stopColor="#FCA5A5" />
      </radialGradient>
      <radialGradient id="negShadow" cx="50%" cy="80%" r="50%">
        <stop offset="0%" stopColor="rgba(239,68,68,0.15)" />
        <stop offset="100%" stopColor="rgba(239,68,68,0)" />
      </radialGradient>
    </defs>
    <circle cx="60" cy="58" r="48" fill="url(#negGrad)" />
    <circle cx="60" cy="58" r="48" fill="url(#negShadow)" />
    <circle cx="60" cy="58" r="48" fill="none" stroke="#DC2626" strokeWidth="2.5" />
    <ellipse cx="48" cy="40" rx="16" ry="10" fill="rgba(255,255,255,0.3)" />
    <path d="M 30 38 L 44 44" stroke="#1A1A2E" strokeWidth="4" strokeLinecap="round" fill="none" />
    <path d="M 90 38 L 76 44" stroke="#1A1A2E" strokeWidth="4" strokeLinecap="round" fill="none" />
    <path d="M 34 56 Q 40 51 46 56" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M 74 56 Q 80 51 86 56" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M 36 76 Q 60 62 84 76" stroke="#1A1A2E" strokeWidth="4" strokeLinecap="round" fill="none" />
  </svg>
);

const NeutralFace3D: React.FC<{ active: boolean }> = ({ active }) => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <ellipse cx="60" cy="80" rx="44" ry="8" fill="rgba(0,0,0,0.06)" />
    <defs>
      <radialGradient id="neuGrad" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stopColor="#FEF3C7" />
        <stop offset="100%" stopColor="#FDE68A" />
      </radialGradient>
      <radialGradient id="neuShadow" cx="50%" cy="80%" r="50%">
        <stop offset="0%" stopColor="rgba(245,158,11,0.12)" />
        <stop offset="100%" stopColor="rgba(245,158,11,0)" />
      </radialGradient>
    </defs>
    <circle cx="60" cy="58" r="48" fill="url(#neuGrad)" />
    <circle cx="60" cy="58" r="48" fill="url(#neuShadow)" />
    <circle cx="60" cy="58" r="48" fill="none" stroke="#D97706" strokeWidth="2.5" />
    <ellipse cx="48" cy="40" rx="16" ry="10" fill="rgba(255,255,255,0.3)" />
    <circle cx="42" cy="52" r="7" fill="#1A1A2E" />
    <circle cx="78" cy="52" r="7" fill="#1A1A2E" />
    <circle cx="44" cy="49" r="3" fill="white" />
    <circle cx="80" cy="49" r="3" fill="white" />
    <path d="M 42 74 Q 60 76 78 74" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" fill="none" />
  </svg>
);

const PositiveFace3D: React.FC<{ active: boolean }> = ({ active }) => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <ellipse cx="60" cy="80" rx="44" ry="8" fill="rgba(0,0,0,0.06)" />
    <defs>
      <radialGradient id="posGrad" cx="40%" cy="35%" r="60%">
        <stop offset="0%" stopColor="#DCFCE7" />
        <stop offset="100%" stopColor="#86EFAC" />
      </radialGradient>
      <radialGradient id="posShadow" cx="50%" cy="80%" r="50%">
        <stop offset="0%" stopColor="rgba(34,197,94,0.12)" />
        <stop offset="100%" stopColor="rgba(34,197,94,0)" />
      </radialGradient>
    </defs>
    <circle cx="60" cy="58" r="48" fill="url(#posGrad)" />
    <circle cx="60" cy="58" r="48" fill="url(#posShadow)" />
    <circle cx="60" cy="58" r="48" fill="none" stroke="#16A34A" strokeWidth="2.5" />
    <ellipse cx="48" cy="40" rx="16" ry="10" fill="rgba(255,255,255,0.3)" />
    <circle cx="42" cy="52" r="8" fill="#1A1A2E" />
    <circle cx="78" cy="52" r="8" fill="#1A1A2E" />
    <circle cx="44" cy="48" r="3.5" fill="white" />
    <circle cx="80" cy="48" r="3.5" fill="white" />
    <path d="M 34 68 Q 60 92 86 68" stroke="#1A1A2E" strokeWidth="4" strokeLinecap="round" fill="none" />
  </svg>
);

const SatisfactionResult: React.FC<SatisfactionResultProps> = ({ 
  sentiment, 
  score, 
  label, 
  description 
}) => {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const duration = 700;
    const steps = 60;
    const increment = score / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current += increment;
      if (step >= steps) {
        setDisplayScore(score);
        clearInterval(timer);
      } else {
        setDisplayScore(Math.round(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score]);

  const faces = [
    { type: 'Negative' as const, component: NegativeFace3D, color: '#EF4444', label: 'Negative' },
    { type: 'Neutral' as const, component: NeutralFace3D, color: '#F59E0B', label: 'Neutral' },
    { type: 'Positive' as const, component: PositiveFace3D, color: '#22C55E', label: 'Positive' },
  ];

  const activeIndex = sentiment === 'Negative' ? 0 : sentiment === 'Neutral' ? 1 : 2;

  return (
    <motion.div 
      className="satisfaction-result"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h3 className="result-title">Satisfaction Rating</h3>

      <div className="faces-container">
        {faces.map((face, index) => {
          const FaceComponent = face.component;
          const isActive = index === activeIndex;

          return (
            <motion.div
              key={face.type}
              className={`face-wrapper ${isActive ? 'active' : 'inactive'}`}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ 
                scale: isActive ? 1.15 : 0.9,
                opacity: isActive ? 1 : 0.4,
                y: isActive ? -10 : 0,
              }}
              transition={{ 
                delay: index * 0.12 + 0.25,
                type: 'spring',
                stiffness: 400,
                damping: 28,
                duration: 0.5,
              }}
            >
              <div 
                className={`face-circle ${isActive ? 'active' : ''}`}
                style={{ 
                  borderColor: isActive ? face.color : '#E5E7EB',
                  boxShadow: isActive ? `0 0 40px ${face.color}33, 0 8px 24px ${face.color}22` : 'none'
                }}
              >
                <FaceComponent active={isActive} />
              </div>
              <span className={`face-label ${isActive ? 'active' : ''}`}>
                {face.label}
              </span>
            </motion.div>
          );
        })}
      </div>

      <div className="result-text">
        <div className="result-label">{label}</div>
        <p className="result-description">{description}</p>
      </div>
    </motion.div>
  );
};

export default SatisfactionResult;