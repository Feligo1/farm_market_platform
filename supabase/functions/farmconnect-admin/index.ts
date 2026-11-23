
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.4";
const sbUrl = Deno.env.get("SUPABASE_URL") || "";
const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const db = createClient(sbUrl,serviceKey,{auth:{persistSession:false,autoRefreshToken:false}});
const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,PATCH,DELETE,OPTIONS","Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Content-Type":"application/json"};
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:cors});
const schema:Record<string,string[]>={
  commodities:["name","category","sub_category","unit_of_measure","icon_emoji","icon_url","color_code","typical_min_price","typical_max_price","description","is_active","display_order"],
  markets:["name","market_code","province","district","town","latitude","longitude","address","market_days","operating_hours","contact_phone","has_weighbridge","has_storage","is_active"],
  price_history:["commodity_id","market_id","price","unit","volume","quality","source_type","source_name","source_url","external_id","currency","data_kind","is_verified","trend","price_date","notes"],
  live_prices:["commodity_id","market_id","current_price","price_7d","price_14d","price_30d","trend","recommendation","confidence"],
  buyers:["business_name","contact_person","contact_phone","contact_email","commodity","location","max_price","min_volume","notes","is_verified","rating","added_by","status"],
  sellers:["farm_name","contact_person","contact_phone","contact_email","commodity","available_volume","price_per_kg","location","notes","is_verified","rating","status"],
  news:["title","content","summary","image_url","video_url","source_url","category","author_name","status","published_at"],
  advertisements:["title","description","image_url","video_url","target_url","placement","status","starts_at","ends_at","sort_order"],
  sms_subscriptions:["user_id","commodity","market","alert_type","threshold","active"],
  sms_history:["phone","message","type","status","provider","sent_at","error_message"],
  messages:["from_user_id","to_user_id","subject","message","is_read"],
  news_comments:["news_id","user_id","comment"],
  news_likes:["news_id","user_id"],
  users:["username","email","phone","first_name","last_name","role","is_active","is_email_verified","location","province","district","main_crops","farm_size_hectares","business_name","sms_alerts_enabled"]
};
const bools=new Set(["is_active","is_verified","active","is_read","is_email_verified","sms_alerts_enabled","has_storage","has_weighbridge"]);
const numeric=new Set(["commodity_id","market_id","news_id","price","current_price","price_7d","price_14d","price_30d","volume","confidence","display_order","typical_min_price","typical_max_price","latitude","longitude","max_price","min_volume","available_volume","price_per_kg","rating","threshold","farm_size_hectares","sort_order"]);
const protect=(resource:string,input:Record<string,unknown>)=>{
 const clean:Record<string,unknown>={};
 for(const field of schema[resource]||[]){
   if(!(field in input))continue;
   let value=input[field];
   if(value===""||value===undefined){clean[field]=null;continue;}
   if(bools.has(field)){if(typeof value!=="boolean")throw new Error(field+" must be boolean");}
   if(numeric.has(field)){if(!Number.isFinite(Number(value)))throw new Error(field+" must be numeric");value=Number(value);}
   if(field==="main_crops"){if(!Array.isArray(value))value=String(value).split(",").map((v)=>v.trim());}
   if(typeof value==="string" && value.length>10000)throw new Error(field+" too long");
   clean[field]=value;
 }
 if(["news","advertisements"].includes(resource)){
   for(const col of ["image_url","video_url","source_url","target_url"]){
     if(typeof clean[col]==="string" && clean[col] && !/^https:\/\//i.test(String(clean[col])))throw new Error(col+" must start with https://");
     if(typeof clean[col]==="string" && clean[col] && String(clean[col]).length>2000)throw new Error(col+" URL too long");
   }
   if(clean.status && !["draft","published","paused"].includes(String(clean.status)))throw new Error("Invalid publishing status");
   if(resource==="advertisements" && clean.placement && !["home","news","both"].includes(String(clean.placement)))throw new Error("Invalid ad placement");
   if(resource==="news" && clean.status==="published" && !clean.published_at && !input.published_at)clean.published_at=new Date().toISOString();
 }
 if(resource==="price_history"){
   if(clean.data_kind==="demo"){clean.is_verified=false;clean.source_type="DEMO_SYNTHETIC";}
   if(clean.source_type==="DEMO_SYNTHETIC"){clean.is_verified=false;clean.data_kind="demo";}
   if(clean.is_verified===true && !clean.source_name && !input.source_name)throw new Error("Verified prices require a source_name");
   if(clean.price!==undefined && clean.price!==null && Number(clean.price)<=0)throw new Error("Price must be positive");
 }
 return clean;
};
const audit=async (uid:string,action:string,resource:string,recordId:unknown)=>{
 const {error}=await db.from("admin_audit_log").insert({actor_id:uid,action,resource,record_id:String(recordId||"")});
 if(error)console.error("audit error",error.message);
};
Deno.serve(async(req:Request)=>{
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 if(!sbUrl||!serviceKey)return reply({success:false,error:"Backend not configured"},503);
 const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
 if(!token)return reply({success:false,error:"Login required"},401);
 const {data:identity,error:authError}=await db.auth.getUser(token);
 if(authError||!identity.user)return reply({success:false,error:"Invalid or expired session"},401);
 const actor=identity.user.id;
 const {data:account,error:accountError}=await db.from("users").select("role,is_active,email").eq("id",actor).maybeSingle();
 if(accountError||!account||account.role!=="admin"||account.is_active!==true)return reply({success:false,error:"Admin access required"},403);
 const u=new URL(req.url), resource=u.searchParams.get("resource")||"price_history",id=u.searchParams.get("id"),limit=Math.min(Math.max(Number(u.searchParams.get("limit"))||100,1),500),offset=Math.max(Number(u.searchParams.get("offset"))||0,0);
 try{
  if(resource==="media_upload" && req.method==="POST"){
    const input=await req.json().catch(()=>null);
    const mime=String(input?.mime||"").toLowerCase();
    const allowed:Record<string,string>={"image/jpeg":"jpg","image/png":"png","image/webp":"webp","image/gif":"gif","video/mp4":"mp4","video/webm":"webm"};
    if(!allowed[mime])return reply({success:false,error:"Unsupported media type. Use JPG, PNG, WebP, GIF, MP4 or WebM."},400);
    const encoded=String(input?.base64||"");
    if(encoded.length>8600000||encoded.length<10)return reply({success:false,error:"File is empty or exceeds 6 MB. Use an HTTPS video URL for larger video ads."},413);
    let bytes:Uint8Array;
    try{const decoded=atob(encoded);bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));}catch{return reply({success:false,error:"Invalid uploaded media"},400)}
    if(bytes.length>6000000)return reply({success:false,error:"Maximum media upload is 6 MB"},413);
    const ext=allowed[mime],fileName=actor+"/"+crypto.randomUUID()+"."+ext;
    const {error:uploadError}=await db.storage.from("farmconnect-media").upload(fileName,bytes,{contentType:mime,upsert:false,cacheControl:"3600"});
    if(uploadError)throw uploadError;
    const {data:publicUrl}=db.storage.from("farmconnect-media").getPublicUrl(fileName);
    await audit(actor,"upload","farmconnect-media",fileName);
    return reply({success:true,url:publicUrl.publicUrl,mime});
  }
  if(resource==="appearance"){
    if(req.method==="GET"){
      const {data,error}=await db.from("site_appearance").select("hero_image_url,hero_color,page_image_url,page_color,hero_overlay,updated_at").eq("id",1).single();
      if(error)throw error;return reply({success:true,appearance:data});
    }
    if(req.method!=="POST")return reply({success:false,error:"Method not allowed"},405);
    const input=await req.json().catch(()=>null);
    if(!input||typeof input!=="object"||Array.isArray(input))return reply({success:false,error:"Invalid appearance settings"},400);
    const colors=["hero_color","page_color"],urls=["hero_image_url","page_image_url"];
    const payload:Record<string,unknown>={};
    for(const field of colors){
      const color=String(input[field]||"");
      if(!/^#[0-9a-fA-F]{6}$/.test(color))return reply({success:false,error:"Choose a valid six-digit background colour"},400);
      payload[field]=color;
    }
    for(const field of urls){
      const source=String(input[field]||"").trim();
      if(source && (source.length>1900 || !/^https:\/\//i.test(source)))return reply({success:false,error:"Background images must have a valid HTTPS URL"},400);
      payload[field]=source||null;
    }
    const overlay=Number(input.hero_overlay);
    if(!Number.isFinite(overlay)||overlay<0.35||overlay>0.90)return reply({success:false,error:"Overlay must be between 35% and 90%"},400);
    payload.hero_overlay=overlay;payload.updated_at=new Date().toISOString();
    const {data,error}=await db.from("site_appearance").update(payload).eq("id",1).select("*").single();
    if(error)throw error;
    await audit(actor,"update","site_appearance",1);
    return reply({success:true,appearance:data});
  }
  if(resource==="pending_listings" && req.method==="GET"){
    const [buyerResult,sellerResult]=await Promise.all([
      db.from("buyers").select("id,business_name,contact_person,contact_phone,commodity,location,min_volume,max_price,notes,created_at").eq("status","pending").eq("is_verified",false).order("created_at",{ascending:false}).limit(100),
      db.from("sellers").select("id,farm_name,contact_person,contact_phone,commodity,location,available_volume,price_per_kg,notes,created_at").eq("status","pending").eq("is_verified",false).order("created_at",{ascending:false}).limit(100)
    ]);
    if(buyerResult.error||sellerResult.error)throw buyerResult.error||sellerResult.error;
    const pending=[
      ...(buyerResult.data||[]).map((v:any)=>({...v,kind:"buyer",name:v.business_name,quantity:v.min_volume,price:v.max_price})),
      ...(sellerResult.data||[]).map((v:any)=>({...v,kind:"seller",name:v.farm_name,quantity:v.available_volume,price:v.price_per_kg}))
    ].sort((a:any,b:any)=>String(b.created_at).localeCompare(String(a.created_at)));
    return reply({success:true,listings:pending,count:pending.length});
  }
  if(resource==="review_listing" && req.method==="POST"){
    const body=await req.json().catch(()=>null);
    const kind=String(body?.kind||"");
    const id=Number(body?.id),action=String(body?.action||"");
    if(!["buyer","seller"].includes(kind)||!Number.isSafeInteger(id)||id<=0||!["approve","reject"].includes(action))
      return reply({success:false,error:"Invalid review request"},400);
    const table=kind==="buyer"?"buyers":"sellers";
    const {data:existing,error:findError}=await db.from(table).select("id,status,is_verified").eq("id",id).maybeSingle();
    if(findError)throw findError;
    if(!existing||existing.status!=="pending"||existing.is_verified===true)return reply({success:false,error:"Listing is no longer awaiting review"},409);
    const change=action==="approve"?{status:"active",is_verified:true}:{status:"rejected",is_verified:false};
    const {data:updated,error:updateError}=await db.from(table).update(change).eq("id",id).eq("status","pending").eq("is_verified",false).select("id,status").maybeSingle();
    if(updateError)throw updateError;
    if(!updated)return reply({success:false,error:"Listing status changed; refresh the queue"},409);
    await audit(actor,action,table,id);
    return reply({success:true,status:updated.status});
  }
  if(resource==="audit" && req.method==="GET"){
   const {data,error}=await db.from("admin_audit_log").select("id,actor_id,action,resource,record_id,occurred_at").order("occurred_at",{ascending:false}).range(offset,offset+limit-1);
   if(error)throw error;return reply({success:true,records:data});
  }

  if(resource==="bulk_history" && req.method==="POST"){
    const body=await req.json().catch(()=>null);
    if(!body||!Array.isArray(body.records)||body.records.length<1||body.records.length>200)
      return reply({success:false,error:"Supply between 1 and 200 records"},400);
    const commodities=(await db.from("commodities").select("id,name").limit(500)).data||[];
    const markets=(await db.from("markets").select("id,name").limit(500)).data||[];
    const norm=(v:unknown)=>String(v||"").trim().toLowerCase().replace(/[^a-z0-9]/g,"");
    const batch:any[]=[],skipped:any[]=[];
    for(const [i,r] of body.records.entries()){
      const c=commodities.find((x:any)=>norm(x.name)===norm(r.commodity));
      const m=markets.find((x:any)=>norm(x.name)===norm(r.market));
      const price=Number(r.price),date=String(r.date||r.price_date||"");
      const currency=String(r.currency||"ZMW").toUpperCase(),unit=String(r.unit||"kg").toLowerCase();
      const source=String(r.source_name||"").trim(),srcUrl=String(r.source_url||"").trim();
      if(!c||!m||!Number.isFinite(price)||price<=0||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(date)||currency!=="ZMW"||!["kg","kilogram","kilograms"].includes(unit)||!source||source.length>100||!srcUrl.startsWith("https://")||!Number.isFinite(new Date(date).getTime())||date>new Date().toISOString().slice(0,10)){
        skipped.push({row:i+1,reason:"Market, commodity, ZMW/kg price, valid date or source could not be validated"});continue;
      }
      const sourceId=String(r.external_id||[norm(r.commodity),norm(r.market),date,price].join("-")).slice(0,240);
      batch.push({commodity_id:c.id,market_id:m.id,price:Math.round(price*100)/100,price_date:date,unit:"kg",currency:"ZMW",source_type:"ADMIN_IMPORTED",source_name:source,source_url:srcUrl,external_id:sourceId,is_verified:false,data_kind:"observed",notes:"Sourced historical observation imported by administrator; pending verification"});
    }
    if(!batch.length)return reply({success:false,error:"No valid rows. Use exact FarmConnect market and commodity names; ZMW per kg only.",skipped:skipped.slice(0,20)},422);
    const {data,error}=await db.from("price_history").upsert(batch,{onConflict:"source_name,external_id",ignoreDuplicates:true}).select("id");
    if(error)throw error;
    await audit(actor,"import","price_history",data?.length||0);
    return reply({success:true,imported:data?.length||0,skipped:skipped.length,errors:skipped.slice(0,20),verified:false,notice:"Imported observations require administrator source verification before public use"});
  }
  if(resource==="import_fews" && req.method==="POST"){
    const input=await req.json().catch(()=>({}));
    const offset=Math.max(0,Math.min(Number(input.offset)||0,20000));
    const sourceUrl=new URL("https://fdw.fews.net/api/marketpricefacts.json");
    sourceUrl.searchParams.set("country_code","ZM");sourceUrl.searchParams.set("page_size","100");sourceUrl.searchParams.set("offset",String(offset));
    sourceUrl.searchParams.set("start_date","2024-01-01");
    let resp:Response;
    try{resp=await fetch(sourceUrl,{headers:{"Accept":"application/json"},signal:AbortSignal.timeout(12000)})}
    catch{return reply({success:false,error:"FEWS NET source could not be reached. Import a CSV file instead."},502)}
    if(!resp.ok)return reply({success:false,error:"FEWS NET request returned HTTP "+resp.status},502);
    const raw:any=await resp.json().catch(()=>null);
    const rows=Array.isArray(raw)?raw:Array.isArray(raw?.results)?raw.results:[];
    const commodities=(await db.from("commodities").select("id,name")).data||[];
    const markets=(await db.from("markets").select("id,name")).data||[];
    const norm=(v:any)=>String(typeof v==="object"?(v?.name||v?.label||""):v||"").toLowerCase().trim().replace(/[^a-z0-9]/g,"");
    const mapped:any[]=[];let unmatched=0;
    for(const x of rows){
      const product=norm(x.product||x.product_name),market=norm(x.market||x.market_name);
      const commodity=commodities.find((c:any)=>norm(c.name)===product||norm(c.name)==="maize"&&["maizegrain","maizewhite","whitemaize","maize"].includes(product));
      const target=markets.find((m:any)=>norm(m.name)===market||norm(m.name)+"market"===market);
      const price=Number(x.value??x.price),date=String(x.period_date||x.price_date||x.date||"").slice(0,10);
      const cur=norm(x.currency||x.currency_code||"zmw"),unit=norm(x.unit||x.unit_name||"kg");
      if(!commodity||!target||!Number.isFinite(price)||price<=0||cur!=="zmw"||!["kg","kilogram","kilograms"].includes(unit)||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(date)){unmatched++;continue;}
      const sourceId=String(x.id||x.dataseries||"series")+":"+product+":"+market+":"+date+":"+price;
      mapped.push({commodity_id:commodity.id,market_id:target.id,price:Math.round(price*100)/100,unit:"kg",currency:"ZMW",price_date:date,source_type:"FEWS_NET",source_name:"FEWS NET FDW",source_url:sourceUrl.toString(),external_id:sourceId.slice(0,240),is_verified:false,data_kind:"observed",notes:"FEWS NET Zambia API record — administrator verification required; verify price type and source before approval"});
    }
    let imported=0;
    if(mapped.length){
      const {data,error}=await db.from("price_history").upsert(mapped,{onConflict:"source_name,external_id",ignoreDuplicates:true}).select("id");
      if(error)throw error;imported=data?.length||0;
    }
    await audit(actor,"import-fews","price_history",imported);
    return reply({success:true,fetched:rows.length,imported,unmatched,offset,next_offset:offset+rows.length,has_more:!!raw?.next,notice:"Imported FEWS records remain unverified until matched against original metadata and reviewed by an administrator."});
  }
  if(!schema[resource])return reply({success:false,error:"Unsupported resource"},400);
  if(req.method==="GET"){
   let query=db.from(resource).select("*",{count:"exact"}).order(resource==="price_history"?"price_date":resource==="users"?"created_at":"id",{ascending:false}).range(offset,offset+limit-1);
   if(resource==="price_history"){
     const commodity=u.searchParams.get("commodity_id"),market=u.searchParams.get("market_id"),kind=u.searchParams.get("data_kind");
     if(commodity)query=query.eq("commodity_id",commodity);
     if(market)query=query.eq("market_id",market);
     if(kind && ["demo","observed"].includes(kind))query=query.eq("data_kind",kind);
   }
   const {data,count,error}=await query;if(error)throw error;
   const cleaned=resource==="users"?(data||[]).map(({password_hash,ussd_pin_hash,...rest}:any)=>rest):data;
   return reply({success:true,records:cleaned,count,fields:schema[resource],resource});
  }
  if(!["POST","PATCH","DELETE"].includes(req.method))return reply({success:false,error:"Method not allowed"},405);
  const input=req.method==="DELETE"?{}:await req.json().catch(()=>null);
  if(req.method!=="DELETE" && (!input||typeof input!=="object"||Array.isArray(input)))return reply({success:false,error:"Invalid object"},400);
  if((req.method==="PATCH"||req.method==="DELETE")&&!id)return reply({success:false,error:"Record ID required"},400);
  if(resource==="users"){
   if(req.method==="DELETE"){
     if(id===actor)return reply({success:false,error:"You cannot deactivate yourself"},400);
     const {data,error}=await db.from("users").update({is_active:false}).eq("id",id).select("id,username,is_active").single();if(error)throw error;
     await audit(actor,"deactivate","users",id);return reply({success:true,record:data});
   }
   if(req.method==="POST"){
     const body=input as Record<string,unknown>, email=String(body.email||"").trim().toLowerCase(),username=String(body.username||"").trim(),password=String(body.password||"");
     if(!email.includes("@")||username.length<3||password.length<10)return reply({success:false,error:"Email, username and a password of at least 10 characters are required"},400);
     const role=["admin","farmer","buyer","trader"].includes(String(body.role))?String(body.role):"farmer";
     const {data:userData,error:createError}=await db.auth.admin.createUser({email,password,email_confirm:true});
     if(createError||!userData.user)return reply({success:false,error:createError?.message||"Could not create auth user"},400);
     const row={...protect("users",body),id:userData.user.id,email,username,role,password_hash:"managed-by-supabase-auth",is_email_verified:true};
     const {data,error}=await db.from("users").insert(row).select("id,username,email,role,is_active").single();if(error)throw error;
     await audit(actor,"create","users",data.id);return reply({success:true,record:data},201);
   }
   const patch=protect("users",input as Record<string,unknown>);
   if(id===actor && (patch.role && patch.role!=="admin" || patch.is_active===false))return reply({success:false,error:"Cannot remove own administrator access"},400);
   if(patch.role && patch.role!=="admin"){
     const {data:target}=await db.from("users").select("role").eq("id",id).single();
     if(target?.role==="admin"){
       const {count}=await db.from("users").select("id",{count:"exact",head:true}).eq("role","admin").eq("is_active",true);
       if((count||0)<=1)return reply({success:false,error:"Cannot remove last administrator"},400);
     }
   }
   delete patch.email; // Auth email changes must happen through verified Supabase Auth flow
   const {data,error}=await db.from("users").update(patch).eq("id",id).select("id,username,email,role,is_active").single();if(error)throw error;
   await audit(actor,"update","users",id);return reply({success:true,record:data});
  }
  if(req.method==="DELETE"){
   const {data,error}=await db.from(resource).delete().eq("id",id).select("id").single();
   if(error)throw error;await audit(actor,"delete",resource,id);return reply({success:true,record:data});
  }
  const payload=protect(resource,input as Record<string,unknown>);
  if(Object.keys(payload).length===0)return reply({success:false,error:"No editable fields"},400);
  if(resource==="price_history" && req.method==="POST"){
   if(!payload.commodity_id||!payload.market_id||!payload.price||!payload.price_date)return reply({success:false,error:"Commodity, market, price and date required"},400);
  }
  if(req.method==="POST"){
   const {data,error}=await db.from(resource).insert(payload).select("*").single();if(error)throw error;
   await audit(actor,"create",resource,data.id);return reply({success:true,record:data},201);
  }
  const {data,error}=await db.from(resource).update(payload).eq("id",id).select("*").single();if(error)throw error;
  await audit(actor,"update",resource,id);return reply({success:true,record:data});
 }catch(error){
  console.error("FarmConnect admin API",error);
  return reply({success:false,error:"Database operation failed; check field values or related records"},400);
 }
});
