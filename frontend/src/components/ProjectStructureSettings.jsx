import { useCallback, useMemo } from 'react';
import { api } from '../api/client';
import {
  DEFAULT_FOLDER_VALUES,
  DEFAULT_PROJECT_ROOT,
  PROJECT_FOLDER_DEFS,
  deriveProjectPaths,
  folderFieldsFromForm,
  normalizeDir,
  projectRootForCase,
  projectStructureTree,
} from '../lib/projectStructure';
import { saveExportFormToStorage } from '../lib/exportPaths';

export default function ProjectStructureSettings({
  exportForm,
  setExportForm,
  forensicCase,
  t = (k, d) => d,
  setStatus,
  setError,
}) {
  const projectRoot = exportForm.project_root || exportForm.output_dir || DEFAULT_PROJECT_ROOT;
  const useStructure = exportForm.use_project_structure !== false;

  const tree = useMemo(
    () => projectStructureTree(projectRoot, folderFieldsFromForm(exportForm)),
    [projectRoot, exportForm],
  );

  const patch = useCallback((key, value) => {
    setExportForm((f) => {
      const next = { ...f, [key]: value };
      if (next.use_project_structure !== false && (key === 'project_root' || key.startsWith('folder_'))) {
        Object.assign(next, deriveProjectPaths(next.project_root || next.output_dir, folderFieldsFromForm(next)));
      }
      saveExportFormToStorage(next);
      return next;
    });
  }, [setExportForm]);

  const applyStructure = useCallback((root, folders) => {
    setExportForm((f) => {
      const next = {
        ...f,
        project_root: root,
        use_project_structure: true,
        use_custom_paths: false,
        ...folders,
        ...deriveProjectPaths(root, folders),
      };
      saveExportFormToStorage(next);
      return next;
    });
  }, [setExportForm]);

  const saveToProject = useCallback(async () => {
    try {
      const payload = {
        project_root: projectRoot,
        use_project_structure: useStructure,
        use_custom_paths: false,
        ...folderFieldsFromForm(exportForm),
        ...deriveProjectPaths(projectRoot, folderFieldsFromForm(exportForm)),
      };
      const r = await api.projectExportSettings(payload);
      setStatus?.(t('settings.structure_saved', 'Project folder structure saved'));
      if (r.export_settings) {
        setExportForm((f) => ({ ...f, ...r.export_settings }));
      }
    } catch (e) {
      setError?.(e.message);
    }
  }, [exportForm, projectRoot, useStructure, setExportForm, setStatus, setError, t]);

  return (
    <div className="fx-panel fx-settings-panel fx-project-structure-panel">
      <div className="fx-panel-head">{t('settings.project_structure', 'Project folder structure')}</div>
      <div className="fx-panel-body fx-settings-body">
        <p className="fx-export-hint">
          {t(
            'settings.structure_hint',
            'Organize exports into named folders under a single project root. Legal Export and reports use these paths automatically.',
          )}
        </p>

        <label className="fx-a11y-row" style={{ marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={useStructure}
            onChange={(e) => patch('use_project_structure', e.target.checked)}
          />
          <span>{t('settings.use_structure', 'Use structured project folders')}</span>
        </label>

        <label htmlFor="proj-root">{t('settings.project_root', 'Project root directory')}</label>
        <input
          id="proj-root"
          className="fx-input fx-input-mono"
          value={projectRoot}
          disabled={!useStructure}
          onChange={(e) => {
            const root = normalizeDir(e.target.value);
            applyStructure(root, folderFieldsFromForm(exportForm));
          }}
          placeholder="~/Desktop/chakshu-export"
        />

        <div className="fx-export-actions-row" style={{ marginTop: 8 }}>
          <button
            type="button"
            className="fx-btn"
            disabled={!useStructure || (!forensicCase?.display_id && !forensicCase?.case_number)}
            onClick={() => {
              const base = normalizeDir(projectRoot).split('/').slice(0, -1).join('/') || '~/Desktop/chakshu-export';
              const caseRoot = projectRootForCase(base, forensicCase);
              applyStructure(caseRoot, folderFieldsFromForm(exportForm));
              setStatus?.(t('settings.case_root_set', 'Project root set for active case'));
            }}
          >
            {t('settings.case_subfolder', 'Use case subfolder')}
          </button>
          <button
            type="button"
            className="fx-btn"
            disabled={!useStructure}
            onClick={() => applyStructure(projectRoot, DEFAULT_FOLDER_VALUES)}
          >
            {t('settings.reset_folders', 'Reset folder names')}
          </button>
          <button type="button" className="fx-btn fx-btn-primary" onClick={saveToProject}>
            {t('settings.save_structure', 'Save to project')}
          </button>
        </div>

        <div className="fx-settings-section">
          <h3 className="fx-settings-section-title">{t('settings.folder_names', 'Folder names')}</h3>
          <div className="fx-project-folder-grid">
            {PROJECT_FOLDER_DEFS.map((def) => (
              <label key={def.key} className="fx-project-folder-field">
                <span>{t(`settings.folder.${def.key}`, def.label)}</span>
                <input
                  className="fx-input fx-input-mono"
                  value={exportForm[def.key] ?? def.default}
                  disabled={!useStructure}
                  onChange={(e) => patch(def.key, e.target.value.replace(/^\/+|\/+$/g, ''))}
                  placeholder={def.default}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="fx-settings-section">
          <h3 className="fx-settings-section-title">{t('settings.structure_preview', 'Layout preview')}</h3>
          <ul className="fx-project-tree">
            {tree.map((item) => (
              <li key={item.path}>
                <span className="fx-project-tree-label">{item.label}</span>
                <code>{item.path}</code>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
