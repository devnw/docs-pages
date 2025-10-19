const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

function loadScript(dom, file) {
  const scriptContent = fs.readFileSync(path.join(__dirname, '..', 'scripts', file), 'utf-8');
  const scriptEl = dom.window.document.createElement('script');
  scriptEl.textContent = scriptContent;
  dom.window.document.body.appendChild(scriptEl);
}

test('metrics.js populates charts container', async () => {
  const dom = new JSDOM(`<!DOCTYPE html><div id="metrics-charts"></div>`, { url: 'http://localhost/' });
  const summary = { metrics: [{ name: 'coverage_percent', file: 'coverage_percent.json' }] };
  const series = [{ time: new Date().toISOString(), value: 50 }];
  dom.window.fetch = async (url) => {
    if (url.endsWith('metrics/summary.json')) return { json: async () => summary };
    return { json: async () => series };
  };
  loadScript(dom, 'metrics.js');
  await new Promise(r => setTimeout(r, 0));
  const container = dom.window.document.getElementById('metrics-charts');
  expect(container.textContent).not.toMatch(/Failed/);
  expect(container.querySelectorAll('canvas').length).toBe(1);
});

test('security.js populates charts container', async () => {
  const dom = new JSDOM(`<!DOCTYPE html><div id="security-charts"></div>`, { url: 'http://localhost/' });
  const summary = { metrics: [{ name: 'severity_critical', file: 'severity_critical.json' }] };
  const series = [{ time: new Date().toISOString(), value: 1 }];
  dom.window.fetch = async (url) => {
    if (url.endsWith('security/summary.json')) return { json: async () => summary };
    return { json: async () => series };
  };
  loadScript(dom, 'security.js');
  await new Promise(r => setTimeout(r, 0));
  const container = dom.window.document.getElementById('security-charts');
  expect(container.querySelectorAll('canvas').length).toBe(1);
});
