// One-off dev helper: screenshot a page at a true mobile viewport via CDP.
// Usage: node scripts/shot.mjs <url> <width> <height> <outfile>
import { spawn } from 'node:child_process';
import fs from 'node:fs';

const [, , url, w = '390', h = '1800', out = 'shot.png'] = process.argv;
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const port = 9331;
const profile = 'C:\\Users\\admin\\Documents\\deepseek-harness\\default-workspace\\automotive-journal\\.shots\\cdp-profile';

const edge = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-crash-reporter',
  '--disable-breakpad', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`, 'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getJson(path) {
  const res = await fetch(`http://127.0.0.1:${port}${path}`);
  return res.json();
}

async function main() {
  let targets;
  for (let i = 0; i < 40; i++) {
    try { targets = await getJson('/json/list'); break; } catch { await sleep(250); }
  }
  const page = targets.find((t) => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result); pending.delete(msg.id); }
  };
  await new Promise((r) => (ws.onopen = r));
  const send = (method, params = {}) =>
    new Promise((resolve) => { const n = ++id; pending.set(n, resolve); ws.send(JSON.stringify({ id: n, method, params })); });

  await send('Emulation.setDeviceMetricsOverride', {
    width: Number(w), height: Number(h), deviceScaleFactor: 2, mobile: true,
  });
  await send('Page.enable');
  await send('Page.navigate', { url });
  await sleep(2500);

  const metrics = await send('Runtime.evaluate', {
    expression: 'JSON.stringify({w: innerWidth, sw: document.documentElement.scrollWidth})',
    returnByValue: true,
  });
  console.log('viewport:', metrics.result.value);

  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log('wrote', out);
  ws.close();
}

main()
  .catch((e) => console.error('ERROR', e.message))
  .finally(() => { edge.kill(); setTimeout(() => process.exit(0), 300); });
