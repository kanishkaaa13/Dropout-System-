
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));
  
  await page.goto('http://localhost:5173/login', {waitUntil: 'networkidle2'});
  
  await page.type('#email', 'admin@demojee.com');
  await page.type('#password', 'Admin@1234');
  await page.click('button[type=\"submit\"]');
  
  await page.waitForNavigation({waitUntil: 'networkidle2', timeout: 5000}).catch(e => console.log('Nav timeout:', e.message));
  
  console.log('Final URL:', page.url());
  await browser.close();
})();

