import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewDataUrl } from './api/client';
import Layout from './components/Layout';
import AudioPlayer from './components/AudioPlayer';

const TITLES = {
  dashboard: 'Dashboard',
  studio: 'Media Studio',
  export: 'Export Center',
  reports: 'Report Generator',
  projects: 'Project Management',
};

const IMPLEMENTED_FILTERS = new Set([
  'clr_grayscale',
  'clr_invert',
  'clr_brightness',
  'clr_contrast',
  'clr_saturation',
  'blr_gaussian',
  'both_blur',
  'shp_unsharp',
  'both_sharpen',
  'ns_denoise',
  'both_denoise',
  'sty_vignette',
  'both_vignette',
  'geo_rotate',
  'utl_clahe',
]);

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [sessionId, setSessionId] = useState(null);
  const [filters, setFilters] = useState([]);
  const [filterSearch, setFilterSearch] = useState('');
  const [preview, setPreview] = useState(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [status, setStatus] = useState('Connecting…');
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [ready, setReady] = useState(false);
  const [license, setLicense] = useState(null);
  const [project, setProject] = useState(null);
  const [mediaPath, setMediaPath] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [reportMeta, setReportMeta] = useState(null);
  const fileRef = useRef(null);
  const [selectedFilter, setSelectedFilter] = useState(null);

  const [exportForm, setExportForm] = useState({
    output_dir: '~/Desktop/AI-IVE-exports',
    input_path: '',
    pdf_path: '~/Desktop/frames.pdf',
    page_size: 'A4',
    orientation: 'portrait',
    columns: 2,
    rows: 3,
    audio_out: '~/Desktop/audio.aac',
    i_frames_dir: '~/Desktop/i-frames',
    include_original: true,
    include_processed: true,
    video_codec: 'libx264',
    use_stream_copy: false,
  });

  const [reportForm, setReportForm] = useState({
    output_dir: '~/Desktop/AI-IVE-reports',
    paper_size: 'A4',
    orientation: 'portrait',
    template: 'standard',
    title: 'AI-IVE Processing Report',
    author: '',
    formats: ['html', 'pdf'],
  });

  const init = useCallback(async () => {
    try {
      const { session_id } = await api.createSession();
      setSessionId(session_id);
      setReady(true);
      const [flt, lic, proj, tpl] = await Promise.all([
        api.fetchFilters().catch(() => ({ filters: [], count: 0 })),
        api.licenseStatus().catch(() => null),
        api.projectCurrent().catch(() => null),
        api.reportTemplates().catch(() => null),
      ]);
      setFilters(flt.filters || []);
      setLicense(lic);
      setProject(proj);
      setReportMeta(tpl);
      setStatus(`Connected · ${flt.count || 0} filters · Project: ${proj?.name || 'Default'}`);
    } catch (e) {
      setReady(false);
      setError(e.message);
      setStatus('Start API: python -m aive.api.server');
    }
  }, []);

  useEffect(() => { init(); }, [init]);

  const filteredList = useMemo(() => {
    const q = filterSearch.toLowerCase();
    if (!q) return filters;
    return filters.filter((f) =>
      f.name.toLowerCase().includes(q) || f.category.includes(q)
    );
  }, [filters, filterSearch]);

  const handlePreview = (data) => {
    if (data.preview) setPreview(previewDataUrl(data.preview));
    setCanUndo(!!data.can_undo);
    setCanRedo(!!data.can_redo);
  };

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setMsg('');
    const local = URL.createObjectURL(file);
    setPreview(local);
    try {
      let sid = sessionId;
      if (!sid) {
        const s = await api.createSession();
        sid = s.session_id;
        setSessionId(sid);
      }
      const data = await api.uploadMedia(sid, file);
      URL.revokeObjectURL(local);
      handlePreview(data);
      setMediaPath(file.name);
      setExportForm((f) => ({ ...f, input_path: file.name }));
      setStatus(`Loaded ${file.name}`);
      setMsg('Media loaded successfully');
    } catch (err) {
      setError(err.message);
    }
    e.target.value = '';
  };

  const onFilter = async (id) => {
    if (!sessionId || !preview) return setError('Load media first');
    try {
      setStatus(`Applying filter: ${id}…`);
      handlePreview(await api.applyFilter(sessionId, id));
      setProject(await api.projectCurrent());
      setMsg(`Applied filter: ${id}`);
      setStatus(`Applied filter: ${id}`);
    } catch (e) {
      setError(e.message);
    }
  };

  const applySelectedFilter = async () => {
    if (!selectedFilter) return setError('Select a filter first');
    return onFilter(selectedFilter.id);
  };

  const runExport = async (fn) => {
    setError('');
    setMsg('');
    try {
      const r = await fn();
      setMsg(r.success !== false ? `Export OK: ${JSON.stringify(r).slice(0, 120)}…` : r.error);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <Layout page={page} setPage={setPage} title={TITLES[page]} status={status} error={error} ready={ready}>
      {page === 'dashboard' && (
        <>
          <div className="erp-grid">
            <div className="erp-card">
              <div className="erp-stat">{filters.length}</div>
              <div className="erp-stat-label">Processing Filters</div>
            </div>
            <div className="erp-card">
              <div className="erp-stat">{project?.workflow_steps?.length || 0}</div>
              <div className="erp-stat-label">Workflow Steps</div>
            </div>
            <div className="erp-card">
              <div className="erp-stat">{license?.valid ? 'Active' : 'Trial'}</div>
              <div className="erp-stat-label">License Status</div>
            </div>
            <div className="erp-card">
              <div className="erp-stat">{ready ? 'Online' : 'Offline'}</div>
              <div className="erp-stat-label">API Status</div>
            </div>
          </div>
          <div className="erp-card">
            <h3>Quick Actions</h3>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button type="button" className="erp-btn erp-btn-primary" onClick={() => fileRef.current?.click()}>
                Open Media
              </button>
              <button type="button" className="erp-btn erp-btn-secondary" onClick={() => setPage('studio')}>
                Media Studio
              </button>
              <button type="button" className="erp-btn erp-btn-secondary" onClick={() => setPage('export')}>
                Export Center
              </button>
              <button type="button" className="erp-btn erp-btn-secondary" onClick={() => setPage('reports')}>
                Generate Report
              </button>
            </div>
            {msg && <p className="erp-success-msg">{msg}</p>}
          </div>
        </>
      )}

      {page === 'studio' && (
        <div className="erp-layout-2">
          <div>
            <div className="erp-card" style={{ marginBottom: 16 }}>
              <h3>Filters</h3>
              <input
                placeholder="Search filters…"
                value={filterSearch}
                onChange={(e) => setFilterSearch(e.target.value)}
                style={{ width: '100%', marginBottom: 12, padding: 8, borderRadius: 8, border: '1px solid var(--erp-border)' }}
              />
              <div style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center' }}>
                <button type="button" className="erp-btn erp-btn-primary" onClick={applySelectedFilter} disabled={!selectedFilter}>
                  Apply
                </button>
                <button type="button" className="erp-btn erp-btn-secondary" onClick={() => setSelectedFilter(null)} disabled={!selectedFilter}>
                  Clear
                </button>
                <div style={{ color: 'var(--erp-muted)', fontSize: '0.8rem' }}>
                  {selectedFilter
                    ? `Selected: ${selectedFilter.name}${IMPLEMENTED_FILTERS.has(selectedFilter.id) ? ' (implemented)' : ' (may be placeholder)'}`
                    : 'Tip: click a filter to select, then Apply. Try: Invert / Grayscale / Gaussian Blur'}
                </div>
              </div>
              {msg && <div className="erp-success-msg" style={{ marginBottom: 10 }}>{msg}</div>}
              <div className="erp-filter-list">
                {filteredList.slice(0, 80).map((f) => (
                  <div
                    key={f.id}
                    className="erp-filter-item"
                    onClick={() => setSelectedFilter(f)}
                    onDoubleClick={() => onFilter(f.id)}
                    style={{
                      background: selectedFilter?.id === f.id ? '#dbeafe' : undefined,
                      borderLeft: selectedFilter?.id === f.id ? '3px solid var(--erp-primary)' : '3px solid transparent',
                    }}
                    title="Click to select. Double-click to apply."
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        setSelectedFilter(f);
                      }
                      if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
                        onFilter(f.id);
                      }
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                      <span>{f.name}</span>
                      {IMPLEMENTED_FILTERS.has(f.id) ? (
                        <span style={{ fontSize: '0.7rem', color: 'var(--erp-success)', fontWeight: 700 }}>LIVE</span>
                      ) : (
                        <span style={{ fontSize: '0.7rem', color: 'var(--erp-muted)' }}>CATALOG</span>
                      )}
                    </div>
                    <div className="cat">{f.category}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="erp-card">
              <h3>Edit</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" className="erp-btn erp-btn-secondary" disabled={!canUndo} onClick={() => api.undo(sessionId).then(handlePreview)}>Undo</button>
                <button type="button" className="erp-btn erp-btn-secondary" disabled={!canRedo} onClick={() => api.redo(sessionId).then(handlePreview)}>Redo</button>
                <button type="button" className="erp-btn erp-btn-primary" onClick={() => fileRef.current?.click()}>Open</button>
              </div>
            </div>
          </div>
          <div>
            <div className="erp-preview-panel">
              {preview ? <img src={preview} alt="Preview" /> : <span style={{ color: '#64748b' }}>No media loaded</span>}
            </div>
            <div className="erp-card" style={{ marginTop: 16 }}>
              <h3>Audio Playback</h3>
              <AudioPlayer src={audioUrl} />
              <p style={{ fontSize: '0.8rem', color: 'var(--erp-muted)', marginTop: 8 }}>
                Extract audio in Export Center, then set URL to local file path via file:// or serve extracted file
              </p>
            </div>
          </div>
        </div>
      )}

      {page === 'export' && (
        <div className="erp-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <div className="erp-card">
            <h3>PDF Frame Export</h3>
            <div className="erp-form-row"><label>Output path</label>
              <input value={exportForm.pdf_path} onChange={(e) => setExportForm({ ...exportForm, pdf_path: e.target.value })} /></div>
            <div className="erp-form-row"><label>Page size</label>
              <select value={exportForm.page_size} onChange={(e) => setExportForm({ ...exportForm, page_size: e.target.value })}>
                <option>A4</option><option>Letter</option><option>Legal</option><option>A3</option>
              </select></div>
            <div className="erp-form-row"><label>Orientation</label>
              <select value={exportForm.orientation} onChange={(e) => setExportForm({ ...exportForm, orientation: e.target.value })}>
                <option>portrait</option><option>landscape</option>
              </select></div>
            <div className="erp-form-row"><label>Grid (cols × rows)</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="number" min={1} max={6} value={exportForm.columns} onChange={(e) => setExportForm({ ...exportForm, columns: +e.target.value })} />
                <input type="number" min={1} max={6} value={exportForm.rows} onChange={(e) => setExportForm({ ...exportForm, rows: +e.target.value })} />
              </div></div>
            <button type="button" className="erp-btn erp-btn-primary" onClick={() => runExport(() => api.exportPdfFrames({
              session_id: sessionId, output_path: exportForm.pdf_path,
              page_size: exportForm.page_size, orientation: exportForm.orientation,
              columns: exportForm.columns, rows: exportForm.rows,
            }))}>Export to PDF</button>
          </div>

          <div className="erp-card">
            <h3>Media Bundle (Original + Processed)</h3>
            <div className="erp-form-row"><label>Input path</label>
              <input value={exportForm.input_path} onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })} placeholder="/full/path/to/video.mp4" /></div>
            <div className="erp-form-row"><label>Output directory</label>
              <input value={exportForm.output_dir} onChange={(e) => setExportForm({ ...exportForm, output_dir: e.target.value })} /></div>
            <div className="erp-form-row"><label>Video codec</label>
              <select value={exportForm.video_codec} onChange={(e) => setExportForm({ ...exportForm, video_codec: e.target.value })}>
                <option>libx264</option><option>libx265</option><option>copy</option>
              </select></div>
            <label><input type="checkbox" checked={exportForm.include_original} onChange={(e) => setExportForm({ ...exportForm, include_original: e.target.checked })} /> Original</label>
            <label style={{ marginLeft: 12 }}><input type="checkbox" checked={exportForm.include_processed} onChange={(e) => setExportForm({ ...exportForm, include_processed: e.target.checked })} /> Processed</label>
            <br /><br />
            <button type="button" className="erp-btn erp-btn-primary" onClick={() => runExport(() => api.exportMediaBundle({
              input_path: exportForm.input_path, output_dir: exportForm.output_dir,
              include_original: exportForm.include_original, include_processed: exportForm.include_processed,
              video_codec: exportForm.video_codec, use_stream_copy: exportForm.use_stream_copy,
            }))}>Export Bundle</button>
          </div>

          <div className="erp-card">
            <h3>Audio Extraction</h3>
            <div className="erp-form-row"><label>Input video</label>
              <input value={exportForm.input_path} onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })} /></div>
            <div className="erp-form-row"><label>Output audio</label>
              <input value={exportForm.audio_out} onChange={(e) => setExportForm({ ...exportForm, audio_out: e.target.value })} /></div>
            <button type="button" className="erp-btn erp-btn-primary" onClick={() => runExport(async () => {
              const r = await api.extractAudio({ input_path: exportForm.input_path, output_path: exportForm.audio_out, codec: 'copy' });
              if (r.success) setAudioUrl(exportForm.audio_out);
              return r;
            })}>Extract Audio</button>
          </div>

          <div className="erp-card">
            <h3>I-Frame Export (Intra-coded)</h3>
            <div className="erp-form-row"><label>Input video</label>
              <input value={exportForm.input_path} onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })} /></div>
            <div className="erp-form-row"><label>Output folder</label>
              <input value={exportForm.i_frames_dir} onChange={(e) => setExportForm({ ...exportForm, i_frames_dir: e.target.value })} /></div>
            <button type="button" className="erp-btn erp-btn-primary" onClick={() => runExport(() => api.exportIFrames({
              input_path: exportForm.input_path, output_dir: exportForm.i_frames_dir,
            }))}>Export I-Frames</button>
          </div>
          {msg && <p className="erp-success-msg" style={{ gridColumn: '1 / -1' }}>{msg}</p>}
        </div>
      )}

      {page === 'reports' && (
        <div className="erp-card" style={{ maxWidth: 640 }}>
          <h3>Automated Report Generation</h3>
          <div className="erp-form-row"><label>Title</label>
            <input value={reportForm.title} onChange={(e) => setReportForm({ ...reportForm, title: e.target.value })} /></div>
          <div className="erp-form-row"><label>Author</label>
            <input value={reportForm.author} onChange={(e) => setReportForm({ ...reportForm, author: e.target.value })} /></div>
          <div className="erp-form-row"><label>Paper size</label>
            <select value={reportForm.paper_size} onChange={(e) => setReportForm({ ...reportForm, paper_size: e.target.value })}>
              {(reportMeta?.paper_sizes || ['A4', 'Letter', 'Legal', 'A3']).map((s) => <option key={s}>{s}</option>)}
            </select></div>
          <div className="erp-form-row"><label>Template</label>
            <select value={reportForm.template} onChange={(e) => setReportForm({ ...reportForm, template: e.target.value })}>
              {(reportMeta?.templates || ['standard']).map((t) => <option key={t}>{t}</option>)}
            </select></div>
          <div className="erp-form-row"><label>Output directory</label>
            <input value={reportForm.output_dir} onChange={(e) => setReportForm({ ...reportForm, output_dir: e.target.value })} /></div>
          <div className="erp-form-row"><label>Formats</label>
            <label><input type="checkbox" checked={reportForm.formats.includes('html')} onChange={(e) => setReportForm({ ...reportForm, formats: e.target.checked ? [...reportForm.formats, 'html'] : reportForm.formats.filter((x) => x !== 'html') })} /> HTML</label>
            <label style={{ marginLeft: 12 }}><input type="checkbox" checked={reportForm.formats.includes('pdf')} onChange={(e) => setReportForm({ ...reportForm, formats: e.target.checked ? [...reportForm.formats, 'pdf'] : reportForm.formats.filter((x) => x !== 'pdf') })} /> PDF</label>
            <label style={{ marginLeft: 12 }}><input type="checkbox" checked={reportForm.formats.includes('docx')} onChange={(e) => setReportForm({ ...reportForm, formats: e.target.checked ? [...reportForm.formats, 'docx'] : reportForm.formats.filter((x) => x !== 'docx') })} /> DOCX</label>
          </div>
          <button type="button" className="erp-btn erp-btn-primary" onClick={() => runExport(() => api.generateReport({
            ...reportForm, output_dir: reportForm.output_dir,
          }))}>Generate Report</button>
          {msg && <p className="erp-success-msg">{msg}</p>}
        </div>
      )}

      {page === 'projects' && (
        <>
          <div className="erp-card" style={{ marginBottom: 20 }}>
            <h3>Project (Human-readable YAML)</h3>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              <button type="button" className="erp-btn erp-btn-primary" onClick={async () => {
                const n = prompt('Project name:', 'My Workflow');
                if (n) { await api.projectNew(n); setProject(await api.projectCurrent()); setMsg('Project created'); }
              }}>New Project</button>
              <button type="button" className="erp-btn erp-btn-secondary" onClick={async () => {
                const p = prompt('Save path (optional):', '~/Desktop/my-project.aive.yaml');
                if (p !== null) { await api.projectSave(project?.name || 'Project', p || undefined); setMsg('Project saved'); }
              }}>Save Project</button>
              <button type="button" className="erp-btn erp-btn-secondary" onClick={async () => {
                const p = prompt('Import path:', '~/Desktop/project.aive.yaml');
                if (p) { await api.projectImport(p); setProject(await api.projectCurrent()); setMsg('Imported'); }
              }}>Import Compatible</button>
            </div>
            <p><strong>ID:</strong> {project?.project_id}</p>
            <p><strong>Name:</strong> {project?.name}</p>
          </div>
          <div className="erp-card">
            <h3>Workflow Steps</h3>
            <table className="erp-table">
              <thead><tr><th>#</th><th>Time</th><th>Action</th><th>Settings</th></tr></thead>
              <tbody>
                {(project?.workflow_steps || []).map((s, i) => (
                  <tr key={i}><td>{i + 1}</td><td>{s.timestamp}</td><td>{s.action}</td><td><code>{JSON.stringify(s.settings).slice(0, 60)}</code></td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <input ref={fileRef} type="file" accept="image/*,video/*" style={{ display: 'none' }} onChange={onUpload} />
    </Layout>
  );
}
