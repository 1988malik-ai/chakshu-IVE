import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import { resolvedExportPaths } from '../lib/exportPaths';

const TEMPLATES = ['standard', 'detailed', 'executive', 'minimal'];
const PAPER_SIZES = ['A4', 'Letter', 'Legal', 'A3'];
const ORIENTATIONS = ['portrait', 'landscape'];

export default function CaseReportsPanel({
  t = (k, d) => d,
  forensicCase,
  exportForm,
  locale,
  setStatus,
  setError,
  notify,
}) {
  const defaultOutputDir = useMemo(() => (
    resolvedExportPaths(exportForm || {}).reports_dir || '~/Desktop/chakshu-export/reports'
  ), [exportForm]);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [outputDir, setOutputDir] = useState(defaultOutputDir);
  const [template, setTemplate] = useState('detailed');
  const [paperSize, setPaperSize] = useState('A4');
  const [orientation, setOrientation] = useState('portrait');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState(forensicCase?.examiner || '');
  const [formats, setFormats] = useState({ html: true, pdf: true, docx: true });
  const [includeSettings, setIncludeSettings] = useState(true);
  const [includeReferences, setIncludeReferences] = useState(true);
  const [includeNotes, setIncludeNotes] = useState(true);
  const [includeBookmarks, setIncludeBookmarks] = useState(true);
  const [lastOutputs, setLastOutputs] = useState([]);

  useEffect(() => {
    setAuthor(forensicCase?.examiner || '');
    if (!title && forensicCase?.display_id) {
      setTitle(
        `${t('report.title', 'Chakshu Processing Report')} — ${forensicCase.display_id || forensicCase.case_number}`,
      );
    }
  }, [forensicCase, t, title]);

  useEffect(() => {
    setOutputDir((current) => (
      !current || current === '[object Object]' || typeof current !== 'string'
        ? defaultOutputDir
        : current
    ));
  }, [defaultOutputDir]);

  const refreshPreview = useCallback(async () => {
    try {
      const r = await api.reportPreview();
      setPreview(r);
    } catch {
      setPreview(null);
    }
  }, []);

  useEffect(() => {
    refreshPreview();
  }, [refreshPreview]);

  const toggleFormat = (key) => setFormats((f) => ({ ...f, [key]: !f[key] }));

  const selectedFormats = () =>
    ['html', 'pdf', 'docx'].filter((k) => formats[k]);

  const generate = async () => {
    const fmt = selectedFormats();
    if (!fmt.length) {
      setError(t('report.no_format', 'Select at least one output format'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const r = await api.generateReport({
        output_dir: outputDir,
        title: title.trim() || t('report.title', 'Chakshu Processing Report'),
        author: author.trim(),
        locale,
        template,
        paper_size: paperSize,
        orientation,
        formats: fmt,
        include_settings: includeSettings,
        include_references: includeReferences,
        include_notes: includeNotes,
        include_bookmarks: includeBookmarks,
      });
      if (!r.success) {
        throw new Error((r.errors || []).join('; ') || t('report.failed', 'Report generation failed'));
      }
      setLastOutputs(r.outputs || []);
      const paths = (r.outputs || []).map((o) => `${o.format}: ${o.path}`).join(' · ');
      setStatus(`${t('report.done', 'Reports generated')} (${r.step_count ?? 0} ${t('report.steps_count', 'steps')}) — ${paths}`);
      notify?.(t('report.toast_done', 'HTML / PDF / DOCX reports saved'), 'success');
      await refreshPreview();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fx-panel fx-reports-panel">
      <div className="fx-panel-head">{t('panel.case_reports', 'Case Report Generation')}</div>
      <div className="fx-panel-body fx-export-form">
        <p className="fx-export-hint">{t('report.hint', 'Includes workflow steps, filter settings, and references for court-ready documentation.')}</p>

        {preview && (
          <div className="fx-reports-stats">
            <span>{preview.step_count} {t('report.steps_recorded', 'processing steps')}</span>
            <span>{preview.pipeline_count} {t('report.pipeline_filters', 'pipeline filters')}</span>
            <span>{preview.notes_count} {t('report.notes_included', 'notes')}</span>
            <span>{preview.bookmark_count} {t('report.bookmarks_included', 'bookmarks')}</span>
          </div>
        )}

        <div className="fx-reports-grid">
          <label>
            {t('report.output_dir', 'Output directory')}
            <input className="fx-input" value={outputDir} onChange={(e) => setOutputDir(e.target.value)} />
          </label>
          <label>
            {t('report.template', 'Template')}
            <select className="fx-input" value={template} onChange={(e) => setTemplate(e.target.value)}>
              {TEMPLATES.map((tpl) => (
                <option key={tpl} value={tpl}>{tpl}</option>
              ))}
            </select>
          </label>
          <label>
            {t('report.paper_size', 'Paper size')}
            <select className="fx-input" value={paperSize} onChange={(e) => setPaperSize(e.target.value)}>
              {PAPER_SIZES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            {t('report.orientation', 'Orientation')}
            <select className="fx-input" value={orientation} onChange={(e) => setOrientation(e.target.value)}>
              {ORIENTATIONS.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </label>
          <label className="fx-reports-span2">
            {t('report.report_title', 'Report title')}
            <input className="fx-input" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            {t('report.author', 'Author / examiner')}
            <input className="fx-input" value={author} onChange={(e) => setAuthor(e.target.value)} />
          </label>
        </div>

        <div className="fx-reports-formats">
          <span className="fx-reports-label">{t('report.formats', 'Output formats')}</span>
          {['html', 'pdf', 'docx'].map((f) => (
            <label key={f} className="fx-reports-check">
              <input type="checkbox" checked={formats[f]} onChange={() => toggleFormat(f)} />
              {f.toUpperCase()}
            </label>
          ))}
        </div>

        <div className="fx-reports-formats">
          <span className="fx-reports-label">{t('report.include', 'Include in report')}</span>
          <label className="fx-reports-check">
            <input type="checkbox" checked={includeSettings} onChange={(e) => setIncludeSettings(e.target.checked)} />
            {t('report.col.settings', 'Settings')}
          </label>
          <label className="fx-reports-check">
            <input type="checkbox" checked={includeReferences} onChange={(e) => setIncludeReferences(e.target.checked)} />
            {t('report.col.references', 'References')}
          </label>
          <label className="fx-reports-check">
            <input type="checkbox" checked={includeNotes} onChange={(e) => setIncludeNotes(e.target.checked)} />
            {t('report.examination_notes', 'Examination notes')}
          </label>
          <label className="fx-reports-check">
            <input type="checkbox" checked={includeBookmarks} onChange={(e) => setIncludeBookmarks(e.target.checked)} />
            {t('report.bookmarks', 'Bookmarks')}
          </label>
        </div>

        {preview?.recent_steps?.length > 0 && (
          <div className="fx-reports-preview-steps">
            <div className="fx-reports-label">{t('report.recent_steps', 'Recent processing steps')}</div>
            <ul>
              {preview.recent_steps.map((s, i) => (
                <li key={`${s.timestamp}-${i}`}>
                  <code>{s.action}</code>
                  {s.references?.length ? ` · ${s.references.join(', ')}` : ''}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="fx-export-actions-row">
          <button type="button" className="fx-btn fx-btn-primary" disabled={loading} onClick={generate}>
            {loading ? t('report.generating', 'Generating…') : t('report.generate', 'Generate HTML / PDF / DOCX')}
          </button>
          <button type="button" className="fx-btn" disabled={loading} onClick={refreshPreview}>
            {t('report.refresh_preview', 'Refresh summary')}
          </button>
        </div>

        {lastOutputs.length > 0 && (
          <ul className="fx-reports-output-list">
            {lastOutputs.map((o) => (
              <li key={o.path}>
                <strong>{o.format.toUpperCase()}</strong>
                <code title={o.path}>{o.path}</code>
                {o.note ? <span className="fx-reports-note">{o.note}</span> : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
