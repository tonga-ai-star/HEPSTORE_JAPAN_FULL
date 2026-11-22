#!/usr/bin/env bash
# Screenshot HTML snapshots produced by smoke_routes.py at desktop and true mobile width.
# Usage: screens.sh <snapshot_dir> <out_dir> [page names...]
# Headless Chrome cannot open a window narrower than 500px, so mobile shots load the
# page inside a 390px iframe in a 500px window; the strip right of 390px is padding.
# Set HEP_THEME=dark to force dark mode.
set -u
SNAP=$(cd "$1" && pwd); OUT=$2; shift 2
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
PAGES=${*:-home catalog book_detail cart_full checkout scan_found m_dashboard m_orders m_pos m_social}
CHROME=$(command -v google-chrome || command -v chromium || command -v chromium-browser)
[ -z "$CHROME" ] && { echo "Không tìm thấy Chrome"; exit 2; }
THEME=${HEP_THEME:-light}; SUFFIX=""; [ "$THEME" = dark ] && SUFFIX="_dark"
FLAGS=(--headless=new --disable-gpu --no-sandbox --hide-scrollbars --allow-file-access-from-files
       --virtual-time-budget=4000 --force-prefers-reduced-motion --blink-settings=preferredColorScheme=$([ "$THEME" = dark ] && echo 0 || echo 1))
shoot(){ timeout 60 "$CHROME" "${FLAGS[@]}" --window-size="$1" --screenshot="$2" "$3" >/dev/null 2>&1 && echo "chụp $2" || echo "LỖI chụp $2"; }
for p in $PAGES; do
  f="$SNAP/$p.html"; [ -f "$f" ] || { echo "bỏ qua $p (không có snapshot)"; continue; }
  shoot 1440,2200 "$OUT/${p}_desktop$SUFFIX.png" "file://$f"
  wrap="$SNAP/.m_$p.html"
  printf '<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#888}iframe{width:390px;height:2400px;border:0;display:block;background:#fff}</style><iframe src="file://%s"></iframe>' "$f" > "$wrap"
  shoot 500,2400 "$OUT/${p}_mobile$SUFFIX.png" "file://$wrap"
done
