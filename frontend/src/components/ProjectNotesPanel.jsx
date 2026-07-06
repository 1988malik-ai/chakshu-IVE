import { useState } from 'react';

function formatTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return iso;
  }
}

export default function ProjectNotesPanel({
  collapsed,
  onToggleCollapse,
  projectName,
  projectId,
  notes,
  author,
  evidenceId,
  frameIndex,
  timeSec,
  onAdd,
  onDelete,
  onRefresh,
  t,
}) {
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [linkEvidence, setLinkEvidence] = useState(true);

  const handleSave = async () => {
    if (!draft.trim() || saving) return;
    setSaving(true);
    try {
      await onAdd({
        body: draft.trim(),
        author: author || 'examiner',
        evidence_id: linkEvidence && evidenceId ? evidenceId : null,
        frame_index: linkEvidence && frameIndex != null ? frameIndex : null,
        time_sec: linkEvidence && timeSec != null ? timeSec : null,
      });
      setDraft('');
    } finally {
      setSaving(false);
    }
  };

  if (collapsed) {
    return (
      <aside className="fx-notes-rail fx-notes-rail-collapsed" aria-label={t('panel.notes', 'Examination Notes')}>
        <button
          type="button"
          className="fx-notes-expand-btn"
          onClick={onToggleCollapse}
          title={t('notes.show', 'Show notes')}
          aria-label={t('notes.show', 'Show notes')}
        >
          Notes
        </button>
      </aside>
    );
  }

  return (
    <aside className="fx-notes-rail" aria-label={t('panel.notes', 'Examination Notes')}>
      <header className="fx-notes-head">
        <div>
          <h2>{t('panel.notes', 'Examination Notes')}</h2>
          <p className="fx-notes-sub" title={projectId}>{projectName || t('notes.project', 'Project')}</p>
        </div>
        <button
          type="button"
          className="fx-notes-collapse-btn"
          onClick={onToggleCollapse}
          title={t('notes.hide', 'Hide notes')}
          aria-label={t('notes.hide', 'Hide notes')}
        >
          ×
        </button>
      </header>

      <div className="fx-notes-compose">
        <textarea
          className="fx-input"
          rows={4}
          value={draft}
          placeholder={t('notes.placeholder', 'Observation, finding, or chain-of-custody note…')}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSave();
          }}
        />
        <label className="fx-notes-link-ev">
          <input
            type="checkbox"
            checked={linkEvidence}
            onChange={(e) => setLinkEvidence(e.target.checked)}
          />
          {t('notes.link_evidence', 'Link to current evidence')}
        </label>
        <div className="fx-notes-compose-actions">
          <button type="button" className="fx-btn fx-btn-primary" disabled={!draft.trim() || saving} onClick={handleSave}>
            {t('action.save_note', 'Save Note')}
          </button>
          <button type="button" className="fx-btn" onClick={onRefresh}>
            {t('notes.refresh', 'Refresh')}
          </button>
        </div>
        <p className="fx-notes-hint">{t('notes.hint', 'Saved to project — persists in .aive.yaml on project save')}</p>
      </div>

      <ul className="fx-notes-list">
        {notes.length === 0 && (
          <li className="fx-notes-empty">{t('notes.empty', 'No notes yet for this project.')}</li>
        )}
        {notes.map((n) => (
          <li key={n.note_id} className="fx-notes-item">
            <div className="fx-notes-item-meta">
              <span>{formatTime(n.timestamp)}</span>
              <span>{n.author}</span>
            </div>
            <p className="fx-notes-item-body">{n.body}</p>
            {(n.evidence_id || n.frame_index != null) && (
              <div className="fx-notes-item-ctx">
                {n.evidence_id && <span title={n.evidence_id}>EV linked</span>}
                {n.frame_index != null && <span>Frame #{n.frame_index}</span>}
                {n.time_sec != null && <span>@ {Number(n.time_sec).toFixed(2)}s</span>}
              </div>
            )}
            <button type="button" className="fx-notes-delete" onClick={() => onDelete(n.note_id)}>
              {t('notes.delete', 'Delete')}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
