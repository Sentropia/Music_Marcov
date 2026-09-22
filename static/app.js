const form = document.querySelector("#generator-form");
const button = document.querySelector("#generate-button");
const status = document.querySelector("#status");

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

    const midi = await response.blob();
    const url = URL.createObjectURL(midi);
    const link = document.createElement("a");
    link.href = url;
    link.download = "markov_music.mid";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    status.className = "status success";
    status.textContent = "Your music is ready to download.";
  } catch (error) {
    status.className = "status error";
    status.textContent = error.message || "Generation failed. Please try again.";
  } finally {
    button.disabled = false;
  }
});
