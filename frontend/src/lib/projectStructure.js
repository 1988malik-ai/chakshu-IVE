/** Canonical project folder layout — configurable in Settings. */

export const DEFAULT_PROJECT_ROOT = '~/Desktop/chakshu-export';

/** Folder keys, labels, and default relative paths under project root. */
export const PROJECT_FOLDER_DEFS = [
  { key: 'folder_evidence', label: 'Evidence (original media)', default: 'evidence' },
  { key: 'folder_examination', label: 'Examination (processed media)', default: 'examination' },
  { key: 'folder_bundles', label: 'Export bundles', default: 'exports/bundles' },
  { key: 'folder_pdf', label: 'PDF frame reports', default: 'reports/pdf' },
  { key: 'folder_reports', label: 'Case reports', default: 'reports' },
  { key: 'folder_video_iframes', label: 'Video I-frames', default: 'video/i-frames' },
  { key: 'folder_video_trim', label: 'Trimmed video segments', default: 'video/trim' },
  { key: 'folder_audio', label: 'Audio extracts', default: 'audio' },
  { key: 'folder_metadata', label: 'Metadata exports', default: 'metadata' },
  { key: 'folder_captures', label: 'Live captures', default: 'captures' },
  { key: 'folder_subtitles', label: 'Subtitled outputs', default: 'subtitles' },
];

export const DEFAULT_FOLDER_VALUES = Object.fromEntries(
  PROJECT_FOLDER_DEFS.map((d) => [d.key, d.default]),
);

export function normalizeDir(dir) {
  if (!dir || typeof dir !== 'string') return DEFAULT_PROJECT_ROOT;
  return dir.trim().replace(/\/+$/, '') || DEFAULT_PROJECT_ROOT;
}

export function joinProjectPath(root, ...segments) {
  const parts = [normalizeDir(root), ...segments]
    .filter(Boolean)
    .join('/')
    .replace(/\/+/g, '/');
  return parts;
}

/**
 * Resolve all export paths from project root + folder map.
 */
export function deriveProjectPaths(projectRoot, folderOverrides = {}) {
  const root = normalizeDir(projectRoot);
  const f = { ...DEFAULT_FOLDER_VALUES, ...folderOverrides };

  const evidenceDir = joinProjectPath(root, f.folder_evidence);
  const examinationDir = joinProjectPath(root, f.folder_examination);
  const bundlesDir = joinProjectPath(root, f.folder_bundles);
  const pdfDir = joinProjectPath(root, f.folder_pdf);
  const reportsDir = joinProjectPath(root, f.folder_reports);
  const iFramesDir = joinProjectPath(root, f.folder_video_iframes);
  const trimDir = joinProjectPath(root, f.folder_video_trim);
  const audioDir = joinProjectPath(root, f.folder_audio);
  const metadataDir = joinProjectPath(root, f.folder_metadata);
  const capturesDir = joinProjectPath(root, f.folder_captures);
  const subtitlesDir = joinProjectPath(root, f.folder_subtitles);

  return {
    project_root: root,
    output_dir: bundlesDir,
    evidence_dir: evidenceDir,
    examination_dir: examinationDir,
    bundles_dir: bundlesDir,
    pdf_path: joinProjectPath(pdfDir, 'frames.pdf'),
    pdf_dir: pdfDir,
    reports_dir: reportsDir,
    i_frames_dir: iFramesDir,
    trim_dir: trimDir,
    audio_out: joinProjectPath(audioDir, 'extract.aac'),
    audio_dir: audioDir,
    metadata_dir: metadataDir,
    metadata_path: joinProjectPath(metadataDir, 'metadata.json'),
    captures_dir: capturesDir,
    subtitles_dir: subtitlesDir,
    ...Object.fromEntries(PROJECT_FOLDER_DEFS.map((d) => [d.key, f[d.key]])),
  };
}

export function projectRootForCase(baseRoot, forensicCase) {
  const root = normalizeDir(baseRoot);
  const slug = forensicCase?.display_id || forensicCase?.case_number;
  if (!slug) return root;
  const safe = String(slug).replace(/[^\w.-]+/g, '_');
  return joinProjectPath(root, safe);
}

/** Tree preview for Settings UI */
export function projectStructureTree(projectRoot, folderOverrides = {}) {
  const paths = deriveProjectPaths(projectRoot, folderOverrides);
  const root = paths.project_root;
  const lines = [
    { path: root, label: 'Project root' },
    { path: paths.evidence_dir, label: 'Evidence' },
    { path: paths.examination_dir, label: 'Examination' },
    { path: paths.bundles_dir, label: 'Bundles' },
    { path: paths.pdf_dir, label: 'PDF reports' },
    { path: paths.reports_dir, label: 'Reports' },
    { path: paths.i_frames_dir, label: 'I-frames' },
    { path: paths.trim_dir, label: 'Trimmed video' },
    { path: paths.audio_dir, label: 'Audio' },
    { path: paths.metadata_dir, label: 'Metadata' },
    { path: paths.captures_dir, label: 'Captures' },
    { path: paths.subtitles_dir, label: 'Subtitles' },
  ];
  return lines.filter((l, i, arr) => arr.findIndex((x) => x.path === l.path) === i);
}

export function folderFieldsFromForm(form) {
  return Object.fromEntries(
    PROJECT_FOLDER_DEFS.map((d) => [d.key, form[d.key] ?? d.default]),
  );
}
