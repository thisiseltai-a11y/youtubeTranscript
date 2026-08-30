const API_BASE = ""; // same-origin

const urlForm = document.getElementById("url-form");
const urlInput = document.getElementById("url-input");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const videoMeta = document.getElementById("video-meta");
const transcriptSection = document.getElementById("transcript-section");
const originalText = document.getElementById("original-text");
const sourceBadge = document.getElementById("source-badge");
const copyOriginalBtn = document.getElementById("copy-original");

const presetSelect = document.getElementById("preset-select");
const topicLabel = document.getElementById("topic-label");
const topicInput = document.getElementById("topic-input");
const instructionsInput = document.getElementById("instructions-input");
const rewriteBtn = document.getElementById("rewrite-btn");
const rewriteText = document.getElementById("rewrite-text");
const copyRewriteBtn = document.getElementById("copy-rewrite");

function setStatus(message, kind) {
  if (!message) {
    statusEl.hidden = true;
    return;
  }
  statusEl.hidden = false;
  statusEl.textContent = message;
  statusEl.className = `status ${kind || "info"}`;
}

function formatDuration(seconds) {
  if (!seconds) return "unknown length";
  const s = Math.round(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  return `${m}m ${sec}s`;
}

const SOURCE_LABELS = {
  manual_captions: "Official captions",
  auto_captions: "Auto captions",
  whisper: "Whisper transcription",
};

urlForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  submitBtn.disabled = true;
  transcriptSection.hidden = true;
  videoMeta.hidden = true;
  rewriteText.hidden = true;
  copyRewriteBtn.hidden = true;
  setStatus("Fetching transcript... this can take a while for long videos without captions (Whisper fallback).", "info");

  try {
    const resp = await fetch(`${API_BASE}/api/transcript`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "Something went wrong fetching the transcript.");
    }

    originalText.value = data.transcript_text;
    sourceBadge.textContent = SOURCE_LABELS[data.source] || data.source;
    transcriptSection.hidden = false;

    videoMeta.hidden = false;
    videoMeta.innerHTML = `
      <h3>${escapeHtml(data.title || data.video_id)}</h3>
      <div class="meta-line">${formatDuration(data.duration)} · ${data.cached ? "from cache" : "freshly processed"}</div>
    `;

    if (data.warning) {
      setStatus(data.warning, "warning");
    } else {
      setStatus(`Transcript ready (${SOURCE_LABELS[data.source] || data.source}).`, "info");
    }
  } catch (err) {
    setStatus(err.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});

presetSelect.addEventListener("change", () => {
  const isNewTopic = presetSelect.value === "new_topic";
  topicLabel.hidden = !isNewTopic;
  topicInput.hidden = !isNewTopic;
});

rewriteBtn.addEventListener("click", async () => {
  const transcript_text = originalText.value.trim();
  if (!transcript_text) {
    setStatus("There's no transcript to rewrite yet.", "error");
    return;
  }

  rewriteBtn.disabled = true;
  rewriteBtn.textContent = "Rewriting...";
  setStatus("Asking Claude to rewrite the transcript...", "info");

  try {
    const resp = await fetch(`${API_BASE}/api/rewrite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        transcript_text,
        preset: presetSelect.value,
        target_topic: topicInput.hidden ? null : topicInput.value.trim() || null,
        instructions: instructionsInput.value.trim(),
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "Something went wrong rewriting the transcript.");
    }

    rewriteText.value = data.rewritten_text;
    rewriteText.hidden = false;
    copyRewriteBtn.hidden = false;
    setStatus("Rewrite complete.", "info");
  } catch (err) {
    setStatus(err.message, "error");
  } finally {
    rewriteBtn.disabled = false;
    rewriteBtn.textContent = "Rewrite with Claude";
  }
});

function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    const original = button.textContent;
    button.textContent = "Copied!";
    setTimeout(() => (button.textContent = original), 1200);
  });
}

copyOriginalBtn.addEventListener("click", () => copyToClipboard(originalText.value, copyOriginalBtn));
copyRewriteBtn.addEventListener("click", () => copyToClipboard(rewriteText.value, copyRewriteBtn));

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
