import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { absaApi } from './services/api';
import { ReviewResponse } from './types';
import Sidebar from './components/Sidebar';
import ReviewInput from './components/ReviewInput';
import SentimentScale from './components/SentimentScale';
import Translator from './components/Translator';
import BatchUpload from './components/BatchUpload';
import './styles/globals.css';
import './styles/layout.css';
import './styles/sidebar.css';
import './styles/review.css';
import './styles/translator.css';
import './styles/batch.css';

type TabType = 'review' | 'translator' | 'batch';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('review');
  const [threshold, setThreshold] = useState(0.6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    checkModelStatus();
  }, []);

  const checkModelStatus = async () => {
    try {
      const info = await absaApi.getModelInfo();
      setModelLoaded(info.model_loaded);
      if (info.model_loaded) {
        toast.success('Model ready!');
      } else {
        toast('Model not loaded. Running in demo mode.', { icon: '⚠️' });
      }
    } catch (error: any) {
      console.error('Failed to get model info:', error);
      setError('Backend not running. Start it with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000');
      toast.error('Cannot connect to backend. Make sure it\'s running on port 8000.');
    }
  };

  const handlePredict = async (text: string, starRating?: number | null) => {
    if (!text.trim()) {
      toast.error('Please enter a review');
      return;
    }

    setLoading(true);
    setShowResult(false);
    setResult(null);
    setError(null);
    setAnalysisComplete(false);

    try {
      console.log('Analyzing review:', text);
      
      const response = await absaApi.predict({
        text: text.trim(),
        star_rating: starRating,
        threshold: threshold
      });
      
      console.log('API Response received:', response);
      
      if (!response) {
        throw new Error('Empty response from API');
      }
      
      setResult(response);
      setAnalysisComplete(true);
      
      setTimeout(() => {
        setShowResult(true);
      }, 100);
      
      if (response.aspects?.length === 0) {
        toast('No aspects detected. Try lowering the threshold.', {
          icon: '⚠️',
        });
      } else {
        toast.success('Analysis complete!');
      }
    } catch (error: any) {
      console.error('Prediction error:', error);
      setError(error.response?.data?.detail || error.message || 'Error analyzing review');
      toast.error(error.response?.data?.detail || 'Error analyzing review');
      setAnalysisComplete(false);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentFromAspects = (res: ReviewResponse): 'negative' | 'neutral' | 'positive' => {
    const aspectSentiments = res.aspect_sentiments || {};
    const aspects = res.aspects || [];
    
    const validAspects = aspects.filter((a: string) => a !== 'none');
    
    if (validAspects.length === 0) {
      return 'neutral';
    }
    
    let positiveCount = 0;
    let negativeCount = 0;
    let neutralCount = 0;
    
    for (const aspect of validAspects) {
      const sentiment = aspectSentiments[aspect];
      if (sentiment === 'positive') positiveCount++;
      else if (sentiment === 'negative') negativeCount++;
      else if (sentiment === 'neutral') neutralCount++;
    }
    
    if (positiveCount > negativeCount && positiveCount >= neutralCount) {
      return 'positive';
    }
    if (negativeCount > positiveCount && negativeCount >= neutralCount) {
      return 'negative';
    }
    if (neutralCount > positiveCount && neutralCount > negativeCount) {
      return 'neutral';
    }
    
    if (positiveCount > 0) return 'positive';
    if (negativeCount > 0) return 'negative';
    
    return 'neutral';
  };

  const getSentimentFromCounts = (res: ReviewResponse): 'negative' | 'neutral' | 'positive' => {
    const counts = res.sentiment_counts || { positive: 0, negative: 0, neutral: 0 };
    
    if (counts.positive > counts.negative && counts.positive > counts.neutral) {
      return 'positive';
    }
    if (counts.negative > counts.positive && counts.negative > counts.neutral) {
      return 'negative';
    }
    if (counts.neutral > counts.positive && counts.neutral > counts.negative) {
      return 'neutral';
    }
    
    return getSentimentFromAspects(res);
  };

  const getOverallSentiment = (res: ReviewResponse): 'negative' | 'neutral' | 'positive' => {
    const fromAspects = getSentimentFromAspects(res);
    if (fromAspects !== 'neutral') {
      return fromAspects;
    }
    return getSentimentFromCounts(res);
  };

  const getSentimentLabel = (sentiment: string): string => {
    if (sentiment === 'positive') return 'Satisfied';
    if (sentiment === 'negative') return 'Unsatisfied';
    return 'Neutral';
  };

  const getSentimentDescription = (sentiment: string): string => {
    if (sentiment === 'positive') {
      return 'Your review expresses a positive experience with the restaurant.';
    }
    if (sentiment === 'negative') {
      return 'Your review expresses a negative experience with the restaurant.';
    }
    return 'Your review expresses a neutral experience with the restaurant.';
  };

  const getCurrentSentiment = (): 'negative' | 'neutral' | 'positive' => {
    if (!result) return 'neutral';
    return getOverallSentiment(result);
  };

  const getTabHeader = () => {
    switch (activeTab) {
      case 'review':
        return {
          title: 'Restaurant Review Analyzer',
          subtitle: 'Analyze customer feedback using AI.'
        };
      case 'translator':
        return {
          title: 'Franco-Arabic Translator',
          subtitle: 'Convert Egyptian Franco-Arabic into Arabic instantly.'
        };
      case 'batch':
        return {
          title: 'Batch Upload',
          subtitle: 'Analyze multiple restaurant reviews at once.'
        };
      default:
        return {
          title: 'Restaurant Review Analyzer',
          subtitle: 'Analyze customer feedback using AI.'
        };
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'review':
        return (
          <>
            <ReviewInput 
              onPredict={handlePredict} 
              loading={loading}
              threshold={threshold}
            />

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {result && showResult && analysisComplete && (
              <div className="result-section">
                <SentimentScale 
                  sentiment={getCurrentSentiment()}
                  animate={true}
                />
                
                <div className="result-details">
                  <div className="result-label">
                    {getSentimentLabel(getCurrentSentiment())}
                  </div>
                  <p className="result-description">
                    {getSentimentDescription(getCurrentSentiment())}
                  </p>
                </div>
              </div>
            )}
          </>
        );
      
      case 'translator':
        return <Translator />;
      
      case 'batch':
        return <BatchUpload />;
      
      default:
        return null;
    }
  };

  const header = getTabHeader();

  return (
    <div className="app">
      <Toaster position="top-right" />
      
      <div className="app-container">
        <Sidebar 
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          threshold={threshold}
          onThresholdChange={setThreshold}
          modelLoaded={modelLoaded}
        />

        <div className="main-content">
          <div className="analyzer-wrapper">
            <div className="analyzer-panel">
              {/* Tab-specific Header */}
              <div className="analyzer-header">
                <h1 className="analyzer-title">{header.title}</h1>
                <p className="analyzer-subtitle">{header.subtitle}</p>
              </div>

              {/* Content changes based on active tab */}
              {renderContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;