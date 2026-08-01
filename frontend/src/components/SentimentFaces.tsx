import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

type SentimentType = 'Positive' | 'Neutral' | 'Negative';

interface SentimentFacesProps {
  sentiment: SentimentType;
  score: number;
  compact?: boolean;
}

// SVG Face Components
const NegativeFace: React.FC = () => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <circle cx="60" cy="60" r="54" fill="#FEE2E2" />
    <circle cx="60" cy="60" r="54" fill="none" stroke="#EF4444" strokeWidth="2.5" />
    <path d="M 32 38 L 42 44" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" />
    <path d="M 88 38 L 78 44" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" />
    <path d="M 35 54 Q 40 50 45 54" stroke="#1A1A2E" strokeWidth="3" strokeLinecap="round" fill="none" />
    <path d="M 75 54 Q 80 50 85 54" stroke="#1A1A2E" strokeWidth="3" strokeLinecap="round" fill="none" />
    <path d="M 38 74 Q 60 62 82 74" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M 28 48 L 32 50" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
    <path d="M 92 48 L 88 50" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" opacity="0.6" />
  </svg>
);

const NeutralFace: React.FC = () => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <circle cx="60" cy="60" r="54" fill="#FEF3C7" />
    <circle cx="60" cy="60" r="54" fill="none" stroke="#F59E0B" strokeWidth="2.5" />
    <circle cx="42" cy="52" r="6" fill="#1A1A2E" />
    <circle cx="78" cy="52" r="6" fill="#1A1A2E" />
    <circle cx="44" cy="50" r="2.5" fill="white" />
    <circle cx="80" cy="50" r="2.5" fill="white" />
    <path d="M 42 72 Q 60 74 78 72" stroke="#1A1A2E" strokeWidth="3" strokeLinecap="round" fill="none" />
  </svg>
);

const PositiveFace: React.FC = () => (
  <svg viewBox="0 0 120 120" className="w-full h-full">
    <circle cx="60" cy="60" r="54" fill="#DCFCE7" />
    <circle cx="60" cy="60" r="54" fill="none" stroke="#22C55E" strokeWidth="2.5" />
    <circle cx="42" cy="52" r="7" fill="#1A1A2E" />
    <circle cx="78" cy="52" r="7" fill="#1A1A2E" />
    <circle cx="44" cy="49" r="3" fill="white" />
    <circle cx="80" cy="49" r="3" fill="white" />
    <path d="M 35 66 Q 60 86 85 66" stroke="#1A1A2E" strokeWidth="3.5" strokeLinecap="round" fill="none" />
    <path d="M 28 62 Q 35 56 42 60" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.5" />
    <path d="M 78 60 Q 85 56 92 62" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.5" />
  </svg>
);

const SentimentFaces: React.FC<SentimentFacesProps> = ({ sentiment, score }) => {
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

  const getConfig = () => {
    if (sentiment === 'Positive') {
      return {
        bgColor: 'bg-green-50',
        barColor: 'bg-green-500',
        FaceComponent: PositiveFace,
        label: 'Positive',
        badgeColor: 'bg-green-100 text-green-700',
      };
    }
    if (sentiment === 'Negative') {
      return {
        bgColor: 'bg-red-50',
        barColor: 'bg-red-500',
        FaceComponent: NegativeFace,
        label: 'Negative',
        badgeColor: 'bg-red-100 text-red-700',
      };
    }
    return {
      bgColor: 'bg-yellow-50',
      barColor: 'bg-yellow-500',
      FaceComponent: NeutralFace,
      label: 'Neutral',
      badgeColor: 'bg-yellow-100 text-yellow-700',
    };
  };

  const config = getConfig();
  const FaceComponent = config.FaceComponent;

  const isActive = (type: SentimentType) => sentiment === type;

  return (
    <div className="w-full">
      {/* Faces Row */}
      <div className="flex items-center justify-center gap-6">
        <div className="flex flex-col items-center">
          <div className={`w-14 h-14 rounded-full p-1.5 transition-all duration-300 ${isActive('Negative') ? 'bg-red-50 scale-110 shadow-md shadow-red-200/30' : 'bg-red-50/40 scale-100 opacity-50'}`}>
            <NegativeFace />
          </div>
          <span className={`text-[9px] font-medium mt-0.5 ${isActive('Negative') ? 'text-red-500' : 'text-gray-300'}`}>Neg</span>
        </div>

        <div className="flex flex-col items-center">
          <div className={`w-14 h-14 rounded-full p-1.5 transition-all duration-300 ${isActive('Neutral') ? 'bg-yellow-50 scale-110 shadow-md shadow-yellow-200/30' : 'bg-yellow-50/40 scale-100 opacity-50'}`}>
            <NeutralFace />
          </div>
          <span className={`text-[9px] font-medium mt-0.5 ${isActive('Neutral') ? 'text-yellow-500' : 'text-gray-300'}`}>Neu</span>
        </div>

        <div className="flex flex-col items-center">
          <div className={`w-14 h-14 rounded-full p-1.5 transition-all duration-300 ${isActive('Positive') ? 'bg-green-50 scale-110 shadow-md shadow-green-200/30' : 'bg-green-50/40 scale-100 opacity-50'}`}>
            <PositiveFace />
          </div>
          <span className={`text-[9px] font-medium mt-0.5 ${isActive('Positive') ? 'text-green-500' : 'text-gray-300'}`}>Pos</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-gray-100 rounded-full overflow-hidden shadow-inner mt-2">
        <motion.div
          className={`h-full rounded-full ${config.barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(0, Math.min(100, score))}%` }}
          transition={{ duration: 0.7, ease: 'easeInOut' }}
        />
      </div>

      {/* Score and Status */}
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-[10px] font-medium text-gray-400">Satisfaction</span>
        <div className="flex items-center gap-2">
          <motion.span
            key={displayScore}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-base font-bold text-gray-800"
          >
            {displayScore}%
          </motion.span>
          <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${config.badgeColor}`}>
            {sentiment}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SentimentFaces;