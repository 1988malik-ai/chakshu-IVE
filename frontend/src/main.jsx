import React from 'react';
import ReactDOM from 'react-dom/client';
import ForensicApp from './ForensicApp';
import { LocaleProvider } from './i18n/LocaleContext';
import './styles/brand.css';
import './styles/forensic.css';
import './styles/compare.css';
import './styles/examine-lab.css';
import './styles/notes-panel.css';
import './styles/sidebar-dock.css';
import './styles/a11y.css';
import './styles/timeline.css';
import './styles/capture.css';
import './styles/export-panel.css';
import './styles/playback.css';
import './styles/audio-redact.css';
import './styles/audio-mux.css';
import './styles/subtitle.css';
import './styles/bookmarks.css';
import './styles/reports-panel.css';
import './styles/grid-overlay.css';
import './styles/timestamp-region.css';
import './styles/perspective.css';
import './styles/panorama.css';
import './styles/video-overlay-compare.css';
import './styles/tracking-stabilize.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LocaleProvider>
      <ForensicApp />
    </LocaleProvider>
  </React.StrictMode>
);
