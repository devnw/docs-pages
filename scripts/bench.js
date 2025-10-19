// Bench history renderer (fallback)
(function () {
  const root = document.getElementById('bench-charts');
  if (!root) return;
  fetch('bench/summary.json')
    .then((r) => r.json())
    .then((summary) => {
      const wrap = document.createElement('div');
      (summary.benchmarks || []).forEach((b) => {
        const div = document.createElement('div');
        div.className = 'bench-chart';
        div.innerHTML = `<h4>${b.name}</h4><canvas width=240 height=60></canvas>`;
        wrap.appendChild(div);
        fetch('bench/data/' + b.file)
          .then((r) => r.json())
          .then((series) => draw(div, series))
          .catch(() => {});
      });
      root.innerHTML = '';
      root.appendChild(wrap);
    })
    .catch(() => {
      root.textContent = 'Failed to load benchmark history.';
    });

  function draw(div, series) {
    const c = div.querySelector('canvas');
    const ctx = c.getContext('2d');
    const w = c.width,
      h = c.height;
    const pts = series.map((s) => ({ t: new Date(s.time), v: s.ns_per_op || 0 }));
    if (!pts.length) return;
    const min = Math.min(...pts.map((p) => p.v));
    const max = Math.max(...pts.map((p) => p.v));
    ctx.strokeStyle = '#2f81f7';
    ctx.lineWidth = 2;
    ctx.beginPath();
    pts.forEach((p, i) => {
      const x = (i / (pts.length - 1)) * (w - 10) + 5;
      const y = h - 5 - (max === min ? 0.5 : (p.v - min) / (max - min)) * (h - 10);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = '#555';
    ctx.font = '10px sans-serif';
    ctx.fillText(min.toFixed(2), 4, h - 2);
    ctx.fillText(max.toFixed(2), 4, 10);
  }
})();
