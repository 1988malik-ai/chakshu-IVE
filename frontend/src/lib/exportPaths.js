/** Export form defaults + persistence (paths derived from project structure). */

import {
  DEFAULT_FOLDER_VALUES,
  DEFAULT_PROJECT_ROOT,
  deriveProjectPaths,
  folderFieldsFromForm,
  projectRootForCase,
} from './projectStructure';

export const DEFAULT_EXPORT_DIR = DEFAULT_PROJECT_ROOT;

const _initialPaths = deriveProjectPaths(DEFAULT_PROJECT_ROOT, DEFAULT_FOLDER_VALUES);

export const DEFAULT_EXPORT_FORM = {
  input_path: '',
  project_root: DEFAULT_PROJECT_ROOT,
  use_project_structure: true,
  use_custom_paths: false,
  ...DEFAULT_FOLDER_VALUES,
  ..._initialPaths,
  pdf_page_size: 'A4',
  pdf_orientation: 'portrait',
  pdf_columns: 2,
  pdf_rows: 3,
  pdf_margin_mm: 12,
  pdf_title: '',
  include_original: true,
  include_processed: true,
  use_session_enhancement: true,
  video_codec: 'auto_gpu',
  audio_codec: 'aac',
  use_stream_copy: false,
  frame_rate_mode: 'cfr',
  export_fps: 29.97,
  prefer_h265: false,
  prefer_gpu: true,
  image_quality: 92,
  crf: 23,
  video_bitrate: '',
  encode_preset: 'medium',
};

const STORAGE_KEY = 'chakshu.exportForm';

export { deriveProjectPaths, projectRootForCase, normalizeDir } from './projectStructure';

/** @deprecated use deriveProjectPaths */
export function derivePathsFromOutputDir(outputDir) {
  return deriveProjectPaths(outputDir, DEFAULT_FOLDER_VALUES);
}

export function outputDirForCase(baseDir, forensicCase) {
  const root = projectRootForCase(baseDir, forensicCase);
  return deriveProjectPaths(root, DEFAULT_FOLDER_VALUES).reports_dir;
}

export function loadExportFormFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_EXPORT_FORM };
    const parsed = JSON.parse(raw);
    const merged = { ...DEFAULT_EXPORT_FORM, ...parsed };
    if (merged.use_project_structure !== false && !merged.use_custom_paths) {
      const root = merged.project_root || merged.output_dir || DEFAULT_PROJECT_ROOT;
      return {
        ...merged,
        ...deriveProjectPaths(root, folderFieldsFromForm(merged)),
      };
    }
    return merged;
  } catch {
    return { ...DEFAULT_EXPORT_FORM };
  }
}

export function saveExportFormToStorage(form) {
  try {
    const { input_path, ...persist } = form;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persist));
  } catch {
    /* private mode / quota */
  }
}

export function mergeExportSettings(form, exportSettings) {
  if (!exportSettings || typeof exportSettings !== 'object') return form;
  const next = { ...form, ...exportSettings };
  if (next.use_project_structure !== false && !next.use_custom_paths) {
    const root = next.project_root || next.output_dir || DEFAULT_PROJECT_ROOT;
    return { ...next, ...deriveProjectPaths(root, folderFieldsFromForm(next)) };
  }
  return next;
}

export function resolvedExportPaths(form) {
  if (form.use_custom_paths || form.use_project_structure === false) {
    return {
      project_root: form.project_root || form.output_dir,
      output_dir: form.output_dir,
      evidence_dir: form.evidence_dir || form.output_dir,
      examination_dir: form.examination_dir || form.output_dir,
      bundles_dir: form.bundles_dir || form.output_dir,
      pdf_path: form.pdf_path,
      i_frames_dir: form.i_frames_dir,
      audio_out: form.audio_out,
      metadata_path: form.metadata_path || `${form.output_dir}/metadata.json`,
      trim_dir: form.trim_dir || form.output_dir,
    };
  }
  const root = form.project_root || form.output_dir || DEFAULT_PROJECT_ROOT;
  return deriveProjectPaths(root, folderFieldsFromForm(form));
}
