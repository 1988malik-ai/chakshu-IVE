import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewDataUrl } from '../api/client';
import { PRODUCT_FULL } from '../brand';

export default function LiveCapture({
  sessionId,
  filters = [],
  onIngest,
  onStatus,
  onError,
}) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const filterLoopRef = useRef(null);
  const [mode, setMode] = useState('browser'); // browser | backend
  const [devices, setDevices] = useState([]);
  const [deviceIndex, setDeviceIndex] = useState(0);
  const [liveFilter, setLiveFilter] = useState('');
  const [active, setActive] = useState(false);
  const [streamKey, setStreamKey] = useState(0);
  const [filteredPreview, setFilteredPreview] = useState(null);
  const [streamError, setStreamError] = useState(false);
  const [screenPath, setScreenPath] = useState('~/Desktop/chakshu-screen.mp4');
  const [seqDir, setSeqDir] = useState('~/Desktop/chakshu-frames');
  const [seqOut, setSeqOut] = useState('~/Desktop/chakshu-sequence.mp4');

  const stopBrowser = useCallback(() => {
    if (filterLoopRef.current) {
      clearInterval(filterLoopRef.current);
      filterLoopRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
    setFilteredPreview(null);
  }, []);

  const restartBackendStream = useCallback(async () => {
    setStreamError(false);
    try {
      await api.capStopCaptureStream(deviceIndex);
    } catch {
      /* ignore */
    }
    setStreamKey((k) => k + 1);
  }, [deviceIndex]);

  const startBrowser = useCallback(async () => {
    onError?.('');
    setStreamError(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setActive(true);
      onStatus?.('Browser webcam active');
    } catch (e) {
      onError?.(e.message || 'Camera permission denied');
    }
  }, [onError, onStatus]);

  useEffect(() => {
    api.capCaptureDevices().then((r) => setDevices(r.devices || [])).catch(() => {});
    return () => {
      stopBrowser();
      api.capStopCaptureStream().catch(() => {});
    };
  }, [stopBrowser]);

  // Restart backend MJPEG when filter or device changes
  useEffect(() => {
    if (mode !== 'backend') return undefined;
    restartBackendStream();
    return () => {
      api.capStopCaptureStream(deviceIndex).catch(() => {});
    };
  }, [mode, deviceIndex, liveFilter, restartBackendStream]);

  // Browser mode: server-side filter preview loop
  useEffect(() => {
    if (filterLoopRef.current) {
      clearInterval(filterLoopRef.current);
      filterLoopRef.current = null;
    }
    if (mode !== 'browser' || !active || !liveFilter || !videoRef.current) {
      setFilteredPreview(null);
      return undefined;
    }

    const tick = async () => {
      const v = videoRef.current;
      if (!v || v.readyState < 2) return;
      const canvas = document.createElement('canvas');
      canvas.width = v.videoWidth || 640;
      canvas.height = v.videoHeight || 480;
      canvas.getContext('2d').drawImage(v, 0, 0);
      const b64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
      try {
        const r = await api.capProcessFrame(liveFilter, b64);
        if (r.preview) setFilteredPreview(previewDataUrl(r.preview));
      } catch (e) {
        onError?.(e.message);
      }
    };

    tick();
    filterLoopRef.current = setInterval(tick, 250);
    return () => {
      if (filterLoopRef.current) clearInterval(filterLoopRef.current);
    };
  }, [mode, active, liveFilter, onError]);

  const captureFrameBase64 = useCallback(async (applyFilter) => {
    if (mode === 'backend') {
      const r = await api.capCaptureSnapshot(deviceIndex, applyFilter || null);
      if (!r.success) throw new Error(r.error || 'Capture failed');
      return r.preview;
    }
    const v = videoRef.current;
    if (!v) throw new Error('No video');
    const canvas = document.createElement('canvas');
    canvas.width = v.videoWidth || 640;
    canvas.height = v.videoHeight || 480;
    canvas.getContext('2d').drawImage(v, 0, 0);
    let b64 = canvas.toDataURL('image/jpeg', 0.92).split(',')[1];
    if (applyFilter) {
      const r = await api.capProcessFrame(applyFilter, b64);
      b64 = r.preview;
    }
    return b64;
  }, [mode, deviceIndex]);

  const snapToEvidence = async () => {
    if (!sessionId) return onError?.('No session');
    try {
      const preview = await captureFrameBase64(liveFilter || null);
      const ing = await api.capCaptureIngest(sessionId, preview, `chakshu-live-${Date.now()}.jpg`);
      onIngest?.(ing);
      onStatus?.(liveFilter ? `Captured with filter: ${liveFilter}` : 'Live frame ingested');
    } catch (e) {
      onError?.(e.message);
    }
  };

  const screenCapture = async () => {
    try {
      const r = await api.capScreenCapture({ output_path: screenPath, duration_sec: 5, fps: 15 });
      if (!r.success) throw new Error(r.error);
      onStatus?.(`Screen saved: ${r.path}`);
    } catch (e) {
      onError?.(e.message);
    }
  };

  const buildSequenceVideo = async () => {
    try {
      const r = await api.capSequenceToVideo({ input_dir: seqDir, output_path: seqOut, fps: 30 });
      if (!r.success) throw new Error(r.error);
      onStatus?.(`Video built: ${r.path} (${r.frame_count} frames)`);
    } catch (e) {
      onError?.(e.message);
    }
  };

  const liveFilters = useMemo(
    () => filters.filter((f) => f.implemented && (f.domain === 'image' || f.domain === 'both')),
    [filters],
  );

  const backendStreamUrl = api.captureStreamUrl(deviceIndex, liveFilter || null, streamKey);

  return (
    <div className="cap-root">
      <div className="cap-header">
        <h2>Live Capture</h2>
        <p>Real-time intake for {PRODUCT_FULL} — webcam, device stream, screen, and image sequences.</p>
      </div>

      <div className="cap-mode">
        <button type="button" className={`fx-btn ${mode === 'browser' ? 'fx-btn-primary' : ''}`} onClick={() => { stopBrowser(); setMode('browser'); }}>Browser Webcam</button>
        <button type="button" className={`fx-btn ${mode === 'backend' ? 'fx-btn-primary' : ''}`} onClick={() => { stopBrowser(); setMode('backend'); onStatus?.('Backend device stream — select filter below'); }}>Backend Device</button>
      </div>

      <div className="cap-grid">
        <div className="cap-viewer">
          {mode === 'browser' ? (
            <>
              <video ref={videoRef} className="cap-video" playsInline muted style={{ opacity: liveFilter && filteredPreview ? 0 : 1 }} />
              {liveFilter && filteredPreview && (
                <img src={filteredPreview} alt="Filtered live" className="cap-video cap-filtered-overlay" />
              )}
              {!active && (
                <div className="cap-placeholder">
                  <button type="button" className="fx-btn fx-btn-primary" onClick={startBrowser}>Start Webcam</button>
                </div>
              )}
            </>
          ) : (
            <>
              {!streamError ? (
                <img
                  key={streamKey}
                  src={backendStreamUrl}
                  alt="Live MJPEG"
                  className="cap-video"
                  onLoad={() => {
                    setStreamError(false);
                    onStatus?.(liveFilter ? `Live stream + ${liveFilter}` : 'Backend stream active');
                  }}
                  onError={() => {
                    setStreamError(true);
                    onError?.('Backend stream failed — allow camera access, try another device index, or restart API');
                  }}
                />
              ) : (
                <div className="cap-placeholder">
                  <p style={{ color: '#f87171', fontSize: '0.8rem', marginBottom: 8 }}>Stream unavailable</p>
                  <button type="button" className="fx-btn fx-btn-primary" onClick={restartBackendStream}>Retry Stream</button>
                </div>
              )}
            </>
          )}
        </div>

        <div className="cap-side">
          <div className="cap-section-label">Live filter</div>
          <select
            className="fx-input"
            value={liveFilter}
            onChange={(e) => setLiveFilter(e.target.value)}
          >
            <option value="">None (raw)</option>
            {liveFilters.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
          <p style={{ fontSize: '0.65rem', color: 'var(--fx-muted)', marginTop: 6 }}>
            {mode === 'browser'
              ? 'Filter preview ~4 fps via server. Snap captures filtered frame.'
              : 'Filter applied on backend MJPEG stream. Use Backend Device if browser preview is slow.'}
          </p>

          {mode === 'backend' && (
            <div style={{ marginTop: 8 }}>
              <label className="cap-section-label">Device index</label>
              <select className="fx-input" value={deviceIndex} onChange={(e) => setDeviceIndex(Number(e.target.value))}>
                {(devices.length ? devices : [{ index: 0 }]).map((d) => (
                  <option key={d.index} value={d.index}>Camera {d.index}</option>
                ))}
              </select>
            </div>
          )}

          <div className="cap-actions">
            <button
              type="button"
              className="fx-btn fx-btn-primary"
              onClick={snapToEvidence}
              disabled={mode === 'browser' && !active}
            >
              Snap to Evidence
            </button>
            {mode === 'browser' && active && (
              <button type="button" className="fx-btn" onClick={stopBrowser}>Stop</button>
            )}
            {mode === 'backend' && (
              <button type="button" className="fx-btn" onClick={restartBackendStream}>Restart Stream</button>
            )}
          </div>

          <div className="cap-section-label" style={{ marginTop: 16 }}>Screen capture (FFmpeg)</div>
          <input className="fx-input" value={screenPath} onChange={(e) => setScreenPath(e.target.value)} />
          <button type="button" className="fx-btn" style={{ marginTop: 6, width: '100%' }} onClick={screenCapture}>Record 5s Screen</button>

          <div className="cap-section-label" style={{ marginTop: 16 }}>Image sequence → video</div>
          <input className="fx-input" placeholder="Frames folder" value={seqDir} onChange={(e) => setSeqDir(e.target.value)} />
          <input className="fx-input" placeholder="Output MP4" value={seqOut} onChange={(e) => setSeqOut(e.target.value)} style={{ marginTop: 6 }} />
          <button type="button" className="fx-btn" style={{ marginTop: 6, width: '100%' }} onClick={buildSequenceVideo}>Build Video</button>
        </div>
      </div>
    </div>
  );
}
