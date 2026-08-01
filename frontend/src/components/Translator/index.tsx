import React, { useState } from 'react';
import { Languages, Copy, Check, Loader2 } from 'lucide-react';
import { absaApi } from '../../services/api';
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
      setTranslatedText(response.translated);
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

  return (
    <div className="translator-container">
      <div className="translator-header">
        <Languages size={20} />
        <h2>Franco-Arabic Translator</h2>
      </div>

      <div className="translator-grid">
        <div className="translator-input">
          <label className="input-label">Franco-Arabic Input</label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type Franco-Arabic text here..."
            className="translator-textarea"
            disabled={loading}
            rows={4}
          />
          <button
            onClick={handleTranslate}
            disabled={loading || !inputText.trim()}
            className="translate-btn"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="spinner" />
                Translating...
              </>
            ) : (
              'Translate'
            )}
          </button>
        </div>

        <div className="translator-output">
          <label className="input-label">Arabic Translation</label>
          <div className="output-container">
            <textarea
              value={translatedText}
              readOnly
              placeholder="Translation will appear here..."
              className="translator-textarea output"
              rows={4}
            />
            {translatedText && (
              <button onClick={handleCopy} className="copy-btn">
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Translator;