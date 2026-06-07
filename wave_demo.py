from __future__ import annotations

import json
import re
import html

def _safe_uid(uid: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(uid))


def wavesurfer_html(audio_url: str, uid: str = "wave", regions=None, height: int = 120) -> str:
    """Return a minimal WaveSurfer HTML component.

    This version intentionally keeps only the core behavior:
    - show waveform
    - show native audio controls
    - clicking / dragging the waveform seeks the same audio element

    It avoids:
    - data:audio base64 conversion
    - RegionsPlugin
    - autoplay/sessionStorage logic

    Add those back only after this minimal version is stable.
    """
    uid = _safe_uid(uid)
    regions = regions or []
    regions_json = json.dumps(regions, ensure_ascii=False)
    audio_url = html.escape(audio_url, quote=True)

    return f"""
<div>
  <div id="loading_{uid}" style="padding:8px;color:#666;">
    WaveSurfer 載入中...
  </div>

  <div id="waveform_{uid}"></div>

  <audio
    id="audio_{uid}"
    controls
    
    style="width:100%; margin-top:8px;"
  ></audio>
</div>

<script type="module">
import WaveSurfer from "https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.esm.js";

const audioEl_{uid} = document.getElementById("audio_{uid}");
const audioData_{uid} = `{audio_url}`;  /* added for decode */
audioEl_{uid}.src = audioData_{uid};  /* added for decode */

const shouldAutoplay =
    window.sessionStorage.getItem("taigi_qc_autoplay") === "1";

audioEl_{uid}.addEventListener("play", () => {{
    window.sessionStorage.setItem("taigi_qc_autoplay", "1");
}});

const ws_{uid} = WaveSurfer.create({{
  container: "#waveform_{uid}",
  waveColor: "#9ca3af",
  progressColor: "#374151",
  cursorColor: "#111827",
  cursorWidth: 2,
  height: {height},
  media: audioEl_{uid}
}});

window.ws_{uid} = ws_{uid};

ws_{uid}.on("ready", () => {{
  const loading = document.getElementById("loading_{uid}");
  if (loading) {{
    loading.style.display = "none";

    if (shouldAutoplay) {{
    setTimeout(() => {{
        audioEl_{uid}.play().catch(() => {{}});
    }}, 100);
}}
  }}
}});

ws_{uid}.on("interaction", () => {{
  audioEl_{uid}.play().catch(() => {{}});
}});

ws_{uid}.on("error", (e) => {{
  console.error("WS ERROR", e);
  const loading = document.getElementById("loading_{uid}");
  if (loading) {{
    loading.innerText = "WaveSurfer 載入失敗，請看 console";
    loading.style.color = "red";
  }}
}});
</script>
"""
