import { useCallback, useEffect, useRef, useState } from 'react';
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
  const [mode, setMode] = useState('browser'); // browser | backend
  const [devices, setDevices] = useState([]);
  const [deviceIndex, setDeviceIndex] = useState(0);
  const [liveFilter, setLiveFilter] = useState('');
  const [active, setActive] = useState(false);
  const [screenPath, setScreenPath] = useState('~/Desktop/chakshu-screen.mp4');
  const [seqDir, setSeqDir] = useState('~/Desktop/chakshu-frames');
  const [seqOut, setSeqOut] = useState('~/Desktop/chakshu-sequence.mp4');

  const stopBrowser = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
  }, []);

  const startBrowser = useCallback(async () => {
    onError?.('');
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
    return () => stopBrowser();
  }, [stopBrowser]);

  const snapBrowser = async () => {
    if (!sessionId || !videoRef.current) return onError?.('Start camera and ensure session exists');
    const v = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = v.videoWidth || 640;
    canvas.height = v.videoHeight || 480;
    canvas.getContext('2d').drawImage(v, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    const b64 = dataUrl.split(',')[1];
    try {
      const r = await api.capCaptureIngest(sessionId, b64, `chakshu-live-${Date.now()}.jpg`);
      onIngest?.(r);
      onStatus?.('Live frame ingested into examination session');
    } catch (e) {
      onError?.(e.message);
    }
  };

  const snapBackend = async () => {
    try {
      const r = await api.capCaptureSnapshot(deviceIndex, liveFilter || null);
      if (!r.success) throw new Error(r.error || 'Capture failed');
      if (!sessionId) return onError?.('No session');
      const ing = await api.capCaptureIngest(sessionId, r.preview, `chakshu-device-${Date.now()}.jpg`);
      onIngest?.(ing);
      onStatus?.('Device frame captured');
    } catch (e) {
      onError?.(e.message);
    }
  };

  const backendStreamUrl = liveFilter
    ? `${api.captureStreamUrl(deviceIndex, liveFilter)}`
    : api.captureStreamUrl(deviceIndex);

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

  const implemented = filters.filter((f) => f.implemented).slice(0, 40);

  return (
    <div className="cap-root">
      <div className="cap-header">
        <h2>Live Capture</h2>
        <p>Real-time intake for {PRODUCT_FULL} — webcam, device stream, screen, and image sequences.</p>
      </div>

      <div className="cap-mode">
        <button type="button" className={`fx-btn ${mode === 'browser' ? 'fx-btn-primary' : ''}`} onClick={() => { stopBrowser(); setMode('browser'); }}>Browser Webcam</button>
        <button type="button" className={`fx-btn ${mode === 'backend' ? 'fx-btn-primary' : ''}`} onClick={() => { stopBrowser(); setMode('backend'); }}>Backend Device</button>
      </div>

      <div className="cap-grid">
        <div className="cap-viewer">
          {mode === 'browser' ? (
            <>
              <video ref={videoRef} className="cap-video" playsInline muted />
              {!active && (
                <div className="cap-placeholder">
                  <button type="button" className="fx-btn fx-btn-primary" onClick={startBrowser}>Start Webcam</button>
                </div>
              )}
            </>
          ) : (
            <img
              src={backendStreamUrl}
              alt="Live MJPEG"
              className="cap-video"
              onError={() => onError?.('Backend stream unavailable — check OpenCV / camera index')}
            />
          )}
        </div>

        <div className="cap-side">
          <div className="cap-section-label">Live filter (backend stream)</div>
          <select className="fx-input" value={liveFilter} onChange={(e) => setLiveFilter(e.target.value)}>
            <option value="">None</option>
            {implemented.map((f) => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>

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
            <button type="button" className="fx-btn fx-btn-primary" onClick={mode === 'browser' ? snapBrowser : snapBackend}>
              Snap to Evidence
            </button>
            {mode === 'browser' && active && (
              <button type="button" className="fx-btn" onClick={stopBrowser}>Stop</button>
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
