/** Derive default export file paths from a base output directory. */

export const DEFAULT_EXPORT_DIR = '~/Desktop/chakshu-export';

export const DEFAULT_EXPORT_FORM = {
  input_path: '',
  output_dir: DEFAULT_EXPORT_DIR,
  pdf_path: `${DEFAULT_EXPORT_DIR}/frames.pdf`,
  i_frames_dir: `${DEFAULT_EXPORT_DIR}/i-frames`,
  audio_out: `${DEFAULT_EXPORT_DIR}/audio-extract.aac`,
  use_custom_paths: false,
  pdf_page_size: 'A4',
  pdf_orientation: 'portrait',
  pdf_columns: 2,
  pdf_rows: 3,
  pdf_margin_mm: 12,
  pdf_title: '',
};

const STORAGE_KEY = 'chakshu.exportForm';

export function normalizeDir(dir) {
  if (!dir || typeof dir !== 'string') return DEFAULT_EXPORT_DIR;
  return dir.trim().replace(/\/+$/, '') || DEFAULT_EXPORT_DIR;
}

export function derivePathsFromOutputDir(outputDir) {
  const base = normalizeDir(outputDir);
  return {
    output_dir: base,
    pdf_path: `${base}/frames.pdf`,
    i_frames_dir: `${base}/i-frames`,
    audio_out: `${base}/audio-extract.aac`,
  };
}

export function outputDirForCase(baseDir, forensicCase) {
  const base = normalizeDir(baseDir);
  const slug = forensicCase?.display_id || forensicCase?.case_number;
  if (!slug) return base;
  const safe = String(slug).replace(/[^\w.-]+/g, '_');
  return `${base}/${safe}`;
}

export function loadExportFormFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_EXPORT_FORM };
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_EXPORT_FORM, ...parsed };
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
  if (!next.use_custom_paths && next.output_dir) {
    return { ...next, ...derivePathsFromOutputDir(next.output_dir) };
  }
  return next;
}
