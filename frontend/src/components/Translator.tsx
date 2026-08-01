import React, { useState } from 'react';
import { ArrowLeftRight, Send, Copy, Check } from 'lucide-react';
import { absaApi } from '../services/api';
import toast from 'react-hot-toast';

const Translator: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleTranslate = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter text to translate');
      return;
    }

    setLoading(true);
    try {
      const response = await absaApi.translate(inputText);
      setTranslatedText(response.translated || response.original);
      toast.success('Translation complete!');
    } catch (error) {
      toast.error('Error translating text');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(translatedText);
      setCopied(true);
      toast.success('Copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleTranslate();
    }
  };

  return (
    <div className="translator-modern">
      {/* No header - using tab-specific header from App.tsx */}

      {/* Translation Panels */}
      <div className="translator-panels">
        {/* Left - Input */}
        <div className="translator-panel input-panel">
          <div className="panel-header">
            <span className="panel-label">Franco-Arabic</span>
            <span className="panel-count">{inputText.length} characters</span>
          </div>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type Franco-Arabic here..."
            className="panel-textarea"
            disabled={loading}
            rows={3}
          />
        </div>

        {/* Swap Icon */}
        <div className="translator-swap">
          <div className="swap-circle">
            <ArrowLeftRight size={18} />
          </div>
        </div>

        {/* Right - Output */}
        <div className="translator-panel output-panel">
          <div className="panel-header">
            <span className="panel-label">Arabic</span>
            {translatedText && (
              <button onClick={handleCopy} className="copy-btn-modern" title="Copy translation">
                {copied ? <Check size={14} /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            )}
          </div>
          <div className="panel-output">
            {translatedText ? (
              <div className="output-text">{translatedText}</div>
            ) : (
              <div className="output-placeholder">Translation will appear here</div>
            )}
          </div>
        </div>
      </div>

      {/* Translate Button */}
      <div className="translator-actions">
        <button
          onClick={handleTranslate}
          disabled={loading || !inputText.trim()}
          className="translate-btn-modern"
        >
          {loading ? (
            <>
              <span className="spinner" />
              Translating...
            </>
          ) : (
            <>
              <Send size={16} />
              Translate
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Translator;