const form = document.querySelector("#generator-form");
const button = document.querySelector("#generate-button");
const status = document.querySelector("#status");
const playerContainer = document.querySelector("#player-container");
const audioPlayer = document.querySelector("#audio-player");
const downloadLink = document.querySelector("#download-link");
let audioUrl;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const order = new FormData(form).get("order");
  button.disabled = true;
  status.className = "status";
  status.textContent = "Generating your music…";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order: Number(order) }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || "Generation failed.");
    }

    const audio = await response.blob();
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = URL.createObjectURL(audio);
    audioPlayer.src = audioUrl;
    downloadLink.href = audioUrl;
    playerContainer.hidden = false;
    status.className = "status success";
    status.textContent = "Your music is ready to play or download.";
  } catch (error) {
    status.className = "status error";
    status.textContent = error.message || "Generation failed. Please try again.";
  } finally {
    button.disabled = false;
  }
});
