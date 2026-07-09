import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function MediaCompatibilityPanel({ t = (k, d) => d, setError }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.mediaFormats()
      .then((r) => { if (mounted) setStatus(r); })
      .catch((e) => setError?.(e.message))
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [setError]);

  const badge = (ok) => (
    <span className={`fx-compat-pill ${ok ? 'is-ok' : 'is-warn'}`}>
      {ok ? 'Available' : 'Needs setup'}
    </span>
  );

  return (
    <div className="fx-panel fx-settings-panel">
      <div className="fx-panel-head">{t('settings.media_compatibility', 'Media compatibility')}</div>
      <div className="fx-panel-body fx-settings-body">
        {loading && <p className="fx-export-hint">Checking local codec support…</p>}
        {status && (
          <>
            <div className="fx-compat-row">
              <span>FFmpeg / system codec extension</span>
              {badge(status.video?.ffmpeg?.ffmpeg)}
            </div>
            <code className="fx-compat-code">{status.video?.ffmpeg?.source || 'unknown source'}</code>
            <div className="fx-compat-row">
              <span>RAW camera formats</span>
              {badge(status.raw?.available)}
            </div>
            {!status.raw?.available && <code className="fx-compat-code">{status.raw?.install}</code>}
            <div className="fx-compat-row">
              <span>HEIC / HEIF</span>
              {badge(status.heif?.available)}
            </div>
            {!status.heif?.available && <code className="fx-compat-code">{status.heif?.install}</code>}

            <div className="fx-compat-summary">
              <strong>Accepted image formats</strong>
              <p>{[...(status.standard_images || []), ...(status.specialized_images || [])].join(', ')}</p>
              <strong>Accepted video formats</strong>
              <p>{(status.video?.extensions || []).join(', ')}</p>
              {(status.video?.system_codec_extension?.hints || []).map((hint, i) => (
                <div key={i} className="fx-compat-warning">{hint}</div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
