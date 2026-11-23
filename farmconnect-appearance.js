/* FarmConnect public appearance – published site preferences only. */
(()=>{
"use strict";
const API="https://qlfsmwvehigoildkuevq.supabase.co/functions/v1/farmconnect-api/appearance";
const DEFAULT={hero_image_url:"https://feligo1.github.io/farm_market_platform/images/maize.jpg",hero_color:"#194932",page_image_url:null,page_color:"#f6f8f5",hero_overlay:0.74};
const hex=v=>typeof v==="string"&&/^#[\da-f]{6}$/i.test(v);
const url=v=>{if(!v)return null;try{const u=new URL(v,location.href);return u.protocol==="https:"?u.href:null}catch{return null}};
function apply(input={}){
 const prefs={...DEFAULT,...input};
 const page=hex(prefs.page_color)?prefs.page_color:DEFAULT.page_color;
 const hero=hex(prefs.hero_color)?prefs.hero_color:DEFAULT.hero_color;
 const overlay=Math.max(.35,Math.min(.90,Number(prefs.hero_overlay)||.74));
 const toRgb=code=>[1,3,5].map(i=>parseInt(code.slice(i,i+2),16)).join(",");
 document.documentElement.style.setProperty("--fc-bg",page);
 document.documentElement.style.setProperty("--fc-canvas",page);
 document.documentElement.style.setProperty("--bg-primary",page);
 document.documentElement.style.setProperty("--admin-bg",page);
 const body=document.body;
 body.style.backgroundColor=page;
 const bg=url(prefs.page_image_url);
 body.style.backgroundImage=bg?"linear-gradient(rgba("+toRgb(page)+",.88),rgba("+toRgb(page)+",.88)),url("+JSON.stringify(bg)+")":"none";
 body.style.backgroundSize=bg?"cover":"";
 body.style.backgroundAttachment=bg?"fixed":"";
 body.style.backgroundPosition=bg?"center":"";
 const heroEl=document.querySelector(".fc-home-hero");
 if(heroEl){
  const photo=url(prefs.hero_image_url);
  heroEl.style.backgroundColor=hero;
  heroEl.style.backgroundImage=photo?"linear-gradient(rgba("+toRgb(hero)+","+overlay+"),rgba("+toRgb(hero)+","+Math.min(.98,overlay+.11)+")),url("+JSON.stringify(photo)+")":"none";
  heroEl.style.backgroundPosition="center";
  heroEl.style.backgroundSize="cover";
 }
}
async function load(){
 apply();
 try{const response=await fetch(API,{headers:{Accept:"application/json"}});
 if(!response.ok)return;const json=await response.json();if(json.success&&json.appearance)apply(json.appearance);
 }catch{ /* A published page must remain readable when settings API is unavailable. */ }
}
window.FarmConnectAppearance={apply,load};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",load);else load();
})();