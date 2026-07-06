import { useRef, useState } from 'react';

export default function AudioPlayer({ src, label = 'Audio preview', compact = false }) {
  const audioRef = useRef(null);
  const [volume, setVolume] = useState(0.8);
  const [muted, setMuted] = useState(false);

  if (!src) {
    return (
      <div className={`fx-audio-player${compact ? ' fx-audio-player-compact' : ''}`}>
        <span className="fx-audio-player-empty">No audio loaded — extract or open a video with audio</span>
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
    <div className={`fx-audio-player${compact ? ' fx-audio-player-compact' : ''}`}>
      <span className="fx-audio-player-label">{label}</span>
      <audio ref={audioRef} src={src} controls className="fx-audio-player-element" />
      <div className="fx-audio-player-controls">
        <button type="button" className="fx-btn fx-btn-sm" onClick={toggleMute}>
          {muted ? 'Unmute' : 'Mute'}
        </button>
        <label className="fx-audio-player-volume">
          Vol
          <input type="range" min="0" max="1" step="0.05" value={muted ? 0 : volume} onChange={onVolume} />
        </label>
      </div>
    </div>
  );
}
