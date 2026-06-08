# Chakshu — Workflow Test Guide

**Document:** End-to-end workflow testing (examiner scenarios)  
**Author:** Mohit M  
**Product:** Chakshu (AI-IVE) v1.0.0  
**Date:** 2026-05-29  

**Related docs**

| Document | Purpose |
|----------|---------|
| [`REQUIREMENTS-TEST-GUIDE.md`](REQUIREMENTS-TEST-GUIDE.md) | Test by requirement ID (R-001 … R-196) |
| [`REQUIREMENTS-TEST-CHECKLIST.md`](REQUIREMENTS-TEST-CHECKLIST.md) | Printable checkbox list per requirement |
| [`REQUIREMENTS-COMPLIANCE.md`](REQUIREMENTS-COMPLIANCE.md) | Compliance matrix |
| [`../examples/workflows/`](../examples/workflows/) | Reference YAML workflows |

This guide tests **Chakshu the way an examiner uses it** — intake → examine → mark up → export → report → custody — not requirement-by-requirement.

---

## How to use this document

1. Start API + UI (Section 1).
2. Prepare the **test data kit** (Section 2).
3. Run workflows **WF-01 → WF-12** in order for a full regression, or pick workflows matching your release scope.
4. Mark each workflow **PASS / FAIL / BLOCKED** on the sign-off sheet (Section 14).
5. For automation, run `./scripts/run-requirements-smoke.sh` after **WF-01** (API health).

**Time estimates** (experienced tester, sample files local):

| Scope | Workflows | ~Duration |
|-------|-----------|-----------|
| Smoke | WF-01, WF-02, WF-05 | 20 min |
| Standard | WF-01 – WF-07 | 60 min |
| Full | WF-01 – WF-12 | 2–3 hr |

---

## 1. Environment setup

### 1.1 Start services

```bash
# Terminal 1
cd ~/Desktop/AI-IVE
source .venv/bin/activate
export PYTHONPATH=src
python -m aive.api.server

# Terminal 2
cd ~/Desktop/AI-IVE/frontend
npm run dev
```

| Service | URL |
|---------|-----|
| UI | http://127.0.0.1:9451 |
| API / Swagger | http://127.0.0.1:9450/docs |

### 1.2 Pre-flight checks

| Step | Action | Pass if |
|------|--------|---------|
| 1 | Open UI | Command Center loads; case number visible |
| 2 | Status bar | No “API offline” error |
| 3 | `GET /api/health` | `"opencv": true`, `"ffmpeg": true` |
| 4 | Command Center stats | Filter count > 140 |

---

## 2. Test data kit

Create a folder `~/Desktop/chakshu-test-data/`:

| File | Spec | Used in |
|------|------|---------|
| `still.jpg` | Any JPEG ≥ 800×600 | WF-02, WF-04 |
| `still-noisy.jpg` | Heavy JPEG compression | WF-09 (artifact filter) |
| `clip.mp4` | H.264, 10–30 s, with audio | WF-03, WF-06, WF-08, WF-09 |
| `clip-b.mp4` | Similar scene, slight time offset | WF-08 (sync) |
| `subs.srt` | 3+ cues synced to clip | WF-09 |
| `audio.aac` | Extracted or separate audio | WF-09 (merge) |
| `export/` | Empty output directory | All export workflows |

---

## 3. Workflow index

| ID | Workflow | Primary UI tabs | Covers (requirements) |
|----|----------|-----------------|------------------------|
| **WF-01** | New case & evidence intake | Command, Examination | R-002, R-040, R-043, R-143 |
| **WF-02** | Image enhancement pipeline | Examination Lab | R-004, R-050, R-052, R-001 |
| **WF-03** | Video timeline examination | Timeline Pro, Examination | R-070–075, R-174, R-175 |
| **WF-04** | Markup, measure & redact | Markup Studio | R-082–085, R-163, R-170–171 |
| **WF-05** | Hash & chain of custody | Forensic Tools, Custody | R-140–144 |
| **WF-06** | Legal export package | Legal Export | R-030–038, R-110 |
| **WF-07** | Live capture intake | Live Capture → Examination | R-180–183 |
| **WF-08** | Compare, MPEG & stream sync | Forensic Tools, Timeline | R-074, R-124, R-172 |
| **WF-09** | Advanced video & subtitles | Forensic Tools | R-121, R-160–165, R-173 |
| **WF-10** | Case report & notes | Case Reports, Forensic Tools | R-130–132, R-195 |
| **WF-11** | Filter pipeline control | Examination Lab | R-050, R-004 (remove one filter) |
| **WF-12** | End-to-end prosecution bundle | All tabs | Full integration |

---

## WF-01 — New case & evidence intake

**Goal:** Examiner opens Chakshu, ingests first evidence item, verifies case linkage.

**Persona:** Digital forensic examiner, day one on a case.

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Open UI | http://127.0.0.1:9451 | Command Center or Examination Lab loads |
| 2 | Command Center | Note case title + case ID | Active case displayed |
| 3 | **Ingest Evidence** | Choose `still.jpg` | Preview appears in Examination Lab |
| 4 | Command Center | Check Evidence Items stat | Count ≥ 1 |
| 5 | Command Center | SHA-256 panel | Hash string visible |
| 6 | **Chain of Custody** | Open tab | INGEST entry for filename |
| 7 | Examination Lab | Load by Path (optional) | Paste full path to `clip.mp4` → Load Path |
| 8 | Examination Lab | Video badge | VIDEO label; scrub bar appears |

### Pass criteria

- [ ] Image and video ingest without error  
- [ ] `storagePath` populated (full path for video tools)  
- [ ] Custody log shows ingest  
- [ ] Evidence hash visible on Command Center  

### Fail / debug

| Symptom | Check |
|---------|--------|
| Video preview blank | FFmpeg installed; re-ingest; use Load by Path |
| No custody entry | Active case exists; re-upload |

---

## WF-02 — Image enhancement pipeline

**Goal:** Non-destructive enhancement with undo, single-filter removal, and reset.

**Reference:** `examples/workflows/image-enhancement.yaml`

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Examination Lab | Ensure `still.jpg` loaded | Preview visible |
| 2 | Filter search | `clahe` → select **CLAHE** | Filter highlighted |
| 3 | **Apply** | Click Apply | Preview contrast improves; pipeline chip #1 |
| 4 | Filter search | `unsharp` → **Unsharp Mask** → Apply | Pipeline chip #2 |
| 5 | Filter search | `dehaze` → **Dehaze** → Apply | Pipeline chip #3 |
| 6 | Pipeline | Click **×** on middle chip (Unsharp) | Preview re-renders without that step; 2 chips remain |
| 7 | **Reset to Original** | Red button | Original image; pipeline empty |
| 8 | Re-apply | CLAHE only → Apply | Single chip; visible change |

### Pass criteria

- [ ] Each filter visibly changes preview  
- [ ] Pipeline chips match applied order  
- [ ] Removing one chip updates preview (others kept)  
- [ ] Reset restores pristine master  

### Advanced filters (optional)

| Filter | Search term | Visual check |
|--------|-------------|--------------|
| Homomorphic | `adv_homomorphic` | Shadow lift on uneven lighting |
| JPEG fix | `adv_jpeg` on `still-noisy.jpg` | Blockiness reduced |
| Super-res | `adv_super_resolution` | Larger/sharper preview |

---

## WF-03 — Video timeline examination

**Goal:** Frame-accurate navigation, I/P/B awareness, region and audio analysis.

**Reference:** `examples/workflows/video-timeline.yaml`

### Prerequisites

- `clip.mp4` loaded with **full storage path** (re-ingest if path missing)

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | **Timeline Pro** | Open tab | Timeline canvas or “build” prompt |
| 2 | Timeline Pro | Build / refresh index if needed | Frame count, I/P/B summary in status |
| 3 | Timeline Pro | Click a frame tick | Preview updates; timecode + frame # in sidebar |
| 4 | Timeline Pro | Shift+drag region on timeline | Region start/end fields update |
| 5 | Timeline Pro | **Analyze Region** | Frame count + I/P/B for region |
| 6 | Timeline Pro | **Probe** (audio) | Channel layout listed |
| 7 | Timeline Pro | **A/V Offset** | Offset ms in status bar |
| 8 | Examination Lab | Scrub → **Load Frame at Time** | Server-side frame matches scrub time |
| 9 | Examination Lab | **Nearest I-Frame** | Jump to I-frame preview |
| 10 | Stream Analysis | Analyze I/P/B Frames | Summary table I/P/B counts |

### Pass criteria

- [ ] Timeline index builds (≥ 10 frames sampled)  
- [ ] Clicking timeline updates preview and metadata  
- [ ] Region analysis returns counts  
- [ ] I-frame seek differs from arbitrary time seek  

---

## WF-04 — Markup, measure & redact

**Goal:** Annotate frame, measure distance, redact PII, burn into master.

**Reference:** Phase 3 / Markup Studio

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Examination Lab | Load frame (image or video frame at 2 s) | Preview ready |
| 2 | **Markup Studio** | Open tab | Canvas over image |
| 3 | **Arrow** tool | Click-drag diagonal line | Line on canvas overlay |
| 4 | **Rectangle** tool | Draw box | Rect on overlay |
| 5 | **Text** tool | Click → enter “Suspect A” | Label on overlay |
| 6 | **Measure** | Set calibration 50 px = 1 cm → draw line | Distance label on canvas |
| 7 | Snap | Enable **Snap 10px** → draw | Points align to grid |
| 8 | Group | Group ID `scene-1` → add line | Listed under annotations |
| 9 | **Apply to Frame** | Burn button | Annotations in preview; overlay clears |
| 10 | Examination Lab | Apply a filter after burn | Annotation still visible (burned) |
| 11 | **Redact** tool | Draw over face region | Pixelated on master immediately |

### Pass criteria

- [ ] Shapes visible on canvas before burn  
- [ ] Apply to Frame persists marks in preview  
- [ ] Measure shows numeric label  
- [ ] Redact pixelates region  
- [ ] Annotation list shows saved items (sidebar)  

---

## WF-05 — Hash verification & chain of custody

**Goal:** Prove integrity before and after processing.

**Reference:** `examples/workflows/hash-custody.yaml`

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Forensic Tools | Set path = `clip.mp4` full path | Path in input |
| 2 | **Hash Evidence File** | Click | MD5, SHA-1, SHA-256, SHA-512 displayed |
| 3 | **Copy Hashes** | Click | Clipboard populated |
| 4 | **Secure Copy + Report** | Output dir = `~/Desktop/chakshu-test-data/export` | Copy + JSON report |
| 5 | Examination Lab | Apply any filter | Enhancement applied |
| 6 | Forensic Tools | **Copy Frame to Clipboard** | Data URL copied (image loaded) |
| 7 | **Chain of Custody** | Open tab | INGEST + ENHANCE entries |
| 8 | API (optional) | `GET /api/forensics/cases/{id}/audit` | FILTER_APPLY events |

### Pass criteria

- [ ] All four file hashes computed  
- [ ] Secure copy report verifies or documents hashes  
- [ ] Custody shows enhancement after filter apply  
- [ ] Frame hash API works when session has frame  

---

## WF-06 — Legal export package

**Goal:** Produce court-ready outputs from examined media.

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | **Legal Export** | Open tab | Paths panel + PDF layout panel visible |
| 2 | **Output configuration** | Set output directory (e.g. `~/Desktop/chakshu-test-data/export`); optional **Use case subfolder**; **Save paths to project** | Derived PDF / I-frame / audio paths shown |
| 2b | Source path | `input_path` = `clip.mp4` (auto after ingest) | Source field filled |
| 3 | **PDF frame layout** | Set page size (e.g. Legal), landscape, 3×2 grid, margin 18 mm, custom title | Grid hint shows 6 frames/page |
| 4 | **Export Frames to PDF** | After frame loaded in Examination Lab | PDF created at pdf_path with chosen layout |
| 5 | **Export I-Frames** | Run | JPEGs in i_frames_dir |
| 6 | **Extract Audio** | Run | `.aac` at audio_out |
| 7 | **Export Examination Bundle** | Run | Folder with bundle artifacts |
| 8 | Disk check | Open output folder | All files present and playable |

### Pass criteria

- [ ] PDF opens with at least one frame; page size/orientation match settings  
- [ ] PDF header shows custom title when set  
- [ ] I-frame JPEGs exist (count > 0 for typical GOP)  
- [ ] Audio file plays  
- [ ] Bundle contains original and/or processed per settings  

---

## WF-07 — Live capture intake

**Goal:** Capture live source into examination pipeline.

**Reference:** `examples/workflows/live-capture.yaml`

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | **Live Capture** | Open tab | Webcam / device options |
| 2 | Browser mode | **Start Camera** → allow permission | Live preview |
| 3 | **Snap Frame** | Capture | Redirected / status: ingested |
| 4 | Examination Lab | Verify preview | Captured frame shown |
| 5 | Live Capture | Backend device (if camera index 0) | Snapshot ingests |
| 6 | Live Capture | Optional live filter on stream | MJPEG with filter (backend) |
| 7 | Screen capture | 5 s screen → path | MP4 file on disk |

### Pass criteria

- [ ] At least one capture method works (browser or backend)  
- [ ] Captured frame usable in Examination / Markup  
- [ ] Screen capture file exists (FFmpeg required)  

---

## WF-08 — Compare, MPEG overlay & stream sync

**Goal:** Multi-source analysis for corroboration.

### Prerequisites

- `clip.mp4` and `clip-b.mp4`

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Forensic Tools | **Probe Video** | Duration, frame count |
| 2 | **Seek Time** at 1.0 s | Preview at timestamp | Frame displayed |
| 3 | **Nearest I-Frame** | Preview jumps | Different/adjacent I-frame |
| 4 | **MPEG Macroblock Overlay** | Overlay on preview | Block grid visualization |
| 5 | **Start Side-by-Side** | Second path = `clip-b.mp4` | Compare session ID |
| 6 | **Render Compare** | Same seek time both sides | Combined preview |
| 7 | **Find Stream Offset** | clip vs clip-b | `recommended_offset_ms` in status |
| 8 | Timeline Pro | Load secondary (API) optional | Secondary registered |

### Pass criteria

- [ ] Macroblock overlay visible  
- [ ] Compare render produces dual view  
- [ ] Sync returns score and offset suggestion  

---

## WF-09 — Advanced video processing & subtitles

**Goal:** Post-process video for clarity and presentation.

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Forensic Tools | Path = `clip.mp4`, output_dir set | Ready |
| 2 | **Stabilize** | Run | `stabilized.mp4` in output dir |
| 3 | **Reverse** | Run | `reversed.mp4` plays backward |
| 4 | **Adjust FPS** → 15 | Run | Shorter/choppier clip |
| 5 | Subtitle panel | SRT path + font size 22 | Fields set |
| 6 | **Burn Subtitles** | Run | Subtitled MP4 with visible captions |
| 7 | **Merge Video + Audio** | Point to `audio.aac` | Muxed MP4 |
| 8 | **Concat Videos** | Append `clip-b.mp4` | Longer concatenated file |

### Pass criteria

- [ ] At least 2 of 4 advanced video ops succeed (stabilize may need vidstab)  
- [ ] Subtitled output shows burned captions  
- [ ] Merge / concat outputs play in VLC  

---

## WF-10 — Case report & examiner notes

**Goal:** Document findings for supervisor / court packet.

### Steps

| # | Tab / action | Details | Expected result |
|---|--------------|---------|-----------------|
| 1 | Forensic Tools | Add note: “Enhancement applied CLAHE @ frame 0” | Note saved |
| 2 | Forensic Tools | Notes list | Note visible with timestamp |
| 3 | **Case Reports** | Open tab | Report generator |
| 4 | Generate report | Template: **detailed**, formats HTML + PDF | Files in output dir |
| 5 | Open HTML report | Browser | Case info, steps documented |
| 6 | Open PDF report | Viewer | Printable layout |
| 7 | Command Center | Example workflow card | Steps list loads |

### Pass criteria

- [ ] Note persists after tab switch  
- [ ] Report HTML + PDF generated  
- [ ] Report references case / examiner fields  

---

## WF-11 — Filter pipeline control (regression)

**Goal:** Verify per-filter removal (Phase 7 feature).

### Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Apply filters A → B → C | 3 pipeline chips |
| 2 | Remove chip B (×) | Preview without B; A + C remain |
| 3 | Remove chip A | Only C remains |
| 4 | Reset to Original | Clean master |

### Pass criteria

- [ ] Order preserved when removing middle filter  
- [ ] No need to reset entire pipeline  

---

## WF-12 — End-to-end prosecution bundle (integration)

**Goal:** Single narrative from intake to deliverables — use for release sign-off.

### Scenario

*Examiner receives CCTV still + clip, enhances, marks suspect, verifies hash, exports package, writes report.*

| Phase | Workflow refs | Key deliverable |
|-------|---------------|-----------------|
| Intake | WF-01 | Evidence in case + custody |
| Still enhance | WF-02 | Enhanced still in session |
| Markup | WF-04 | Burned annotations |
| Video review | WF-03 | Timeline notes + region stats |
| Integrity | WF-05 | Hash report + secure copy |
| Export | WF-06 | PDF + I-frames + audio |
| Advanced | WF-09 | Stabilized clip (optional) |
| Document | WF-10 | Case report PDF |
| Review | WF-05 step 7 | Custody complete |

### Pass criteria (integration)

- [ ] All phases complete without manual API calls  
- [ ] Output folder contains: PDF, I-frames, report, optional stabilized MP4  
- [ ] Custody log shows ingest → enhance → (export if logged)  
- [ ] No uncaught UI errors in status bar  

**Suggested duration:** 45–60 minutes.

---

## 4. Workflow ↔ requirement map (quick reference)

| Workflow | Primary requirement IDs |
|----------|-------------------------|
| WF-01 | R-002, R-040, R-043, R-143, R-144 |
| WF-02 | R-001, R-004, R-050, R-052, R-150–167 |
| WF-03 | R-010, R-070–075, R-174, R-175 |
| WF-04 | R-082–085, R-163, R-170–171 |
| WF-05 | R-134, R-140–144 |
| WF-06 | R-030–038, R-110, R-193 |
| WF-07 | R-180–183 |
| WF-08 | R-074, R-075, R-124, R-172 |
| WF-09 | R-121, R-160–165, R-173 |
| WF-10 | R-130–132, R-195, R-196 |
| WF-11 | R-004, R-050 |
| WF-12 | Cross-cutting |

---

## 5. Automation alignment

After manual **WF-01**, run:

```bash
SAMPLE_IMAGE=~/Desktop/chakshu-test-data/still.jpg \
SAMPLE_VIDEO=~/Desktop/chakshu-test-data/clip.mp4 \
SAMPLE_SRT=~/Desktop/chakshu-test-data/subs.srt \
SAMPLE_VIDEO_B=~/Desktop/chakshu-test-data/clip-b.mp4 \
./scripts/run-requirements-smoke.sh
```

Maps loosely to: WF-01 (session/case), WF-02 (filters), WF-04 (markup), WF-03/08 (video/timeline), WF-05 (hash), WF-09 (advanced/subtitles).

---

## WF-13 — Localization & accessibility (R-100, R-101)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Sidebar → change **Language** to **हिन्दी (Hindi)** | Nav labels in Hindi (Devanagari) |
| 2 | Switch to **मराठी (Marathi)** or **ગુજરાતી (Gujarati)** | Labels update in respective script |
| 3 | Enable **High contrast** + **Protanopia** | UI contrast and accent colors change |
| 4 | **Case Reports** → Generate report | `locale` matches UI language |
| 5 | Open generated HTML | `lang` attribute and table headers localized (hi / mr / gu) |

API checks:

```bash
curl -s http://127.0.0.1:9450/api/i18n/locales
curl -s http://127.0.0.1:9450/api/i18n/hi | head -c 300
curl -s http://127.0.0.1:9450/api/i18n/mr | head -c 300
curl -s http://127.0.0.1:9450/api/i18n/gu | head -c 300
```

---

## 6. Known limitations (expect during test)

| Area | Limitation | Workaround |
|------|------------|------------|
| Video path | Must be full saved path for tools | Re-ingest or Load by Path |
| Stabilize | vidstab may be missing in FFmpeg | deshake fallback; note in report |
| R-145 / R-157 | Secure batch / multi-image align | Not in UI — skip |
| Multi-video UI | Secondary stream API only | WF-08 API step |
| Clipboard | Browser permission for Copy Frame | Allow clipboard when prompted |

---

## 7. Troubleshooting

| Issue | Fix |
|-------|-----|
| API offline | Start `python -m aive.api.server`; check port 9450 |
| OpenCV false | Python 3.12 venv; `./scripts/install.sh -y` |
| Markup not visible | Use Markup Studio; Apply to Frame; check storagePath |
| Timeline empty | Build index; confirm video path absolute |
| Export fails | Create output dir; check FFmpeg |

---

## 8. Printable workflow checklist

Copy for test runs:

```
Date: __________  Tester: __________  Build: __________

☐ WF-01  New case & intake          ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-02  Image enhancement          ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-03  Video timeline             ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-04  Markup & redact            ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-05  Hash & custody             ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-06  Legal export               ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-07  Live capture               ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-08  Compare & sync             ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-09  Advanced video             ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-10  Report & notes             ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-11  Filter pipeline            ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-12  End-to-end bundle          ☐ PASS  ☐ FAIL  Notes: ___________
☐ WF-13  i18n & accessibility       ☐ PASS  ☐ FAIL  Notes: ___________ ☐ PASS  ☐ FAIL
Approver: __________  Date: __________
```

---

## 9. Document maintenance

| Change | Update |
|--------|--------|
| New UI tab or workflow | Add WF-XX section + index row |
| Example YAML added | Link in workflow header |
| Feature removed | Mark workflow step N/A |

**Prepared by:** Mohit M  
**Next review:** Each release tag
