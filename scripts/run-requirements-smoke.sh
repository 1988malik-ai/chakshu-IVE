#!/usr/bin/env bash
# Chakshu requirements API smoke test
# Usage:
#   ./scripts/run-requirements-smoke.sh
#   SAMPLE_IMAGE=~/Desktop/sample.jpg SAMPLE_VIDEO=~/Desktop/sample.mp4 ./scripts/run-requirements-smoke.sh
#
# Requires API running: python -m aive.api.server

set -uo pipefail

BASE="${CHAKSHU_API:-http://127.0.0.1:9450}"
PASS=0
FAIL=0
SKIP=0
SESSION=""
TMPDIR="${TMPDIR:-/tmp}/chakshu-smoke-$$"
mkdir -p "$TMPDIR"

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "${GRN}PASS${NC}  $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}FAIL${NC}  $1 — $2"; FAIL=$((FAIL + 1)); }
skip() { echo -e "${YLW}SKIP${NC}  $1 — $2"; SKIP=$((SKIP + 1)); }

# $1=id $2=method $3=path [$4=extra curl args]
check_http() {
  local id="$1" method="$2" path="$3"
  shift 3
  local code
  code=$(curl -s -o "$TMPDIR/out.json" -w "%{http_code}" -X "$method" "$BASE$path" "$@")
  if [[ "$code" =~ ^2 ]]; then
    pass "$id"
    return 0
  fi
  fail "$id" "HTTP $code"
  return 1
}

check_json_field() {
  local id="$1" field="$2" expect="$3"
  if python3 -c "
import json, sys
d=json.load(open('$TMPDIR/out.json'))
v=d
for part in '$field'.split('.'):
    if part.isdigit():
        v=v[int(part)]
    else:
        v=v.get(part) if isinstance(v, dict) else None
    if v is None:
        sys.exit(1)
if '$expect' == 'truthy':
    sys.exit(0 if v else 1)
if '$expect' == 'positive':
    sys.exit(0 if (isinstance(v,(int,float)) and v>0) or (isinstance(v,str) and len(v)>0) else 1)
sys.exit(0 if str(v)==('$expect') else 1)
" 2>/dev/null; then
    pass "$id (field $field)"
  else
    fail "$id (field $field)" "expected $expect"
  fi
}

echo "=============================================="
echo " Chakshu Requirements Smoke Test"
echo " API: $BASE"
echo " $(date)"
echo "=============================================="
echo ""

# --- Core (no media) ---
echo "--- Section 1: Core ---"
check_http "R-001 filters" GET "/api/filters" && check_json_field "R-001 count" "count" "positive"
check_http "R-003 license" GET "/api/license/status" && check_json_field "R-003 machine_id" "machine_id" "truthy"
check_http "R-060 gpu" GET "/api/gpu/encoders"
check_http "health" GET "/api/health" && check_json_field "health status" "status" "ok"

check_http "R-002 session" POST "/api/session" && SESSION=$(python3 -c "import json; print(json.load(open('$TMPDIR/out.json'))['session_id'])" 2>/dev/null || true)
[[ -n "$SESSION" ]] && pass "session_id captured" || fail "session_id captured" "empty"

echo ""
echo "--- Section 3: Projects / Case ---"
check_http "R-021 project" GET "/api/project/current"
check_http "R-143 active case" GET "/api/forensics/cases/active" && check_json_field "R-143 case_id" "case_id" "truthy"
check_http "R-020 bookmarks" GET "/api/bookmarks"
check_http "R-196 examples" GET "/api/capture/examples"

echo ""
echo "--- Section 11/19: i18n / reports templates ---"
check_http "R-100 i18n es" GET "/api/i18n/es"
check_http "R-130 templates" GET "/api/reports/templates"

# --- Media-dependent ---
if [[ -n "${SAMPLE_IMAGE:-}" && -f "$SAMPLE_IMAGE" ]]; then
  echo ""
  echo "--- Media tests (image: $SAMPLE_IMAGE) ---"
  check_http "upload image" POST "/api/media/upload?session_id=$SESSION" -F "file=@$SAMPLE_IMAGE"

  check_http "R-004 apply filter" POST "/api/filters/apply" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\",\"filter_id\":\"clr_brightness\",\"params\":{\"amount\":0.3}}"

  check_http "R-050 undo" POST "/api/edit/undo" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\"}"

  check_http "R-141 frame hash" GET "/api/capabilities/hash/frame?session_id=$SESSION&algorithm=sha256"

  check_http "R-134 clipboard frame" GET "/api/capabilities/clipboard/frame?session_id=$SESSION"

  check_http "R-083 markup add" POST "/api/markup/annotations" \
    -H "Content-Type: application/json" \
    -d "{\"media_id\":\"$SAMPLE_IMAGE\",\"type\":\"arrow\",\"frame_index\":0,\"points\":[[10,10],[80,80]],\"image_width\":640,\"image_height\":480}"

  check_http "R-083 markup render" POST "/api/markup/render" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\",\"media_id\":\"$SAMPLE_IMAGE\",\"frame_index\":0,\"persist\":false}"

  check_http "R-154 adv filter" POST "/api/filters/apply" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\",\"filter_id\":\"adv_auto_contrast\",\"params\":{}}"

  check_http "R-050 redo" POST "/api/edit/redo" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\"}"

  check_http "R-052 reset" POST "/api/forensics/examination/reset" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\"}"

  check_http "R-140 hash file" POST "/api/capabilities/hash/file" \
    -H "Content-Type: application/json" \
    -d "{\"path\":\"$SAMPLE_IMAGE\"}"

  OUT_PDF="$TMPDIR/smoke-frames.pdf"
  check_http "R-034 pdf export" POST "/api/export/pdf-frames" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\",\"output_path\":\"$OUT_PDF\",\"title\":\"Smoke Test\"}"
  [[ -f "$OUT_PDF" ]] && pass "R-034 pdf file exists" || fail "R-034 pdf file exists" "missing $OUT_PDF"
else
  skip "image tests" "set SAMPLE_IMAGE=/path/to/sample.jpg"
fi

if [[ -n "${SAMPLE_VIDEO:-}" && -f "$SAMPLE_VIDEO" ]]; then
  echo ""
  echo "--- Media tests (video: $SAMPLE_VIDEO) ---"
  check_http "R-010 load path" POST "/api/media/load-path" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION\",\"path\":\"$SAMPLE_VIDEO\"}"

  check_http "R-072 analyze video" POST "/api/forensics/examination/analyze-video?path=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SAMPLE_VIDEO'))")"

  check_http "R-075 video info" POST "/api/capabilities/video/info" \
    -H "Content-Type: application/json" \
    -d "{\"path\":\"$SAMPLE_VIDEO\"}"

  check_http "R-070 timeline build" POST "/api/timeline/build" \
    -H "Content-Type: application/json" \
    -d "{\"path\":\"$SAMPLE_VIDEO\",\"limit\":500,\"force_refresh\":false}"

  check_http "R-113 audio channels" GET "/api/timeline/audio/channels?path=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SAMPLE_VIDEO'))")"

  check_http "R-074 mpeg viz" POST "/api/capabilities/mpeg/visualize?mode=macroblock" \
    -H "Content-Type: application/json" \
    -d "{\"path\":\"$SAMPLE_VIDEO\",\"time_sec\":0.5}"

  OUT_TRIM="$TMPDIR/trim.mp4"
  check_http "R-037 trim" POST "/api/capabilities/video/trim" \
    -H "Content-Type: application/json" \
    -d "{\"input_path\":\"$SAMPLE_VIDEO\",\"output_path\":\"$OUT_TRIM\",\"start_sec\":0,\"end_sec\":1}"

  if [[ -n "${SAMPLE_VIDEO_B:-}" && -f "$SAMPLE_VIDEO_B" ]]; then
    check_http "R-172 stream sync" POST "/api/capabilities/sync/similarity" \
      -H "Content-Type: application/json" \
      -d "{\"path_a\":\"$SAMPLE_VIDEO\",\"path_b\":\"$SAMPLE_VIDEO_B\",\"time_a\":0,\"search_sec\":1}"
  else
    skip "R-172 dual video" "set SAMPLE_VIDEO_B for sync test"
  fi

  OUT_STABLE="$TMPDIR/stable.mp4"
  check_http "R-160 stabilize" POST "/api/capabilities/advanced/stabilize" \
    -H "Content-Type: application/json" \
    -d "{\"input_path\":\"$SAMPLE_VIDEO\",\"output_path\":\"$OUT_STABLE\",\"smoothing\":5}" || true
  # stabilize may fail without vidstab — don't count as hard fail for CI

  if [[ -n "${SAMPLE_SRT:-}" && -f "$SAMPLE_SRT" ]]; then
    OUT_SUB="$TMPDIR/subtitled.mp4"
    check_http "R-121 subtitle burn" POST "/api/capabilities/subtitles/burn" \
      -H "Content-Type: application/json" \
      -d "{\"video_path\":\"$SAMPLE_VIDEO\",\"subtitle_path\":\"$SAMPLE_SRT\",\"output_path\":\"$OUT_SUB\",\"font_size\":20}"
  else
    skip "R-121 subtitles" "set SAMPLE_SRT=/path/to/sample.srt"
  fi
else
  skip "video tests" "set SAMPLE_VIDEO=/path/to/sample.mp4"
fi

echo ""
echo "--- Planned (expect skip) ---"
skip "R-145 secure batch" "PLANNED — no API"
skip "R-157 multi-image align" "PLANNED — no API"

echo ""
echo "=============================================="
echo " Results: ${GRN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YLW}$SKIP skipped${NC}"
echo " Temp:   $TMPDIR"
echo " Full guide: docs/REQUIREMENTS-TEST-GUIDE.md"
echo " Checklist:  docs/REQUIREMENTS-TEST-CHECKLIST.md"
echo "=============================================="

rm -rf "$TMPDIR" 2>/dev/null || true
[[ "$FAIL" -eq 0 ]]
