import React from 'react';
import { 
  Coffee, 
  Settings, 
  FileText, 
  Upload, 
  Languages,
  Menu,
  X,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeTab: 'review' | 'translator' | 'batch';
  onTabChange: (tab: 'review' | 'translator' | 'batch') => void;
  threshold: number;
  onThresholdChange: (value: number) => void;
  modelLoaded: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  activeTab,
  onTabChange,
  threshold,
  onThresholdChange,
  modelLoaded
}) => {
  const navItems = [
    { id: 'review' as const, label: 'Review', icon: FileText },
    { id: 'translator' as const, label: 'Translator', icon: Languages },
    { id: 'batch' as const, label: 'Batch Upload', icon: Upload },
  ];

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'visible' : ''}`} onClick={onToggle} />
      
      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-inner">
          <div className="sidebar-header">
            <button className="sidebar-toggle" onClick={onToggle}>
              {isOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            {isOpen && (
              <div className="sidebar-brand">
               
                <span className="brand-name">ReviewAI</span>
              </div>
            )}
          </div>

          <div className="sidebar-divider" />

          <nav className="sidebar-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => onTabChange(item.id)}
                >
                  <Icon size={18} />
                  {isOpen && <span>{item.label}</span>}
                  {isActive && isOpen && <span className="nav-indicator" />}
                </button>
              );
            })}
          </nav>

          {isOpen && (
            <>
              <div className="sidebar-divider" />
              <div className="sidebar-settings">
                <div className="settings-header">
                  <Settings size={14} />
                  <span>Settings</span>
                </div>
                <div className="settings-group">
                  <label className="settings-label">Threshold</label>
                  <div className="settings-slider">
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.05"
                      value={threshold}
                      onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
                      className="threshold-slider"
                    />
                    <span className="threshold-value">{threshold.toFixed(2)}</span>
                  </div>
                  <p className="settings-helper">Higher = fewer, more confident</p>
                </div>
              </div>
            </>
          )}

          <div className="sidebar-footer">
            <div className="model-status">
              <span className={`status-dot ${modelLoaded ? 'online' : 'offline'}`} />
              {isOpen && <span className="status-text">{modelLoaded ? 'Model Ready' : 'Demo Mode'}</span>}
            </div>
            {isOpen && (
              <button className="settings-footer-btn">
                <Sparkles size={14} />
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;