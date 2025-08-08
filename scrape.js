const puppeteer = require('puppeteer');
const fs = require('fs');

async function scrapeCarAtIndex(page, index) {
  const url = `https://www.fordfairfield.com/new-inventory/index.htm?start=${index}`;
  await page.goto(url, { waitUntil: 'networkidle2' });

  try {
    await page.waitForSelector('.vehicle-card', { timeout: 8000 });
  } catch (e) {
    return null; // No card found
  }

  const card = await page.$('.vehicle-card');
  if (!card) return null;

  let title = 'N/A';
  try {
    title = await card.$eval('.vehicle-card-title.inv-type-new', el => el.textContent.trim());
  } catch {}

  let description = 'N/A', stock = 'N/A', vin = 'N/A', exterior = 'N/A', interior = 'N/A', status = 'N/A', mpg = 'N/A';
  let descriptionItems = [];
  try {
    descriptionItems = await card.$$eval('.vehicle-card-description.single-col li', lis => lis.map(li => li.textContent.trim()));
    description = descriptionItems.join('\n');
    descriptionItems.forEach(item => {
      if (item.startsWith('Stock #')) stock = item.replace(/Stock #\s*(:)?\s*/, '').trim();
      if (item.startsWith('VIN')) vin = item.replace(/VIN\s*(:)?\s*/, '').trim();
      if (item.endsWith('Exterior')) exterior = item.replace(/ Exterior$/, '').trim();
      if (item.endsWith('Interior')) interior = item.replace(/ Interior$/, '').trim();
      if (item === 'IN STOCK' || item === 'IN TRANSIT') status = item.trim();
      if (item.includes('MPG City/Hwy')) mpg = item.replace(/ MPG City\/Hwy$/, '').trim();
    });
  } catch {}

  let pricingText = 'N/A';
  try {
    pricingText = await card.$eval('.pricing-detail.inv-type-new', el => el.textContent.trim());
  } catch {}

  const msrpMatch = pricingText.match(/MSRP\d*\s*([\-\+]?)\s*\$?([\d,]+)/i);
  const msrp = msrpMatch ? (msrpMatch[1] || '') + msrpMatch[2] : 'N/A';

  const discountMatch = pricingText.match(/Discount(s?)\d*\s*([\-\+]?)\s*\$?([\d,]+)/i);
  const discounts = discountMatch ? (discountMatch[2] || '') + discountMatch[3] : 'N/A';

  const rebateMatch = pricingText.match(/Rebate(s?)\d*\s*([\-\+]?)\s*\$?([\d,]+)/i);
  const rebates = rebateMatch ? (rebateMatch[2] || '') + rebateMatch[3] : 'N/A';

  const retailMatch = pricingText.match(/Retail Price\d*\s*([\-\+]?)\s*\$?([\d,]+)/i);
  const retail = retailMatch ? (retailMatch[1] || '') + retailMatch[2] : 'N/A';

  if (!vin || vin === 'N/A') {
    return null; // Stop when no VIN is present
  }

  return {
    index,
    title,
    stock,
    vin,
    msrp,
    discounts,
    rebates,
    retail,
    exterior,
    interior,
    status,
    mpg
  };
}

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Start fresh CSV with header
  const header = 'index,title,stock,vin,msrp,discounts,rebates,retail_price,exterior,interior,status,mpg';
  fs.writeFileSync('car_data.csv', header + '\n');

  let index = 0;
  let count = 0;

  while (true) {
    const car = await scrapeCarAtIndex(page, index);
    if (!car) break;

    const row = `${car.index},"${car.title.replace(/"/g, '""')}","${car.stock.replace(/"/g, '""')}","${car.vin.replace(/"/g, '""')}","${car.msrp.replace(/"/g, '""')}","${car.discounts.replace(/"/g, '""')}","${car.rebates.replace(/"/g, '""')}","${car.retail.replace(/"/g, '""')}","${car.exterior.replace(/"/g, '""')}","${car.interior.replace(/"/g, '""')}","${car.status.replace(/"/g, '""')}","${car.mpg.replace(/"/g, '""')}"`;
    fs.appendFileSync('car_data.csv', row + '\n');

    process.stdout.write(`Scraped index ${index}: ${car.vin}\n`);
    index += 1;
    count += 1;
  }

  console.log(`Done. Total vehicles scraped: ${count}. Last index attempted: ${index}.`);
  await browser.close();
})();


