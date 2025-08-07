const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const fetch = require('node-fetch');

async function scrapeInventory() {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  let currentUrl = 'https://www.fordfairfield.com/new-inventory/index.htm?start=0';
  const data = [];
  const photosFolder = 'photos';
  if (!fs.existsSync(photosFolder)) fs.mkdirSync(photosFolder);

  while (true) {
    await page.goto(currentUrl, { waitUntil: 'networkidle2' });
    const cards = await page.$$('.vehicle-card');
    if (cards.length === 0) break;

    for (const card of cards) {
      const title = await card.evaluate(el => el.querySelector('.vehicle-card-title')?.textContent.trim() || '');
      const descText = await card.evaluate(el => el.querySelector('.vehicle-card-description')?.textContent.trim() || '');
      const priceText = await card.evaluate(el => el.querySelector('.pricing-detail')?.textContent.trim() || '');

      const stockMatch = descText.match(/Stock #\s*([\w-]+)/i);
      const vinMatch = descText.match(/VIN\s*([\w\d]+)/i);
      const stock = stockMatch ? stockMatch[1] : '';
      const vin = vinMatch ? vinMatch[1] : '';

      const msrpMatch = priceText.match(/MSRP\s*\$([\d,]+)/i);
      const discountMatch = priceText.match(/Discount\s*-\$([\d,]+)/i);
      const rebateMatch = priceText.match(/Rebate\s*-\$([\d,]+)/i);
      const retailMatch = priceText.match(/Retail Price\s*\$([\d,]+)/i);
      const msrp = msrpMatch ? msrpMatch[1] : '';
      const discount = discountMatch ? discountMatch[1] : '';
      const rebate = rebateMatch ? rebateMatch[1] : '';
      const retail = retailMatch ? retailMatch[1] : '';

      // Collect all photos without clicking
      const photos = await card.evaluate(el => {
        const imgs = el.querySelectorAll('.vehicle-card-photo img, .carousel-item img');
        return Array.from(imgs).map(img => img.src || img.getAttribute('data-src') || '').filter(src => src);
      });

      // Add to data
      data.push({ title, stock, vin, description: descText, msrp, discount, rebate, retail, photos: photos.join(',') });

      // Download photos later
    }

    // Get next URL from pagination
    const nextHref = await page.evaluate(() => document.querySelector('.pagination .next a, .page-next a')?.href || null);
    if (!nextHref) break;
    currentUrl = nextHref;
  }

  // Download all photos
  for (const item of data) {
    const vin = item.vin || 'unknown';
    const photoUrls = item.photos.split(',');
    for (let i = 0; i < photoUrls.length; i++) {
      const url = photoUrls[i];
      if (url) {
        try {
          const res = await fetch(url);
          const buffer = await res.buffer();
          fs.writeFileSync(path.join(photosFolder, `${vin}_${i + 1}.jpg`), buffer);
        } catch (e) {
          console.error(`Failed to download ${url}: ${e}`);
        }
      }
    }
  }

  await browser.close();

  // Write CSV
  const csvHeader = 'Title,Stock,VIN,Description,MSRP,Discount,Rebate,Retail,Photos\n';
  const csvRows = data.map(d => `"${d.title.replace(/"/g, '""')}","${d.stock}","${d.vin}","${d.description.replace(/"/g, '""')}","${d.msrp}","${d.discount}","${d.rebate}","${d.retail}","${d.photos.replace(/"/g, '""')}"`);
  fs.writeFileSync('vehicles.csv', csvHeader + csvRows.join('\n'));

  console.log('Scraped! Check vehicles.csv and photos folder.');
}

scrapeInventory();