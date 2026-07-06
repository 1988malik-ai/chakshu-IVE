import { api } from '../api/client';
import AudioPlayer from './AudioPlayer';
import ForensicTimeline, { formatTc } from './ForensicTimeline';
import ForensicVideoTransport from './ForensicVideoTransport';
import RegionAnalysisPanel from './RegionAnalysisPanel';

export default function TimelineProPage({
  t = (k, d) => d,
  timeline,
  timelineLoading,
  seekTime,
  seekToTime,
  regionStart,
  regionEnd,
  onRegionChange,
  preview,
  storagePath,
  videoRef,
  playback,
  buildTimeline,
  stepFrame,
  sessionId,
  frameIndex,
  currentFrameMeta,
  mediaIdLabel,
  regionAnalysis,
  onRegionAnalysis,
  timestampContext,
  videoMeta,
  audioChannels,
  onAudioChannels,
  onPlayReverse,
  setStatus,
  setError,
  onOpenTools,
  onVideoTimeUpdate,
}) {
  const duration = timeline?.duration || videoMeta?.duration || 0;
  const fps = timestampContext?.fps || timeline?.fps || 30;

  return (
    <div className="fx-content ftl-page">
      <ForensicTimeline
        timeline={timeline}
        currentTime={seekTime}
        loading={timelineLoading}
        onSeek={seekToTime}
        onRegionSelect={(a, b) => {
          onRegionChange({
            regionStart: Math.round(a * 100) / 100,
            regionEnd: Math.round(b * 100) / 100,
          });
        }}
      />

      <div className="ftl-studio">
        <div className="ftl-main">
          <div className="ftl-viewer">
            {preview ? (
              <img src={preview} alt="Frame" />
            ) : storagePath ? (
              <video
                ref={videoRef}
                src={api.mediaServeUrl(storagePath)}
                onTimeUpdate={(e) => {
                  if (playback.direction !== 'reverse') onVideoTimeUpdate?.(e.target.currentTime);
                }}
                onPlay={() => {
                  if (playback.direction === 'reverse') videoRef.current?.pause();
                }}
              />
            ) : (
              <span className="ftl-viewer-empty">Load video evidence</span>
            )}
          </div>

          <div className="ftl-transport-bar">
            <div className="ftl-index-actions">
              <button
                type="button"
                className="fx-btn fx-btn-primary"
                onClick={() => buildTimeline(false)}
                disabled={!storagePath || timelineLoading}
              >
                Deep Index
              </button>
              <button
                type="button"
                className="fx-btn"
                onClick={() => buildTimeline(true)}
                disabled={!storagePath || timelineLoading}
                title="Rebuild index"
              >
                ↻
              </button>
            </div>
            <ForensicVideoTransport
              t={t}
              direction={playback.direction}
              speed={playback.speed}
              onSpeedChange={playback.setSpeed}
              onPlayForward={playback.playForward}
              onPlayReverse={onPlayReverse}
              onPause={playback.pause}
              onStepBack={() => { playback.pause(); stepFrame(-1); }}
              onStepForward={() => { playback.pause(); stepFrame(1); }}
              onStepIframe={() => { playback.pause(); stepFrame(1, true); }}
              disabled={!sessionId}
              compact
            />
          </div>
        </div>

        <aside className="ftl-inspector">
          <div className="ftl-frame-meta">
            <div><strong>Timecode</strong> {formatTc(seekTime, fps)}</div>
            <div><strong>Frame</strong> #{frameIndex}{currentFrameMeta ? ` · ${currentFrameMeta.type}` : ''}</div>
            <div><strong>PTS</strong> {seekTime.toFixed(4)}s</div>
            {currentFrameMeta?.size && <div><strong>Size</strong> {currentFrameMeta.size} B</div>}
            <div className="ftl-evidence-line"><strong>Evidence</strong> {mediaIdLabel()}</div>
          </div>

          <div className="ftl-inspector-section">
            <div className="ftl-section-label">Audio &amp; Sync</div>
            <div className="ftl-audio-row">
              <button
                type="button"
                className="fx-btn"
                disabled={!storagePath}
                onClick={async () => {
                  try {
                    const r = await api.timelineAudioChannels(storagePath);
                    onAudioChannels(r);
                  } catch (e) {
                    setError(e.message);
                  }
                }}
              >
                Probe
              </button>
              <button
                type="button"
                className="fx-btn"
                disabled={!storagePath}
                onClick={async () => {
                  try {
                    const r = await api.timelineAvOffset(storagePath);
                    setStatus(`A/V offset: ${r.recommendation_ms} ms`);
                  } catch (e) {
                    setError(e.message);
                  }
                }}
              >
                A/V Offset
              </button>
            </div>
            {audioChannels?.streams?.map((s, i) => (
              <div key={i} className="ftl-audio-stream">
                Ch {s.index}: {s.codec} · {s.layout} · {s.channels}ch
              </div>
            ))}
            <AudioPlayer src={storagePath ? api.mediaServeUrl(storagePath) : null} label="Synced audio" compact />
          </div>

          {onOpenTools && (
            <div className="ftl-tools-link">
              <button type="button" className="fx-btn" onClick={onOpenTools}>
                Audio redaction &amp; mux → Tools
              </button>
            </div>
          )}
        </aside>
      </div>

      <div className="ftl-analysis-card">
        <RegionAnalysisPanel
          embedded
          compact
          mediaPath={storagePath}
          regionStart={regionStart}
          regionEnd={regionEnd}
          onRegionChange={onRegionChange}
          seekTime={seekTime}
          duration={duration}
          fps={fps}
          regionAnalysis={regionAnalysis}
          onAnalysis={onRegionAnalysis}
          onSeek={seekToTime}
          t={t}
          setStatus={setStatus}
          setError={setError}
        />
      </div>
    </div>
  );
}
