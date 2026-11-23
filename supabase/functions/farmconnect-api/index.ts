import { createClient } from "https://esm.sh/@supabase/supabase-js@2.57.4";
const headers = { "Access-Control-Allow-Origin":"*", "Access-Control-Allow-Methods":"GET, POST, PUT, PATCH, OPTIONS", "Access-Control-Allow-Headers":"authorization, x-client-info, apikey, content-type", "Content-Type":"application/json; charset=utf-8" };
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
 if(req.method==="POST" && endpoint==="register") return respond({success:false,error:"Public registration is disabled. FarmConnect is free to use without an account."},410);
 if(req.method==="POST" && (endpoint==="register" || endpoint==="login")){
   let body:any;try{body=await req.json()}catch{return respond({success:false,error:"Invalid JSON"},400)}
   if(endpoint==="register"){
     const email=String(body.email||"").trim().toLowerCase(), password=String(body.password||"");
     let username=String(body.username||"").trim();
     if(!/^\S+@\S+\.\S+$/.test(email)||password.length<8||password.length>128)
       return respond({success:false,error:"Enter a valid email address and a password of at least 8 characters."},400);
     if(username&&!/^[a-zA-Z0-9_.-]{3,50}$/.test(username))
       return respond({success:false,error:"Username must have 3–50 letters, numbers, dots, underscores or hyphens."},400);
     if(username){
       const existing=await db.from("users").select("id").ilike("username",username).maybeSingle();
       if(existing.data)return respond({success:false,error:"Username is already taken."},409);
     }else{
       const prefix=email.split("@")[0].replace(/[^a-zA-Z0-9_.-]/g,"").slice(0,22)||"member";
       username=prefix+"_"+crypto.randomUUID().slice(0,8);
     }
     const {data:registered,error:registerError}=await authClient.auth.signUp({email,password});
     if(registerError){
       if(registerError.code==="over_email_send_rate_limit"||registerError.status===429||/email rate limit exceeded/i.test(registerError.message||""))
         return respond({success:false,code:"EMAIL_RATE_LIMIT",error:"Registration emails are temporarily unavailable because the Supabase email limit was reached. Please try again after the email allowance resets. The administrator needs to configure custom SMTP for reliable public registration."},429);
       if(registerError.code==="email_address_not_authorized")
         return respond({success:false,code:"EMAIL_PROVIDER_RESTRICTED",error:"This email provider currently accepts only approved project addresses. The FarmConnect administrator must configure custom SMTP before public signup."},503);
       return respond({success:false,error:registerError.message||"Account registration failed."},400);
     }
     if(!registered.user||!registered.user.identities?.length)
       return respond({success:true,requires_email_confirmation:true,message:"If this address can be registered, check its inbox for confirmation."});
     const user=registered.user;
     const {error:profileError}=await db.from("users").insert({
       id:user.id,username,email,password_hash:"managed-by-supabase-auth",role:"farmer",
       first_name:null,last_name:null,is_active:true,is_email_verified:!!user.email_confirmed_at
     });
     if(profileError){console.error("Registration profile error",profileError);return respond({success:false,error:"Account created but profile setup needs support. Do not register again."},500)}
     const view={user_id:user.id,id:user.id,username,name:username,email,role:"farmer"};
     return respond({success:true,requires_email_confirmation:!registered.session,token:registered.session?.access_token||null,user:view,message:registered.session?"Account created. Complete your profile when ready.":"Check your email to confirm your account before logging in."});
   }
   const identifier=String(body.username||body.email||"").trim(), password=String(body.password||"");
   if(!identifier||!password) return respond({success:false,error:"Invalid credentials"},401);
   let email=identifier;
   if(!identifier.includes("@")){
     const lookup=await db.from("users").select("email").ilike("username",identifier).maybeSingle();
     if(lookup.error||!lookup.data?.email)return respond({success:false,error:"Invalid credentials"},401);
     email=lookup.data.email;
   }
   const {data:session,error:signInError}=await authClient.auth.signInWithPassword({email,password});
   if(signInError||!session.session||!session.user) return respond({success:false,error:"Invalid credentials or unconfirmed email"},401);
   const {data:profile,error:profileError}=await db.from("users").select("id,username,first_name,last_name,role,email,location,is_active").eq("id",session.user.id).maybeSingle();
   if(profileError||!profile||profile.is_active===false)return respond({success:false,error:"Account is inactive or unavailable"},403);
   return respond({success:true,token:session.session.access_token,user:{user_id:profile.id,id:profile.id,username:profile.username,name:[profile.first_name,profile.last_name].filter(Boolean).join(" "),email:profile.email,role:profile.role,location:profile.location}});
 }
 if(endpoint==="profile" && ["GET","PUT","PATCH"].includes(req.method)){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   if(!token)return respond({success:false,error:"Please log in."},401);
   const {data:identity,error:identityError}=await db.auth.getUser(token);
   if(identityError||!identity.user)return respond({success:false,error:"Session expired. Please log in again."},401);
   const userId=identity.user.id;
   const {data:account,error:readError}=await db.from("users").select("*").eq("id",userId).maybeSingle();
   if(readError||!account||account.is_active===false)return respond({success:false,error:"Account is unavailable."},403);
   const userView=(x:any)=>{const {password_hash,ussd_pin_hash,...safe}=x;return {...safe,name:[x.first_name,x.last_name].filter(Boolean).join(" ")||x.username,sms_alerts:x.sms_alerts_enabled};};
   if(req.method==="GET")return respond({success:true,profile:userView(account),user:userView(account)});
   const body:any=await req.json().catch(()=>null);
   if(!body||typeof body!=="object"||Array.isArray(body))return respond({success:false,error:"Invalid profile details."},400);
   const allowed=["first_name","last_name","phone","location","province","district","farm_size_hectares","main_crops","business_name","business_registration_number","preferred_language","sms_alerts_enabled","email_alerts_enabled","notification_frequency"];
   const data:Record<string,unknown>={};
   for(const field of allowed)if(Object.prototype.hasOwnProperty.call(body,field)){
     let value=body[field];
     if(typeof value==="string"){value=value.trim().slice(0,250);if(!value)value=null}
     if(field==="main_crops")value=(Array.isArray(value)?value:String(value||"").split(",")).map((v:any)=>String(v).trim()).filter(Boolean).slice(0,30);
     if(field==="farm_size_hectares")value=value===null||value===""?null:Number(value);
     if(field==="farm_size_hectares" && value!==null && (!Number.isFinite(value)||Number(value)<0))return respond({success:false,error:"Invalid farm size."},400);
     if(["sms_alerts_enabled","email_alerts_enabled"].includes(field)){if(typeof value!=="boolean")return respond({success:false,error:field+" must be true or false."},400)}
     data[field]=value;
   }
   if("username" in body){
     const candidate=String(body.username||"").trim();
     if(!/^[a-zA-Z0-9_.-]{3,50}$/.test(candidate))return respond({success:false,error:"Username must have 3–50 letters, numbers, dots, underscores or hyphens."},400);
     if(candidate.toLowerCase()!==String(account.username).toLowerCase()){
       const {data:collision,error:collisionError}=await db.from("users").select("id").ilike("username",candidate).neq("id",userId).maybeSingle();
       if(collisionError)return respond({success:false,error:"Could not check username availability."},500);
       if(collision)return respond({success:false,error:"Username is already taken."},409);
       data.username=candidate;
     }
   }
   if("name" in body&&!("first_name" in body)){
      const names=String(body.name||"").trim().slice(0,200).split(/\s+/).filter(Boolean);
      data.first_name=names[0]||null;data.last_name=names.slice(1).join(" ")||null;
   }
   if("role" in body && account.role!=="admin"){
     const newRole=String(body.role);
     if(!["farmer","buyer","trader"].includes(newRole))return respond({success:false,error:"Invalid account type."},400);
     data.role=newRole;
   }
   if(!Object.keys(data).length)return respond({success:false,error:"No profile fields provided."},400);
   const {data:saved,error:saveError}=await db.from("users").update(data).eq("id",userId).select("*").single();
   if(saveError){console.error("Profile update failed",saveError);return respond({success:false,error:"Could not save profile details."},500)}
   return respond({success:true,profile:userView(saved),user:userView(saved)});
 }
 if(endpoint==="password" && req.method==="PUT" && u.pathname.includes("/profile/")){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   const {data:identity,error:identityError}=await db.auth.getUser(token);
   if(identityError||!identity.user)return respond({success:false,error:"Please log in again."},401);
   const body:any=await req.json().catch(()=>null);
   const current=String(body?.current_password||""),replacement=String(body?.new_password||"");
   if(!current||replacement.length<8||replacement.length>128)return respond({success:false,error:"Current password and new password (8+ characters) are required."},400);
   const {error:verifyError}=await authClient.auth.signInWithPassword({email:identity.user.email!,password:current});
   if(verifyError)return respond({success:false,error:"Current password is incorrect."},401);
   const {error:changeError}=await db.auth.admin.updateUserById(identity.user.id,{password:replacement});
   if(changeError){console.error("Password update failed",changeError);return respond({success:false,error:"Could not change password."},500)}
   return respond({success:true,message:"Password changed. Sign in again using your new password."});
 }
 if(endpoint==="subscriptions" && req.method==="GET" && u.pathname.includes("/sms/")){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   const {data:identity,error}=await db.auth.getUser(token);
   if(error||!identity.user)return respond({success:false,error:"Log in to view subscriptions."},401);
   const {data,error:readError}=await db.from("sms_subscriptions").select("id,commodity,market,alert_type,threshold,active").eq("user_id",identity.user.id).order("created_at",{ascending:false});
   if(readError)throw readError;
   return respond({success:true,subscriptions:data});
 }
 if(["subscribe","unsubscribe"].includes(endpoint) && req.method==="POST" && u.pathname.includes("/sms/")){
   const token=(req.headers.get("authorization")||"").replace(/^Bearer\s+/i,"");
   const {data:identity,error}=await db.auth.getUser(token);
   if(error||!identity.user)return respond({success:false,error:"Please log in."},401);
   const body:any=await req.json().catch(()=>({}));
   if(endpoint==="subscribe"){
     const commodity=String(body.commodity||"").trim();
     if(!commodity||commodity.length>90)return respond({success:false,error:"Choose a commodity."},400);
     const {data:exists}=await db.from("commodities").select("name").eq("name",commodity).maybeSingle();
     if(!exists)return respond({success:false,error:"Unknown commodity."},400);
     const {data:created,error:insertError}=await db.from("sms_subscriptions").insert({user_id:identity.user.id,commodity,alert_type:"price_change",threshold:Number(body.threshold)||5,active:true}).select("id").single();
     if(insertError)throw insertError;
     return respond({success:true,id:created.id,notice:"Alert preferences saved; SMS delivery is not yet enabled."});
   }
   let query=db.from("sms_subscriptions").update({active:false}).eq("user_id",identity.user.id);
   if(body.id)query=query.eq("id",body.id);else if(body.commodity)query=query.eq("commodity",String(body.commodity));else return respond({success:false,error:"Select subscription."},400);
   const {error:updateError}=await query;if(updateError)throw updateError;
   return respond({success:true});
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
   const commodity=String(u.searchParams.get("commodity")||"Maize").trim();
   const market=String(u.searchParams.get("market")||"").trim();

   const rawMonths=Number(u.searchParams.get("months")||"3");
   if(!Number.isInteger(rawMonths)||rawMonths<1||rawMonths>12)
     return respond({success:false,error:"Choose between 1 and 12 forecast months."},400);
   const months=rawMonths;
   const {data:commodityRecord,error:commodityError}=await db.from("commodities").select("id,unit_of_measure").eq("name",commodity).maybeSingle();
   if(commodityError)throw commodityError;
   if(!commodityRecord)return respond({success:false,error:"Unknown commodity"},404);
   if(!market)return respond({success:false,error:"Select a market"},400);
   const {data:marketRecord,error:marketError}=await db.from("markets").select("id").eq("name",market).maybeSingle();
   if(marketError)throw marketError;
   if(!marketRecord)return respond({success:false,error:"Unknown market"},404);
   const unit=String(commodityRecord.unit_of_measure||"kg");
   const monthDate=(value:string,offset:number)=>{
     const d=new Date(value+"T00:00:00Z");
     return new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+offset,1)).toISOString().slice(0,10);
   };
   type Observation={date:string;price:number};
   let history:Observation[]=[];
   const {data:rows,error:historyError}=await db.from("price_history")
     .select("price,price_date").eq("commodity_id",commodityRecord.id)
     .eq("market_id",marketRecord.id).eq("is_verified",true)
     .neq("data_kind","demo").order("price_date",{ascending:false}).limit(500);
   if(historyError)throw historyError;
   const byMonth=new Map<string,{total:number;count:number}>();
   for(const row of rows||[]){
     const date=String(row.price_date||"").slice(0,7);
     const price=Number(row.price);
     if(!/^\d{4}-\d{2}$/.test(date)||!Number.isFinite(price)||price<=0)continue;
     const record=byMonth.get(date)||{total:0,count:0};
     record.total+=price;record.count++;byMonth.set(date,record);
   }
   history=[...byMonth.entries()].sort(([a],[b])=>a.localeCompare(b))
     .map(([month,v])=>({date:month+"-01",price:Math.round(v.total/v.count*100)/100}));
   if(history.length<3)return respond({success:false,code:"INSUFFICIENT_HISTORY",
     error:"At least three distinct months of sourced historical prices are required for this commodity and market.",
     required_observations:3,available_observations:history.length},422);
   const tail=history.slice(-Math.min(12,history.length));
   const n=tail.length;
   const mean=tail.reduce((a,v)=>a+v.price,0)/n;
   const midpoint=(n-1)/2;
   const denominator=tail.reduce((a,_,i)=>a+(i-midpoint)**2,0);
   const slope=denominator>0?tail.reduce((a,v,i)=>a+(i-midpoint)*(v.price-mean),0)/denominator:0;
   const latest=history[history.length-1].price;
   const monthlyStep=Math.max(-latest*0.10,Math.min(latest*0.10,slope));
   const residual=Math.sqrt(tail.reduce((a,v,i)=>a+(v.price-(mean+slope*(i-midpoint)))**2,0)/n);
   const forecast=Array.from({length:months},(_,i)=>{
     const latestDate=new Date(history[history.length-1].date+"T00:00:00Z");
     const today=new Date();
     const monthsSinceLatest=Math.max(0,(today.getUTCFullYear()-latestDate.getUTCFullYear())*12+today.getUTCMonth()-latestDate.getUTCMonth());
     const step=monthsSinceLatest+i+1;
     const predicted=Math.max(0.01,latest+monthlyStep*step);
     // Indicative bands, NOT statistically calibrated confidence intervals.
     const spread=Math.max(latest*0.05,residual)*Math.sqrt(step);
     return {date:monthDate(history[history.length-1].date,step),
       predicted_price:Math.round(predicted*100)/100,
       lower_estimate:Math.round(Math.max(0.01,predicted-spread)*100)/100,
       upper_estimate:Math.round((predicted+spread)*100)/100};
   });
   const lastObservedDate=history[history.length-1].date;
   return respond({success:true,mode:"verified",commodity,market,unit,
     model_used:"Historical monthly trend (experimental)",
     observations:history.length,current_price:latest,last_observed_date:lastObservedDate,
     historical:history.slice(-12),forecast,
     notice:"Latest recorded price is from "+lastObservedDate+". National averages are not today's local prices. These forecasts extrapolate older data and have high uncertainty; do not rely on them for trading decisions."});

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
   return respond({success:true,history,count:history.length,verified_count:verified,demo_count:history.filter((r:any)=>r.data_kind==="demo").length,notice:"Only sourced historical market observations are shown."});
  }
  if(endpoint==="prices" || (endpoint==="real" && u.pathname.endsWith("/prices/real"))){
   // Only real verified observations, no simulated market prices.
   let query=db.from("price_history").select("id,price,unit,trend,price_date,recorded_at,commodities!inner(name,icon_emoji),markets!inner(name,province)").eq("is_verified",true).neq("data_kind","demo").order("price_date",{ascending:false}).limit(limit);
   const commodity=u.searchParams.get("commodity"),market=u.searchParams.get("market");
   if(commodity)query=query.eq("commodities.name",commodity);
   if(market)query=query.eq("markets.name",market);
   const {data,error}=await query;if(error)throw error;
   const prices=(data||[]).map((r:any)=>({id:r.id,commodity_name:r.commodities?.name,commodity:r.commodities?.name,icon_emoji:r.commodities?.icon_emoji,market_name:r.markets?.name,market:r.markets?.name,province:r.markets?.province,price:r.price,unit:r.unit,trend:r.trend,last_updated:r.price_date,is_verified:true}));
   return respond({success:true,prices,count:prices.length});
  }
  return respond({success:false,error:"Unknown endpoint"},404);
 }catch(e){console.error("FarmConnect API failure",e);return respond({success:false,error:"Database request failed"},500);}
});
