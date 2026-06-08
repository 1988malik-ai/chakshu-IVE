import { useCallback } from 'react';
import { api } from '../api/client';
import { derivePathsFromOutputDir, normalizeDir, outputDirForCase } from '../lib/exportPaths';

const PAGE_SIZES = ['A4', 'Letter', 'Legal', 'A3'];
const ORIENTATIONS = ['portrait', 'landscape'];

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
  return {
    output_dir: form.output_dir,
    pdf_path: form.pdf_path,
    i_frames_dir: form.i_frames_dir,
    audio_out: form.audio_out,
    input_path: form.input_path || undefined,
    use_custom_paths: form.use_custom_paths,
    pdf_page_size: form.pdf_page_size,
    pdf_orientation: form.pdf_orientation,
    pdf_columns: Number(form.pdf_columns) || 2,
    pdf_rows: Number(form.pdf_rows) || 3,
    pdf_margin_mm: Number(form.pdf_margin_mm) || 12,
    pdf_title: form.pdf_title || undefined,
  };
}

export default function LegalExportPanel({
  exportForm,
  setExportForm,
  sessionId,
  forensicCase,
  hasPreview,
  t,
  setStatus,
  setError,
}) {
  const patch = (key, value) => setExportForm((f) => ({ ...f, [key]: value }));

  const setOutputDir = useCallback((dir, syncDerived = true) => {
    const normalized = dir?.trim() || exportForm.output_dir;
    setExportForm((f) => {
      const next = { ...f, output_dir: normalized };
      if (!f.use_custom_paths && syncDerived) {
        Object.assign(next, derivePathsFromOutputDir(normalized));
      }
      return next;
    });
  }, [exportForm.output_dir, setExportForm]);

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

  const exportPdf = () => run('PDF export', async () => {
    if (!sessionId) throw new Error(t('export.no_session', 'Start examination session and load a frame first'));
    const title = (exportForm.pdf_title || '').trim() || defaultPdfTitle;
    return api.exportPdfFrames({
      session_id: sessionId,
      output_path: exportForm.pdf_path,
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

  const custom = exportForm.use_custom_paths;

  return (
    <div className="fx-export-layout">
      <div className="fx-panel fx-export-output-panel">
        <div className="fx-panel-head">{t('export.output_config', 'Output configuration')}</div>
        <div className="fx-panel-body fx-export-form">
          <Field
            id="exp-out-main"
            label={t('export.output_dir', 'Output directory')}
            hint={t('export.output_dir_hint', 'All exports write under this folder unless you enable custom paths below.')}
          >
            <input
              id="exp-out-main"
              className="fx-input fx-input-mono"
              value={exportForm.output_dir}
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
                const parts = normalizeDir(exportForm.output_dir).split('/');
                const base = parts.length > 1 ? parts.slice(0, -1).join('/') : '~/Desktop/chakshu-export';
                setOutputDir(outputDirForCase(base, forensicCase), true);
                setStatus(t('export.case_folder_set', 'Output folder set for active case'));
              }}
              disabled={!forensicCase?.display_id && !forensicCase?.case_number}
            >
              {t('export.use_case_folder', 'Use case subfolder')}
            </button>
            <button type="button" className="fx-btn" onClick={() => setOutputDir(exportForm.output_dir, true)}>
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
                    return { ...f, use_custom_paths: false, ...derivePathsFromOutputDir(f.output_dir) };
                  }
                  return { ...f, use_custom_paths: true };
                });
              }}
            />
            <label htmlFor="exp-custom-paths">{t('export.custom_paths', 'Custom paths for each export type')}</label>
          </div>
          {!custom && (
            <ul className="fx-export-derived-list">
              <li><span>PDF</span><code>{exportForm.pdf_path}</code></li>
              <li><span>I-frames</span><code>{exportForm.i_frames_dir}</code></li>
              <li><span>Audio</span><code>{exportForm.audio_out}</code></li>
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

      <div className="fx-panel">
        <div className="fx-panel-head">{t('panel.legal_export', 'Legal Export')} — {t('export.media_actions', 'Media & metadata')}</div>
        <div className="fx-panel-body">
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
              output_path: `${exportForm.output_dir}/trim.mp4`,
              start_sec: 0,
              end_sec: 30,
            }))}
          >
            {t('export.trim_btn', 'Trim Segment (stream copy)')}
          </button>
          <p className="fx-export-hint" style={{ marginTop: 8 }}>
            {t('export.redact_hint', 'Configure mute regions in Forensic Tools or Timeline Pro → Audio Redaction.')}
          </p>
          <button
            type="button"
            className="fx-btn"
            style={{ marginTop: 8 }}
            disabled={!exportForm.input_path}
            onClick={() => run('Metadata export', () => api.capMetadataExport(
              exportForm.input_path,
              `${exportForm.output_dir}/metadata.json`,
            ))}
          >
            {t('export.metadata_btn', 'Export Metadata Bundle')}
          </button>
          <button
            type="button"
            className="fx-btn"
            style={{ marginTop: 8 }}
            disabled={!exportForm.input_path}
            onClick={() => run('Examination bundle', () => api.exportMediaBundle({
              input_path: exportForm.input_path,
              output_dir: exportForm.output_dir,
              include_original: true,
              include_processed: true,
            }))}
          >
            {t('export.bundle_btn', 'Export Examination Bundle')}
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
    </div>
  );
}
