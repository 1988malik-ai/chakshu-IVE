import { useState } from 'react';
import { api } from '../api/client';

export default function ProjectImportPanel({ t = (k, d) => d, setStatus, setError }) {
  const [path, setPath] = useState('');
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);

  const inspect = async () => {
    if (!path.trim()) return setError?.('Enter a project file path first.');
    setBusy(true);
    try {
      const r = await api.projectImportInspect(path.trim());
      setSummary(r);
      setStatus?.(r.supported ? 'Project compatibility checked' : 'Project is not compatible');
    } catch (e) {
      setError?.(e.message);
    } finally {
      setBusy(false);
    }
  };

  const importProject = async () => {
    if (!path.trim()) return setError?.('Enter a project file path first.');
    setBusy(true);
    try {
      const r = await api.projectImport(path.trim());
      setSummary(r.summary || summary);
      setStatus?.(`Imported project: ${r.name || r.project_id}`);
    } catch (e) {
      setError?.(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fx-panel fx-settings-panel">
      <div className="fx-panel-head">{t('settings.project_import', 'Project import')}</div>
      <div className="fx-panel-body fx-settings-body">
        <p className="fx-export-hint">
          {t('settings.project_import_hint', 'Inspect .aive.yaml, .aive.yml, or compatible JSON projects before importing them into the active workspace.')}
        </p>
        <label htmlFor="project-import-path">{t('settings.project_import_path', 'Project file path')}</label>
        <input
          id="project-import-path"
          className="fx-input fx-input-mono"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="~/Desktop/case/project.aive.yaml"
        />
        <div className="fx-export-actions-row" style={{ marginTop: 8 }}>
          <button type="button" className="fx-btn" onClick={inspect} disabled={busy}>Inspect</button>
          <button type="button" className="fx-btn fx-btn-primary" onClick={importProject} disabled={busy || summary?.supported === false}>
            Import project
          </button>
        </div>
        {summary && (
          <div className="fx-compat-summary">
            <div><strong>Status:</strong> {summary.supported ? 'Compatible' : 'Not compatible'}</div>
            <div><strong>Format:</strong> {summary.format || 'unknown'}</div>
            <div><strong>Name:</strong> {summary.name || 'Imported'}</div>
            <div className="fx-compat-counts">
              {Object.entries(summary.counts || {}).map(([k, v]) => (
                <span key={k}>{k}: {v}</span>
              ))}
            </div>
            {(summary.warnings || []).map((w, i) => (
              <div key={i} className="fx-compat-warning">{w}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
