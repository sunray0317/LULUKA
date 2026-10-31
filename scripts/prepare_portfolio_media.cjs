// Run locally after adding originals. Publication uses the committed derivatives.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
let sharp;
try { sharp = require(process.env.LULUKA_SHARP_MODULE || 'sharp'); }
catch (error) {
  if (process.env.LULUKA_SHARP_MODULE) throw error;
  sharp = require(path.join(require('os').homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'));
}
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'brands/assets/portfolio-media');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'scripts/public-files.json')));
const priorFile = path.join(root, 'docs/portfolio-image-delivery.json');
const prior = fs.existsSync(priorFile) ? JSON.parse(fs.readFileSync(priorFile)) : {images:{}};

(async () => {
  fs.mkdirSync(output, {recursive:true});
  const sources = new Set(Object.keys(prior.images));
  for (const relative of manifest.filter(file => file.endsWith('.html'))) {
    const html = fs.readFileSync(path.join(root, relative), 'utf8');
    for (const match of html.matchAll(/<img\b[^>]*\bsrc="(\/[^\"]+\.(?:png|jpg))"/g)) sources.add(match[1]);
  }
  const cssSources = new Set([...Object.keys(prior.backgrounds || {}), '/brands/assets/bg.jpg', '/brands/assets/luluka-classic-wordmark-20261017.png']);
  for (const relative of manifest.filter(file => file.endsWith('.css'))) {
    const css = fs.readFileSync(path.join(root, relative), 'utf8');
    for (const match of css.matchAll(/url\(["']?(\/[^"'()]+luluka-gold-background\.png)["']?\)/g)) cssSources.add(match[1]);
  }
  for (const source of cssSources) sources.add(source);
  const images = {}, backgrounds = {...(prior.backgrounds || {})};
  let originalBytes = 0, representativeBytes = 0;
  // Bound encoder concurrency: keep memory stable even for tall seating plans.
  for (const source of sources) {
    const file = path.join(root, source);
    if (!fs.existsSync(file)) continue;
    const data = fs.readFileSync(file), sourceHash = crypto.createHash('sha256').update(data).digest('hex'), hash = sourceHash.slice(0,12);
    const meta = await sharp(file).metadata();
    const icon = source.startsWith('/brands/assets/sdg/');
    const logo = source.includes('classic-wordmark');
    const cssOnly = cssSources.has(source);
    const widths = [...new Set((icon ? [160,320] : cssOnly ? [meta.width] : [320,640,960,1600,2400,meta.width]).filter(width=>width<=meta.width))].sort((a,b)=>a-b);
    const variants = [];
    for (const width of widths) {
      const name = `${hash}-${width}.webp`, destination = path.join(output,name);
      if (!fs.existsSync(destination)) {
        await sharp(file).resize({width,withoutEnlargement:true}).webp(icon || logo ? {lossless:true,effort:5} : {quality:88,effort:5,smartSubsample:true}).toFile(destination);
      }
      variants.push({url:'/brands/assets/portfolio-media/'+name,width,bytes:fs.statSync(destination).size});
    }
    images[source] = {width:meta.width,height:meta.height,originalBytes:data.length,sourceSHA256:sourceHash,variants};
    if (cssOnly) backgrounds[source] = variants[variants.length-1].url;
    const representative = variants.reduce((best,row)=>Math.abs(row.width-(icon?160:640))<Math.abs(best.width-(icon?160:640))?row:best);
    originalBytes += data.length; representativeBytes += representative.bytes;
  }
  const report = {images,backgrounds,originalBytes,representativeBytes,description:'Responsive WebP delivery only; source artwork files remain untouched. Regenerate locally when adding or replacing originals.'};
  fs.writeFileSync(priorFile,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({sources:Object.keys(images).length,originalBytes,representativeBytes,reductionPercent:Math.round((1-representativeBytes/originalBytes)*100)},null,2));
})().catch(error=>{console.error(error);process.exitCode=1});
