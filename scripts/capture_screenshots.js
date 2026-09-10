const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function main() {
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

  console.log('1. Capturando Cockpit Dashboard & Risk Queue...');
  await page.goto('https://retainiq-197215016090.us-central1.run.app/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);
  await page.screenshot({ path: path.join(screenshotsDir, '01_cockpit_dashboard.png'), fullPage: false });

  console.log('2. Capturando Portal MkDocs (Visão Geral)...');
  await page.goto('https://henriquebotelhogomes.github.io/telco_churn/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(screenshotsDir, '02_mkdocs_documentation.png'), fullPage: false });

  console.log('3. Capturando Arquitetura de Live Streaming MkDocs...');
  await page.goto('https://henriquebotelhogomes.github.io/telco_churn/streaming/live-streaming-architecture/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(screenshotsDir, '03_streaming_architecture.png'), fullPage: false });

  console.log('4. Capturando Swagger / OpenAPI Docs...');
  await page.goto('https://retainiq-197215016090.us-central1.run.app/docs', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(screenshotsDir, '04_swagger_api_docs.png'), fullPage: false });

  console.log('5. Capturando Feature Store Feast Docs...');
  await page.goto('https://henriquebotelhogomes.github.io/telco_churn/streaming/feast-feature-store/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(screenshotsDir, '05_feature_store_architecture.png'), fullPage: false });

  await browser.close();
  console.log('Todas as screenshots foram capturadas com sucesso!');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
