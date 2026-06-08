import { useCallback, useState } from 'react';
import { api } from '../api/client';

export default function AudioStreamPanel({
  t = (k, d) => d,
  videoPath,
  outputDir,
  setStatus,
  setError,
  notify,
}) {
  const [audioPath, setAudioPath] = useState(`${outputDir}/external-audio.aac`);
  const [outputPath, setOutputPath] = useState(`${outputDir}/video-with-audio.mp4`);
  const [replaceOriginal, setReplaceOriginal] = useState(false);
  const [audioCodec, setAudioCodec] = useState('aac');
  const [delayMs, setDelayMs] = useState(0);
  const [autoPadVideo, setAutoPadVideo] = useState(true);
  const [useShortest, setUseShortest] = useState(false);
  const [durationInfo, setDurationInfo] = useState(null);
  const [streamTitle, setStreamTitle] = useState('');
  const [streamLanguage, setStreamLanguage] = useState('');
  const [streams, setStreams] = useState(null);
  const [loading, setLoading] = useState(false);

  const probe = useCallback(async () => {
    if (!videoPath) throw new Error(t('audio_mux.no_video', 'Set source video path first'));
    const r = await api.capAudioStreams(videoPath);
    setStreams(r);
    if (audioPath.trim()) {
      try {
        const d = await api.capAudioDurationCompare(videoPath, audioPath.trim());
        setDurationInfo(d);
      } catch {
        setDurationInfo(null);
      }
    }
    setStatus(
      `${t('audio_mux.probed', 'Audio streams')}: ${r.count} ${t('audio_mux.on_file', 'on file')}`,
    );
  }, [videoPath, audioPath, setStatus, t]);

  const refreshDuration = useCallback(async () => {
    if (!videoPath || !audioPath.trim()) {
      setDurationInfo(null);
      return;
    }
    try {
      const d = await api.capAudioDurationCompare(videoPath, audioPath.trim());
      setDurationInfo(d);
    } catch {
      setDurationInfo(null);
    }
  }, [videoPath, audioPath]);

  const runMux = useCallback(async () => {
    if (!videoPath) throw new Error(t('audio_mux.no_video', 'Set source video path first'));
    if (!audioPath.trim()) throw new Error(t('audio_mux.no_audio', 'Enter external audio file path'));
    setLoading(true);
    setError('');
    try {
      const r = await api.capAudioMux({
        video_path: videoPath,
        audio_path: audioPath.trim(),
        output_path: outputPath.trim(),
        mode: replaceOriginal ? 'replace' : 'add',
        audio_codec: audioCodec,
        audio_delay_ms: Number(delayMs) || 0,
        use_shortest: useShortest,
        auto_pad_video: autoPadVideo,
        stream_title: streamTitle.trim() || undefined,
        stream_language: streamLanguage.trim() || undefined,
      });
      if (!r.success) throw new Error(r.error || r.stderr || t('audio_mux.failed', 'Failed to add audio stream'));
      const kept = r.kept_existing_audio !== false;
      const msg = kept
        ? t('audio_mux.done_add', 'Added audio track (kept existing)')
        : t('audio_mux.done_replace', 'Replaced audio track');
      const keptNote = kept && (r.existing_audio_streams ?? 0) > 0
        ? ` · ${t('audio_mux.kept_count', 'kept')} ${r.existing_audio_streams} + 1 ${t('audio_mux.new_track', 'new')}`
        : '';
      const padNote = r.video_padded
        ? ` · ${t('audio_mux.padded', 'padded')} ${r.pad_seconds}s`
        : '';
      setStatus(
        `${msg}: ${r.output || outputPath}${keptNote}${padNote} · ${t('audio_mux.total_streams', 'total')}: ${r.audio_streams_after ?? '?'}`,
      );
      notify?.(`${msg}: ${r.output || outputPath}`, 'success');
      await probe();
    } finally {
      setLoading(false);
    }
  }, [
    videoPath,
    audioPath,
    outputPath,
    replaceOriginal,
    audioCodec,
    delayMs,
    autoPadVideo,
    useShortest,
    streamTitle,
    streamLanguage,
    setError,
    setStatus,
    notify,
    probe,
    t,
  ]);

  const handleProbe = () => {
    probe().catch((e) => setError(e.message));
  };

  const handleMux = () => {
    runMux().catch((e) => setError(e.message));
  };

  return (
    <div className="fx-panel fx-audio-mux-panel">
      <div className="fx-panel-head">{t('audio_mux.title', 'Add Audio Stream (R-115)')}</div>
      <div className="fx-panel-body fx-export-form">
        <p className="fx-export-hint">
          {t(
            'audio_mux.hint',
            'Mux an external audio file onto video. Add mode keeps existing audio tracks and appends a new one; Replace mode swaps the default audio.',
          )}
        </p>

        <div className="fx-export-actions-row">
          <button type="button" className="fx-btn" disabled={!videoPath} onClick={handleProbe}>
            {t('audio_mux.probe', 'Probe video audio')}
          </button>
        </div>

        {streams && (
          <ul className="fx-audio-mux-streams">
            {streams.streams?.length ? (
              streams.streams.map((s) => (
                <li key={s.index}>
                  #{s.index} · {s.codec} · {s.channels}ch · {s.sample_rate}Hz
                  {s.language ? ` · ${s.language}` : ''}
                </li>
              ))
            ) : (
              <li>{t('audio_mux.no_streams', 'No audio streams on source video')}</li>
            )}
          </ul>
        )}

        <label>
          {t('audio_mux.external_audio', 'External audio file')}
          <input
            className="fx-input"
            value={audioPath}
            onChange={(e) => setAudioPath(e.target.value)}
            onBlur={refreshDuration}
          />
        </label>

        {durationInfo && (
          <div className={`fx-audio-mux-duration${durationInfo.needs_video_padding ? ' fx-audio-mux-duration-pad' : ''}`}>
            <span>
              {t('audio_mux.video_dur', 'Video')}: {durationInfo.video_duration_sec?.toFixed(2) ?? '—'}s
            </span>
            <span>
              {t('audio_mux.audio_dur', 'Audio')}: {durationInfo.audio_duration_sec?.toFixed(2) ?? '—'}s
            </span>
            {durationInfo.needs_video_padding && autoPadVideo && (
              <span className="fx-audio-mux-pad-hint">
                {t('audio_mux.will_pad', 'Audio longer — video will be padded automatically')} (+{durationInfo.pad_seconds}s)
              </span>
            )}
            {durationInfo.recommended_policy === 'trim_shortest' && !useShortest && (
              <span>{t('audio_mux.video_longer', 'Video is longer than audio')}</span>
            )}
          </div>
        )}
        <label>
          {t('audio_mux.output', 'Output video')}
          <input className="fx-input" value={outputPath} onChange={(e) => setOutputPath(e.target.value)} />
        </label>

        <div className="fx-audio-mux-keep-banner">
          {t(
            'audio_mux.keep_default',
            'Default: keeps all existing audio on the video and adds your file as an extra track.',
          )}
        </div>

        <label className="fx-audio-mux-replace-opt">
          <input
            type="checkbox"
            checked={replaceOriginal}
            onChange={(e) => setReplaceOriginal(e.target.checked)}
          />
          {t('audio_mux.replace_check', 'Replace original audio (do not keep existing tracks)')}
        </label>

        <div className="fx-audio-mux-row">
          <label>
            {t('audio_mux.codec', 'Audio codec')}
            <select className="fx-input" value={audioCodec} onChange={(e) => setAudioCodec(e.target.value)}>
              <option value="aac">AAC</option>
              <option value="copy">{t('audio_mux.codec_copy', 'Copy')}</option>
              <option value="libmp3lame">MP3</option>
            </select>
          </label>
        </div>

        <div className="fx-audio-mux-row">
          <label>
            {t('audio_mux.delay', 'Delay new audio (ms)')}
            <input
              type="number"
              className="fx-input"
              value={delayMs}
              onChange={(e) => setDelayMs(e.target.value)}
            />
          </label>
          <label>
            {t('audio_mux.stream_title', 'Track title (optional)')}
            <input className="fx-input" value={streamTitle} onChange={(e) => setStreamTitle(e.target.value)} />
          </label>
        </div>

        <label>
          {t('audio_mux.stream_lang', 'Track language (optional)')}
          <input className="fx-input" value={streamLanguage} onChange={(e) => setStreamLanguage(e.target.value)} placeholder="eng" />
        </label>

        <div className="fx-audio-mux-checks">
          <label className="fx-reports-check">
            <input type="checkbox" checked={autoPadVideo} onChange={(e) => setAutoPadVideo(e.target.checked)} />
            {t('audio_mux.auto_pad', 'Automatically pad video when audio is longer (R-117)')}
          </label>
          <label className="fx-reports-check">
            <input type="checkbox" checked={useShortest} onChange={(e) => setUseShortest(e.target.checked)} />
            {t('audio_mux.shortest', 'Trim to shortest when video is longer')}
          </label>
        </div>

        <div className="fx-export-actions-row">
          <button
            type="button"
            className="fx-btn fx-btn-primary"
            disabled={!videoPath || loading}
            onClick={handleMux}
          >
            {loading ? t('audio_mux.working', 'Muxing…') : t('audio_mux.run', 'Add audio to video')}
          </button>
        </div>
      </div>
    </div>
  );
}
