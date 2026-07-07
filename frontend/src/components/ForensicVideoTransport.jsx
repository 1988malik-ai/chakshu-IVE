/** Playback transport — forward (HTML5) and reverse (forensic frame step). */

export default function ForensicVideoTransport({
  t = (k, d) => d,
  direction,
  speed,
  currentTime = 0,
  duration = 0,
  fps = 30,
  onSpeedChange,
  onPlayForward,
  onPlayReverse,
  onPause,
  onStepBack,
  onStepForward,
  onStepIframe,
  disabled = false,
  compact = false,
}) {
  const playingFwd = direction === 'forward';
  const playingRev = direction === 'reverse';
  const previousFrameLabel = t('playback.step_back', 'Previous frame');
  const playForwardLabel = playingFwd
    ? t('playback.pause_forward', 'Pause forward playback')
    : t('playback.play_forward', 'Play forward');
  const playReverseLabel = playingRev
    ? t('playback.pause_reverse', 'Pause reverse playback')
    : t('playback.play_reverse', 'Play reverse frame-by-frame');
  const nextFrameLabel = t('playback.step_forward', 'Next frame');
  const nextIframeLabel = t('playback.next_iframe', 'Next I-frame');
  const stopLabel = t('playback.stop', 'Stop playback');
  const formatTimecode = (seconds) => {
    const safe = Math.max(0, Number(seconds) || 0);
    const totalFrames = Math.round(safe * Math.max(1, fps));
    const frame = totalFrames % Math.max(1, Math.round(fps));
    const totalSeconds = Math.floor(safe);
    const s = totalSeconds % 60;
    const m = Math.floor(totalSeconds / 60) % 60;
    const h = Math.floor(totalSeconds / 3600);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}:${String(frame).padStart(2, '0')}`;
  };

  return (
    <div className={`fx-playback-transport${compact ? ' fx-playback-compact' : ''}`}>
      <div className="fx-playback-buttons">
        <button
          type="button"
          className="fx-btn fx-transport-btn fx-transport-step"
          disabled={disabled}
          onClick={onStepBack}
          title={previousFrameLabel}
          aria-label={previousFrameLabel}
        >
          <span aria-hidden="true">|◀</span>
        </button>
        <button
          type="button"
          className={`fx-btn fx-transport-btn fx-transport-play${playingFwd ? ' fx-btn-primary' : ''}`}
          disabled={disabled}
          onClick={playingFwd ? onPause : onPlayForward}
          title={playForwardLabel}
          aria-label={playForwardLabel}
        >
          <span aria-hidden="true">{playingFwd ? '⏸' : '▶'}</span>
        </button>
        <button
          type="button"
          className={`fx-btn fx-transport-btn fx-transport-reverse${playingRev ? ' fx-btn-primary' : ''}`}
          disabled={disabled}
          onClick={playingRev ? onPause : onPlayReverse}
          title={playReverseLabel}
          aria-label={playReverseLabel}
        >
          <span aria-hidden="true">{playingRev ? '⏸' : '◀◀'}</span>
        </button>
        <button
          type="button"
          className="fx-btn fx-transport-btn fx-transport-step"
          disabled={disabled}
          onClick={onStepForward}
          title={nextFrameLabel}
          aria-label={nextFrameLabel}
        >
          <span aria-hidden="true">▶|</span>
        </button>
        {!compact && (
          <button
            type="button"
            className="fx-btn fx-transport-btn fx-transport-iframe"
            disabled={disabled}
            onClick={onStepIframe}
            title={nextIframeLabel}
            aria-label={nextIframeLabel}
          >
            <span aria-hidden="true">I▶|</span>
          </button>
        )}
        {(playingFwd || playingRev) && (
          <button
            type="button"
            className="fx-btn fx-transport-btn fx-transport-stop"
            disabled={disabled}
            onClick={onPause}
            title={stopLabel}
            aria-label={stopLabel}
          >
            {t('playback.stop_short', 'Stop')}
          </button>
        )}
      </div>
      <label className="fx-playback-speed">
        <span>{t('playback.speed', 'Speed')}</span>
        <select
          value={speed}
          disabled={disabled}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
          aria-label={t('playback.speed', 'Speed')}
        >
          <option value={0.25}>0.25×</option>
          <option value={0.5}>0.5×</option>
          <option value={1}>1×</option>
          <option value={1.5}>1.5×</option>
          <option value={2}>2×</option>
          <option value={4}>4×</option>
        </select>
      </label>
      <span className="fx-playback-timestamp" title={t('playback.timestamp_speed', 'Timestamp-based playback speed')}>
        {formatTimecode(currentTime)}
        {duration ? ` / ${formatTimecode(duration)}` : ''}
      </span>
      {playingRev && (
        <span className="fx-playback-badge">{t('playback.reverse_active', 'Reverse playback')}</span>
      )}
    </div>
  );
}
