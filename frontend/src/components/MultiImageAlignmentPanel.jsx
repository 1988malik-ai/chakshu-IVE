import { useMemo, useState } from 'react';
import { api } from '../api/client';
import { resolvedExportPaths } from '../lib/exportPaths';
import { formatApiError } from '../lib/notify';

function splitPaths(raw) {
  return raw
    .split(/[\n,]+/)
    .map((p) => p.trim())
    .filter(Boolean);
}

function alignmentOutputDir(exportForm) {
  const paths = resolvedExportPaths(exportForm || {});
  const base = paths.examination_dir || paths.output_dir || '~/Desktop/chakshu-export';
  return `${base}/perspective-alignment`;
}

export default function MultiImageAlignmentPanel({
  inputPath,
  exportForm,
  disabled = false,
  setStatus,
  reportSuccess,
  reportError,
  t = (k, d) => d,
}) {
  const [active, setActive] = useState(false);
  const [referencePath, setReferencePath] = useState(inputPath || '');
  const [targetPaths, setTargetPaths] = useState('');
  const [outputDir, setOutputDir] = useState(() => alignmentOutputDir(exportForm));
  const [method, setMethod] = useState('auto');
  const [manualJson, setManualJson] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  const targets = useMemo(() => splitPaths(targetPaths), [targetPaths]);
  const canRun = !disabled && referencePath.trim() && targets.length > 0 && !running;

  const useCurrentEvidence = () => {
    if (inputPath) setReferencePath(inputPath);
  };

  const addTarget = () => {
    if (!inputPath) return;
    setTargetPaths((prev) => (prev.trim() ? `${prev.trim()}\n${inputPath}` : inputPath));
  };

  const runAlignment = async () => {
    if (!canRun) return;
    setRunning(true);
    setResult(null);
    try {
      let correspondences = [];
      if (manualJson.trim()) {
        correspondences = JSON.parse(manualJson);
      }
      const r = await api.capMultiImageAlign({
        reference_path: referencePath.trim(),
        input_paths: targets,
        output_dir: outputDir.trim(),
        method,
        correspondences,
      });
      setResult(r);
      const msg = t('align.saved', `Aligned ${r.outputs?.length || 0} image(s)`);
      setStatus?.(`${msg} — ${r.output_dir}`);
      reportSuccess?.(msg);
    } catch (e) {
      const msg = formatApiError(e, 'Perspective alignment failed');
      reportError?.(msg, 'Multi-image alignment');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className={`fx-perspective-panel fx-align-panel${active ? ' fx-perspective-panel-active' : ''}`}>
      <div className="fx-perspective-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={active}
            disabled={disabled}
            onChange={(e) => setActive(e.target.checked)}
          />
          <span>{t('align.title', 'Multi-image perspective alignment')}</span>
        </label>
      </div>
      {active && (
        <div className="fx-perspective-body">
          <p className="fx-grid-hint">
            {t(
              'align.hint',
              'Align target images into the same plane as a reference image. Use Auto for feature matching, or Manual with point-pair JSON for low-texture evidence.',
            )}
          </p>
          <div className="fx-align-grid">
            <label>
              <span>{t('align.reference', 'Reference image')}</span>
              <input
                className="fx-input"
                value={referencePath}
                onChange={(e) => setReferencePath(e.target.value)}
                placeholder="/path/to/reference.jpg"
              />
            </label>
            <div className="fx-align-inline-actions">
              <button type="button" className="fx-btn" disabled={!inputPath} onClick={useCurrentEvidence}>
                {t('align.use_current', 'Use current evidence')}
              </button>
              <button type="button" className="fx-btn" disabled={!inputPath} onClick={addTarget}>
                {t('align.add_current', 'Add current as target')}
              </button>
            </div>
            <label>
              <span>{t('align.targets', 'Target image paths')}</span>
              <textarea
                className="fx-input"
                rows={3}
                value={targetPaths}
                onChange={(e) => setTargetPaths(e.target.value)}
                placeholder={'/path/to/target-1.jpg\n/path/to/target-2.jpg'}
              />
            </label>
            <label>
              <span>{t('align.output_dir', 'Output folder')}</span>
              <input className="fx-input" value={outputDir} onChange={(e) => setOutputDir(e.target.value)} />
            </label>
            <label>
              <span>{t('align.method', 'Method')}</span>
              <select className="fx-input" value={method} onChange={(e) => setMethod(e.target.value)}>
                <option value="auto">{t('align.auto', 'Auto feature match')}</option>
                <option value="manual">{t('align.manual', 'Manual point pairs')}</option>
              </select>
            </label>
            <label>
              <span>{t('align.manual_json', 'Manual point-pair JSON')}</span>
              <textarea
                className="fx-input fx-align-json"
                rows={4}
                value={manualJson}
                onChange={(e) => setManualJson(e.target.value)}
                placeholder='[{"input_path":"target.jpg","reference_points":[[0,0],[300,0],[300,200],[0,200]],"moving_points":[[8,12],[292,5],[310,210],[2,190]]}]'
              />
            </label>
          </div>
          <div className="fx-export-actions-row">
            <button type="button" className="fx-btn fx-btn-primary" disabled={!canRun} onClick={runAlignment}>
              {running ? t('align.running', 'Aligning…') : t('align.run', 'Align images')}
            </button>
            <span className="fx-grid-hint">{targets.length} {t('align.targets_count', 'target(s) queued')}</span>
          </div>
          {result?.outputs?.length > 0 && (
            <ul className="fx-align-results">
              {result.outputs.map((o) => (
                <li key={o.output_path}>
                  <strong>{o.method}</strong>
                  <code title={o.output_path}>{o.output_path}</code>
                  <span>{t('align.error_px', 'RMS')} {o.rms_error_px}px</span>
                </li>
              ))}
            </ul>
          )}
          {result?.errors?.length > 0 && (
            <p className="fx-grid-hint fx-align-warning">{result.errors.join(' · ')}</p>
          )}
        </div>
      )}
    </div>
  );
}
