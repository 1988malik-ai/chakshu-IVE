import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewDataUrl } from './api/client';
import AudioPlayer from './components/AudioPlayer';
import ForensicTimeline, { formatTc } from './components/ForensicTimeline';
import ExamCanvas from './components/ExamCanvas';
import LiveCapture from './components/LiveCapture';
import LocaleSettings from './components/LocaleSettings';
import ProjectStructureSettings from './components/ProjectStructureSettings';
import ExamCompareDock from './components/ExamCompareDock';
import ProjectNotesPanel from './components/ProjectNotesPanel';
import LegalExportPanel from './components/LegalExportPanel';
import ForensicVideoTransport from './components/ForensicVideoTransport';
import AudioRedactionPanel from './components/AudioRedactionPanel';
import AudioStreamPanel from './components/AudioStreamPanel';
import SubtitlePanel from './components/SubtitlePanel';
import BookmarksPanel from './components/BookmarksPanel';
import CaseReportsPanel from './components/CaseReportsPanel';
import SidebarFooter from './components/SidebarFooter';
import { useForensicPlayback } from './hooks/useForensicPlayback';
import CompareFrameView from './components/CompareFrameView';
import { useLocale } from './i18n/LocaleContext';
import BrandMark from './components/BrandMark';
import {
  derivePathsFromOutputDir,
  loadExportFormFromStorage,
  mergeExportSettings,
  outputDirForCase,
  saveExportFormToStorage,
} from './lib/exportPaths';
import { formatApiError, toastDuration } from './lib/notify';
import { filtersForMediaType, filterScopeSummary, mediaContext, examinationToolGroups } from './lib/mediaContext';
import MediaTypeGate, { MediaTypeEmpty } from './components/MediaTypeGate';
import GridOverlayPanel from './components/GridOverlayPanel';
import TimestampEditorPanel from './components/TimestampEditorPanel';
import PerspectiveCorrectionPanel from './components/PerspectiveCorrectionPanel';
import PanoramaConversionPanel from './components/PanoramaConversionPanel';
import VideoOverlayComparePanel from './components/VideoOverlayComparePanel';
import TrackingStabilizePanel from './components/TrackingStabilizePanel';
import RegionAnalysisPanel from './components/RegionAnalysisPanel';
import TimelineProPage from './components/TimelineProPage';
import {
  loadGridOverlaySettings,
  overlayBurnPayload,
  saveGridOverlaySettings,
} from './lib/gridOverlay';
import {
  loadTimestampSettings,
  resolveTimestampText,
  saveTimestampSettings,
} from './lib/timestampEdit';

const NAV_KEYS = [
  { id: 'command', key: 'nav.command', icon: '◈' },
  { id: 'examine', key: 'nav.examine', icon: '◎' },
  { id: 'capture', key: 'nav.capture', icon: '▣' },
  { id: 'markup', key: 'nav.markup', icon: '✎' },
  { id: 'timeline', key: 'nav.timeline', icon: '▤' },
  { id: 'tools', key: 'nav.tools', icon: '⫶' },
  { id: 'custody', key: 'nav.custody', icon: '⊞' },
  { id: 'export', key: 'nav.export', icon: '⇪' },
  { id: 'reports', key: 'nav.reports', icon: '≡' },
];

const MEASUREMENT_UNITS = [
  { value: 'px', label: 'Pixels (px)' },
  { value: 'mm', label: 'Millimeters (mm)' },
  { value: 'cm', label: 'Centimeters (cm)' },
  { value: 'm', label: 'Meters (m)' },
  { value: 'in', label: 'Inches (in)' },
  { value: 'ft', label: 'Feet (ft)' },
];

export default function ForensicApp() {
  const { t, locale } = useLocale();
  const [page, setPage] = useState('examine');
  const [sessionId, setSessionId] = useState(null);
  const [filters, setFilters] = useState([]);
  const [filterSearch, setFilterSearch] = useState('');
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewOriginal, setPreviewOriginal] = useState(null);
  const [filterChain, setFilterChain] = useState([]);
  const [forensicCase, setForensicCase] = useState(null);
  const [custody, setCustody] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [evidenceId, setEvidenceId] = useState(null);
  const [evidenceHash, setEvidenceHash] = useState('');
  const [allHashes, setAllHashes] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [notes, setNotes] = useState([]);
  const [projectMeta, setProjectMeta] = useState({ project_id: null, name: 'Examination' });
  const [caseDraft, setCaseDraft] = useState('');
  const [caseSubmitting, setCaseSubmitting] = useState(false);
  const [notesCollapsed, setNotesCollapsed] = useState(
    () => {
      const stored = localStorage.getItem('chakshu.notesCollapsed');
      if (stored != null) return stored === '1';
      return typeof window !== 'undefined' && window.innerWidth <= 1180;
    },
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => {
      const stored = localStorage.getItem('chakshu.sidebarCollapsed');
      if (stored != null) return stored === '1';
      return true;
    },
  );
  const [pipelineCollapsed, setPipelineCollapsed] = useState(
    () => localStorage.getItem('chakshu.pipelineCollapsed') === '1',
  );
  const [compareId, setCompareId] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [toasts, setToasts] = useState([]);
  const [blockingOverlay, setBlockingOverlay] = useState(null);
  const [mediaPath, setMediaPath] = useState('');
  const [storagePath, setStoragePath] = useState('');
  const [mediaType, setMediaType] = useState('image');
  const [videoMeta, setVideoMeta] = useState(null);
  const [seekTime, setSeekTime] = useState(0);
  const [timeline, setTimeline] = useState(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [currentFrameMeta, setCurrentFrameMeta] = useState(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [audioChannels, setAudioChannels] = useState(null);
  const [regionStart, setRegionStart] = useState(0);
  const [regionEnd, setRegionEnd] = useState(10);
  const [regionAnalysis, setRegionAnalysis] = useState(null);
  const [calibration, setCalibration] = useState({
    pixelsPerUnit: 1,
    unitName: 'px',
    pointUncertaintyPx: 0.5,
    calibrationUncertaintyPercent: 0,
    perspectiveUncertaintyPercent: 0,
    deltaTime: null,
  });
  const [examples, setExamples] = useState([]);
  const [selectedExample, setSelectedExample] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [subtitleForm, setSubtitleForm] = useState({
    subtitle_path: '',
    output_path: '~/Desktop/chakshu-subtitled.mp4',
    font_size: 22,
    margin_v: 28,
  });
  const [aiStatus, setAiStatus] = useState(null);
  const [aiTools, setAiTools] = useState([]);
  const [aiModels, setAiModels] = useState([]);
  const [aiTool, setAiTool] = useState('auto_enhance');
  const [aiModelId, setAiModelId] = useState('');
  const [aiStrength, setAiStrength] = useState(1.0);
  const [labFlash, setLabFlash] = useState('');
  const [filterApplying, setFilterApplying] = useState(false);
  const [autoOpenLab, setAutoOpenLab] = useState(
    () => localStorage.getItem('chakshu.autoOpenLab') !== '0',
  );
  const [showOriginalPreview, setShowOriginalPreview] = useState(
    () => localStorage.getItem('chakshu.showOriginalPreview') === '1',
  );
  const [gridOverlay, setGridOverlay] = useState(loadGridOverlaySettings);
  const [gridBurning, setGridBurning] = useState(false);
  const [timestampSettings, setTimestampSettings] = useState(loadTimestampSettings);
  const [timestampBurning, setTimestampBurning] = useState(false);
  const aiModelFileRef = useRef(null);
  const fileRef = useRef(null);
  const videoRef = useRef(null);
  const seekTimeRef = useRef(0);

  const [exportForm, setExportForm] = useState(loadExportFormFromStorage);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const notify = useCallback((message, type = 'success') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev.slice(-4), { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, toastDuration(type));
  }, []);

  const reportError = useCallback((err, context) => {
    const message = formatApiError(typeof err === 'string' ? { message: err } : err);
    const full = context ? `${context}: ${message}` : message;
    setError(message);
    notify(full, 'error');
  }, [notify]);

  useEffect(() => {
    const activeLabel = forensicCase?.display_id || forensicCase?.case_number || forensicCase?.case_id || '';
    setCaseDraft(activeLabel);
  }, [forensicCase?.case_id, forensicCase?.case_number, forensicCase?.display_id]);

  const reportSuccess = useCallback((message) => {
    setError('');
    setStatus(message);
    notify(message, 'success');
  }, [notify]);

  const setBlocking = useCallback((active, opts = {}) => {
    if (!active) {
      setBlockingOverlay(null);
      return;
    }
    setBlockingOverlay({
      message: opts.message || t('subtitle.burning', 'Processing…'),
      detail: opts.detail || '',
      wait: opts.wait || t('subtitle.burning_wait', 'Please wait until the file is saved.'),
    });
  }, [t]);

  const refreshProjectNotes = useCallback(async () => {
    try {
      const r = await api.projectNotes();
      setNotes(r.notes || []);
      setProjectMeta({ project_id: r.project_id, name: r.project_name || 'Examination' });
    } catch {
      /* API may be offline */
    }
  }, []);

  const init = useCallback(async () => {
    const attempt = async (retriesLeft) => {
      try {
        const { session_id } = await api.createSession();
        setSessionId(session_id);
        const [flt, fc, proj] = await Promise.all([
          api.fetchFilters(),
          api.forensicsActiveCase(),
          api.projectCurrent(),
        ]);
        setFilters(flt.filters || []);
        setForensicCase(fc);
        if (proj?.export_settings) {
          setExportForm((f) => mergeExportSettings(f, proj.export_settings));
        }
        await refreshProjectNotes();
        setStatus(`${fc.display_id || fc.case_number} · ${flt.implemented_count || 0} forensic filters ready`);
      } catch (e) {
        if (retriesLeft > 0 && /Failed to fetch|NetworkError|Load failed/i.test(e?.message || '')) {
          await new Promise((r) => setTimeout(r, 800));
          return attempt(retriesLeft - 1);
        }
        reportError(e, 'Startup failed');
        setStatus(t('status.api_offline', 'API offline — start Chakshu or Run-Chakshu.bat'));
      }
    };
    await attempt(4);
  }, [t, refreshProjectNotes, reportError]);

  useEffect(() => { init(); }, [init]);

  useEffect(() => {
    saveExportFormToStorage(exportForm);
  }, [exportForm]);

  useEffect(() => {
    if (!labFlash) return undefined;
    const t = setTimeout(() => setLabFlash(''), 5000);
    return () => clearTimeout(t);
  }, [labFlash]);

  useEffect(() => {
    if (page !== 'examine' || !sessionId) return;
    api.forensicsPreview(sessionId)
      .then(handlePreview)
      .catch((e) => {
        if (!/No frame loaded/i.test(e?.message || '')) {
          reportError(e, 'Could not refresh examination preview');
        }
      });
  }, [page, sessionId, reportError]);

  useEffect(() => {
    if (!status) setStatus(t('status.init', 'Initializing forensic services…'));
  }, [t, status]);

  useEffect(() => {
    const collapseSidePanels = () => {
      if (window.innerWidth > 1180) return;
      setNotesCollapsed(true);
      localStorage.setItem('chakshu.notesCollapsed', '1');
      if (window.innerWidth <= 960) {
        setSidebarCollapsed(true);
        localStorage.setItem('chakshu.sidebarCollapsed', '1');
      }
    };

    collapseSidePanels();
    window.addEventListener('resize', collapseSidePanels);
    return () => window.removeEventListener('resize', collapseSidePanels);
  }, []);

  const { hasEvidence, isVideo, isImage } = useMemo(
    () => mediaContext({ preview, previewOriginal, storagePath, mediaType }),
    [preview, previewOriginal, storagePath, mediaType],
  );

  const toolGroups = useMemo(
    () => examinationToolGroups({ preview, previewOriginal, storagePath, mediaType }),
    [preview, previewOriginal, storagePath, mediaType],
  );

  useEffect(() => {
    if (!hasEvidence || !selectedFilter) return;
    const allowed = filtersForMediaType(filters, mediaType, true);
    if (!allowed.some((f) => f.id === selectedFilter.id)) {
      setSelectedFilter(null);
    }
  }, [mediaType, hasEvidence, filters, selectedFilter]);

  const forensicFilters = useMemo(() => {
    const q = filterSearch.toLowerCase();
    let list = filtersForMediaType(filters, mediaType, hasEvidence);
    if (!q) return list;
    return list.filter((f) => f.name.toLowerCase().includes(q) || f.id.includes(q));
  }, [filters, filterSearch, mediaType, hasEvidence]);

  const filterScope = useMemo(
    () => filterScopeSummary(filters, mediaType, hasEvidence),
    [filters, mediaType, hasEvidence],
  );

  const filterDomainLabel = (domain) => {
    if (domain === 'video') return 'VID';
    if (domain === 'both') return 'BOTH';
    return 'IMG';
  };

  const filterLabel = useCallback(
    (id) => filters.find((f) => f.id === id)?.name || id,
    [filters],
  );

  const caseLabel = forensicCase?.display_id || forensicCase?.case_number || forensicCase?.case_id || '—';

  const handlePreview = (data) => {
    if (data.preview) setPreview(previewDataUrl(data.preview));
    if (data.preview_original) {
      setPreviewOriginal(previewDataUrl(data.preview_original));
    } else if (data.preview && !data.is_enhanced && !(data.filter_chain?.length)) {
      setPreviewOriginal(previewDataUrl(data.preview));
    }
    if (data.filter_chain) setFilterChain(data.filter_chain);
    else if (data.is_enhanced === false) setFilterChain([]);
  };

  const handleCaseSubmit = useCallback(async (event) => {
    event.preventDefault();
    const nextCaseId = caseDraft.trim();
    if (!nextCaseId) {
      reportError('Enter a case ID before starting a case.', 'Case');
      return;
    }
    if (nextCaseId === caseLabel) {
      setStatus(`Active case: ${nextCaseId}`);
      return;
    }
    setCaseSubmitting(true);
    try {
      const created = await api.forensicsCreateCase({
        case_number: nextCaseId,
        title: forensicCase?.title || 'New Examination',
        examiner: forensicCase?.examiner || 'Examiner',
        agency: forensicCase?.agency || '',
      });
      setForensicCase(created);
      setCustody([]);
      reportSuccess(`Active case set: ${created.display_id || created.case_number || nextCaseId}`);
    } catch (e) {
      reportError(e, 'Case setup failed');
    } finally {
      setCaseSubmitting(false);
    }
  }, [caseDraft, caseLabel, forensicCase, reportError, reportSuccess]);

  const updateGridOverlay = useCallback((patch) => {
    setGridOverlay((prev) => {
      const next = { ...prev, ...patch };
      saveGridOverlaySettings(next);
      return next;
    });
  }, []);

  const updateTimestampSettings = useCallback((next) => {
    setTimestampSettings(next);
    saveTimestampSettings(next);
  }, []);

  const timestampContext = useMemo(() => ({
    seekTime,
    fps: timeline?.fps || videoMeta?.fps || videoInfo?.fps || 30,
    frameIndex,
    mediaType,
  }), [seekTime, timeline?.fps, videoMeta?.fps, videoInfo?.fps, frameIndex, mediaType]);

  const handleRegionChange = useCallback((patch) => {
    if (patch.regionStart != null) setRegionStart(patch.regionStart);
    if (patch.regionEnd != null) setRegionEnd(patch.regionEnd);
    setRegionAnalysis(null);
  }, []);

  const applyToSession = useCallback((data, message, options = {}) => {
    const shouldOpen = options.openLab !== undefined ? options.openLab : autoOpenLab;
    if (data?.preview) handlePreview(data);
    if (data?.filter_chain) setFilterChain(data.filter_chain);
    if (message) {
      setLabFlash(message);
      setStatus(message);
    }
    if (shouldOpen && page !== 'examine') {
      setPage('examine');
    }
  }, [autoOpenLab, page]);

  const burnGridOverlay = useCallback(async () => {
    if (!sessionId) return;
    setGridBurning(true);
    try {
      let timestampText = '';
      if (gridOverlay.burnTimestamp) {
        timestampText = resolveTimestampText(
          { ...timestampSettings, enabled: true },
          timestampContext,
        );
      }
      const payload = overlayBurnPayload(
        gridOverlay.preset,
        timestampText,
        timestampSettings.position,
      );
      const r = await api.capOverlay(sessionId, payload);
      applyToSession(r, 'Grid burned into frame', { openLab: false });
      reportSuccess('Grid overlay burned into examination frame');
    } catch (e) {
      reportError(e, 'Grid burn-in failed');
    } finally {
      setGridBurning(false);
    }
  }, [sessionId, gridOverlay, timestampSettings, timestampContext, applyToSession, reportSuccess, reportError]);

  const burnTimestamp = useCallback(async (payload) => {
    if (!sessionId) return;
    setTimestampBurning(true);
    try {
      const r = await api.capOverlay(sessionId, payload);
      applyToSession(r, 'Timestamp burned into frame', { openLab: false });
      reportSuccess('Timestamp burned into examination frame');
    } catch (e) {
      reportError(e, 'Timestamp burn-in failed');
    } finally {
      setTimestampBurning(false);
    }
  }, [sessionId, applyToSession, reportSuccess, reportError]);

  const syncCapPreviewToSession = useCallback(async (capResult, timeSec, message) => {
    const path = exportForm.input_path || storagePath;
    const samePath = sessionId && storagePath && path
      && (storagePath === path || storagePath.endsWith(path) || path.endsWith(storagePath));
    if (samePath && sessionId != null && timeSec != null) {
      try {
        const r = await api.seekVideo(sessionId, timeSec);
        applyToSession(r, message);
        setSeekTime(timeSec);
        return;
      } catch (e) {
        reportError(e, 'Seek failed');
      }
    }
    applyToSession(capResult, message || 'Preview updated — open Examination Lab to sync pipeline', {
      openLab: autoOpenLab,
    });
  }, [sessionId, storagePath, exportForm.input_path, autoOpenLab, applyToSession]);

  const showWorkflowBar = !['command', 'examine', 'capture', 'markup', 'timeline', 'tools', 'custody', 'settings'].includes(page);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setPage('examine');
    setBlocking(true, {
      message: 'Ingesting evidence…',
      detail: file.name,
      wait: 'Creating preview, storing evidence, and linking it to the active case.',
    });
    setPreviewOriginal(null);
    setPreview(URL.createObjectURL(file));
    try {
      let sid = sessionId;
      if (!sid) {
        const s = await api.createSession();
        sid = s.session_id;
        setSessionId(sid);
      }
      const data = await api.uploadMedia(sid, file);
      handlePreview(data);
      const saved = data.storage_path || data.source_path || '';
      setStoragePath(saved);
      setMediaPath(file.name);
      setMediaType(data.media_type || 'image');
      if (data.evidence_id) setEvidenceId(data.evidence_id);
      setVideoMeta(data.metadata || null);
      setSeekTime(0);
      setExportForm((f) => ({ ...f, input_path: saved || file.name }));
      const fc = await api.forensicsActiveCase();
      setForensicCase(fc);
      if (fc.evidence?.length) {
        const last = fc.evidence[fc.evidence.length - 1];
        setEvidenceHash(last.sha256);
        setEvidenceId(last.evidence_id || null);
        if (!saved && last.storage_path) {
          setStoragePath(last.storage_path);
          setExportForm((f) => ({ ...f, input_path: last.storage_path }));
        }
      }
      if (data.media_type === 'video' && saved) {
        try {
          setTimelineLoading(true);
          const r = await api.timelineBuild(saved, 25000, false);
          setTimeline(r);
          setVideoMeta({ ...(data.metadata || {}), duration: r.duration, fps: r.fps, vfr: r.vfr });
          setVideoInfo({ duration: r.duration, fps: r.fps, frame_count: r.frame_sample_count });
          if (r.duration) {
            setRegionStart(0);
            setRegionEnd(r.duration);
          }
        } catch { /* optional */ }
        finally { setTimelineLoading(false); }
      }
      const kind = data.media_type === 'video' ? 'Video' : 'Image';
      reportSuccess(`${kind} ingested: ${file.name}`);
      setPage('examine');
    } catch (err) {
      reportError(err, 'Upload failed');
    } finally {
      setBlocking(false);
    }
    e.target.value = '';
  };

  const applyFilter = async () => {
    if (!sessionId) return reportError('Session not ready — wait a moment or refresh the page.', 'Filter');
    if (!selectedFilter) return reportError('Select a filter from the list first.', 'Filter');
    if (!preview && !previewOriginal) {
      return reportError('Load evidence first — use Browse or Load by Path.', 'Filter');
    }
    if (!selectedFilter.implemented) {
      notify(`"${selectedFilter.name}" is catalog-only. Use a FORENSIC filter for reliable results.`, 'warn');
    }
    setFilterApplying(true);
    try {
      const data = await api.forensicsApplyFilter(sessionId, selectedFilter.id);
      applyToSession(data, `Applied: ${selectedFilter.name}`, { openLab: false });
      notify(`Applied: ${selectedFilter.name}`, 'success');
      setError('');
    } catch (e) {
      reportError(e, `Filter "${selectedFilter.name}" failed`);
    } finally {
      setFilterApplying(false);
    }
  };

  const resetEnhancement = async () => {
    if (!sessionId) return reportError('No active session.', 'Reset');
    try {
      const data = await api.forensicsReset(sessionId);
      handlePreview(data);
      setFilterChain([]);
      reportSuccess('Restored to original master frame');
    } catch (e) {
      reportError(e, 'Reset failed');
    }
  };

  const removeFilterAt = async (index) => {
    if (!sessionId) return;
    try {
      const data = await api.forensicsRemoveFilter(sessionId, index);
      handlePreview(data);
      reportSuccess(`Removed: ${filterLabel(data.removed_filter_id || filterChain[index])}`);
    } catch (e) {
      reportError(e, 'Remove filter failed');
    }
  };

  const seekToFrame = async (f) => {
    if (!sessionId || !storagePath) return;
    playback.pause();
    try {
      const r = await api.seekVideo(sessionId, f.pts);
      handlePreview(r);
      setSeekTime(f.pts);
      setFrameIndex(f.index);
      setCurrentFrameMeta(f);
      if (videoRef.current) videoRef.current.currentTime = f.pts;
      setStatus(`Frame #${f.index} (${f.type}) @ ${f.pts.toFixed(3)}s`);
    } catch (e) { reportError(e, 'Seek frame failed'); }
  };

  const stepFrame = async (delta, useIframe = false) => {
    if (!sessionId) return;
    try {
      const r = await api.timelineStepFrame(sessionId, delta, useIframe);
      handlePreview(r);
      setSeekTime(r.time_sec);
      setFrameIndex(r.frame_index);
      if (r.frame_type || r.type) {
        setCurrentFrameMeta({ index: r.frame_index, pts: r.time_sec, type: r.frame_type || r.type });
      }
      if (videoRef.current) videoRef.current.currentTime = r.time_sec;
      setStatus(`Frame #${r.frame_index} @ ${r.time_sec?.toFixed(3)}s`);
    } catch (e) { reportError(e, 'Frame step failed'); }
  };

  const playbackFps = timeline?.fps || videoMeta?.fps || videoInfo?.fps || 30;
  const videoPlaybackEnabled = mediaType === 'video' && Boolean(sessionId && storagePath);

  seekTimeRef.current = seekTime;

  const playback = useForensicPlayback({
    enabled: videoPlaybackEnabled,
    videoRef,
    fps: playbackFps,
    stepFrame,
    getCurrentTime: () => seekTimeRef.current,
  });

  const handlePlayReverse = useCallback(() => {
    if (seekTimeRef.current <= 0.001) {
      setStatus(t('playback.reverse_at_start', 'Seek forward before reverse playback'));
      return;
    }
    playback.playReverse();
  }, [playback, t]);

  const handlePlaybackPause = useCallback(async () => {
    const wasForward = playback.direction === 'forward';
    const currentTime = videoRef.current?.currentTime;
    playback.pause();
    if (!wasForward || !sessionId || !Number.isFinite(currentTime)) return;
    try {
      const r = await api.seekVideo(sessionId, currentTime);
      handlePreview(r);
      setSeekTime(currentTime);
      setStatus(`Paused at ${currentTime.toFixed(2)}s`);
    } catch (e) {
      reportError(e, 'Pause frame sync failed');
    }
  }, [playback, sessionId, reportError]);

  const buildTimeline = async (forceRefresh = false) => {
    if (!storagePath) return reportError('Load video evidence first.', 'Timeline');
    setTimelineLoading(true);
    setError('');
    try {
      const r = await api.timelineBuild(storagePath, 25000, forceRefresh);
      setTimeline(r);
      setVideoMeta((m) => ({ ...m, duration: r.duration, fps: r.fps, vfr: r.vfr }));
      if (r.duration) setRegionEnd(r.duration);
      const q = r.index_quality === 'forensic' ? 'FORENSIC' : 'STANDARD';
      setStatus(`${q} index: ${r.frame_sample_count?.toLocaleString()} frames · I:${r.summary?.I} P:${r.summary?.P} B:${r.summary?.B}${r.from_cache ? ' (cache)' : ''}`);
    } catch (e) { reportError(e, 'Timeline build failed'); }
    finally { setTimelineLoading(false); }
  };

  const seekToTime = async (t, frameIdxHint = null) => {
    playback.pause();
    setSeekTime(t);
    if (videoRef.current) videoRef.current.currentTime = t;
    const near = timeline?.frames?.reduce((best, f) => (
      !best || Math.abs(f.pts - t) < Math.abs(best.pts - t) ? f : best
    ), null);
    if (near) setCurrentFrameMeta(near);
    if (frameIdxHint != null) setFrameIndex(frameIdxHint);
    if (!sessionId) return;
    try {
      const r = await api.seekVideo(sessionId, t);
      handlePreview(r);
      setFrameIndex(r.frame_index ?? frameIdxHint ?? near?.index ?? 0);
    } catch (e) {
      notify(formatApiError(e, 'Seek failed'), 'warn');
    }
  };

  const handleBookmarkApplyFilter = useCallback(async (filterId, params = {}) => {
    if (!sessionId) throw new Error(t('bookmark.need_session', 'Open Examination Lab with loaded evidence to jump'));
    try {
      const data = await api.forensicsApplyFilter(sessionId, filterId, params);
      applyToSession(data, `${t('bookmark.jumped', 'Jumped to bookmark')}: ${filterLabel(filterId)}`, { openLab: false });
      notify(`${t('bookmark.jumped', 'Jumped to bookmark')}: ${filterLabel(filterId)}`, 'success');
    } catch (e) {
      reportError(e, `Bookmark filter "${filterLabel(filterId)}" failed`);
      throw e;
    }
  }, [sessionId, applyToSession, filterLabel, t, notify, reportError]);

  const loadCustody = async () => {
    if (!forensicCase?.case_id) return;
    const data = await api.forensicsCustody(forensicCase.case_id);
    setCustody(data.entries || []);
  };

  useEffect(() => {
    if (page === 'command') {
      api.capExamples().then((r) => setExamples(r.examples || [])).catch(() => {});
    }
    if (page === 'custody') loadCustody();
    if (page === 'tools') {
      Promise.all([api.aiStatus(), api.aiTools(), api.aiModels()])
        .then(([st, tools, models]) => {
          setAiStatus(st);
          setAiTools(tools.tools || []);
          setAiModels(models.models || []);
        })
        .catch(() => {});
    }
  }, [page, forensicCase?.case_id]);

  const handleLiveIngest = (data) => {
    handlePreview(data);
    if (data.storage_path) setStoragePath(data.storage_path);
    setMediaType(data.media_type || 'image');
    setPage('examine');
  };

  const markupMediaId = useMemo(
    () => storagePath || evidenceId || sessionId || 'default',
    [storagePath, evidenceId, sessionId],
  );

  const currentPageLabel = useMemo(() => {
    const item = NAV_KEYS.find((n) => n.id === page);
    return item ? t(item.key, item.id) : page;
  }, [page, t]);

  const mediaIdLabel = () => {
    const id = storagePath || mediaPath || '—';
    return id.length > 40 ? `…${id.slice(-36)}` : id;
  };

  const renderFilterPipeline = (variant = '') => (
    <div className={`fx-pipeline ${variant}`.trim()}>
      {filterChain.length === 0 && (
        <span className="fx-pipeline-empty">No filters applied</span>
      )}
      {filterChain.map((id, index) => {
        const label = filterLabel(id);
        return (
          <span key={`${id}-${index}`} className="fx-pipeline-chip">
            <span className="fx-pipeline-step">{index + 1}</span>
            <span className="fx-pipeline-label" title={label}>{label}</span>
            <button
              type="button"
              className="fx-pipeline-remove"
              title={`Remove ${label}`}
              aria-label={`Remove filter ${label}`}
              onClick={() => removeFilterAt(index)}
            >
              ×
            </button>
          </span>
        );
      })}
    </div>
  );

  return (
    <div className={`fx-app${blockingOverlay ? ' fx-app-blocked' : ''}${sidebarCollapsed ? ' fx-app--sidebar-collapsed' : ''}`}>
      <aside className={`fx-sidebar${sidebarCollapsed ? ' fx-sidebar--collapsed' : ''}`}>
        <button
          type="button"
          className="fx-sidebar-toggle"
          aria-label={sidebarCollapsed ? t('nav.expand', 'Expand navigation') : t('nav.collapse', 'Collapse navigation')}
          title={sidebarCollapsed ? t('nav.expand', 'Expand navigation') : t('nav.collapse', 'Collapse navigation')}
          onClick={() => {
            setSidebarCollapsed((c) => {
              const next = !c;
              localStorage.setItem('chakshu.sidebarCollapsed', next ? '1' : '0');
              return next;
            });
          }}
        >
          {sidebarCollapsed ? '›' : '‹'}
        </button>
        <div className="fx-brand">
          <BrandMark variant="sidebar" />
        </div>
        <nav className="fx-nav">
          {NAV_KEYS.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`fx-nav-btn ${page === n.id ? 'active' : ''}`}
              onClick={() => setPage(n.id)}
              title={t(n.key, n.id)}
              aria-label={t(n.key, n.id)}
              aria-current={page === n.id ? 'page' : undefined}
            >
              <span className="fx-nav-icon" aria-hidden>{n.icon}</span>
              <span className="fx-nav-label">{t(n.key, n.id)}</span>
            </button>
          ))}
        </nav>
        <SidebarFooter
          caseLabel={caseLabel}
          caseId={forensicCase?.case_id}
          examiner={forensicCase?.examiner}
          onOpenSettings={() => setPage('settings')}
        />
      </aside>

      <div className={`fx-workspace${notesCollapsed ? '' : ' fx-workspace--notes-open'}`}>
      <div className="fx-main-column">
      <div className="fx-main">
        <header className="fx-topbar">
          <div className="fx-topbar-primary">
            <div className="fx-topbar-brandline">
              <button
                type="button"
                className="fx-topbar-menu-btn"
                aria-label={sidebarCollapsed ? t('nav.expand', 'Expand navigation') : t('nav.collapse', 'Collapse navigation')}
                onClick={() => {
                  setSidebarCollapsed((c) => {
                    const next = !c;
                    localStorage.setItem('chakshu.sidebarCollapsed', next ? '1' : '0');
                    return next;
                  });
                }}
              >
                ☰
              </button>
              <BrandMark variant="sidebar" className="fx-topbar-brandmark" />
            </div>
            <div className="fx-topbar-context">
              <form className="fx-case-workflow" onSubmit={handleCaseSubmit}>
                <label className="fx-case-workflow-label" htmlFor="fx-active-case-id">
                  {t('case.id', 'Case ID')}
                </label>
                <input
                  id="fx-active-case-id"
                  className="fx-case-workflow-input"
                  value={caseDraft}
                  onChange={(e) => setCaseDraft(e.target.value)}
                  placeholder="CHK-20260706-001"
                  aria-label={t('case.id', 'Case ID')}
                />
                <button
                  type="submit"
                  className="fx-case-workflow-submit"
                  disabled={caseSubmitting || !caseDraft.trim()}
                >
                  {caseSubmitting ? t('case.setting', 'Setting') : t('case.set', 'Set')}
                </button>
              </form>
              <div className="fx-topbar-meta">
                <strong>{forensicCase?.title || 'Examination'}</strong>
                <span className="case-id" title={forensicCase?.case_id}>{caseLabel}</span>
              </div>
            </div>
            <div className="fx-topbar-actions">
              <button
                type="button"
                className="fx-topbar-icon-btn"
                onClick={() => setPage('settings')}
                aria-label={t('nav.settings', 'Settings')}
                title={t('nav.settings', 'Settings')}
              >
                ⚙
              </button>
            </div>
          </div>
          <nav className="fx-topbar-nav" aria-label={t('nav.primary', 'Primary navigation')}>
            {NAV_KEYS.map((n) => (
              <button
                key={n.id}
                type="button"
                className={`fx-topbar-nav-btn ${page === n.id ? 'active' : ''}`}
                onClick={() => setPage(n.id)}
                aria-current={page === n.id ? 'page' : undefined}
              >
                {t(n.key, n.id)}
              </button>
            ))}
          </nav>
        </header>

        <ExamCompareDock
          visible={showWorkflowBar}
          originalSrc={previewOriginal}
          enhancedSrc={preview}
          filterChain={filterChain}
          filterLabel={filterLabel}
          lastAction={labFlash}
          pathLabel={mediaIdLabel()}
          hasPreview={Boolean(preview)}
          mediaType={mediaType}
          isEnhanced={filterChain.length > 0}
          showOriginal={showOriginalPreview}
          onShowOriginalChange={hasEvidence ? (v) => {
            setShowOriginalPreview(v);
            localStorage.setItem('chakshu.showOriginalPreview', v ? '1' : '0');
          } : undefined}
          t={t}
          autoOpenLab={autoOpenLab}
          onAutoOpenLabChange={(v) => {
            setAutoOpenLab(v);
            localStorage.setItem('chakshu.autoOpenLab', v ? '1' : '0');
          }}
          onOpenLab={() => setPage('examine')}
          onIngest={() => fileRef.current?.click()}
          gridOverlay={hasEvidence ? gridOverlay : null}
          onGridOverlayToggle={hasEvidence ? (v) => updateGridOverlay({ enabled: v }) : undefined}
        />

        {page === 'settings' && (
          <div className="fx-content fx-settings-page">
            <div className="fx-settings-hero">
              <div>
                <h2>{t('nav.settings', 'Settings')}</h2>
                <p>{caseLabel}</p>
              </div>
              <button type="button" className="fx-btn" onClick={() => setPage('examine')}>
                {t('action.examination_lab', 'Examination Lab')}
              </button>
            </div>
            <div className="fx-settings-layout">
              <LocaleSettings />
              <ProjectStructureSettings
                exportForm={exportForm}
                setExportForm={setExportForm}
                forensicCase={forensicCase}
                t={t}
                setStatus={setStatus}
                setError={reportError}
              />
            </div>
          </div>
        )}

        {page === 'command' && (
          <div className="fx-content fx-command-page">
            <section className="fx-command-summary">
              <div>
                <span className="fx-command-kicker">Command Center</span>
                <h2>{caseLabel}</h2>
                <p>{forensicCase?.title || 'New Examination'}</p>
              </div>
              <div className="fx-command-actions">
                <button type="button" className="fx-btn fx-btn-primary" onClick={() => fileRef.current?.click()}>
                  Ingest Evidence
                </button>
                <button type="button" className="fx-btn" onClick={() => setPage('examine')}>
                  Examination Lab
                </button>
              </div>
            </section>

            <div className="fx-command-grid">
              <div className="fx-stat"><div className="val">{forensicCase?.evidence?.length || 0}</div><div className="lbl">Evidence Items</div></div>
              <div className="fx-stat"><div className="val">{filters.filter((f) => f.implemented).length}</div><div className="lbl">Forensic Filters</div></div>
              <div className="fx-stat"><div className="val">{filterChain.length}</div><div className="lbl">Pipeline Steps</div></div>
              <div className="fx-stat"><div className="val">{analysis?.summary?.I ?? '—'}</div><div className="lbl">I-Frames (last scan)</div></div>
            </div>

            {evidenceHash && (
              <div className="fx-panel">
                <div className="fx-panel-head">Evidence Integrity (SHA-256)</div>
                <div className="fx-panel-body"><div className="fx-hash">{evidenceHash}</div></div>
              </div>
            )}
            <div className="fx-panel cap-examples">
              <div className="fx-panel-head">Learning & Example Workflows</div>
              <div className="fx-panel-body">
                {examples.map((ex) => (
                  <div
                    key={ex.id}
                    className="cap-example-card"
                    role="button"
                    tabIndex={0}
                    onClick={async () => {
                      try {
                        const r = await api.capExample(ex.id);
                        setSelectedExample(r.workflow || { title: ex.title, steps: ex.steps });
                        setStatus(`Loaded example: ${ex.title}`);
                      } catch (e) { setError(e.message); }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.currentTarget.click();
                      }
                    }}
                  >
                    <h4>{ex.title}</h4>
                    <p>{ex.description || ex.phase}</p>
                  </div>
                ))}
                {selectedExample && (
                  <div style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--fx-muted)' }}>
                    <strong>{selectedExample.title}</strong>
                    <ol style={{ paddingLeft: 18, marginTop: 6 }}>
                      {(selectedExample.steps || []).map((s, i) => <li key={i}>{s}</li>)}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {page === 'capture' && (
          <div className="fx-content">
            <LiveCapture
              sessionId={sessionId}
              filters={filters}
              onIngest={handleLiveIngest}
              onStatus={setStatus}
              onError={(msg) => reportError(msg, 'Capture')}
            />
          </div>
        )}

        {page === 'examine' && (
          <div className={`fx-content fx-grid-examine${hasEvidence ? ' fx-grid-examine--has-side' : ' fx-grid-examine--preview-wide'}${isVideo ? ' fx-grid-examine--video' : (hasEvidence && isImage ? ' fx-grid-examine--image' : '')}${pipelineCollapsed ? ' fx-grid-examine--pipeline-collapsed' : ''}`}>
            <div className={`fx-panel fx-examine-pipeline${pipelineCollapsed ? ' fx-examine-pipeline--collapsed' : ''}`}>
              <div className="fx-panel-head">
                <span className="fx-pipeline-toggle-label">Enhancement Pipeline</span>
                {hasEvidence && !pipelineCollapsed && (
                  <span className={`fx-badge ${isVideo ? 'fx-badge-live' : 'fx-badge-image'}`} style={{ marginLeft: 8 }}>
                    {isVideo ? 'VIDEO' : 'IMAGE'}
                  </span>
                )}
                <button
                  type="button"
                  className="fx-pipeline-toggle"
                  aria-label={pipelineCollapsed ? 'Expand filter pipeline' : 'Collapse filter pipeline'}
                  title={pipelineCollapsed ? 'Expand filters' : 'Collapse filters'}
                  onClick={() => {
                    setPipelineCollapsed((c) => {
                      const next = !c;
                      localStorage.setItem('chakshu.pipelineCollapsed', next ? '1' : '0');
                      return next;
                    });
                  }}
                >
                  {pipelineCollapsed ? '›' : '‹'}
                </button>
              </div>
              <div className="fx-panel-body">
                <input className="fx-input" placeholder="Search filters…" value={filterSearch} onChange={(e) => setFilterSearch(e.target.value)} />
                {!hasEvidence && (
                  <p className="fx-filter-scope fx-filter-scope-empty">
                    {t('filter.ingest_for_scope', 'Ingest image or video evidence — the filter list will show only filters compatible with that media type.')}
                  </p>
                )}
                {hasEvidence && (
                  <p className="fx-filter-scope">
                    {isVideo
                      ? t('filter.scope_video_count', `Showing ${filterScope.total} video-compatible filters (${filterScope.videoCount} video · ${filterScope.bothCount} shared)`)
                      : t('filter.scope_image_count', `Showing ${filterScope.total} image-compatible filters (${filterScope.imageCount} image · ${filterScope.bothCount} shared)`)}
                  </p>
                )}
                <div className="fx-filter-actions">
                  <button
                    type="button"
                    className={`fx-btn fx-btn-primary${filterApplying ? ' fx-btn-loading' : ''}`}
                    onClick={applyFilter}
                    disabled={!selectedFilter || filterApplying}
                  >
                    {filterApplying ? 'Applying…' : 'Apply'}
                  </button>
                  <button type="button" className="fx-btn fx-btn-danger" onClick={resetEnhancement}>Reset</button>
                </div>
                <div className="fx-applied-pipeline">
                  <div className="fx-applied-pipeline-head">
                    <span>Applied filters</span>
                    <span className="fx-applied-pipeline-count">{filterChain.length}</span>
                  </div>
                  {renderFilterPipeline('fx-pipeline--side')}
                </div>
                <div className="fx-filter-list">
                  {!hasEvidence && (
                    <div className="fx-filter-empty">
                      {t('filter.waiting_evidence', 'No filters loaded — waiting for evidence')}
                    </div>
                  )}
                  {forensicFilters.map((f) => (
                    <div
                      key={f.id}
                      className={`fx-filter-item ${selectedFilter?.id === f.id ? 'selected' : ''}`}
                      role="button"
                      tabIndex={0}
                      aria-pressed={selectedFilter?.id === f.id}
                      onClick={() => setSelectedFilter(f)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedFilter(f);
                        }
                      }}
                    >
                      <span className="fx-filter-name">{f.name}</span>
                      <span className="fx-filter-badges">
                        <span className={`fx-badge fx-badge-domain fx-badge-domain-${f.domain || 'image'}`}>
                          {filterDomainLabel(f.domain)}
                        </span>
                        <span className={`fx-badge ${f.implemented ? 'fx-badge-live' : 'fx-badge-cat'}`}>
                          {f.implemented ? 'FORENSIC' : 'CAT'}
                        </span>
                      </span>
                    </div>
                  ))}
                  {hasEvidence && forensicFilters.length === 0 && (
                    <div className="fx-filter-empty">
                      {t('filter.none_match', 'No filters match your search for this media type')}
                    </div>
                  )}
                </div>
                {selectedFilter && (
                  <p className="fx-filter-hint">
                    {selectedFilter.description || selectedFilter.id}
                    {!selectedFilter.implemented && ' — prefer FORENSIC-tagged filters for reliable results.'}
                  </p>
                )}
              </div>
            </div>

            <div className="fx-panel fx-examine-preview">
              <div className="fx-panel-head">
                Frame Examination (Non-destructive)
                {isVideo && <span className="fx-badge fx-badge-live" style={{ marginLeft: 8 }}>VIDEO</span>}
                {isImage && <span className="fx-badge fx-badge-image" style={{ marginLeft: 8 }}>IMAGE</span>}
              </div>
              {hasEvidence && (
                <div className={`fx-preview-pipeline${filterChain.length ? ' fx-preview-pipeline--active' : ''}`}>
                  <span className="fx-preview-pipeline-title">Applied filters</span>
                  {renderFilterPipeline('fx-pipeline--preview')}
                </div>
              )}
              <div className="fx-examine-viewport">
              {isVideo && storagePath && (
                <div className={`fx-examine-live-video-frame${playback.direction === 'forward' ? ' is-active' : ''}`}>
                  <span className="fx-compare-pane-label fx-compare-pane-label-enh">
                    {t('playback.live_video', 'Live playback')}
                  </span>
                  <video
                    ref={videoRef}
                    src={api.mediaServeUrl(storagePath)}
                    className="fx-examine-live-video"
                    playsInline
                    onTimeUpdate={(e) => {
                      if (playback.direction !== 'reverse') setSeekTime(e.target.currentTime);
                    }}
                    onPlay={() => {
                      if (playback.direction === 'reverse') videoRef.current?.pause();
                    }}
                  />
                </div>
              )}
              <div className={playback.direction === 'forward' ? 'fx-static-frame-hidden' : ''}>
              <CompareFrameView
                originalSrc={previewOriginal}
                enhancedSrc={preview}
                flash={Boolean(labFlash)}
                variant="lab"
                compareEnabled={hasEvidence}
                isEnhanced={filterChain.length > 0}
                showOriginal={showOriginalPreview}
                onShowOriginalChange={hasEvidence ? (v) => {
                  setShowOriginalPreview(v);
                  localStorage.setItem('chakshu.showOriginalPreview', v ? '1' : '0');
                } : undefined}
                gridOverlay={hasEvidence ? gridOverlay : null}
                onGridOverlayToggle={hasEvidence ? (v) => updateGridOverlay({ enabled: v }) : undefined}
                t={t}
              />
              </div>
              {isVideo && storagePath && (
                <div className="fx-examine-playback fx-examine-playback--bar">
                  <ForensicVideoTransport
                    t={t}
                    direction={playback.direction}
                    speed={playback.speed}
                    currentTime={seekTime}
                    duration={videoMeta?.duration || videoInfo?.duration || 0}
                    fps={playbackFps}
                    onSpeedChange={playback.setSpeed}
                    onPlayForward={playback.playForward}
                    onPlayReverse={handlePlayReverse}
                    onPause={handlePlaybackPause}
                    onStepBack={() => { playback.pause(); stepFrame(-1); }}
                    onStepForward={() => { playback.pause(); stepFrame(1); }}
                    onStepIframe={() => { playback.pause(); stepFrame(1, true); }}
                    disabled={!sessionId}
                    compact
                  />
                  <input
                    type="range"
                    className="fx-examine-scrub"
                    min={0}
                    max={videoMeta?.duration || videoInfo?.duration || 120}
                    step={0.05}
                    value={seekTime}
                    onChange={(e) => {
                      playback.pause();
                      setSeekTime(Number(e.target.value));
                    }}
                  />
                  <code className="fx-examine-playback-time">
                    {seekTime.toFixed(2)}s{videoMeta?.duration ? ` / ${Number(videoMeta.duration).toFixed(1)}s` : ''}
                  </code>
                  <button
                    type="button"
                    className="fx-btn fx-btn-primary fx-btn-sm"
                    onClick={async () => {
                      playback.pause();
                      try {
                        const r = await api.seekVideo(sessionId, seekTime);
                        handlePreview(r);
                        setStatus(`Examining frame at ${seekTime.toFixed(2)}s`);
                      } catch (err) { setError(err.message); }
                    }}
                  >
                    {t('playback.load_frame', 'Load frame')}
                  </button>
                  <button
                    type="button"
                    className="fx-btn fx-btn-sm"
                    onClick={async () => {
                      if (!storagePath) return;
                      try {
                        const r = await api.capSeekIframe(storagePath, seekTime);
                        if (r.preview) setPreview(previewDataUrl(r.preview));
                        setStatus(`I-frame near ${seekTime.toFixed(2)}s`);
                      } catch (err) { setError(err.message); }
                    }}
                  >
                    {t('playback.nearest_iframe', 'I-frame')}
                  </button>
                </div>
              )}
              </div>
              {!hasEvidence && (
                <div className="fx-tools-empty">
                  <div className="fx-tools-empty-icon" aria-hidden>⧉</div>
                  <p className="fx-tools-empty-title">{t('tools.empty_title', 'No evidence loaded')}</p>
                  <p className="fx-tools-empty-sub">
                    {t('tools.empty_sub', 'Ingest an image or video — enhancement, overlay and geometry tools relevant to that media type will appear here.')}
                  </p>
                  <button type="button" className="fx-btn fx-btn-primary" onClick={() => fileRef.current?.click()}>
                    {t('action.ingest', 'Ingest Evidence')}
                  </button>
                </div>
              )}
            </div>

            {hasEvidence && (
              <div className={isVideo ? 'fx-examine-tools-rail' : 'fx-examine-tools-scroll'}>
              {isVideo && (
                <div className="fx-examine-tools-rail-head">{t('tools.panel_title', 'Examination tools')}</div>
              )}
              {toolGroups.overlays && (
              <div className="fx-tool-stack">
                <details className="fx-tool-group">
                  <summary className="fx-tool-group-head">
                    <span className="fx-tool-group-title">{t('tools.overlays', 'Overlays & annotation')}</span>
                    <span className="fx-tool-group-scope">{t('tools.scope_both', 'Image & video')}</span>
                  </summary>
                  <div className="fx-tool-group-body">
              <GridOverlayPanel
                settings={gridOverlay}
                onChange={updateGridOverlay}
                onBurnIn={burnGridOverlay}
                burning={gridBurning}
                disabled={!hasEvidence}
                sessionId={sessionId}
                t={t}
              />
              <TimestampEditorPanel
                settings={timestampSettings}
                onChange={updateTimestampSettings}
                onApply={burnTimestamp}
                applying={timestampBurning}
                disabled={!hasEvidence}
                sessionId={sessionId}
                seekTime={seekTime}
                fps={timestampContext.fps}
                frameIndex={frameIndex}
                mediaType={mediaType}
                t={t}
              />
                  </div>
                </details>
                {toolGroups.geometry && (
                <details className="fx-tool-group">
                  <summary className="fx-tool-group-head">
                    <span className="fx-tool-group-title">{t('tools.geometry', 'Geometry correction')}</span>
                    <span className="fx-tool-group-scope">{t('tools.scope_both', 'Image & video')}</span>
                  </summary>
                  <div className="fx-tool-group-body">
              <PerspectiveCorrectionPanel
                imageSrc={previewOriginal || preview}
                sessionId={sessionId}
                mediaType={mediaType}
                mediaKey={storagePath || mediaPath || sessionId}
                filterChain={filterChain}
                disabled={!hasEvidence}
                onPreviewUpdate={setPreview}
                onApplied={(data) => applyToSession(data, 'Perspective correction applied', { openLab: false })}
                setStatus={setStatus}
                setError={setError}
                t={t}
              />
              <PanoramaConversionPanel
                imageSrc={previewOriginal || preview}
                sessionId={sessionId}
                inputPath={exportForm.input_path || storagePath}
                outputDir={exportForm.output_dir}
                disabled={!hasEvidence}
                onPreviewUpdate={setPreview}
                onApplied={(data) => applyToSession(data, 'Panorama conversion applied', { openLab: false })}
                setStatus={setStatus}
                setError={setError}
                notify={notify}
                reportSuccess={reportSuccess}
                reportError={reportError}
                t={t}
              />
                  </div>
                </details>
                )}
                <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
                <details className="fx-tool-group fx-tool-group--video">
                  <summary className="fx-tool-group-head">
                    <span className="fx-tool-group-title">{t('tools.video', 'Video tools')}</span>
                    <span className="fx-tool-group-scope fx-tool-group-scope--video">{t('tools.scope_video', 'Video only')}</span>
                  </summary>
                  <div className="fx-tool-group-body">
              <VideoOverlayComparePanel
                leftPath={exportForm.input_path || storagePath}
                sessionId={sessionId}
                seekTime={seekTime}
                duration={timeline?.duration || videoMeta?.duration || videoInfo?.duration || 0}
                gridOverlay={gridOverlay}
                timestampSettings={timestampSettings}
                timestampContext={timestampContext}
                disabled={!hasEvidence}
                onPreviewUpdate={setPreview}
                onApplied={(data) => applyToSession(data, 'Overlay / compare applied', { openLab: false })}
                setStatus={setStatus}
                setError={setError}
                notify={notify}
                reportSuccess={reportSuccess}
                reportError={reportError}
                t={t}
              />
              {storagePath && (
                <TrackingStabilizePanel
                  imageSrc={previewOriginal || preview}
                  videoPath={exportForm.input_path || storagePath}
                  outputDir={exportForm.output_dir}
                  sessionId={sessionId}
                  compactRail={isVideo}
                  onSeekFrame={sessionId ? async (timeSec) => {
                    playback.pause();
                    const r = await api.seekVideo(sessionId, timeSec);
                    handlePreview(r);
                    return r;
                  } : undefined}
                  seekTime={seekTime}
                  duration={timeline?.duration || videoMeta?.duration || videoInfo?.duration || 0}
                  disabled={!hasEvidence}
                  setStatus={setStatus}
                  setError={setError}
                  notify={notify}
                  reportSuccess={reportSuccess}
                  reportError={reportError}
                  t={t}
                />
              )}
                  </div>
                </details>
                </MediaTypeGate>
              </div>
            )}
              </div>
            )}

            {hasEvidence && (
              <div className="fx-examine-side">
                <div className="fx-panel fx-examine-evidence">
                  <div className="fx-panel-head">{t('evidence.load_path', 'Evidence path')}</div>
                  <div className="fx-panel-body">
                    <label className="fx-field">
                      <span className="fx-field-label">{t('evidence.full_path', 'Full path (video / image)')}</span>
                      <input
                        className="fx-input fx-input-mono"
                        placeholder="/Users/you/Desktop/evidence.mp4"
                        value={exportForm.input_path}
                        onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })}
                      />
                    </label>
                    <div className="fx-action-row">
                      <button
                        type="button"
                        className="fx-btn fx-btn-primary"
                        disabled={!sessionId || !exportForm.input_path}
                        onClick={async () => {
                          if (!sessionId || !exportForm.input_path) return;
                          try {
                            const r = await api.loadMediaPath(sessionId, exportForm.input_path);
                            handlePreview(r);
                            setStoragePath(r.storage_path || exportForm.input_path);
                            setMediaType(r.media_type || 'image');
                            setVideoMeta(r.metadata || null);
                            setStatus(`Loaded: ${r.media_type}`);
                          } catch (err) { setError(err.message); }
                        }}
                      >
                        {t('evidence.load_path_btn', 'Load path')}
                      </button>
                    </div>
                    <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
                      <AudioPlayer src={storagePath ? api.mediaServeUrl(storagePath) : null} label="Audio track" compact />
                    </MediaTypeGate>
                  </div>
                </div>
                <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
                  <RegionAnalysisPanel
                    mediaPath={exportForm.input_path || storagePath}
                    regionStart={regionStart}
                    regionEnd={regionEnd}
                    onRegionChange={handleRegionChange}
                    seekTime={seekTime}
                    duration={timeline?.duration || videoMeta?.duration || videoInfo?.duration || 0}
                    fps={timestampContext.fps}
                    regionAnalysis={regionAnalysis}
                    onAnalysis={setRegionAnalysis}
                    onSeek={seekToTime}
                    t={t}
                    setStatus={setStatus}
                    setError={setError}
                    compact
                  />
                  <div className="fx-panel fx-examine-stream">
                    <div className="fx-panel-head">{t('stream.title', 'Stream analysis')}</div>
                    <div className="fx-panel-body">
                      <p className="fx-export-hint">
                        {t('stream.hint', 'Analyze I/P/B frame distribution for the loaded evidence path.')}
                      </p>
                      <p className="fx-path-snippet" title={exportForm.input_path || storagePath}>
                        {exportForm.input_path || storagePath || '—'}
                      </p>
                      <div className="fx-action-row">
                        <button
                          type="button"
                          className="fx-btn fx-btn-primary"
                          disabled={!exportForm.input_path && !storagePath}
                          onClick={async () => {
                            const path = exportForm.input_path || storagePath;
                            if (!path) return;
                            try {
                              const r = await api.forensicsAnalyzeVideo(path);
                              setAnalysis(r);
                              setStatus(`I:${r.summary?.I} P:${r.summary?.P} B:${r.summary?.B}`);
                            } catch (e) { reportError(e, 'Stream analysis failed'); }
                          }}
                        >
                          {t('stream.analyze', 'Analyze I/P/B frames')}
                        </button>
                      </div>
                      {analysis && (
                        <table className="fx-table" style={{ marginTop: 12 }}>
                          <tbody>
                            {Object.entries(analysis.summary || {}).map(([k, v]) => (
                              <tr key={k}><td>{k}</td><td>{v}</td></tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                </MediaTypeGate>

                <BookmarksPanel
                  t={t}
                  mediaPath={exportForm.input_path || storagePath}
                  mediaType={mediaType}
                  sessionId={sessionId}
                  frameIndex={frameIndex}
                  timeSec={seekTime}
                  selectedFilter={selectedFilter}
                  filterChain={filterChain}
                  filterLabel={filterLabel}
                  onSeek={isVideo ? seekToTime : undefined}
                  onApplyFilter={handleBookmarkApplyFilter}
                  setStatus={setStatus}
                  setError={reportError}
                  notify={notify}
                />
              </div>
            )}
          </div>
        )}

        {page === 'markup' && (
          <div className="fx-content">
            <div className="fx-panel">
              <div className="fx-panel-head">Phase 3 — Annotations, Redaction &amp; Measurement</div>
              <div className="fx-panel-body">
                <div className="fx-measurement-settings">
                  <div className="fx-measurement-field">
                    <label>Calibration</label>
                    <input
                      type="number"
                      className="fx-input"
                      min="0.001"
                      step="0.001"
                      value={calibration.pixelsPerUnit}
                      onChange={(e) => setCalibration({ ...calibration, pixelsPerUnit: Number(e.target.value) || 1 })}
                      title="Pixels represented by one selected unit. Example: 10 means 10 px = 1 cm if unit is cm."
                    />
                  </div>
                  <div className="fx-measurement-field">
                    <label>Unit</label>
                    <select
                      className="fx-input"
                      value={calibration.unitName}
                      onChange={(e) => setCalibration({ ...calibration, unitName: e.target.value })}
                      title="Measurement output unit"
                    >
                      {MEASUREMENT_UNITS.map((unit) => (
                        <option key={unit.value} value={unit.value}>{unit.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="fx-measurement-field">
                    <label>Point error</label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      className="fx-input"
                      value={calibration.pointUncertaintyPx}
                      onChange={(e) => setCalibration({ ...calibration, pointUncertaintyPx: Number(e.target.value) || 0 })}
                      title="Expected endpoint picking error in pixels"
                    />
                  </div>
                  <div className="fx-measurement-field">
                    <label>Cal error</label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      className="fx-input"
                      value={calibration.calibrationUncertaintyPercent}
                      onChange={(e) => setCalibration({ ...calibration, calibrationUncertaintyPercent: Number(e.target.value) || 0 })}
                      title="Calibration uncertainty percentage"
                    />
                  </div>
                  <div className="fx-measurement-field">
                    <label>Perspective</label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      className="fx-input"
                      value={calibration.perspectiveUncertaintyPercent}
                      onChange={(e) => setCalibration({ ...calibration, perspectiveUncertaintyPercent: Number(e.target.value) || 0 })}
                      title="Extra uncertainty if the measured plane is angled or perspective-corrected"
                    />
                  </div>
                  {isVideo && (
                    <div className="fx-measurement-field">
                      <label>Δt speed</label>
                      <input
                        type="number"
                        step="0.001"
                        className="fx-input"
                        value={calibration.deltaTime ?? ''}
                        onChange={(e) => setCalibration({ ...calibration, deltaTime: e.target.value ? Number(e.target.value) : null })}
                        title="Optional seconds between positions for speed estimation"
                      />
                    </div>
                  )}
                  <span className="fx-measurement-context">
                    Frame #{frameIndex} · {mediaIdLabel()}
                  </span>
                </div>
                <ExamCanvas
                  imageSrc={preview}
                  sessionId={sessionId}
                  mediaId={markupMediaId}
                  frameIndex={frameIndex}
                  timeSec={seekTime}
                  pixelsPerUnit={calibration.pixelsPerUnit}
                  unitName={calibration.unitName}
                  pointUncertaintyPx={calibration.pointUncertaintyPx}
                  calibrationUncertaintyPercent={calibration.calibrationUncertaintyPercent}
                  perspectiveUncertaintyPercent={calibration.perspectiveUncertaintyPercent}
                  deltaTimeSec={calibration.deltaTime}
                  onPreviewUpdate={setPreview}
                  onStatus={setStatus}
                  onError={(msg) => reportError(msg, 'Markup')}
                />
              </div>
            </div>
          </div>
        )}

        {page === 'timeline' && !isVideo && (
          <div className="fx-content">
            <MediaTypeEmpty requires="video" mediaType={mediaType} hasEvidence={hasEvidence} t={t} />
          </div>
        )}

        {page === 'timeline' && isVideo && (
          <TimelineProPage
            t={t}
            timeline={timeline}
            timelineLoading={timelineLoading}
            seekTime={seekTime}
            seekToTime={seekToTime}
            regionStart={regionStart}
            regionEnd={regionEnd}
            onRegionChange={handleRegionChange}
            preview={preview}
            storagePath={storagePath}
            videoRef={videoRef}
            playback={playback}
            buildTimeline={buildTimeline}
            stepFrame={stepFrame}
            sessionId={sessionId}
            frameIndex={frameIndex}
            currentFrameMeta={currentFrameMeta}
            mediaIdLabel={mediaIdLabel}
            regionAnalysis={regionAnalysis}
            onRegionAnalysis={setRegionAnalysis}
            timestampContext={timestampContext}
            videoMeta={videoMeta}
            audioChannels={audioChannels}
            onAudioChannels={setAudioChannels}
            onPlayReverse={handlePlayReverse}
            setStatus={setStatus}
            setError={setError}
            onOpenTools={() => setPage('tools')}
            onVideoTimeUpdate={setSeekTime}
          />
        )}

        {page === 'tools' && (
          <div className="fx-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
              <AudioRedactionPanel
                t={t}
                inputPath={exportForm.input_path}
                outputDir={exportForm.output_dir}
                playheadSec={seekTime}
                selectionStart={regionStart}
                selectionEnd={regionEnd}
                setStatus={setStatus}
                setError={reportError}
              />
            </MediaTypeGate>
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
              <AudioStreamPanel
                t={t}
                videoPath={exportForm.input_path || storagePath}
                outputDir={exportForm.output_dir}
                setStatus={setStatus}
                setError={reportError}
                notify={notify}
              />
            </MediaTypeGate>
            <div className="fx-panel" style={{ gridColumn: '1 / -1' }}>
              <div className="fx-panel-head">AI / ML Enhancement (R-090, R-091)</div>
              <div className="fx-panel-body">
                <p style={{ fontSize: '0.75rem', color: 'var(--fx-muted)', marginTop: 0 }}>
                  Built-in AI-style tools work without ONNX. Changes update the live preview bar above and sync to
                  <strong> Examination Lab</strong> (enable “Open Examination Lab after apply” or click the button).
                  {aiStatus && (
                    <span>
                      {' '}ONNX runtime: {aiStatus.onnxruntime_available ? `yes (${aiStatus.onnxruntime_version})` : 'not installed — pip install onnxruntime'}
                    </span>
                  )}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px auto', gap: 8, alignItems: 'end', marginTop: 10 }}>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Tool</label>
                    <select className="fx-input" value={aiTool} onChange={(e) => {
                      setAiTool(e.target.value);
                      if (e.target.value !== 'custom_onnx') setAiModelId('');
                    }}>
                      {aiTools.filter((t) => !t.id?.startsWith('model:')).map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Custom model (optional)</label>
                    <select className="fx-input" value={aiModelId} onChange={(e) => {
                      setAiModelId(e.target.value);
                      if (e.target.value) setAiTool('custom_onnx');
                    }}>
                      <option value="">— built-in only —</option>
                      {aiModels.map((m) => (
                        <option key={m.id} value={m.id}>{m.name} ({m.task})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Strength {aiStrength.toFixed(1)}</label>
                    <input type="range" min={0.1} max={3} step={0.1} value={aiStrength} onChange={(e) => setAiStrength(Number(e.target.value))} style={{ width: '100%' }} />
                  </div>
                  <button type="button" className="fx-btn fx-btn-primary" disabled={!sessionId} onClick={async () => {
                    try {
                      const r = await api.aiEnhanceSession({
                        session_id: sessionId,
                        tool: aiModelId ? 'custom_onnx' : aiTool,
                        model_id: aiModelId,
                        strength: aiStrength,
                      });
                      applyToSession(r, `AI applied: ${aiModelId || aiTool}`);
                      notify(`AI applied: ${aiModelId || aiTool}`, 'success');
                    } catch (e) { reportError(e, 'AI enhance failed'); }
                  }}>Apply to Frame</button>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                  <button type="button" className="fx-btn" onClick={() => aiModelFileRef.current?.click()}>Import ONNX Model</button>
                  <button type="button" className="fx-btn" onClick={async () => {
                    const p = prompt('Full path to .onnx on this machine:', '');
                    if (!p) return;
                    try {
                      await api.aiImportModelPath({ path: p });
                      const models = await api.aiModels();
                      setAiModels(models.models || []);
                      setStatus('Model imported');
                    } catch (e) { setError(e.message); }
                  }}>Import from Path</button>
                  {aiModelId && (
                    <button type="button" className="fx-btn" onClick={async () => {
                      if (!confirm(`Remove model ${aiModelId}?`)) return;
                      try {
                        await api.aiDeleteModel(aiModelId);
                        setAiModelId('');
                        const models = await api.aiModels();
                        setAiModels(models.models || []);
                        setStatus('Model removed');
                      } catch (e) { setError(e.message); }
                    }}>Delete Selected Model</button>
                  )}
                </div>
                {aiModels.length > 0 && (
                  <ul style={{ marginTop: 10, fontSize: '0.7rem', color: 'var(--fx-muted)' }}>
                    {aiModels.map((m) => (
                      <li key={m.id}><strong>{m.name}</strong> — {m.task} · {m.id}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Multi-Algorithm Hash Verification</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" onClick={async () => {
                  try {
                    const r = await api.capHashFile(exportForm.input_path);
                    setAllHashes(r.hashes);
                    setStatus('Computed MD5, SHA-1, SHA-256, SHA-512');
                  } catch (e) { setError(e.message); }
                }}>Hash Evidence File</button>
                {allHashes && (
                  <div style={{ marginTop: 10, fontSize: '0.7rem' }}>
                    {Object.entries(allHashes).map(([k, v]) => (
                      <div key={k} className="fx-hash"><strong>{k}:</strong> {v}</div>
                    ))}
                  </div>
                )}
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await api.capSecureCopy({
                      source: exportForm.input_path,
                      destination: `${exportForm.output_dir}/secure-copy`,
                      report_path: `${exportForm.output_dir}/copy-report.json`,
                    });
                    setStatus(r.verified ? 'Secure copy verified' : 'Copy completed — verify hashes');
                  } catch (e) { setError(e.message); }
                }}>Secure Copy + Report</button>
              </div>
            </div>
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
            <div className="fx-panel">
              <div className="fx-panel-head">Video Seek & I-Frame</div>
              <div className="fx-panel-body">
                <input type="range" min={0} max={videoInfo?.duration || 60} step={0.1} value={seekTime} onChange={(e) => setSeekTime(Number(e.target.value))} style={{ width: '100%' }} />
                <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                  <button type="button" className="fx-btn" onClick={async () => {
                    try {
                      const r = await api.capVideoInfo(exportForm.input_path);
                      setVideoInfo(r);
                      setStatus(`Duration: ${r.duration}s · ${r.frame_count} frames`);
                    } catch (e) { setError(e.message); }
                  }}>Probe Video</button>
                  <button type="button" className="fx-btn fx-btn-primary" onClick={async () => {
                    try {
                      const r = await api.capSeekTime(exportForm.input_path, seekTime);
                      await syncCapPreviewToSession(r, seekTime, `Frame at ${seekTime.toFixed(2)}s`);
                    } catch (e) { setError(e.message); }
                  }}>Seek Time</button>
                  <button type="button" className="fx-btn" onClick={async () => {
                    try {
                      const r = await api.capSeekIframe(exportForm.input_path, seekTime);
                      await syncCapPreviewToSession(r, seekTime, `I-frame near ${seekTime.toFixed(2)}s`);
                    } catch (e) { setError(e.message); }
                  }}>Nearest I-Frame</button>
                </div>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await api.capMpegViz(exportForm.input_path, seekTime, 'macroblock');
                    if (sessionId) {
                      applyToSession(r, 'Macroblock overlay preview');
                    } else {
                      applyToSession(r, 'Macroblock overlay — ingest in Examination Lab to edit', { openLab: true });
                    }
                  } catch (e) { setError(e.message); }
                }}>MPEG Macroblock Overlay</button>
              </div>
            </div>
            </MediaTypeGate>
            <div className="fx-panel">
              <div className="fx-panel-head">Compare & Overlay</div>
              <div className="fx-panel-body">
                <p className="fx-grid-hint">
                  Full video overlay and side-by-side tools are in Examination Lab → Video overlays & side-by-side compare.
                </p>
                <button type="button" className="fx-btn fx-btn-primary" onClick={() => setPage('examine')}>
                  Open Examination Lab
                </button>
                <button type="button" className="fx-btn" style={{ marginLeft: 6 }} disabled={!sessionId} onClick={async () => {
                  if (!sessionId) return;
                  try {
                    const timestampText = resolveTimestampText(
                      { ...timestampSettings, enabled: true },
                      timestampContext,
                    );
                    const payload = overlayBurnPayload(
                      gridOverlay.preset,
                      timestampText,
                      timestampSettings.position,
                    );
                    const r = await api.capOverlay(sessionId, payload);
                    applyToSession(r, 'Timestamp + grid applied');
                  } catch (e) { reportError(e, 'Overlay apply failed'); }
                }}>Quick: Timestamp + Grid</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Clipboard Export (R-134)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" disabled={!sessionId} onClick={async () => {
                  try {
                    const r = await api.capClipboardFrame(sessionId, true);
                    await navigator.clipboard.writeText(r.data_url || r.base64);
                    setStatus(`Frame copied (${r.width}×${r.height}) · SHA-256 in response`);
                  } catch (e) { setError(e.message); }
                }}>Copy Frame to Clipboard</button>
                <button type="button" className="fx-btn" style={{ marginLeft: 6 }} disabled={!allHashes} onClick={async () => {
                  try {
                    const text = Object.entries(allHashes || {}).map(([k, v]) => `${k}: ${v}`).join('\n');
                    await navigator.clipboard.writeText(text);
                    setStatus('Hashes copied to clipboard');
                  } catch (e) { setError(e.message); }
                }}>Copy Hashes</button>
              </div>
            </div>
            <BookmarksPanel
              t={t}
              mediaPath={exportForm.input_path || storagePath}
              mediaType={mediaType}
              sessionId={sessionId}
              frameIndex={frameIndex}
              timeSec={seekTime}
              selectedFilter={selectedFilter}
              filterChain={filterChain}
              filterLabel={filterLabel}
              onSeek={isVideo ? seekToTime : undefined}
              onApplyFilter={handleBookmarkApplyFilter}
              setStatus={setStatus}
              setError={reportError}
              notify={notify}
            />
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
            <SubtitlePanel
              t={t}
              videoPath={exportForm.input_path}
              outputDir={exportForm.output_dir}
              sessionId={sessionId}
              playheadSec={seekTime}
              fontSize={subtitleForm.font_size}
              marginV={subtitleForm.margin_v}
              onFontSizeChange={(v) => setSubtitleForm((f) => ({ ...f, font_size: v }))}
              onMarginVChange={(v) => setSubtitleForm((f) => ({ ...f, margin_v: v }))}
              outputPath={subtitleForm.output_path}
              onOutputPathChange={(p) => setSubtitleForm((f) => ({ ...f, output_path: p }))}
              onApplyPreview={(data, msg) => applyToSession(data, msg, { openLab: false })}
              setStatus={setStatus}
              setError={reportError}
              notify={notify}
              onBlockingChange={setBlocking}
            />
            </MediaTypeGate>
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
            <div className="fx-panel">
              <div className="fx-panel-head">Stream Sync &amp; Merge (R-172 / R-173)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={async () => {
                  try {
                    const second = prompt('Second video path for sync search:', exportForm.input_path) || exportForm.input_path;
                    const r = await api.capStreamSync({
                      path_a: exportForm.input_path,
                      path_b: second,
                      time_a: seekTime,
                      search_sec: 3,
                    });
                    setSyncResult(r);
                    setStatus(r.recommended_offset_ms != null
                      ? `Best offset: ${r.recommended_offset_ms} ms (score ${r.best_score})`
                      : `Similarity: ${r.similarity?.score}`);
                  } catch (e) { setError(e.message); }
                }}>Find Stream Offset</button>
                {syncResult && (
                  <div style={{ marginTop: 8, fontSize: '0.68rem', fontFamily: 'var(--fx-mono)', color: 'var(--fx-muted)' }}>
                    {JSON.stringify(syncResult, null, 0).slice(0, 200)}…
                  </div>
                )}
                <p className="fx-export-hint" style={{ marginTop: 8 }}>
                  {t('audio_mux.use_panel', 'Add or replace audio tracks using the Add Audio Stream panel above.')}
                </p>
                <button type="button" className="fx-btn" style={{ marginTop: 6, display: 'block' }} onClick={async () => {
                  try {
                    const second = prompt('Second video to append:', exportForm.input_path);
                    if (!second) return;
                    const r = await api.capMergeVideos({
                      paths: [exportForm.input_path, second],
                      output_path: `${exportForm.output_dir}/concat.mp4`,
                    });
                    setStatus(r.success ? `Concatenated ${r.segment_count} clips` : (r.stderr || 'Concat failed'));
                  } catch (e) { setError(e.message); }
                }}>Concat Videos</button>
              </div>
            </div>
            </MediaTypeGate>
            <MediaTypeGate requires="video" mediaType={mediaType} hasEvidence={hasEvidence}>
            <div className="fx-panel">
              <div className="fx-panel-head">Advanced Video (Phase 6)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={async () => {
                  try {
                    const r = await api.capAdvancedStabilize({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/stabilized.mp4`,
                    });
                    setStatus(r.success ? `Stabilized (${r.method || 'ok'})` : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Global Stabilize</button>
                <p className="fx-grid-hint" style={{ margin: '8px 0' }}>
                  For object-tracking stabilization, use Examination Lab → Object-tracking stabilization (draw box on object).
                </p>
                <button type="button" className="fx-btn" style={{ marginLeft: 6 }} onClick={async () => {
                  try {
                    const r = await api.capAdvancedReverse({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/reversed.mp4`,
                    });
                    setStatus(r.success ? 'Reversed video exported' : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Reverse</button>
                <button type="button" className="fx-btn" style={{ marginTop: 6, display: 'block' }} onClick={async () => {
                  try {
                    const fps = Number(prompt('Target FPS:', '15') || '15');
                    const r = await api.capAdvancedFps({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/fps-adjusted.mp4`,
                      target_fps: fps,
                    });
                    setStatus(r.success ? `FPS adjusted to ${fps}` : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Adjust FPS</button>
              </div>
            </div>
            </MediaTypeGate>
          </div>
        )}

        {page === 'custody' && (
          <div className="fx-content">
            <div className="fx-panel">
              <div className="fx-panel-head">Chain of Custody Log</div>
              <div className="fx-panel-body">
                <table className="fx-table">
                  <thead>
                    <tr><th>Time</th><th>Action</th><th>Actor</th><th>File</th><th>Notes</th></tr>
                  </thead>
                  <tbody>
                    {custody.map((c, i) => (
                      <tr key={i}>
                        <td>{c.timestamp}</td>
                        <td>{c.action}</td>
                        <td>{c.actor}</td>
                        <td>{c.filename}</td>
                        <td>{c.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {page === 'export' && (
          <LegalExportPanel
            exportForm={exportForm}
            setExportForm={setExportForm}
            sessionId={sessionId}
            forensicCase={forensicCase}
            hasPreview={Boolean(preview)}
            mediaType={mediaType}
            hasEvidence={hasEvidence}
            filterChain={filterChain}
            t={t}
            setStatus={setStatus}
            setError={reportError}
            notify={notify}
          />
        )}

        {page === 'reports' && (
          <div className="fx-content">
            <CaseReportsPanel
              t={t}
              forensicCase={forensicCase}
              exportForm={exportForm}
              locale={locale}
              setStatus={setStatus}
              setError={reportError}
              notify={notify}
            />
          </div>
        )}

        <footer className="fx-statusbar">
          {status}
          {error && <span style={{ color: 'var(--fx-danger)' }}> | {error}</span>}
        </footer>
        {toasts.length > 0 && (
          <div className="fx-toast-stack" aria-live="polite">
            {toasts.map((toast) => {
              const split = toast.message.match(/^([^:]{2,48}):\s+(.+)$/s);
              const title = split?.[1];
              const body = split?.[2] || toast.message;
              return (
              <div key={toast.id} className={`fx-toast fx-toast-${toast.type}`} role="status">
                <span className="fx-toast-icon" aria-hidden="true">
                  {toast.type === 'error' ? '✕' : toast.type === 'warn' ? '!' : '✓'}
                </span>
                <span className="fx-toast-body">
                  {title ? <span className="fx-toast-title">{title}</span> : null}
                  {body}
                </span>
                <button
                  type="button"
                  className="fx-toast-close"
                  aria-label="Dismiss"
                  onClick={() => dismissToast(toast.id)}
                >
                  ×
                </button>
              </div>
              );
            })}
          </div>
        )}
      </div>
      </div>

      {blockingOverlay && (
        <div className="fx-blocking-overlay" role="alertdialog" aria-modal="true" aria-busy="true">
          <div className="fx-blocking-card">
            <div className="fx-blocking-spinner" aria-hidden="true" />
            <p className="fx-blocking-title">{blockingOverlay.message}</p>
            <p className="fx-blocking-detail">{blockingOverlay.wait}</p>
            {blockingOverlay.detail ? (
              <code className="fx-blocking-path">{blockingOverlay.detail}</code>
            ) : null}
          </div>
        </div>
      )}

      <ProjectNotesPanel
        collapsed={notesCollapsed}
        onToggleCollapse={() => {
          setNotesCollapsed((c) => {
            const next = !c;
            localStorage.setItem('chakshu.notesCollapsed', next ? '1' : '0');
            return next;
          });
        }}
        projectName={caseLabel}
        projectId={forensicCase?.case_id || projectMeta.project_id}
        notes={notes}
        author={forensicCase?.examiner}
        evidenceId={evidenceId}
        frameIndex={frameIndex}
        timeSec={seekTime}
        t={t}
        onRefresh={refreshProjectNotes}
        onAdd={async (payload) => {
          await api.projectNoteAdd({
            ...payload,
            case_id: forensicCase?.case_id,
          });
          await refreshProjectNotes();
          setStatus(t('notes.saved', 'Note saved to project'));
        }}
        onDelete={async (noteId) => {
          await api.projectNoteDelete(noteId);
          await refreshProjectNotes();
          setStatus(t('notes.deleted', 'Note deleted'));
        }}
      />
      </div>

      <input ref={fileRef} type="file" accept="image/*,.heic,.heif,video/*" style={{ display: 'none' }} onChange={onUpload} />
      <input
        ref={aiModelFileRef}
        type="file"
        accept=".onnx"
        style={{ display: 'none' }}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          try {
            await api.aiImportModel(file, { name: file.name.replace(/\.onnx$/i, '') });
            const models = await api.aiModels();
            setAiModels(models.models || []);
            setAiModelId(models.models?.[models.models.length - 1]?.id || '');
            setAiTool('custom_onnx');
            setStatus(`Imported ${file.name}`);
          } catch (err) { setError(err.message); }
          e.target.value = '';
        }}
      />
    </div>
  );
}
