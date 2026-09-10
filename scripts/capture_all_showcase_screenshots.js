const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function capture() {
  const screenshotsDir = path.join(__dirname, '..', 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.5,
  });

  const page = await context.newPage();

  console.log('1. Capturando Cockpit Dashboard Executivo...');
  await page.goto('https://retainiq-197215016090.us-central1.run.app/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(8000);
  await page.screenshot({ path: path.join(screenshotsDir, '01_cockpit_dashboard.png'), fullPage: false });

  console.log('2. Capturando Risk Queue (Fila de Risco Priorizada)...');
  try {
    await page.click('text=Risk Queue');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotsDir, '02_risk_queue_table.png'), fullPage: false });
  } catch (e) {
    console.error('Erro ao capturar Risk Queue:', e);
  }

  console.log('3. Capturando MLOps Health & Monitoramento...');
  try {
    await page.click('text=MLOps Health');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(screenshotsDir, '03_mlops_monitoring.png'), fullPage: false });
  } catch (e) {
    console.error('Erro ao capturar MLOps Health:', e);
  }

  console.log('4. Capturando Portal MkDocs (Visão Geral)...');
  await page.goto('https://henriquebotelhogomes.github.io/telco_churn/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(screenshotsDir, '04_mkdocs_portal.png'), fullPage: false });

  console.log('5. Capturando Arquitetura de Live Streaming MkDocs...');
  await page.goto('https://henriquebotelhogomes.github.io/telco_churn/streaming/live-streaming-architecture/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(screenshotsDir, '05_streaming_architecture.png'), fullPage: false });

  console.log('6. Capturando OpenAPI / Swagger Docs...');
  await page.goto('https://retainiq-197215016090.us-central1.run.app/docs', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);
  await page.screenshot({ path: path.join(screenshotsDir, '06_swagger_api_docs.png'), fullPage: false });

  await browser.close();
  console.log('🎉 Todas as 6 screenshots foram capturadas com sucesso em /screenshots!');
}

capture().catch(console.error);
