/* FarmConnect lightweight offline shell. No authentication or API responses are cached. */
const CACHE="farmconnect-public-shell-v3";
const SHELL=[
 "./","./index.html","./prices.html","./find-buyers.html","./post-listing.html",
 "./match.html","./profit-calculator.html","./farmer-guide.html","./news.html","./livestock.html","./feedback.html",
 "./farmconnect-redesign.css","./farmconnect-mobile.css","./farmconnect-nav.js","./farmconnect-appearance.js"
];
const PUBLIC_PATHS=new Set(SHELL.map(item=>new URL(item,self.registration.scope).pathname));
self.addEventListener("install",event=>{
 event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);
  await Promise.allSettled(SHELL.map(path=>cache.add(new Request(path,{cache:"reload"}))));
  await self.skipWaiting();
 })());
});
self.addEventListener("activate",event=>{
 event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith("farmconnect-public-shell-")&&key!==CACHE).map(key=>caches.delete(key)));
  await self.clients.claim();
 })());
});
self.addEventListener("fetch",event=>{
 const req=event.request;
 if(req.method!=="GET")return;
 const url=new URL(req.url);
 if(url.origin!==self.location.origin)return;
 if(!PUBLIC_PATHS.has(url.pathname))return; // never cache admin/login or personal data.
 event.respondWith((async()=>{
  try{
   const response=await fetch(req);
   if(response.ok && response.type==="basic"){
    const cache=await caches.open(CACHE);await cache.put(req,response.clone());
   }
   return response;
  }catch{
   const cached=await caches.match(req,{ignoreSearch:true});
   if(cached)return cached;
   return Response.error();
  }
 })());
});
