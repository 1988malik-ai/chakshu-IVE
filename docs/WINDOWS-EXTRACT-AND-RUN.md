# Chakshu on Windows — extract and run

**No Python. No Node. No Setup-Chakshu.bat.**

---

## Recommended: native Windows app (no browser)

| Step | Action |
|------|--------|
| 1 | Get **`Chakshu-Native-1.0.0.exe`** (one file) |
| 2 | Double-click it |
| 3 | Chakshu opens in its **own window** (Electron) |

To stop: close the Chakshu window.

### How to get `Chakshu-Native-1.0.0.exe`

| Method | Steps |
|--------|--------|
| **GitHub Actions** | Actions → **Build Windows installer** → download artifact **`Chakshu-Native`** |
| **Build once on Windows** | `Install-Prerequisites.bat` → **`Build-Native.bat`** → copy `release\Chakshu-Native-1.0.0.exe` |

If SmartScreen warns: **More info → Run anyway** (unsigned build).

---

## Alternative: browser mode (lighter zip)

| Step | Action |
|------|--------|
| 1 | Unzip **`Chakshu-Portable.zip`** |
| 2 | Double-click **`Run-Chakshu.bat`** |
| 3 | Opens in **Chrome/Edge** at http://127.0.0.1:9450 |

Get zip from GitHub artifact **`Chakshu-Portable`**, or run **`Build-Portable.bat`** once.

```text
Chakshu-Portable/
  Run-Chakshu.bat
  aive-api.exe
  frontend-dist/
```

---

## Optional: installed app (Start Menu shortcut)

From GitHub Actions, download **`Chakshu-Windows-Setup`** → run **`Chakshu-Setup-1.0.0.exe`**.

Installs **Chakshu Forensics** to Start Menu / Desktop (native window, same as Native exe).

---

## Old dev setup (only if you edit code)

| File | When |
|------|------|
| `Install-Prerequisites.bat` | Need Python + Node |
| `Setup-Chakshu.bat` | First-time dev install |
| `Run-Chakshu.bat` | Dev mode from source |

For daily use, prefer **`Chakshu-Portable.zip`**.

See also: [`WINDOWS-QUICKSTART.md`](WINDOWS-QUICKSTART.md) · [`COPY-TO-WINDOWS.md`](COPY-TO-WINDOWS.md)
