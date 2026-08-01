// components/SettingsSidebar.tsx
import React from 'react';
import { 
  Coffee, 
  Settings, 
  FileText, 
  Upload, 
  Languages,
  Menu,
  X
} from 'lucide-react';

interface SettingsSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeTab: 'single' | 'batch' | 'translate';
  onTabChange: (tab: 'single' | 'batch' | 'translate') => void;
  threshold: number;
  onThresholdChange: (value: number) => void;
  modelLoaded: boolean;
}

const SettingsSidebar: React.FC<SettingsSidebarProps> = ({
  isOpen,
  onToggle,
  activeTab,
  onTabChange,
  threshold,
  onThresholdChange,
  modelLoaded
}) => {
  const navItems = [
    { id: 'single', label: 'Single Review', icon: FileText },
    { id: 'batch', label: 'Batch Upload', icon: Upload },
    { id: 'translate', label: 'Translator', icon: Languages },
  ] as const;

  return (
    <>
      <div className={`sidebar-overlay ${isOpen ? 'visible' : ''}`} onClick={onToggle} />
      
      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="sidebar-toggle" onClick={onToggle}>
            {isOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          {isOpen && (
            <div className="sidebar-brand">
              <div className="brand-icon">
                <Coffee size={18} />
              </div>
              <span className="brand-name">Restaurant</span>
            </div>
          )}
        </div>

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
                <p className="settings-helper">
                  Higher = fewer, more confident aspects
                </p>
              </div>
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
                    <Icon size={16} />
                    <span>{item.label}</span>
                    {isActive && <span className="nav-indicator" />}
                  </button>
                );
              })}
            </nav>

            <div className="sidebar-footer">
              <div className="model-status">
                <span className={`status-dot ${modelLoaded ? 'online' : 'offline'}`} />
                <span className="status-text">
                  {modelLoaded ? 'Model Ready' : 'Demo Mode'}
                </span>
              </div>
              <button className="settings-footer-btn">
                <Settings size={14} />
              </button>
            </div>
          </>
        )}
      </aside>
    </>
  );
};

export default SettingsSidebar;