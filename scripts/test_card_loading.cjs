const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname,'../brands/assets/brand.js'),'utf8');
const loader = source.slice(source.indexOf('const loadedImages ='),source.indexOf("document.querySelectorAll('.brand-card').forEach(observeCardMedia);"));
function setup(mobile) {
  let intersection;
  const context = {carouselLayout:{matches:mobile},IntersectionObserver:class{constructor(callback){intersection=callback;}observe(){}},WeakSet};
  vm.runInNewContext(loader+';globalThis.testLoader={loadCardImage,prepareActiveArt};',context);
  return {...context.testLoader,intersect:entries=>intersection(entries)};
}
function image(active=false) {
  const events = {};
  const card = {ready:false,classList:{add(){card.ready=true;}}};
  return {dataset:{src:'/card.webp',srcset:'/small.webp 320w, /card.webp 640w'},events,card,complete:false,naturalWidth:0,classList:{contains:name=>active&&name==='art-active'},closest:()=>card,addEventListener(name,callback){events[name]=callback;}};
}
const touch = setup(true);
const touchArt = image(true);
touch.prepareActiveArt({querySelector:()=>touchArt});
assert.equal(touchArt.src,undefined,'Mobile must not fetch hidden feedback artwork');
const desktop = setup(false);
const feedback = image(true);
desktop.prepareActiveArt({querySelector:()=>feedback});
assert.equal(feedback.src,'/card.webp');
assert.equal(feedback.srcset,'/small.webp 320w, /card.webp 640w');
assert.equal(feedback.card.ready,false,'Idle art stays visible until feedback is ready');
feedback.naturalWidth=640;
feedback.events.load();
assert.equal(feedback.card.ready,true);
const failed = image(true);
desktop.loadCardImage(failed);
failed.events.error();
failed.dataset.src='/retry.webp';
desktop.loadCardImage(failed);
assert.equal(failed.src,'/retry.webp','A failed image may be retried');
const idle = image();
const neverRequested = image(true);
desktop.intersect([{isIntersecting:true,target:{classList:{toggle(){}},querySelector:selector=>selector==='.art-idle'?idle:neverRequested}}]);
assert.equal(idle.src,'/card.webp');
assert.equal(neverRequested.src,undefined,'Intersection must not prefetch feedback');
console.log('Passed: mobile feedback suppression, desktop readiness, error retry, idle-only intersection loading');
