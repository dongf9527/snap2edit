// 渲染 HTML → PNG 截图
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1776, height: 1020 }, deviceScaleFactor: 1 });
  await p.goto('file:///home/z/my-project/download/德勤AI落地方法论拆解.html');
  await p.waitForTimeout(900);
  const el = await p.$('#canvas');
  await el.screenshot({ path: '/tmp/render_html.png' });
  await b.close();
  console.log('done');
})();
