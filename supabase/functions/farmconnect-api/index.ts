import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.4";
const headers = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Methods":"GET, POST, OPTIONS", "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type", "Content-Type":"application/json; charset=utf-8" };
const respond = (body: unknown, status=200) => new Response(JSON.stringify(body),{status,headers});
const url = Deno.env.get("SUPABASE_URL");
const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
if (!url || !key) throw new Error("Supabase server-side configuration missing");
const db = createClient(url,key,{auth:{persistSession:false}});
Deno.serve(async (req: Request) => {
 if(req.method==="OPTIONS") return new Response(null,{status:204,headers});

 const u=new URL(req.url);
 const endpoint=u.pathname.split("/").filter(Boolean).pop()||"status";
 const limit=Math.max(1,Math.min(Number(u.searchParams.get("limit"))||100,1000));

 const authClient = createClient(url!, Deno.env.get("SUPABASE_ANON_KEY") || key!, {auth:{persistSession:false,autoRefreshToken:false}});
 if(req.method==="POST" && (endpoint==="register" || endpoint==="login")){
   let body:any;try{body=await req.json()}catch{return respond({success:false,error:"Invalid JSON"},400)}
   if(endpoint==="register"){
     const username=String(body.username||"").trim(), email=String(body.email||"").trim().toLowerCase(), password=String(body.password||"");
     const name=String(body.name||"").trim(), role=["farmer","buyer","trader"].includes(body.role)?body.role:"farmer";
     if(!/^[a-zA-Z0-9_.-]{3,50}$/.test(username)||!/^\S+@\S+\.\S+$/.test(email)||password.length<10||password.length>128||!name) return respond({success:false,error:"Provide a valid username, email, name and password of at least 10 characters"},400);
     const {data:existing}=await db.from("users").select("id").eq("username",username).maybeSingle();
     if(existing) return respond({success:false,error:"Username already registered"},409);
     const {data:registered,error:registerError}=await authClient.auth.signUp({email,password,options:{data:{display_name:name}}});
     if(registerError||!registered.user) return respond({success:false,error:"Could not register account. Check email or try another address."},400);
     const user=registered.user;
     const names=name.split(/\s+/);
     const {error:profileError}=await db.from("users").upsert({
       id:user.id,username,email,password_hash:"managed-by-supabase-auth",
       first_name:names[0]||name,last_name:names.slice(1).join(" "),
       role,phone:body.phone?String(body.phone).slice(0,20):null,
       location:body.location?String(body.location).slice(0,200):null,
       business_name:body.business_name?String(body.business_name).slice(0,200):null,
       farm_size_hectares:Number(body.farm_size_hectares)||null,
       main_crops:body.main_crops?String(body.main_crops).split(",").map((x:string)=>x.trim()).filter(Boolean):null
     },{onConflict:"id"});
     if(profileError){console.error("Profile creation failed",profileError);return respond({success:false,error:"Account created but profile setup requires support; do not register again."},500)}
     const view={user_id:user.id,id:user.id,username,name,email,role};
     return respond({success:true,requires_email_confirmation:!registered.session,token:registered.session?.access_token||null,user:view});
   }
   const identifier=String(body.username||body.email||"").trim(), password=String(body.password||"");
   if(!identifier||!password) return respond({success:false,error:"Invalid credentials"},401);
   let email=identifier;
   if(!identifier.includes("@")){
     const lookup=await db.from("users").select("email").eq("username",identifier).maybeSingle();
     if(lookup.error||!lookup.data?.email)return respond({success:false,error:"Invalid credentials"},401);
     email=lookup.data.email;
   }
   const {data:session,error:signInError}=await authClient.auth.signInWithPassword({email,password});
   if(signInError||!session.session||!session.user) return respond({success:false,error:"Invalid credentials or unconfirmed email"},401);
   const {data:profile,error:profileError}=await db.from("users").select("id,username,first_name,last_name,role,email,location,is_active").eq("id",session.user.id).maybeSingle();
   if(profileError||!profile||profile.is_active===false)return respond({success:false,error:"Account is inactive or unavailable"},403);
   return respond({success:true,token:session.session.access_token,user:{user_id:profile.id,id:profile.id,username:profile.username,name:[profile.first_name,profile.last_name].filter(Boolean).join(" "),email:profile.email,role:profile.role,location:profile.location}});
 }
 if(req.method==="GET" && endpoint==="profile"){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   if(!token) return respond({success:false,error:"Authentication required"},401);
   const {data:userRecord,error:tokenError}=await db.auth.getUser(token);
   if(tokenError||!userRecord.user) return respond({success:false,error:"Invalid session"},401);
   const {data:profile,error:profileError}=await db.from("users").select("id,username,first_name,last_name,role,email,location,province,district,farm_size_hectares,main_crops,business_name").eq("id",userRecord.user.id).maybeSingle();
   if(profileError||!profile)return respond({success:false,error:"Profile not found"},404);
   return respond({success:true,user:profile,profile});
 }
 if(req.method==="GET" && endpoint==="stats" && u.pathname.includes("/admin/")){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   if(!token)return respond({success:false,error:"Admin authentication required"},401);
   const {data:identity,error:identityError}=await db.auth.getUser(token);
   if(identityError||!identity.user)return respond({success:false,error:"Invalid session"},401);
   const {data:access}=await db.from("users").select("role").eq("id",identity.user.id).maybeSingle();
   if(access?.role!=="admin")return respond({success:false,error:"Administrator access required"},403);
   const tables=["users","commodities","markets","price_history","live_prices","buyers","sellers","news","sms_subscriptions"];
   const stats:Record<string,number>={};
   for(const t of tables){const {count,error}=await db.from(t).select("id",{count:"exact",head:true});if(error)throw error;stats[t]=count||0;}
   return respond({success:true,stats,users:stats.users,commodities:stats.commodities,markets:stats.markets});
 }
 if(req.method==="GET" && endpoint==="forecast"){
   const commodity=String(u.searchParams.get("commodity")||"Maize"),market=u.searchParams.get("market");
   const days=Math.min(30,Math.max(1,Number(u.searchParams.get("days"))||7));
   const c=await db.from("commodities").select("id").eq("name",commodity).maybeSingle();
   if(!c.data)return respond({success:false,error:"Unknown commodity"},404);
   let query=db.from("price_history").select("price,price_date,markets!inner(name)").eq("commodity_id",c.data.id).eq("is_verified",true).order("price_date",{ascending:false}).limit(90);
   if(market)query=query.eq("markets.name",market);
   const {data:prices,error:priceError}=await query;
   if(priceError)throw priceError;
   if(!prices||prices.length<7)return respond({success:false,error:"Insufficient verified historical prices for a defensible forecast",required_observations:7,available_observations:prices?.length||0},422);
   const values=prices.map((p:any)=>Number(p.price)).filter(Number.isFinite);
   const latest=values[0], mean=values.slice(0,Math.min(7,values.length)).reduce((a:number,b:number)=>a+b,0)/Math.min(7,values.length);
   const observations=values.length;
   const forecast=Array.from({length:days},(_,i)=>({day:i+1,predicted_price:Math.round(mean*100)/100}));
   return respond({success:true,commodity,market:market||"All markets",model_used:"7-observation simple moving average baseline",current_price:latest,forecast,observations,notice:"Historical-price baseline, not a market demand forecast. Validate accuracy before decision-making."});
 }

 if(req.method!=="GET") return respond({success:false,error:"Unsupported operation"},405);
 try{
  if(endpoint==="status"){
   const tables=["commodities","markets","live_prices"];
   const counts:Record<string,number>={};
   for(const t of tables){ const {count,error}=await db.from(t).select("id",{count:"exact",head:true});if(error)throw error;counts[t]=count||0; }
   return respond({status:"online",success:true,version:"supabase-edge-1",database:"Supabase PostgreSQL",stats:counts});
  }
  if(endpoint==="commodities"||endpoint==="markets"){
   const query=endpoint==="commodities"
    ?db.from("commodities").select("id,name,category,sub_category,unit_of_measure,icon_emoji,color_code,description,is_active").eq("is_active",true).order("name").limit(limit)
    :db.from("markets").select("id,name,market_code,province,district,town,latitude,longitude,market_days,operating_hours,has_weighbridge,has_storage,is_active").eq("is_active",true).order("name").limit(limit);
   const {data,error}=await query;if(error)throw error;
   return respond({success:true,[endpoint]:data,count:data?.length||0});
  }
  if(endpoint==="news"){
   const {data,error}=await db.from("news").select("id,title,content,summary,image_url,category,author_name,status,view_count,like_count,comment_count,published_at,created_at").eq("status","published").order("published_at",{ascending:false}).limit(Math.min(limit,200));
   if(error)throw error;return respond({success:true,news:data,count:data?.length||0});
  }
  if(endpoint==="buyers"||endpoint==="sellers"){
   const columns=endpoint==="buyers"?"id,business_name,contact_person,contact_phone,contact_email,commodity,location,max_price,min_volume,notes,is_verified,rating,status":"id,farm_name,contact_person,contact_phone,contact_email,commodity,available_volume,price_per_kg,location,is_verified,rating,status";
   let query=db.from(endpoint).select(columns).eq("is_verified",true).eq("status","active").limit(limit);
   const commodity=u.searchParams.get("commodity");if(commodity)query=query.ilike("commodity",commodity);
   const {data,error}=await query;if(error)throw error;
   return respond({success:true,[endpoint]:data,count:data?.length||0});
  }
  if(endpoint==="history" && u.pathname.endsWith("/prices/history")){
   const commodity=String(u.searchParams.get("commodity")||"").trim(),market=String(u.searchParams.get("market")||"").trim();
   const days=Math.max(7,Math.min(Number(u.searchParams.get("days"))||365,3650));
   const since=new Date(Date.now()-days*86400000).toISOString().slice(0,10);
   let query=db.from("price_history").select("id,commodity_id,market_id,price,unit,trend,price_date,is_verified,source_name,source_url,data_kind,notes,commodities!inner(name),markets!inner(name,province)").gte("price_date",since).order("price_date",{ascending:false}).limit(1000);
   if(commodity&&commodity!=="all")query=query.eq("commodities.name",commodity);
   if(market&&market!=="all")query=query.eq("markets.name",market);
   const {data,error}=await query;if(error)throw error;
   const history=(data||[]).map((r:any)=>({id:r.id,commodity:r.commodities?.name,market:r.markets?.name,price:r.price,unit:r.unit,trend:r.trend,price_date:r.price_date,is_verified:r.is_verified===true,data_kind:r.data_kind||"observed",source_name:r.source_name,source_url:r.source_url}));
   const verified=history.filter((r:any)=>r.is_verified&&r.data_kind!=="demo").length;
   return respond({success:true,history,count:history.length,verified_count:verified,demo_count:history.filter((r:any)=>r.data_kind==="demo").length,notice:"DEMO rows are synthetic, not observed prices. Only verified sourced prices are real market evidence."});
  }
  if(endpoint==="prices" || (endpoint==="real" && u.pathname.endsWith("/prices/real"))){
   // Only real verified observations, no simulated market prices.
   let query=db.from("price_history").select("id,price,unit,trend,price_date,recorded_at,commodities!inner(name,icon_emoji),markets!inner(name,province)").eq("is_verified",true).order("price_date",{ascending:false}).limit(limit);
   const commodity=u.searchParams.get("commodity"),market=u.searchParams.get("market");
   if(commodity)query=query.eq("commodities.name",commodity);
   if(market)query=query.eq("markets.name",market);
   const {data,error}=await query;if(error)throw error;
   const prices=(data||[]).map((r:any)=>({id:r.id,commodity_name:r.commodities?.name,commodity:r.commodities?.name,icon_emoji:r.commodities?.icon_emoji,market_name:r.markets?.name,market:r.markets?.name,province:r.markets?.province,price:r.price,unit:r.unit,trend:r.trend,last_updated:r.recorded_at,is_verified:true}));
   return respond({success:true,prices,count:prices.length});
  }
  return respond({success:false,error:"Unknown endpoint"},404);
 }catch(e){console.error("FarmConnect API failure",e);return respond({success:false,error:"Database request failed"},500);}
});
