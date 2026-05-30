const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '▣' },
  { id: 'studio', label: 'Media Studio', icon: '◫' },
  { id: 'export', label: 'Export Center', icon: '↗' },
  { id: 'reports', label: 'Reports', icon: '▤' },
  { id: 'projects', label: 'Projects', icon: '▦' },
];

export default function Layout({ page, setPage, title, children, status, error, ready }) {
  return (
    <div className="erp-app">
      <aside className="erp-sidebar">
        <div className="erp-brand">
          <h1>AI-IVE</h1>
          <span>Enterprise Media Suite</span>
        </div>
        <nav className="erp-nav">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`erp-nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
            >
              <span className="erp-nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div style={{ padding: 16, fontSize: '0.75rem', color: '#64748b' }}>
          {ready ? '● System Online' : '○ API Offline'}
        </div>
      </aside>
      <div className="erp-main">
        <header className="erp-header">
          <h2>{title}</h2>
          <div className="erp-header-actions">
            <span className="erp-badge">v1.0</span>
            <span className="erp-badge">191 Filters</span>
          </div>
        </header>
        <main className="erp-content">{children}</main>
        <footer className="erp-footer-status">
          {status}
          {error && <span className="erp-error"> — {error}</span>}
        </footer>
      </div>
    </div>
  );
}

export { NAV };
