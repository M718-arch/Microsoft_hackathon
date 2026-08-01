import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileSpreadsheet, 
  X, 
  Check, 
  Loader2, 
  BarChart3,
  FileText,
  AlertCircle,
  Download
} from 'lucide-react';
import { absaApi } from '../services/api';
import toast from 'react-hot-toast';

interface ReviewResult {
  review_id: number;
  text: string;
  aspects: string[];
  aspect_sentiments: Record<string, string>;
  sentiment_counts: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

interface UploadResponse {
  filename: string;
  total_processed: number;
  results: ReviewResult[];
  summary: {
    positive: number;
    negative: number;
    neutral: number;
  };
  errors: any[];
}

// Aspect icons mapping - Using custom image assets
const ASPECT_ICONS: Record<string, string> = {
  food: '/food.png',
  service: '/service.png',
  price: '/price.png',
  cleanliness: '/cleanliness.png',
  delivery: '/delivery.png',
  ambiance: '/ambiance.png',
  app_experience: '/app_experience.png',
  general: '/general.png',
};

const ASPECT_NAMES: Record<string, string> = {
  food: 'Food',
  service: 'Service',
  price: 'Price',
  cleanliness: 'Cleanliness',
  delivery: 'Delivery',
  ambiance: 'Ambiance',
  app_experience: 'App Experience',
  general: 'General',
};

const BatchUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<UploadResponse | null>(null);
  const [threshold, setThreshold] = useState(0.6);
  const [showAllResults, setShowAllResults] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setFile(file);
      setResults(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  });

  const handleRemoveFile = () => {
    setFile(null);
    setResults(null);
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    setLoading(true);
    try {
      const response = await absaApi.uploadFile(file, threshold);
      setResults(response);
      
      if (response.total_processed === 0) {
        toast.error('No valid reviews found in the file');
      } else {
        toast.success(`Processed ${response.total_processed} reviews!`);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error processing file');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!results) return;
    
    const jsonStr = JSON.stringify(results, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `absa_results_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getFileExtension = (filename: string) => {
    return filename.split('.').pop()?.toUpperCase() || 'FILE';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getSentimentLabel = (sentiment: string) => {
    if (sentiment === 'positive') return 'Positive';
    if (sentiment === 'negative') return 'Negative';
    return 'Neutral';
  };

  const getAspectIcon = (aspect: string) => {
    return ASPECT_ICONS[aspect] || '/general.png';
  };

  const getAspectName = (aspect: string) => {
    return ASPECT_NAMES[aspect] || aspect.charAt(0).toUpperCase() + aspect.slice(1);
  };

  const getAspectSummary = (results: ReviewResult[]) => {
    const aspectMap: Record<string, { positive: number; negative: number; neutral: number; total: number }> = {};
    
    const allAspects = ['food', 'service', 'price', 'cleanliness', 'delivery', 'ambiance', 'app_experience', 'general'];
    allAspects.forEach((aspect) => {
      aspectMap[aspect] = { positive: 0, negative: 0, neutral: 0, total: 0 };
    });
    
    results.forEach((r) => {
      r.aspects.forEach((aspect) => {
        if (aspect === 'none') return;
        if (!aspectMap[aspect]) {
          aspectMap[aspect] = { positive: 0, negative: 0, neutral: 0, total: 0 };
        }
        const sentiment = r.aspect_sentiments[aspect] || 'neutral';
        aspectMap[aspect][sentiment as keyof typeof aspectMap[typeof aspect]]++;
        aspectMap[aspect].total++;
      });
    });
    
    return aspectMap;
  };

  const getActiveAspects = (aspectMap: Record<string, any>) => {
    return Object.entries(aspectMap)
      .filter(([_, counts]) => counts.total > 0)
      .sort((a, b) => b[1].total - a[1].total);
  };

  return (
    <div className="batch-upload-modern">
      {/* Upload Area - Compact File Card */}
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
      >
        <input {...getInputProps()} />
        
        {!file ? (
          <div className="upload-content">
            <div className="upload-icon-wrap">
              <Upload size={28} />
            </div>
            <div className="upload-text">
              <span className="upload-title">Upload your review file</span>
              <span className="upload-description">
                Drag & drop your file here, or <span className="browse-link">Browse files</span>
              </span>
            </div>
            <div className="upload-formats">
              <span className="format-badge">.CSV</span>
              <span className="format-separator">•</span>
              <span className="format-badge">.XLSX</span>
              <span className="format-separator">•</span>
              <span className="format-badge">.TXT</span>
            </div>
          </div>
        ) : (
          <div className="file-card">
            <div className="file-card-icon">
              <FileSpreadsheet size={20} />
            </div>
            <div className="file-card-info">
              <span className="file-card-name">{file.name}</span>
              <span className="file-card-meta">
                {getFileExtension(file.name)} • {formatFileSize(file.size)} • {results ? results.total_processed : 0} reviews
              </span>
            </div>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveFile();
              }}
              className="file-card-remove"
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Threshold Section */}
      <div className="threshold-section-compact">
        <div className="threshold-header-compact">
          <label className="threshold-label-compact">Sentiment Threshold</label>
          <span className="threshold-value-compact">{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          value={threshold}
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          className="threshold-slider-modern"
          style={{
            background: `linear-gradient(to right, #F97316 0%, #F97316 ${((threshold - 0.1) / 0.8) * 100}%, #E8E0D6 ${((threshold - 0.1) / 0.8) * 100}%, #E8E0D6 100%)`
          }}
        />
        <p className="threshold-helper-compact">
          Higher = fewer, more confident aspect detections
        </p>
      </div>

      {/* Process Button */}
      <div className="process-section-compact">
        <button
          onClick={handleUpload}
          disabled={loading || !file}
          className="process-btn-compact"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="spinner" />
              Processing...
            </>
          ) : (
            <>
              <BarChart3 size={16} />
              Process File
            </>
          )}
        </button>
      </div>

      {/* Results Section - Only Aspect Detection */}
      {results && (
        <div className="results-section-full">
          {/* Results Header */}
          <div className="results-header-full">
            <div className="results-success-full">
              <Check size={18} />
              <span>Processed Successfully</span>
              <span className="results-count-badge-full">{results.total_processed} reviews</span>
            </div>
            <button onClick={handleDownload} className="results-download-full">
              <Download size={16} />
              Download Results
            </button>
          </div>

          {/* Aspect Detection - Full Width Cards with Two Column Layout */}
          {results.results && results.results.length > 0 && (
            <div className="aspect-section-full">
              <h3 className="aspect-section-title">Aspect Detection</h3>
              <div className="aspect-cards-full">
                {getActiveAspects(getAspectSummary(results.results)).map(([aspect, counts]) => {
                  const total = counts.total;
                  if (total === 0) return null;
                  const positivePct = Math.round((counts.positive / total) * 100);
                  const negativePct = Math.round((counts.negative / total) * 100);
                  const neutralPct = 100 - positivePct - negativePct;
                  
                  let dominantColor = 'neutral';
                  if (positivePct > negativePct && positivePct > neutralPct) dominantColor = 'positive';
                  else if (negativePct > positivePct && negativePct > neutralPct) dominantColor = 'negative';
                  
                  return (
                    <div key={aspect} className={`aspect-card-full ${dominantColor}`}>
                      {/* Left Column - Icon and Name */}
                      <div className="aspect-card-left">
                        <div className="aspect-card-icon">
                          <img 
                            src={getAspectIcon(aspect)} 
                            alt={getAspectName(aspect)}
                            className="aspect-icon-image"
                          />
                        </div>
                        <span className="aspect-card-name">{getAspectName(aspect)}</span>
                      </div>
                      
                      {/* Right Column - Bar and Percentages */}
                      <div className="aspect-card-right">
                        <div className="aspect-card-bar">
                          <div className="aspect-bar-positive" style={{ width: `${positivePct}%` }} />
                          <div className="aspect-bar-neutral" style={{ width: `${neutralPct}%` }} />
                          <div className="aspect-bar-negative" style={{ width: `${negativePct}%` }} />
                        </div>
                        <div className="aspect-card-pcts">
                          <span className="pct-positive">{positivePct}% Positive</span>
                          <span className="pct-neutral">{neutralPct}% Neutral</span>
                          <span className="pct-negative">{negativePct}% Negative</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Review Preview */}
          {results.results && results.results.length > 0 && (
            <div className="preview-section-full">
              <div className="preview-header-full">
                <h4>Review Preview</h4>
                <button 
                  className="toggle-preview-btn-full"
                  onClick={() => setShowAllResults(!showAllResults)}
                >
                  {showAllResults ? 'Show Less' : 'Show All'}
                </button>
              </div>
              {(showAllResults ? results.results : results.results.slice(0, 5)).map((r: ReviewResult, idx: number) => {
                const sentiment = Object.values(r.aspect_sentiments || {})[0] || 'neutral';
                const aspects = r.aspects.filter(a => a !== 'none').map(a => getAspectName(a)).join(', ') || 'General';
                return (
                  <div key={idx} className={`preview-item-full ${sentiment}`}>
                    <span className="preview-text-full">{r.text}</span>
                    <div className="preview-meta-full">
                      <span className="preview-aspects-full">{aspects}</span>
                      <span className={`preview-sentiment-full ${sentiment}`}>
                        {getSentimentLabel(sentiment)}
                      </span>
                    </div>
                  </div>
                );
              })}
              {!showAllResults && results.results.length > 5 && (
                <div className="preview-more-full">
                  + {results.results.length - 5} more reviews
                </div>
              )}
            </div>
          )}

          {results.errors && results.errors.length > 0 && (
            <div className="results-errors-full">
              <AlertCircle size={16} />
              <span>{results.errors.length} errors encountered</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BatchUpload;