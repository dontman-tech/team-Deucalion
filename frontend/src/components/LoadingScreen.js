import React from 'react';
import './LoadingScreen.css';

function LoadingScreen({ message = 'Loading...' }) {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <div className="spinner">
          <div className="spinner-circle"></div>
        </div>
        <p className="loading-message">{message}</p>
        <div className="loading-brand">LUMINA CAMEROON</div>
      </div>
    </div>
  );
}

export default LoadingScreen;
