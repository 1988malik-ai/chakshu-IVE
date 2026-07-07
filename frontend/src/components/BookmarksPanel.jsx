import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';

const EMPTY_FORM = {
  label: '',
  notes: '',
  tags: '',
  priority: 'medium',
  examiner: '',
  case_ref: '',
};

function metaFromForm(form) {
  const tags = String(form.tags || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  return {
    notes: form.notes || '',
    tags,
    priority: form.priority || 'medium',
    examiner: form.examiner || '',
    case_ref: form.case_ref || '',
  };
}

function formFromBookmark(bm) {
  const m = bm.metadata || {};
  const tags = Array.isArray(m.tags) ? m.tags.join(', ') : (m.tags || '');
  return {
    label: bm.label || '',
    notes: m.notes || '',
    tags,
    priority: m.priority || 'medium',
    examiner: m.examiner || '',
    case_ref: m.case_ref || '',
  };
}

function formatTime(sec) {
  if (sec == null || Number.isNaN(sec)) return '—';
  return `${Number(sec).toFixed(2)}s`;
}

export default function BookmarksPanel({
  t = (k, d) => d,
  mediaPath = '',
  sessionId,
  frameIndex = 0,
  timeSec = 0,
  selectedFilter = null,
  filterChain = [],
  filterLabel = (id) => id,
  mediaType = 'image',
  onSeek,
  onApplyFilter,
  setStatus,
  setError,
  notify,
}) {
  const isVideo = mediaType === 'video';
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);

  const path = mediaPath?.trim() || '';

  const refresh = useCallback(async () => {
    if (!path) {
      setBookmarks([]);
      return;
    }
    setLoading(true);
    try {
      const r = await api.bookmarksList(path);
      setBookmarks(r.bookmarks || []);
    } catch (e) {
      setError?.(e.message);
    } finally {
      setLoading(false);
    }
  }, [path, setError]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const patchForm = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const saveFrame = async () => {
    if (!path) throw new Error(t('bookmark.no_media', 'Load evidence with a saved media path first'));
    const r = await api.bookmarksAdd({
      media_path: path,
      bookmark_type: 'frame',
      frame_index: frameIndex,
      time_sec: timeSec,
      label: form.label.trim() || t('bookmark.default_frame', 'Frame bookmark'),
      metadata: metaFromForm(form),
    });
    setBookmarks((list) => [...list, r.bookmark]);
    setStatus?.(
      `${t('bookmark.saved_frame', 'Frame bookmark saved')} @ ${formatTime(timeSec)} · #${frameIndex}`,
    );
    notify?.(t('bookmark.toast_frame', 'Frame bookmark saved'), 'success');
    return r.bookmark;
  };

  const saveFilter = async () => {
    if (!path) throw new Error(t('bookmark.no_media', 'Load evidence with a saved media path first'));
    const filterId = filterChain[filterChain.length - 1] || selectedFilter?.id;
    if (!filterId) {
      throw new Error(t('bookmark.no_filter', 'Select a filter or apply one to the pipeline first'));
    }
    const r = await api.bookmarksAdd({
      media_path: path,
      bookmark_type: 'filter',
      filter_id: filterId,
      filter_params: {},
      frame_index: frameIndex,
      time_sec: timeSec,
      label: form.label.trim() || `${t('bookmark.default_filter', 'Filter')}: ${filterLabel(filterId)}`,
      metadata: metaFromForm(form),
    });
    setBookmarks((list) => [...list, r.bookmark]);
    setStatus?.(
      `${t('bookmark.saved_filter', 'Filter bookmark saved')}: ${filterLabel(filterId)} @ ${formatTime(timeSec)}`,
    );
    notify?.(t('bookmark.toast_filter', 'Filter bookmark saved'), 'success');
    return r.bookmark;
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    setError?.('');
    try {
      const r = await api.bookmarksUpdate(editingId, {
        label: form.label.trim(),
        metadata: metaFromForm(form),
      });
      setBookmarks((list) => list.map((b) => (b.id === editingId ? r.bookmark : b)));
      setEditingId(null);
      setForm(EMPTY_FORM);
      setStatus?.(t('bookmark.updated', 'Bookmark updated'));
      notify?.(t('bookmark.toast_updated', 'Bookmark updated'), 'success');
    } catch (e) {
      setError?.(e.message);
    }
  };

  const handleDelete = async (id) => {
    setError?.('');
    try {
      await api.bookmarksDelete(id);
      setBookmarks((list) => list.filter((b) => b.id !== id));
      if (editingId === id) {
        setEditingId(null);
        setForm(EMPTY_FORM);
      }
      setStatus?.(t('bookmark.deleted', 'Bookmark deleted'));
    } catch (e) {
      setError?.(e.message);
    }
  };

  const jumpTo = async (bm) => {
    if (!sessionId) {
      setError?.(t('bookmark.need_session', 'Open Examination Lab with loaded evidence to jump'));
      return;
    }
    setError?.('');
    try {
      if (isVideo && bm.time_sec != null && onSeek) {
        await onSeek(bm.time_sec, bm.frame_index);
      }
      if (bm.bookmark_type === 'filter' && bm.filter_id && onApplyFilter) {
        await onApplyFilter(bm.filter_id, bm.filter_params || {});
      }
      setStatus?.(
        `${t('bookmark.jumped', 'Jumped to bookmark')}: ${bm.label || bm.id}`,
      );
    } catch (e) {
      setError?.(e.message);
    }
  };

  const startEdit = (bm) => {
    setEditingId(bm.id);
    setForm(formFromBookmark(bm));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const runAction = async (fn) => {
    setError?.('');
    try {
      await fn();
    } catch (e) {
      const message = e?.message || t('bookmark.failed', 'Bookmark action failed');
      setError?.(message);
      notify?.(message, 'error');
    }
  };

  const activeFilterId = filterChain[filterChain.length - 1] || selectedFilter?.id;

  return (
    <div className="fx-panel fx-bookmarks-panel">
      <div className="fx-panel-head">{t('bookmark.title', 'Bookmarks — Frames & Filters (R-020)')}</div>
      <div className="fx-panel-body fx-export-form">
        <p className="fx-export-hint">
          {t(
            'bookmark.hint',
            'Save the current frame or filter preset with custom metadata (notes, tags, priority, examiner). Jump back from the list below.',
          )}
        </p>

        {!path && (
          <p className="fx-bookmark-warn">{t('bookmark.no_media', 'Load evidence with a saved media path first')}</p>
        )}

        <div className="fx-bookmark-pos">
          <span>{t('bookmark.position', 'Position')}</span>
          <code>
            {isVideo ? `${formatTime(timeSec)} · ` : ''}
            {t('bookmark.frame', 'frame')} #{frameIndex}
            {activeFilterId ? ` · ${filterLabel(activeFilterId)}` : ''}
          </code>
        </div>

        <div className="fx-bookmark-meta-grid">
          <label>
            {t('bookmark.label', 'Label')}
            <input
              className="fx-input"
              value={form.label}
              onChange={(e) => patchForm('label', e.target.value)}
              placeholder={t('bookmark.label_ph', 'e.g. License plate visible')}
            />
          </label>
          <label>
            {t('bookmark.priority', 'Priority')}
            <select className="fx-input" value={form.priority} onChange={(e) => patchForm('priority', e.target.value)}>
              <option value="low">{t('bookmark.priority_low', 'Low')}</option>
              <option value="medium">{t('bookmark.priority_med', 'Medium')}</option>
              <option value="high">{t('bookmark.priority_high', 'High')}</option>
            </select>
          </label>
          <label className="fx-bookmark-span2">
            {t('bookmark.notes', 'Notes')}
            <textarea
              className="fx-input fx-bookmark-notes"
              rows={2}
              value={form.notes}
              onChange={(e) => patchForm('notes', e.target.value)}
              placeholder={t('bookmark.notes_ph', 'Observation, finding, or chain-of-custody detail…')}
            />
          </label>
          <label>
            {t('bookmark.tags', 'Tags (comma-separated)')}
            <input
              className="fx-input"
              value={form.tags}
              onChange={(e) => patchForm('tags', e.target.value)}
              placeholder={t('bookmark.tags_ph', 'enhancement, region-a')}
            />
          </label>
          <label>
            {t('bookmark.examiner', 'Examiner')}
            <input
              className="fx-input"
              value={form.examiner}
              onChange={(e) => patchForm('examiner', e.target.value)}
            />
          </label>
          <label>
            {t('bookmark.case_ref', 'Case reference')}
            <input
              className="fx-input"
              value={form.case_ref}
              onChange={(e) => patchForm('case_ref', e.target.value)}
            />
          </label>
        </div>

        <div className="fx-export-actions-row">
          <button type="button" className="fx-btn fx-btn-primary" disabled={!path} onClick={() => runAction(saveFrame)}>
            {t('bookmark.save_frame', 'Bookmark this frame')}
          </button>
          <button type="button" className="fx-btn" disabled={!path || !activeFilterId} onClick={() => runAction(saveFilter)}>
            {t('bookmark.save_filter', 'Bookmark current filter')}
          </button>
          {editingId ? (
            <>
              <button type="button" className="fx-btn fx-btn-primary" onClick={() => runAction(handleSaveEdit)}>
                {t('bookmark.save_edit', 'Save changes')}
              </button>
              <button type="button" className="fx-btn" onClick={cancelEdit}>
                {t('bookmark.cancel_edit', 'Cancel')}
              </button>
            </>
          ) : null}
          <button type="button" className="fx-btn" disabled={!path} onClick={refresh}>
            {loading ? t('bookmark.loading', 'Loading…') : t('bookmark.refresh', 'Refresh list')}
          </button>
        </div>

        <ul className="fx-bookmark-list">
          {bookmarks.length === 0 && !loading && (
            <li className="fx-bookmark-empty">{t('bookmark.empty', 'No bookmarks for this evidence yet.')}</li>
          )}
          {bookmarks.map((bm) => (
            <li key={bm.id} className={editingId === bm.id ? 'fx-bookmark-item editing' : 'fx-bookmark-item'}>
              <div className="fx-bookmark-item-head">
                <span className={`fx-bookmark-type fx-bookmark-type-${bm.bookmark_type || bm.type}`}>
                  {(bm.bookmark_type || bm.type) === 'filter'
                    ? t('bookmark.type_filter', 'FILTER')
                    : t('bookmark.type_frame', 'FRAME')}
                </span>
                <strong>{bm.label || bm.id.slice(0, 8)}</strong>
              </div>
              <div className="fx-bookmark-item-meta">
                {isVideo && bm.time_sec != null ? `${formatTime(bm.time_sec)} · ` : ''}
                {bm.frame_index != null ? `#${bm.frame_index}` : ''}
                {bm.filter_id ? ` · ${filterLabel(bm.filter_id)}` : ''}
              </div>
              {bm.metadata?.notes && (
                <p className="fx-bookmark-item-notes">{bm.metadata.notes}</p>
              )}
              {Array.isArray(bm.metadata?.tags) && bm.metadata.tags.length > 0 && (
                <div className="fx-bookmark-tags">
                  {bm.metadata.tags.map((tag) => (
                    <span key={tag} className="fx-bookmark-tag">{tag}</span>
                  ))}
                </div>
              )}
              <div className="fx-bookmark-item-actions">
                <button type="button" className="fx-btn fx-btn-primary" disabled={!sessionId} onClick={() => runAction(() => jumpTo(bm))}>
                  {t('bookmark.jump', 'Go to')}
                </button>
                <button type="button" className="fx-btn" onClick={() => startEdit(bm)}>
                  {t('bookmark.edit', 'Edit')}
                </button>
                <button type="button" className="fx-btn fx-btn-danger" onClick={() => runAction(() => handleDelete(bm.id))}>
                  {t('bookmark.delete', 'Delete')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
