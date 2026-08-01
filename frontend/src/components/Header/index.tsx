import React from 'react';
import { Coffee, Sparkles } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-left">
        <div className="header-icon">
          <Coffee size={22} />
        </div>
        <div>
          <h1 className="header-title">Restaurant Review Analyzer</h1>
          <p className="header-subtitle">Analyze customer feedback using AI.</p>
        </div>
      </div>
      <div className="header-badge">
        <Sparkles size={12} />
        <span>AI</span>
      </div>
    </header>
  );
};

export default Header;