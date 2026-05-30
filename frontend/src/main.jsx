import React from 'react';
import ReactDOM from 'react-dom/client';
import ForensicApp from './ForensicApp';
import './styles/forensic.css';
import './styles/timeline.css';
import './styles/capture.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ForensicApp />
  </React.StrictMode>
);
