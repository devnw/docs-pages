// Security history sparklines
(function () {
  const root = document.getElementById("security-charts");
  if (!root) return;
  root.innerHTML = "<canvas></canvas>";

  function draw(div, series) {
    const pts = series.map((s) => ({ t: new Date(s.time), v: s.value }));
    const c = div.querySelector("canvas") || div;
    const ctx = c.getContext && c.getContext("2d");
    const w = (c.width || 240), h = (c.height || 60);
    if (!ctx) return;
    if (pts.length > 1) {
      const min = Math.min(...pts.map((p) => p.v));
      const max = Math.max(...pts.map((p) => p.v));
      ctx.strokeStyle = "#d73a49";
      ctx.lineWidth = 2;
      ctx.beginPath();
      pts.forEach((p, i) => {
        const x = (i / (pts.length - 1)) * (w - 10) + 5;
        const y = h - 5 - (max === min ? 0.5 : (p.v - min) / (max - min)) * (h - 10);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      });
      ctx.stroke();
      ctx.fillStyle = "#555";
      ctx.font = "10px sans-serif";
      ctx.fillText(min.toFixed(0), 4, h - 2);
      ctx.fillText(max.toFixed(0), 4, 10);
    } else if (pts.length === 1) {
      ctx.fillStyle = "#d73a49";
      ctx.beginPath();
      ctx.arc(w / 2, h / 2, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  fetch("security/summary.json")
    .then((r) => r.json())
    .then((summary) => {
      const first = (summary.metrics || [])[0];
      if (!first) return;
      fetch("security/data/" + first.file)
        .then((r) => r.json())
        .then((series) => draw(root, series))
        .catch(() => {});
    })
    .catch(() => {
      root.textContent = "Failed to load security history.";
    });
})();
