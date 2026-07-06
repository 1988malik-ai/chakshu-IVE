import { useCallback, useState } from 'react';
import { api } from '../api/client';
import { deriveProjectPaths, normalizeDir, resolvedExportPaths, saveExportFormToStorage } from '../lib/exportPaths';
import { folderFieldsFromForm, projectRootForCase } from '../lib/projectStructure';

const PAGE_SIZES = ['A4', 'Letter', 'Legal', 'A3'];
const ORIENTATIONS = ['portrait', 'landscape'];
const VIDEO_CODECS = [
  { id: 'auto_gpu', label: 'Auto (GPU if available)' },
  { id: 'libx264', label: 'H.264 (libx264)' },
  { id: 'libx265', label: 'H.265 (libx265)' },
  { id: 'copy', label: 'Stream copy (no re-encode)' },
];
const AUDIO_CODECS = [
  { id: 'copy', label: 'Copy original audio' },
  { id: 'aac', label: 'AAC' },
  { id: 'pcm_s16le', label: 'PCM 16-bit' },
];
const FRAME_RATE_MODES = [
  { id: 'cfr', label: 'CFR (constant frame rate)' },
  { id: 'vfr', label: 'VFR (variable frame rate)' },
];
const ENCODE_PRESETS = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'];

function Field({ id, label, children, hint }) {
  return (
    <div className="fx-export-field">
      <label htmlFor={id}>{label}</label>
      {children}
      {hint ? <p className="fx-export-field-hint">{hint}</p> : null}
    </div>
  );
}

function pathsPayload(form) {
  const paths = resolvedExportPaths(form);
  return {
    project_root: paths.project_root,
    use_project_structure: form.use_project_structure !== false,
    ...folderFieldsFromForm(form),
    output_dir: paths.bundles_dir || paths.output_dir,
    evidence_dir: paths.evidence_dir,
    examination_dir: paths.examination_dir,
    bundles_dir: paths.bundles_dir,
    pdf_path: paths.pdf_path,
    i_frames_dir: paths.i_frames_dir,
    audio_out: paths.audio_out,
    metadata_path: paths.metadata_path,
    input_path: form.input_path || undefined,
    use_custom_paths: form.use_custom_paths,
    pdf_page_size: form.pdf_page_size,
    pdf_orientation: form.pdf_orientation,
    pdf_columns: Number(form.pdf_columns) || 2,
    pdf_rows: Number(form.pdf_rows) || 3,
    pdf_margin_mm: Number(form.pdf_margin_mm) || 12,
    pdf_title: form.pdf_title || undefined,
    include_original: form.include_original,
    include_processed: form.include_processed,
    use_session_enhancement: form.use_session_enhancement,
    video_codec: form.video_codec,
    audio_codec: form.audio_codec,
    use_stream_copy: form.use_stream_copy,
    frame_rate_mode: form.frame_rate_mode,
    export_fps: Number(form.export_fps) || 29.97,
    prefer_h265: form.prefer_h265,
    prefer_gpu: form.prefer_gpu,
    image_quality: Number(form.image_quality) || 92,
    crf: Number(form.crf) || 23,
    video_bitrate: form.video_bitrate || undefined,
    encode_preset: form.encode_preset,
  };
}

function bundlePayload(form, sessionId) {
  const paths = resolvedExportPaths(form);
  return {
    input_path: form.input_path,
    output_dir: paths.bundles_dir || paths.output_dir,
    original_dir: paths.evidence_dir,
    processed_dir: paths.examination_dir,
    session_id: sessionId || undefined,
    include_original: form.include_original,
    include_processed: form.include_processed,
    use_session_enhancement: form.use_session_enhancement,
    video_codec: form.video_codec,
    audio_codec: form.audio_codec,
    use_stream_copy: form.use_stream_copy,
    frame_rate_mode: form.frame_rate_mode,
    fps: Number(form.export_fps) || 29.97,
    prefer_h265: form.prefer_h265,
    prefer_gpu: form.prefer_gpu,
    image_quality: Number(form.image_quality) || 92,
    crf: Number(form.crf) || 23,
    video_bitrate: form.video_bitrate?.trim() || null,
    encode_preset: form.encode_preset,
  };
}

export default function LegalExportPanel({
  exportForm,
  setExportForm,
  sessionId,
  forensicCase,
  hasPreview,
  mediaType = 'image',
  hasEvidence = false,
  filterChain = [],
  t,
  setStatus,
  setError,
}) {
  const isVideo = hasEvidence && mediaType === 'video';
  const hasEnhancement = filterChain.length > 0;
  const patch = (key, value) => setExportForm((f) => ({ ...f, [key]: value }));
  const [secureRoot, setSecureRoot] = useState('');
  const [secureScan, setSecureScan] = useState(null);
  const [secureBusy, setSecureBusy] = useState(false);
  const secureOutputDir = exportForm.bundles_dir || exportForm.output_dir || '~/Desktop/chakshu-export/secure-batch';

  const scanSecureMediaAt = useCallback(async (rootPath) => {
    const root = String(rootPath || '').trim();
    if (!root) {
      setError(t('export.secure_need_root', 'Enter secure media folder path'));
      return;
    }
    setSecureBusy(true);
    setError('');
    try {
      const r = await api.forensicsSecureMediaScan(root);
      setSecureScan(r);
      setStatus(t('export.secure_scanned', `Scanned ${r.count} file(s) in secure media`));
    } catch (e) {
      setError(e.message);
    } finally {
      setSecureBusy(false);
    }
  }, [setError, setStatus, t]);

  const browseSecureFolder = useCallback(async () => {
    setSecureBusy(true);
    setError('');
    try {
      const r = await api.browseFolder(secureRoot.trim());
      if (r.cancelled) {
        setStatus(t('export.secure_browse_cancel', 'Folder browse cancelled'));
        return;
      }
      if (!r.path) {
        setError(t('export.secure_browse_fail', 'Could not open folder picker on this system'));
        return;
      }
      setSecureRoot(r.path);
      await scanSecureMediaAt(r.path);
    } catch (e) {
      setError(e.message);
    } finally {
      setSecureBusy(false);
    }
  }, [secureRoot, scanSecureMediaAt, setError, setStatus, t]);

  const setOutputDir = useCallback((dir, syncDerived = true) => {
    const normalized = dir?.trim() || exportForm.project_root || exportForm.output_dir;
    setExportForm((f) => {
      const next = { ...f, project_root: normalized };
      if (!f.use_custom_paths && syncDerived) {
        Object.assign(next, deriveProjectPaths(normalized, folderFieldsFromForm(f)));
      }
      saveExportFormToStorage(next);
      return next;
    });
  }, [exportForm.project_root, exportForm.output_dir, setExportForm]);

  const savePathsToProject = useCallback(async () => {
    try {
      const r = await api.projectExportSettings(pathsPayload(exportForm));
      setStatus(t('export.paths_saved', 'Export paths saved to project'));
      if (r.export_settings) {
        setExportForm((f) => ({ ...f, ...r.export_settings }));
      }
    } catch (e) {
      setError(e.message);
    }
  }, [exportForm, setExportForm, setError, setStatus, t]);

  const defaultPdfTitle = forensicCase?.display_id || forensicCase?.case_number
    ? `${t('export.pdf_title_default', 'Chakshu Frame Export')} — ${forensicCase.display_id || forensicCase.case_number}`
    : t('export.pdf_title_default', 'Chakshu Frame Export');

  const run = useCallback(async (label, fn) => {
    setError('');
    try {
      const r = await fn();
      if (r?.success === false) {
        setError(r.stderr || r.error || `${label} failed`);
        return;
      }
      if (r?.output) {
        const extra = r.frame_count != null ? ` · ${r.frame_count} frame(s)` : '';
        setStatus(`${label}: ${r.output}${extra}`);
      } else if (r?.files?.length) {
        const names = r.files.map((f) => f.role).join(', ');
        setStatus(`${label}: ${r.files.length} file(s) (${names}) → ${r.output_dir || exportForm.output_dir}`);
      } else if (r?.count != null) {
        setStatus(`${label}: ${r.count} item(s)`);
      } else {
        setStatus(`${label} — done`);
      }
      await api.projectExportSettings(pathsPayload(exportForm));
    } catch (e) {
      setError(e.message);
    }
  }, [exportForm, setError, setStatus]);

  const scanSecureMedia = useCallback(async () => {
    await scanSecureMediaAt(secureRoot);
  }, [secureRoot, scanSecureMediaAt]);

  const loadSecureMedia = useCallback(async () => {
    if (!secureRoot.trim()) return;
    setSecureBusy(true);
    try {
      const r = await api.forensicsSecureMediaLoad(
        secureRoot.trim(),
        forensicCase?.examiner || 'examiner',
        forensicCase?.case_id,
      );
      setStatus(
        t('export.secure_loaded', `Loaded ${r.registered} file(s) from secure media (${r.skipped} skipped)`),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setSecureBusy(false);
    }
  }, [secureRoot, forensicCase, setError, setStatus, t]);

  const batchExportSecureMedia = useCallback(async () => {
    if (!secureRoot.trim()) return;
    setSecureBusy(true);
    try {
      const r = await api.forensicsSecureMediaBatchExport({
        source_root: secureRoot.trim(),
        output_dir: secureOutputDir,
        mode: 'copy',
        preserve_structure: true,
      });
      if (r.failed > 0) {
        setError(t('export.secure_batch_partial', `${r.failed} of ${r.total} exports failed — see report`));
      }
      setStatus(
        t('export.secure_batch_done', `Batch export: ${r.done}/${r.total} → ${r.output_dir}`),
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setSecureBusy(false);
    }
  }, [secureRoot, secureOutputDir, setError, setStatus, t]);

  const exportPdf = () => run('PDF export', async () => {
    if (!sessionId) throw new Error(t('export.no_session', 'Start examination session and load a frame first'));
    const title = (exportForm.pdf_title || '').trim() || defaultPdfTitle;
    const paths = resolvedExportPaths(exportForm);
    return api.exportPdfFrames({
      session_id: sessionId,
      output_path: paths.pdf_path,
      page_size: exportForm.pdf_page_size,
      orientation: exportForm.pdf_orientation,
      columns: Math.max(1, Number(exportForm.pdf_columns) || 2),
      rows: Math.max(1, Number(exportForm.pdf_rows) || 3),
      margin_mm: Math.max(0, Number(exportForm.pdf_margin_mm) || 12),
      title,
    });
  });

  const gridHint = `${exportForm.pdf_columns || 2}×${exportForm.pdf_rows || 3} = ${
    (Number(exportForm.pdf_columns) || 2) * (Number(exportForm.pdf_rows) || 3)
  } ${t('export.frames_per_page', 'frames per page')}`;

  const exportBundle = (overrides = {}) => run('Media export', () => api.exportMediaBundle({
    ...bundlePayload(exportForm, sessionId),
    ...overrides,
  }));

  const exportPaths = resolvedExportPaths(exportForm);
  const custom = exportForm.use_custom_paths;
  const useStructure = exportForm.use_project_structure !== false;

  return (
    <div className="fx-export-layout">
      <div className="fx-panel fx-export-output-panel">
        <div className="fx-panel-head">{t('export.output_config', 'Output configuration')}</div>
        <div className="fx-panel-body fx-export-form">
            <Field
            id="exp-out-main"
            label={useStructure ? t('export.project_root', 'Project root') : t('export.output_dir', 'Output directory')}
            hint={useStructure
              ? t('export.project_root_hint', 'Configure folder names in Settings → Project folder structure.')
              : t('export.output_dir_hint', 'All exports write under this folder unless you enable custom paths below.')}
          >
            <input
              id="exp-out-main"
              className="fx-input fx-input-mono"
              value={exportForm.project_root || exportForm.output_dir}
              onChange={(e) => setOutputDir(e.target.value)}
              onBlur={(e) => setOutputDir(e.target.value, true)}
              placeholder="~/Desktop/chakshu-export"
            />
          </Field>
          <div className="fx-export-actions-row">
            <button
              type="button"
              className="fx-btn"
              onClick={() => {
                const root = exportForm.project_root || exportForm.output_dir;
                const parts = normalizeDir(root).split('/');
                const base = parts.length > 1 ? parts.slice(0, -1).join('/') : '~/Desktop/chakshu-export';
                const caseRoot = projectRootForCase(base, forensicCase);
                setExportForm((f) => {
                  const next = {
                    ...f,
                    project_root: caseRoot,
                    ...deriveProjectPaths(caseRoot, folderFieldsFromForm(f)),
                  };
                  saveExportFormToStorage(next);
                  return next;
                });
                setStatus(t('export.case_folder_set', 'Project root set for active case'));
              }}
              disabled={!forensicCase?.display_id && !forensicCase?.case_number}
            >
              {t('export.use_case_folder', 'Use case subfolder')}
            </button>
            <button type="button" className="fx-btn" onClick={() => setOutputDir(exportForm.project_root || exportForm.output_dir, true)}>
              {t('export.apply_derived', 'Apply default file paths')}
            </button>
            <button type="button" className="fx-btn fx-btn-primary" onClick={savePathsToProject}>
              {t('export.save_paths', 'Save paths to project')}
            </button>
          </div>
          <div className="fx-a11y-row" style={{ marginTop: 4 }}>
            <input
              id="exp-custom-paths"
              type="checkbox"
              checked={custom}
              onChange={(e) => {
                const useCustom = e.target.checked;
                setExportForm((f) => {
                  if (!useCustom) {
                    const root = f.project_root || f.output_dir;
                    return {
                      ...f,
                      use_custom_paths: false,
                      ...deriveProjectPaths(root, folderFieldsFromForm(f)),
                    };
                  }
                  return { ...f, use_custom_paths: true };
                });
              }}
            />
            <label htmlFor="exp-custom-paths">{t('export.custom_paths', 'Custom paths for each export type')}</label>
          </div>
          {!custom && (
            <ul className="fx-export-derived-list">
              <li><span>Evidence</span><code>{exportPaths.evidence_dir}</code></li>
              <li><span>Examination</span><code>{exportPaths.examination_dir}</code></li>
              <li><span>Bundles</span><code>{exportPaths.bundles_dir}</code></li>
              <li><span>PDF</span><code>{exportPaths.pdf_path}</code></li>
              <li><span>I-frames</span><code>{exportPaths.i_frames_dir}</code></li>
              <li><span>Audio</span><code>{exportPaths.audio_out}</code></li>
              <li><span>Metadata</span><code>{exportPaths.metadata_path}</code></li>
            </ul>
          )}
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">{t('export.paths', 'Paths')}</div>
        <div className="fx-panel-body fx-export-form">
          <Field id="exp-input" label={t('export.input_path', 'Source media path')}>
            <input
              id="exp-input"
              className="fx-input fx-input-mono"
              value={exportForm.input_path}
              onChange={(e) => patch('input_path', e.target.value)}
              placeholder="/path/to/evidence.mp4"
            />
          </Field>
          {custom && (
            <>
              <Field id="exp-pdf" label={t('export.pdf_path', 'PDF output file')}>
                <input
                  id="exp-pdf"
                  className="fx-input fx-input-mono"
                  value={exportForm.pdf_path}
                  onChange={(e) => patch('pdf_path', e.target.value)}
                />
              </Field>
              <Field id="exp-iframe" label={t('export.iframe_dir', 'I-frame output folder')}>
                <input
                  id="exp-iframe"
                  className="fx-input fx-input-mono"
                  value={exportForm.i_frames_dir}
                  onChange={(e) => patch('i_frames_dir', e.target.value)}
                />
              </Field>
              <Field id="exp-audio" label={t('export.audio_path', 'Audio extract path')}>
                <input
                  id="exp-audio"
                  className="fx-input fx-input-mono"
                  value={exportForm.audio_out}
                  onChange={(e) => patch('audio_out', e.target.value)}
                />
              </Field>
            </>
          )}
        </div>
      </div>

      <div className="fx-panel fx-export-encoding-panel">
        <div className="fx-panel-head">{t('export.media_bundle', 'Original & processed media export')}</div>
        <div className="fx-panel-body fx-export-form">
          <p className="fx-export-hint">
            {t(
              'export.bundle_hint',
              'Export bit-exact original evidence and processed output. Images use the examination session when filters are applied; video is re-encoded with the settings below.',
            )}
          </p>
          <div className="fx-export-check-row">
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.include_original}
                onChange={(e) => patch('include_original', e.target.checked)}
              />
              {t('export.include_original', 'Include original media')}
            </label>
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.include_processed}
                onChange={(e) => patch('include_processed', e.target.checked)}
              />
              {t('export.include_processed', 'Include processed media')}
            </label>
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.use_session_enhancement}
                disabled={!sessionId}
                onChange={(e) => patch('use_session_enhancement', e.target.checked)}
              />
              {t('export.use_session', 'Use examination session (enhanced frame)')}
            </label>
          </div>
          {sessionId && hasEnhancement && (
            <p className="fx-export-hint fx-export-session-hint">
              {t('export.session_ready', 'Active session has')} {filterChain.length} {t('export.filters_applied', 'filter(s) — processed image will reflect enhancements.')}
            </p>
          )}
          <div className="fx-export-grid-2">
            <Field id="exp-vcodec" label={t('export.video_codec', 'Video codec')}>
              <select id="exp-vcodec" className="fx-input" value={exportForm.video_codec} onChange={(e) => patch('video_codec', e.target.value)}>
                {VIDEO_CODECS.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
              </select>
            </Field>
            <Field id="exp-acodec" label={t('export.audio_codec', 'Audio codec')}>
              <select id="exp-acodec" className="fx-input" value={exportForm.audio_codec} onChange={(e) => patch('audio_codec', e.target.value)}>
                {AUDIO_CODECS.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
              </select>
            </Field>
            <Field id="exp-frmode" label={t('export.frame_rate_mode', 'Frame rate mode')}>
              <select id="exp-frmode" className="fx-input" value={exportForm.frame_rate_mode} onChange={(e) => patch('frame_rate_mode', e.target.value)}>
                {FRAME_RATE_MODES.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
            </Field>
            <Field id="exp-fps" label={t('export.fps', 'Export FPS (CFR)')}>
              <input
                id="exp-fps"
                type="number"
                step="0.01"
                min={1}
                max={120}
                className="fx-input"
                value={exportForm.export_fps}
                onChange={(e) => patch('export_fps', e.target.value)}
              />
            </Field>
            <Field id="exp-crf" label={t('export.crf', 'Quality (CRF)')} hint={t('export.crf_hint', 'Lower = higher quality. Typical 18–28 for H.264/H.265.')}>
              <input
                id="exp-crf"
                type="number"
                min={0}
                max={51}
                className="fx-input"
                value={exportForm.crf}
                onChange={(e) => patch('crf', e.target.value)}
              />
            </Field>
            <Field id="exp-bitrate" label={t('export.bitrate', 'Bitrate (optional)')} hint={t('export.bitrate_hint', 'e.g. 8M — overrides CRF when set')}>
              <input
                id="exp-bitrate"
                className="fx-input"
                placeholder="8M"
                value={exportForm.video_bitrate}
                onChange={(e) => patch('video_bitrate', e.target.value)}
              />
            </Field>
            <Field id="exp-preset" label={t('export.encode_preset', 'CPU encode preset')}>
              <select id="exp-preset" className="fx-input" value={exportForm.encode_preset} onChange={(e) => patch('encode_preset', e.target.value)}>
                {ENCODE_PRESETS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field id="exp-imgq" label={t('export.image_quality', 'JPEG quality (images)')}>
              <input
                id="exp-imgq"
                type="number"
                min={50}
                max={100}
                className="fx-input"
                value={exportForm.image_quality}
                onChange={(e) => patch('image_quality', e.target.value)}
              />
            </Field>
          </div>
          <div className="fx-export-check-row" style={{ marginTop: 8 }}>
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.use_stream_copy}
                onChange={(e) => patch('use_stream_copy', e.target.checked)}
              />
              {t('export.stream_copy', 'Stream copy (no video re-encode)')}
            </label>
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.prefer_h265}
                onChange={(e) => patch('prefer_h265', e.target.checked)}
              />
              {t('export.prefer_h265', 'Prefer H.265 when auto-selecting')}
            </label>
            <label className="fx-export-check">
              <input
                type="checkbox"
                checked={exportForm.prefer_gpu}
                onChange={(e) => patch('prefer_gpu', e.target.checked)}
              />
              {t('export.prefer_gpu', 'Prefer GPU encoder when auto-selecting')}
            </label>
          </div>
          <div className="fx-export-actions-row" style={{ marginTop: 12 }}>
            <button
              type="button"
              className="fx-btn fx-btn-primary"
              disabled={!exportForm.input_path || (!exportForm.include_original && !exportForm.include_processed)}
              onClick={() => exportBundle()}
            >
              {t('export.bundle_btn', 'Export examination bundle')}
            </button>
            <button
              type="button"
              className="fx-btn"
              disabled={!exportForm.input_path}
              onClick={() => exportBundle({ include_processed: false, include_original: true })}
            >
              {t('export.original_only', 'Original only')}
            </button>
            <button
              type="button"
              className="fx-btn"
              disabled={!exportForm.input_path}
              onClick={() => exportBundle({ include_original: false, include_processed: true })}
            >
              {t('export.processed_only', 'Processed only')}
            </button>
          </div>
        </div>
      </div>

      <div className="fx-panel">
        <div className="fx-panel-head">{t('panel.legal_export', 'Legal Export')} — {t('export.media_actions', 'Media & metadata')}</div>
        <div className="fx-panel-body">
          {isVideo && (
            <>
              <button
                type="button"
                className="fx-btn fx-btn-primary"
                disabled={!exportForm.input_path}
                onClick={() => run('I-frame export', () => api.exportIFrames({
                  input_path: exportForm.input_path,
                  output_dir: exportForm.i_frames_dir,
                }))}
              >
                {t('export.iframe_btn', 'Export I-Frames Only')}
              </button>
              <button
                type="button"
                className="fx-btn"
                style={{ marginTop: 8 }}
                disabled={!exportForm.input_path}
                onClick={() => run('Audio extract', () => api.extractAudio({
                  input_path: exportForm.input_path,
                  output_path: exportForm.audio_out,
                }))}
              >
                {t('export.audio_btn', 'Extract Audio Stream')}
              </button>
              <button
                type="button"
                className="fx-btn"
                style={{ marginTop: 8 }}
                disabled={!exportForm.input_path}
                onClick={() => run('Trim segment', () => api.capTrim({
                  input_path: exportForm.input_path,
                  output_path: `${exportPaths.trim_dir || exportPaths.bundles_dir}/trim.mp4`,
                  start_sec: 0,
                  end_sec: 30,
                }))}
              >
                {t('export.trim_btn', 'Trim Segment (stream copy)')}
              </button>
              <p className="fx-export-hint" style={{ marginTop: 8 }}>
                {t('export.redact_hint', 'Configure mute regions in Forensic Tools or Timeline Pro → Audio Redaction.')}
              </p>
            </>
          )}
          {!isVideo && hasEvidence && (
            <p className="fx-export-hint">
              {t('export.image_only_hint', 'Video export actions appear when video evidence is loaded.')}
            </p>
          )}
          <button
            type="button"
            className="fx-btn"
            style={{ marginTop: 8 }}
            disabled={!exportForm.input_path}
            onClick={() => run('Metadata export', () => api.capMetadataExport(
              exportForm.input_path,
              exportPaths.metadata_path,
            ))}
          >
            {t('export.metadata_btn', 'Export Metadata Bundle')}
          </button>
        </div>
      </div>

      <div className="fx-panel fx-export-pdf-panel">
        <div className="fx-panel-head">{t('export.pdf_layout', 'PDF frame layout')}</div>
        <div className="fx-panel-body fx-export-form">
          <p className="fx-export-hint">
            {hasPreview
              ? t('export.pdf_ready', 'Exports the current examination frame from the active session.')
              : t('export.pdf_need_frame', 'Load evidence in Examination Lab (or seek a frame) before exporting to PDF.')}
            {' '}
            <code className="fx-export-inline-path">{exportForm.pdf_path}</code>
          </p>
          <div className="fx-export-grid-2">
            <Field id="pdf-size" label={t('export.page_size', 'Page size')}>
              <select
                id="pdf-size"
                className="fx-input"
                value={exportForm.pdf_page_size}
                onChange={(e) => patch('pdf_page_size', e.target.value)}
              >
                {PAGE_SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field id="pdf-orient" label={t('export.orientation', 'Orientation')}>
              <select
                id="pdf-orient"
                className="fx-input"
                value={exportForm.pdf_orientation}
                onChange={(e) => patch('pdf_orientation', e.target.value)}
              >
                {ORIENTATIONS.map((o) => (
                  <option key={o} value={o}>{t(`export.orientation.${o}`, o)}</option>
                ))}
              </select>
            </Field>
            <Field id="pdf-cols" label={t('export.columns', 'Columns')}>
              <input
                id="pdf-cols"
                type="number"
                min={1}
                max={6}
                className="fx-input"
                value={exportForm.pdf_columns}
                onChange={(e) => patch('pdf_columns', e.target.value)}
              />
            </Field>
            <Field id="pdf-rows" label={t('export.rows', 'Rows')}>
              <input
                id="pdf-rows"
                type="number"
                min={1}
                max={8}
                className="fx-input"
                value={exportForm.pdf_rows}
                onChange={(e) => patch('pdf_rows', e.target.value)}
              />
            </Field>
            <Field id="pdf-margin" label={t('export.margin_mm', 'Margin (mm)')}>
              <input
                id="pdf-margin"
                type="number"
                min={0}
                max={40}
                step={0.5}
                className="fx-input"
                value={exportForm.pdf_margin_mm}
                onChange={(e) => patch('pdf_margin_mm', e.target.value)}
              />
            </Field>
          </div>
          <p className="fx-export-hint fx-export-grid-hint">{gridHint}</p>
          <Field id="pdf-title" label={t('export.pdf_title', 'Report title (header)')}>
            <input
              id="pdf-title"
              className="fx-input"
              value={exportForm.pdf_title}
              onChange={(e) => patch('pdf_title', e.target.value)}
              placeholder={defaultPdfTitle}
            />
          </Field>
          <button
            type="button"
            className="fx-btn fx-btn-primary"
            style={{ marginTop: 4 }}
            disabled={!sessionId}
            onClick={exportPdf}
          >
            {t('export.pdf_btn', 'Export Frames to PDF')}
          </button>
        </div>
      </div>

      <div className="fx-panel fx-export-pdf-panel">
        <div className="fx-panel-head">{t('export.secure_media_title', 'Secure media batch (R-145)')}</div>
        <div className="fx-panel-body fx-export-form">
          <p className="fx-export-hint">
            {t(
              'export.secure_media_hint',
              'Scan a read-only evidence folder (nested folders supported), load files into the case by reference, or batch-export with SHA-256 verified copies and reports.',
            )}
          </p>
          <Field id="secure-root" label={t('export.secure_root', 'Secure media folder')}>
            <div className="fx-export-path-row">
              <input
                id="secure-root"
                className="fx-input fx-export-path-input"
                placeholder="/Volumes/Evidence/case-001"
                value={secureRoot}
                onChange={(e) => {
                  setSecureRoot(e.target.value);
                  setSecureScan(null);
                }}
              />
              <button
                type="button"
                className="fx-btn fx-export-browse-btn"
                disabled={secureBusy}
                onClick={browseSecureFolder}
              >
                {secureBusy ? '…' : t('export.browse_folder', 'Browse…')}
              </button>
            </div>
          </Field>
          <p className="fx-export-hint">
            {t('export.secure_output', 'Batch output')}: <code className="fx-export-inline-path">{secureOutputDir}</code>
          </p>
          {secureScan?.count != null && (
            <p className="fx-export-hint">
              {t('export.secure_scan_result', `${secureScan.count} media file(s) found`)}
              {secureScan.has_manifest ? ` · ${t('export.secure_manifest', 'manifest present')}` : ''}
            </p>
          )}
          <div className="fx-export-actions-row">
            <button type="button" className="fx-btn" disabled={secureBusy} onClick={scanSecureMedia}>
              {secureBusy ? '…' : t('export.secure_scan_btn', 'Scan folder')}
            </button>
            <button type="button" className="fx-btn" disabled={secureBusy || !secureScan?.count} onClick={loadSecureMedia}>
              {t('export.secure_load_btn', 'Load into case')}
            </button>
            <button
              type="button"
              className="fx-btn fx-btn-primary"
              disabled={secureBusy || !secureScan?.count}
              onClick={batchExportSecureMedia}
            >
              {t('export.secure_batch_btn', 'Batch export (verified copy)')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
