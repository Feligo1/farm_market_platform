/* FarmConnect shared primary navigation. Do not touch legacy page IDs or app handlers. */
(function(){
'use strict';
function run(){
 if(document.getElementById('fc-global-nav'))return;
 var page=(location.pathname.split('/').pop()||'index.html').toLowerCase();
 var simple=['login.html','register.html','profile.html','admin.html'].includes(page);
 if(simple)document.body.classList.add('fc-simple-page');
 var existing=document.body.querySelector('header');
 if(simple&&existing)existing.setAttribute('aria-hidden','true');
 var nav=document.createElement('nav');nav.id='fc-global-nav';nav.className='fc-global-nav';nav.setAttribute('aria-label','FarmConnect main navigation');
 var brand=document.createElement('a');brand.href='index.html';brand.className='fc-brand';
 var mark=document.createElement('span');mark.className='fc-brand-mark';mark.textContent='🌽';mark.setAttribute('aria-hidden','true');
 var title=document.createElement('span');title.textContent='FarmConnect Zambia';brand.append(mark,title);
 var toggle=document.createElement('button');toggle.type='button';toggle.className='fc-nav-toggle';toggle.setAttribute('aria-label','Open navigation');toggle.setAttribute('aria-expanded','false');toggle.textContent='☰';
 var links=document.createElement('div');links.className='fc-nav-links';
 var items=[['index.html','Home'],['dashboard.html','Dashboard'],['prices.html','Market Prices'],['find-buyers.html','Buyers & Sellers'],['news.html','News'],['profile.html','My Profile'],['admin.html','Admin'],['login.html','Sign In'],['register.html','Register']];
 var currentUser=null;try{currentUser=JSON.parse(localStorage.getItem('userData')||'null')}catch(_){}
 var signedIn=!!localStorage.getItem('authToken'),isAdmin=signedIn&&currentUser?.role==='admin';
 for(var item of items){
  var a=document.createElement('a');a.href=item[0];a.textContent=item[1];
  if(page===item[0]){a.classList.add('fc-current');a.setAttribute('aria-current','page')}
  if(item[0]==='admin.html'&&!isAdmin)a.hidden=true;
  if(item[0]==='profile.html'&&!signedIn)a.hidden=true;
  if((item[0]==='register.html'||item[0]==='login.html')&&signedIn)a.hidden=true;
  if(item[0]==='register.html')a.classList.add('fc-join');
  links.append(a);
 }
 if(signedIn){
  var out=document.createElement('a');out.href='login.html';out.textContent='Log out';
  out.addEventListener('click',function(e){e.preventDefault();localStorage.removeItem('authToken');localStorage.removeItem('userData');location.href='login.html'});
  links.append(out);
 }
 toggle.addEventListener('click',function(){var expanded=nav.classList.toggle('fc-expanded');toggle.setAttribute('aria-expanded',String(expanded));toggle.setAttribute('aria-label',expanded?'Close navigation':'Open navigation')});
 nav.append(brand,toggle,links);
 document.body.insertBefore(nav,document.body.firstChild);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();
