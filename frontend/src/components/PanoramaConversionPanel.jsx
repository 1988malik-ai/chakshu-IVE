import { useCallback, useState } from 'react';
import { api, previewDataUrl } from '../api/client';
import { formatApiError } from '../lib/notify';
import {
  DEFAULT_PANORAMA_SETTINGS,
  FISHEYE_MODELS,
  FILTER_ID,
  OUTPUT_TYPES,
  SOURCE_TYPES,
  buildPanoramaExportPath,
  panoramaParams,
  showFisheyeControls,
  showViewControls,
} from '../lib/panoramaConversion';

export default function PanoramaConversionPanel({
  imageSrc,
  sessionId,
  inputPath,
  outputDir,
  disabled = false,
  onPreviewUpdate,
  onApplied,
  setStatus,
  setError,
  notify,
  reportSuccess,
  reportError,
  t = (k, d) => d,
}) {
  const [active, setActive] = useState(false);
  const [settings, setSettings] = useState(DEFAULT_PANORAMA_SETTINGS);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastPath, setLastPath] = useState('');

  const patch = useCallback((next) => {
    setSettings((prev) => ({ ...prev, ...next }));
  }, []);

  const runPreview = useCallback(async () => {
    if (!sessionId) return;
    setPreviewing(true);
    setError?.('');
    try {
      const r = await api.forensicsPreviewFilter(sessionId, FILTER_ID, panoramaParams(settings));
      onPreviewUpdate?.(previewDataUrl(r.preview));
      setStatus?.(t('panorama.previewed', 'Panorama conversion preview'));
    } catch (e) {
      const msg = formatApiError(e, 'Preview failed');
      setError?.(msg);
      reportError?.(e, 'Panorama preview');
    } finally {
      setPreviewing(false);
    }
  }, [sessionId, settings, onPreviewUpdate, setStatus, setError, reportError, t]);

  const applyToFrame = useCallback(async () => {
    if (!sessionId) return;
    setApplying(true);
    setError?.('');
    try {
      const r = await api.forensicsApplyFilter(sessionId, FILTER_ID, panoramaParams(settings), { insertAt: 0 });
      onApplied?.(r);
      const msg = t('panorama.applied', 'Panorama conversion applied to examination frame');
      setStatus?.(msg);
      notify?.(msg, 'success');
    } catch (e) {
      reportError?.(e, 'Panorama apply');
    } finally {
      setApplying(false);
    }
  }, [sessionId, settings, onApplied, setStatus, reportError, notify, t]);

  const saveToFile = useCallback(async () => {
    if (!sessionId && !inputPath) {
      reportError?.(t('panorama.no_path', 'Load evidence and seek to a frame first'), 'Panorama export');
      return;
    }
    const out = buildPanoramaExportPath(outputDir, settings);
    setSaving(true);
    setError?.('');
    try {
      const params = panoramaParams(settings);
      const r = sessionId
        ? await api.capPanoramaSession({ session_id: sessionId, output_path: out, ...params })
        : await api.capPanoramaConvert({
          input_path: inputPath,
          output_path: out,
          ...params,
        });
      const msg = t('panorama.saved', `Panorama saved: ${r.output_path}`);
      setLastPath(r.output_path);
      setStatus?.(msg);
      reportSuccess?.(msg);
    } catch (e) {
      reportError?.(e, 'Panorama export');
    } finally {
      setSaving(false);
    }
  }, [sessionId, inputPath, outputDir, settings, setStatus, reportSuccess, reportError, t]);

  const nextFile = inputPath ? buildPanoramaExportPath(outputDir, settings) : '';

  return (
    <div className={`fx-panorama-panel${active ? ' fx-panorama-panel-active' : ''}`}>
      <div className="fx-panorama-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={active}
            disabled={disabled || !imageSrc}
            onChange={(e) => setActive(e.target.checked)}
          />
          <span>{t('panorama.title', 'Omnidirectional → Panorama')}</span>
        </label>
      </div>
      {active && imageSrc && (
        <div className="fx-panorama-body">
          <p className="fx-grid-hint">
            {t(
              'panorama.hint',
              'Convert fisheye or 360° equirectangular sources into flat panoramic or perspective views. Preview on the current frame, apply to the lab, or save a full-resolution JPEG.',
            )}
          </p>
          <div className="fx-panorama-fields">
            <label>
              <span>{t('panorama.source', 'Source type')}</span>
              <select className="fx-input" value={settings.source_type} onChange={(e) => patch({ source_type: e.target.value })}>
                {SOURCE_TYPES.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>{t('panorama.output', 'Output panorama')}</span>
              <select className="fx-input" value={settings.output_type} onChange={(e) => patch({ output_type: e.target.value })}>
                {OUTPUT_TYPES.map((o) => (
                  <option key={o.id} value={o.id}>{o.label}</option>
                ))}
              </select>
            </label>
            {showFisheyeControls(settings) && (
              <>
                <label>
                  <span>{t('panorama.fov', `Lens FOV ${settings.fov_deg}°`)}</span>
                  <input
                    type="range"
                    min={90}
                    max={220}
                    value={settings.fov_deg}
                    onChange={(e) => patch({ fov_deg: Number(e.target.value) })}
                  />
                </label>
                <label>
                  <span>{t('panorama.model', 'Fisheye model')}</span>
                  <select className="fx-input" value={settings.fisheye_model} onChange={(e) => patch({ fisheye_model: e.target.value })}>
                    {FISHEYE_MODELS.map((m) => (
                      <option key={m.id} value={m.id}>{m.label}</option>
                    ))}
                  </select>
                </label>
              </>
            )}
            {showViewControls(settings) && (
              <>
                <label>
                  <span>{t('panorama.yaw', `Yaw ${settings.yaw_deg}°`)}</span>
                  <input
                    type="range"
                    min={-180}
                    max={180}
                    value={settings.yaw_deg}
                    onChange={(e) => patch({ yaw_deg: Number(e.target.value) })}
                  />
                </label>
                <label>
                  <span>{t('panorama.pitch', `Pitch ${settings.pitch_deg}°`)}</span>
                  <input
                    type="range"
                    min={-90}
                    max={90}
                    value={settings.pitch_deg}
                    onChange={(e) => patch({ pitch_deg: Number(e.target.value) })}
                  />
                </label>
                <label>
                  <span>{t('panorama.roll', `Roll ${settings.roll_deg}°`)}</span>
                  <input
                    type="range"
                    min={-180}
                    max={180}
                    value={settings.roll_deg}
                    onChange={(e) => patch({ roll_deg: Number(e.target.value) })}
                  />
                </label>
                {settings.output_type === 'rectilinear' && (
                  <>
                    <label>
                      <span>{t('panorama.fov_h', `Horizontal FOV ${settings.fov_h_deg}°`)}</span>
                      <input
                        type="range"
                        min={30}
                        max={140}
                        value={settings.fov_h_deg}
                        onChange={(e) => patch({ fov_h_deg: Number(e.target.value) })}
                      />
                    </label>
                    <label>
                      <span>{t('panorama.fov_v', `Vertical FOV ${settings.fov_v_deg}°`)}</span>
                      <input
                        type="range"
                        min={30}
                        max={120}
                        value={settings.fov_v_deg}
                        onChange={(e) => patch({ fov_v_deg: Number(e.target.value) })}
                      />
                    </label>
                  </>
                )}
              </>
            )}
            <label>
              <span>{t('panorama.width', 'Output width')}</span>
              <input
                type="number"
                className="fx-input"
                min={128}
                step={16}
                placeholder={t('panorama.auto', 'Auto')}
                value={settings.out_width}
                onChange={(e) => patch({ out_width: e.target.value })}
              />
            </label>
            <label>
              <span>{t('panorama.height', 'Output height')}</span>
              <input
                type="number"
                className="fx-input"
                min={128}
                step={16}
                placeholder={t('panorama.auto', 'Auto')}
                value={settings.out_height}
                onChange={(e) => patch({ out_height: e.target.value })}
              />
            </label>
          </div>
          <div className="fx-export-actions-row">
            <button type="button" className="fx-btn" disabled={disabled || previewing || !sessionId} onClick={runPreview}>
              {previewing ? t('panorama.previewing', 'Previewing…') : t('panorama.preview', 'Preview')}
            </button>
            <button type="button" className="fx-btn" disabled={disabled || applying || !sessionId} onClick={applyToFrame}>
              {applying ? t('panorama.applying', 'Applying…') : t('panorama.apply', 'Apply to frame')}
            </button>
            <button
              type="button"
              className="fx-btn fx-btn-primary"
              disabled={disabled || saving || (!sessionId && !inputPath)}
              onClick={saveToFile}
            >
              {saving ? t('panorama.saving', 'Saving…') : t('panorama.save', 'Save panoramic JPEG')}
            </button>
          </div>
          {nextFile && (
            <p className="fx-panorama-file-hint">
              {t('panorama.next_file', 'Next file')}: {nextFile.split('/').pop()}
            </p>
          )}
          {lastPath && (
            <p className="fx-panorama-file-hint fx-panorama-file-hint--saved">
              {t('panorama.last_saved', 'Last saved')}: {lastPath}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
