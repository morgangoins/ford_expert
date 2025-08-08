const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://www.fordfairfield.com/new-inventory/index.htm?start=0', { waitUntil: 'networkidle2' });
  await page.waitForSelector('.vehicle-card');

  const card = await page.$('.vehicle-card'); // First card

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

  const msrpMatch = pricingText.match(/MSRP\d*\s*([-\+]?)\s*\$?([\d,]+)/i);
  const msrp = msrpMatch ? (msrpMatch[1] || '') + msrpMatch[2] : 'N/A';

  const discountMatch = pricingText.match(/Discount(s?)\d*\s*([-\+]?)\s*\$?([\d,]+)/i);
  const discounts = discountMatch ? (discountMatch[2] || '') + discountMatch[3] : 'N/A';

  const rebateMatch = pricingText.match(/Rebate(s?)\d*\s*([-\+]?)\s*\$?([\d,]+)/i);
  const rebates = rebateMatch ? (rebateMatch[2] || '') + rebateMatch[3] : 'N/A';

  const retailMatch = pricingText.match(/Retail Price\d*\s*([-\+]?)\s*\$?([\d,]+)/i);
  const retail = retailMatch ? (retailMatch[1] || '') + retailMatch[2] : 'N/A';

  const csv = `index,title,stock,vin,msrp,discounts,rebates,retail_price,exterior,interior,status,mpg\n0,"${title.replace(/"/g, '""')}","${stock.replace(/"/g, '""')}","${vin.replace(/"/g, '""')}","${msrp.replace(/"/g, '""')}","${discounts.replace(/"/g, '""')}","${rebates.replace(/"/g, '""')}","${retail.replace(/"/g, '""')}","${exterior.replace(/"/g, '""')}","${interior.replace(/"/g, '""')}","${status.replace(/"/g, '""')}","${mpg.replace(/"/g, '""')}"`;
  fs.writeFileSync('car_data.csv', csv);

  console.log('CSV saved: car_data.csv');
  console.log('Debug pricingText:', pricingText);
  console.log('Debug msrp:', msrp);
  console.log('Debug discounts:', discounts);
  console.log('Debug rebates:', rebates);
  console.log('Debug retail:', retail);
  console.log('Debug description:', description);
  console.log('Debug stock:', stock);
  console.log('Debug vin:', vin);
  console.log('Debug exterior:', exterior);
  console.log('Debug interior:', interior);
  console.log('Debug status:', status);
  console.log('Debug mpg:', mpg);

  await browser.close();
})();