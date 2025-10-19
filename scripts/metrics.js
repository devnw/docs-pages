// Simple metrics history renderer
(function () {
  const container = document.getElementById("metrics-charts");
  if (!container) return;
  container.innerHTML = "<canvas></canvas>";

  function drawSeries(div, series) {
    const points = series.map((s) => ({ t: new Date(s.time), v: s.value }));
    const canvas = div.querySelector("canvas");
    if (!canvas) return;
    const ctx = canvas.getContext && canvas.getContext("2d");
    const w = 240, h = 60;
    canvas.width = w; canvas.height = h;
    if (!ctx) return;
    if (points.length > 1) {
      const min = Math.min(...points.map((p) => p.v));
      const max = Math.max(...points.map((p) => p.v));
      ctx.strokeStyle = "#0366d6";
      ctx.lineWidth = 2;
      ctx.beginPath();
      points.forEach((p, i) => {
        const x = (i / (points.length - 1)) * (w - 10) + 5;
        const y = h - 5 - (max === min ? 0.5 : (p.v - min) / (max - min)) * (h - 10);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      });
      ctx.stroke();
      ctx.fillStyle = "#555";
      ctx.font = "10px sans-serif";
      ctx.fillText(min.toFixed(2), 4, h - 2);
      ctx.fillText(max.toFixed(2), 4, 10);
    } else if (points.length === 1) {
      ctx.fillStyle = "#0366d6";
      ctx.beginPath();
      ctx.arc(w / 2, h / 2, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  fetch("metrics/summary.json")
    .then((r) => r.json())
    .then((summary) => {
      const first = (summary.metrics || [])[0];
      if (!first) return;
      fetch("metrics/data/" + first.file)
        .then((r) => r.json())
        .then((series) => drawSeries(container, series))
        .catch(() => {});
    })
    .catch(() => {
      container.textContent = "Failed to load metrics history.";
    });
})();
