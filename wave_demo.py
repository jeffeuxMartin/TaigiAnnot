from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path

import requests


def _safe_uid(uid: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(uid))


def _audio_to_data_url(audio_url: str) -> str:
    if audio_url.startswith("data:"):
        return audio_url

    if audio_url.startswith("http://") or audio_url.startswith("https://"):
        r = requests.get(audio_url, timeout=30)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "").split(";")[0].strip() or "audio/wav"
        audio_bytes = r.content
    else:
        path = Path(audio_url)
        audio_bytes = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "audio/wav"

    b64 = base64.b64encode(audio_bytes).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def wavesurfer_html(audio_url: str, uid: str = "wave", regions=None, height: int = 120) -> str:
    regions = regions or []
    uid = _safe_uid(uid)
    regions_json = json.dumps(regions, ensure_ascii=False)
    data_url = _audio_to_data_url(audio_url)

    return f"""
<div>
  <div id="loading_{uid}" style="padding:8px;color:#666;">
    音訊載入中...
  </div>

  <div id="waveform_{uid}"></div>

  <audio
    id="audio_{uid}"
    controls
    src="{data_url}"
    style="width:100%; margin-top:8px; display:none;"
  ></audio>
</div>

<script type="module">
import WaveSurfer from "https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.esm.js";
import RegionsPlugin from "https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.esm.js";

const audioEl_{uid} = document.getElementById("audio_{uid}");
const regionsPlugin_{uid} = RegionsPlugin.create();

const ws_{uid} = WaveSurfer.create({{
  container: "#waveform_{uid}",
  waveColor: "#9ca3af",
  progressColor: "#374151",
  cursorColor: "#111827",
  cursorWidth: 2,
  height: {height},
  media: audioEl_{uid},
  plugins: [regionsPlugin_{uid}]
}});

window.ws_{uid} = ws_{uid};

function tryAutoplay_{uid}() {{
  const shouldAutoplay = window.sessionStorage.getItem("taigi_qc_autoplay") === "1";
  if (!shouldAutoplay) return;
  audioEl_{uid}.play().catch(() => {{}});
}}

audioEl_{uid}.addEventListener("play", () => {{
  window.sessionStorage.setItem("taigi_qc_autoplay", "1");
}});

function showReady_{uid}() {{
  const loading = document.getElementById("loading_{uid}");
  if (loading) {{
    loading.style.display = "none";
  }}

  audioEl_{uid}.style.display = "block";
  setTimeout(() => tryAutoplay_{uid}(), 120);
}}

ws_{uid}.on("ready", () => {{
  showReady_{uid}();

  const initRegions = {regions_json};
  for (const r of initRegions) {{
    regionsPlugin_{uid}.addRegion({{
      start: r.start,
      end: r.end,
      color: r.color || "rgba(0,120,255,0.25)",
      drag: false,
      resize: false
    }});
  }}
}});

ws_{uid}.on("error", (e) => {{
  console.error("WS ERROR", e);
  showReady_{uid}();
}});
</script>
"""
