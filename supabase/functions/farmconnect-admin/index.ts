
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
  sellers:["farm_name","contact_person","contact_phone","contact_email","commodity","available_volume","price_per_kg","location","is_verified","rating","status"],
  news:["title","content","summary","image_url","category","author_name","status","published_at"],
  sms_subscriptions:["user_id","commodity","market","alert_type","threshold","active"],
  sms_history:["phone","message","type","status","provider","sent_at","error_message"],
  messages:["from_user_id","to_user_id","subject","message","is_read"],
  news_comments:["news_id","user_id","comment"],
  news_likes:["news_id","user_id"],
  users:["username","email","phone","first_name","last_name","role","is_active","is_email_verified","location","province","district","main_crops","farm_size_hectares","business_name","sms_alerts_enabled"]
};
const bools=new Set(["is_active","is_verified","active","is_read","is_email_verified","sms_alerts_enabled","has_storage","has_weighbridge"]);
const numeric=new Set(["commodity_id","market_id","news_id","price","current_price","price_7d","price_14d","price_30d","volume","confidence","display_order","typical_min_price","typical_max_price","latitude","longitude","max_price","min_volume","available_volume","price_per_kg","rating","threshold","farm_size_hectares"]);
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
  if(resource==="audit" && req.method==="GET"){
   const {data,error}=await db.from("admin_audit_log").select("id,actor_id,action,resource,record_id,occurred_at").order("occurred_at",{ascending:false}).range(offset,offset+limit-1);
   if(error)throw error;return reply({success:true,records:data});
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
