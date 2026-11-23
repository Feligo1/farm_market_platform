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
  menu.innerHTML='<span aria-hidden="true">☰</span><span>Menu</span>';
  const top=document.createElement('div');top.className='fc-nav-top';top.append(brand,menu);
  const links=document.createElement('div');links.id='fc-nav-links';links.className='fc-nav-links';
  const items=[['index.html','Home'],['prices.html','Market prices'],['find-buyers.html','Marketplace'],['post-listing.html','Post listing'],['news.html','News']];
  for(const [url,label] of items){
   const a=document.createElement('a');a.href=url;a.textContent=label;
   if(page===url){a.classList.add('fc-current');a.setAttribute('aria-current','page')}
   links.append(a);
  }
  inner.append(top,links);nav.append(inner);
  document.body.insertBefore(nav,document.body.firstChild);
  menu.addEventListener('click',()=>{
   const expanded=menu.getAttribute('aria-expanded')==='true';
   menu.setAttribute('aria-expanded',String(!expanded));menu.setAttribute('aria-label',expanded?'Open navigation':'Close navigation');
   nav.classList.toggle('fc-mobile-expanded',!expanded);
  });
  document.addEventListener('keydown',event=>{if(event.key==='Escape'){nav.classList.remove('fc-mobile-expanded');menu.setAttribute('aria-expanded','false')}});
  if(!simple){
    const bottom=document.createElement('nav');bottom.className='fc-mobile-bottom';bottom.setAttribute('aria-label','Quick navigation');
    const shortcuts=[['index.html','⌂','Home'],['prices.html','▤','Prices'],['find-buyers.html','⇄','Market'],['post-listing.html','+','Post']];
    for(const [url,symbol,label] of shortcuts){
      const a=document.createElement('a');a.href=url;if(page===url){a.setAttribute('aria-current','page');a.className='active'}
      const icon=document.createElement('span');icon.textContent=symbol;icon.className='fc-mobile-bottom-icon';icon.setAttribute('aria-hidden','true');
      const name=document.createElement('span');name.textContent=label;
      a.append(icon,name);bottom.append(a);
    }
    document.body.append(bottom);
  }
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();