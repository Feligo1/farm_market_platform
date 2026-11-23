/* Shared, accessible FarmConnect navigation */
(() => {
 'use strict';
 function init(){
  if(document.getElementById('fc-global-nav'))return;
  const page=(location.pathname.split('/').pop()||'index.html').toLowerCase();
  const simple=['login.html','register.html','profile.html','admin.html'].includes(page);
  if(simple)document.body.classList.add('fc-simple-page');
  const nav=document.createElement('nav');
  nav.id='fc-global-nav';nav.className='fc-global-nav';nav.setAttribute('aria-label','Main navigation');
  const inner=document.createElement('div');inner.className='fc-nav-inner';
  const brand=document.createElement('a');brand.href='index.html';brand.className='fc-brand';
  brand.innerHTML='<span class="fc-brand-mark" aria-hidden="true">FC</span><span>FarmConnect <span class="fc-brand-accent">Zambia</span></span>';
  const menu=document.createElement('button');menu.type='button';menu.className='fc-mobile-toggle';
  menu.setAttribute('aria-label','Open navigation');menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-controls','fc-nav-links');
  menu.innerHTML='<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg><span>Menu</span>';
  const top=document.createElement('div');top.className='fc-nav-top';top.append(brand,menu);
  const links=document.createElement('div');links.id='fc-nav-links';links.className='fc-nav-links';
  const items=[['index.html','Home'],['prices.html','Prices'],['find-buyers.html','Marketplace'],['match.html','Find a match'],['news.html','News']];
  const extras=[['livestock.html','Livestock hub'],['profit-calculator.html','Profit calculator'],['price-watch.html','Price watch'],['farmer-guide.html','Farmer guide'],['post-listing.html','Post listing'],['feedback.html','Give feedback']];
  const makeLink=(url,label)=>{
    const a=document.createElement('a');a.href=url;a.textContent=label;
    if(page===url){a.classList.add('fc-current');a.setAttribute('aria-current','page')}
    return a;
  };
  for(const [url,label] of items)links.append(makeLink(url,label));
  const more=document.createElement('details');more.className='fc-nav-more';
  if(extras.some(([url])=>url===page))more.classList.add('fc-more-current');
  const summary=document.createElement('summary');summary.textContent='More tools';
  const moreLinks=document.createElement('div');moreLinks.className='fc-nav-more-links';
  for(const [url,label] of extras)moreLinks.append(makeLink(url,label));
  more.append(summary,moreLinks);links.append(more);
  inner.append(top,links);nav.append(inner);
  document.body.insertBefore(nav,document.body.firstChild);
  menu.addEventListener('click',()=>{
   const expanded=menu.getAttribute('aria-expanded')==='true';
   menu.setAttribute('aria-expanded',String(!expanded));menu.setAttribute('aria-label',expanded?'Open navigation':'Close navigation');
   nav.classList.toggle('fc-mobile-expanded',!expanded);
  });
  document.addEventListener('keydown',event=>{if(event.key==='Escape'){nav.classList.remove('fc-mobile-expanded');menu.setAttribute('aria-expanded','false')}});

 }
 // Cache only public pages on repeat visits. Admin screens and remote market APIs are never cached.
 if('serviceWorker' in navigator && location.protocol==='https:'){
   window.addEventListener('load',()=>navigator.serviceWorker.register('service-worker.js').catch(()=>{}),{once:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();