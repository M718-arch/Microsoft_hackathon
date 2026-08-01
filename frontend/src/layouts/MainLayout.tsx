import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="main-layout">
      <div className="main-panel">
        {children}
      </div>
    </div>
  );
};

export default MainLayout;