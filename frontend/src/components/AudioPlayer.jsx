import { useRef, useState } from 'react';

export default function AudioPlayer({ src, label = 'Audio preview' }) {
  const audioRef = useRef(null);
  const [volume, setVolume] = useState(0.8);
  const [muted, setMuted] = useState(false);

  if (!src) {
    return (
      <div className="erp-audio-bar">
        <span style={{ color: 'var(--erp-muted)' }}>No audio loaded — extract or open a video with audio</span>
      </div>
    );
  }

  const onVolume = (e) => {
    const v = parseFloat(e.target.value);
    setVolume(v);
    if (audioRef.current) {
      audioRef.current.volume = v;
      audioRef.current.muted = false;
      setMuted(false);
    }
  };

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !muted;
      setMuted(!muted);
    }
  };

  return (
    <div className="erp-audio-bar">
      <span style={{ fontWeight: 600, minWidth: 100 }}>{label}</span>
      <audio ref={audioRef} src={src} controls style={{ flex: 1, maxWidth: 400 }} />
      <button type="button" className="erp-btn erp-btn-secondary" onClick={toggleMute}>
        {muted ? 'Unmute' : 'Mute'}
      </button>
      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem' }}>
        Vol
        <input type="range" min="0" max="1" step="0.05" value={muted ? 0 : volume} onChange={onVolume} />
      </label>
    </div>
  );
}
