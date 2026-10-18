/* Delivery derivatives only: preserve the full-resolution source PNGs. */
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
const themes = ['visual-design','brand-incubation','advertising-publishing','resident-dining','fashion-lifestyle'];
(async () => {
  const inventory = [];
  for (const theme of themes) {
    for (const state of ['idle','active']) {
      const source = `brands/assets/bronze-mural-${theme}${state === 'active' ? '-feedback' : ''}-v2.png`;
      const original = await fs.stat(path.join(root, source));
      for (const width of [320,640,960]) {
        const file = `brands/assets/bronze-${theme}-${state}-${width}.webp`;
        const info = await sharp(path.join(root, source)).resize({width,withoutEnlargement:true}).webp({quality:82,effort:6}).toFile(path.join(root,file));
        const decoded = await sharp(path.join(root,file)).metadata();
        if (decoded.width !== width || decoded.height <= width) throw new Error('Invalid derivative: ' + file);
        inventory.push({source,sourceBytes:original.size,file,width:info.width,height:info.height,bytes:info.size});
      }
    }
  }
  await fs.writeFile(path.join(root,'docs/bronze-card-delivery.json'), JSON.stringify(inventory,null,2)+'\n');
  const sum = rows => rows.reduce((n,r)=>n+r.bytes,0);
  console.log(JSON.stringify({files:inventory.length,originalIdleBytes:inventory.filter(r=>r.width===640&&r.file.includes('-idle-')).reduce((n,r)=>n+r.sourceBytes,0),idle320Bytes:sum(inventory.filter(r=>r.width===320&&r.file.includes('-idle-'))),idle640Bytes:sum(inventory.filter(r=>r.width===640&&r.file.includes('-idle-'))),allDerivativesBytes:sum(inventory)}));
})().catch(err=>{console.error(err);process.exitCode=1;});
