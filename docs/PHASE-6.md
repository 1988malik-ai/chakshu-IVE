# Phase 6 — Advanced Processing (Section 16)

**Author:** Mohit M  
**Status:** Done

## Scope

Implements the largest compliance gap — **Advanced Video / Image Processing** (R-150–R-167).

## Modules

| Module | Requirements | Description |
|--------|--------------|-------------|
| `src/aive/filters/advanced.py` | R-150–R-159, R-166–R-167 | Frame-level deinterlace, homomorphic, deblur, JPEG de-artifact, channel ops, lens correction, super-res, panorama preview |
| `src/aive/video/advanced.py` | R-150, R-158–R-165 | FFmpeg pipelines: deinterlace, stabilize, FPS adjust, freeze, reverse |
| `src/aive/api/routes_capabilities.py` | R-158–R-165 | `/api/capabilities/advanced/*` endpoints |

## New catalog filters

- `adv_homomorphic`, `adv_auto_contrast`, `adv_color_separate`
- `adv_motion_deblur`, `adv_jpeg_artifact`, `adv_channel_replace`
- `adv_super_resolution`, `adv_panorama`, `adv_deinterlace`, `adv_interlace`
- `adv_perspective`, `rst_jpeg_artifact`

## API endpoints

```
POST /api/capabilities/advanced/fps-adjust     # R-161, R-162
POST /api/capabilities/advanced/reverse        # R-165
POST /api/capabilities/advanced/freeze         # R-164
POST /api/capabilities/advanced/deinterlace    # R-150 (video)
POST /api/capabilities/advanced/stabilize      # R-160
POST /api/capabilities/advanced/perspective-stabilize  # R-158
```

## Remaining gaps

- **R-158** Perspective stabilization — preview/frame-level workflow exists; full multi-frame tracking polish remains deferred

## Run

Existing filter apply path picks up advanced operators automatically:

```bash
export PYTHONPATH=src
python -m aive.api.server
```

Apply `adv_homomorphic` or `both_deblur_ai` via the Filter panel, or call advanced video endpoints from Forensic Tools / API client.
