"""Owner panel UI. Cairo typeface self-hosted from /admin/font, SVG icons
(no emoji), and full driver profiles: photo, car model, plate and color."""

PANEL_HTML = r"""<!doctype html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة تحكم تكسي واحد عراق</title>
<style>
  @font-face{font-family:'Cairo';src:url('/admin/font/regular') format('truetype');font-weight:400 600;font-display:swap}
  @font-face{font-family:'Cairo';src:url('/admin/font/bold') format('truetype');font-weight:700 800;font-display:swap}
  *{box-sizing:border-box}
  body{font-family:'Cairo',system-ui,sans-serif;background:#0A1729;color:#fff;margin:0;padding:16px;max-width:640px;margin-inline:auto}
  h1{font-size:1.15rem;color:#FFA22B;margin:6px 0 14px;display:flex;align-items:center;gap:8px}
  .card{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:14px;margin-bottom:12px}
  label{display:block;font-size:.8rem;color:rgba(255,255,255,.65);margin-bottom:4px}
  input,textarea{width:100%;font-family:'Cairo';background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:10px;color:#fff;padding:9px;font-size:.92rem;margin-bottom:8px}
  input[type=color]{padding:2px;height:42px;cursor:pointer}
  button{font-family:'Cairo';background:#FFA22B;color:#221400;border:0;border-radius:12px;padding:11px 14px;font-size:.92rem;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:6px;justify-content:center}
  button.full{width:100%}
  button.small{padding:6px 12px;font-size:.8rem;border-radius:9px}
  button.ghost{background:rgba(255,255,255,.12);color:#fff}
  button.green{background:#34D077;color:#00210E}
  button.red{background:#FF6B6B;color:#330606}
  .row{display:flex;gap:8px}.row>div{flex:1}
  .msg{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);padding:10px 18px;border-radius:12px;display:none;z-index:99;font-size:.9rem;box-shadow:0 6px 20px rgba(0,0,0,.4)}
  .ok{background:#123527;color:#34D077;border:1px solid #34D077}
  .err{background:#3a1418;color:#FF6B6B;border:1px solid #FF6B6B}
  h3{font-size:.95rem;margin:4px 0 10px;color:#34D077;display:flex;align-items:center;gap:7px}
  .tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
  .tabs button{background:rgba(255,255,255,.09);color:rgba(255,255,255,.85);font-weight:600;padding:8px 12px;border-radius:11px;font-size:.82rem}
  .tabs button.active{background:#FFA22B;color:#221400}
  .tabs button svg{width:15px;height:15px}
  .stat{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.07);font-size:.9rem}
  .stat:last-child{border-bottom:0}
  .stat b{color:#34D077;font-size:.95rem}
  .item{border-bottom:1px solid rgba(255,255,255,.08);padding:11px 0}
  .item:last-child{border-bottom:0}
  .muted{color:rgba(255,255,255,.5);font-size:.78rem}
  .chip{display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:99px;font-size:.72rem;font-weight:700}
  .chip.open{background:rgba(255,162,43,.18);color:#FFA22B}
  .chip.done{background:rgba(52,208,119,.16);color:#34D077}
  svg{width:18px;height:18px;flex-shrink:0}
  /* driver card */
  .dhead{display:flex;align-items:center;gap:12px}
  .avatar{width:58px;height:58px;border-radius:50%;object-fit:cover;border:2px solid #FFA22B;flex-shrink:0}
  .avatar.ph{display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1D2F4C,#31415f);color:#FFA22B;font-weight:800;font-size:1.3rem;border:2px solid rgba(255,162,43,.5)}
  .dname{font-weight:800;font-size:.98rem}
  .carline{display:flex;align-items:center;gap:8px;margin-top:10px;flex-wrap:wrap}
  .swatch{width:20px;height:20px;border-radius:6px;border:2px solid rgba(255,255,255,.35);flex-shrink:0}
  .plate{background:#f4f4f4;color:#111;border-radius:6px;padding:2px 10px;font-weight:800;font-size:.82rem;border-inline-start:8px solid #d64545;letter-spacing:.5px;box-shadow:0 1px 3px rgba(0,0,0,.4)}
  .dbtns{display:flex;gap:8px;margin-top:11px;flex-wrap:wrap}
  .editbox{margin-top:12px;border-top:1px dashed rgba(255,255,255,.15);padding-top:12px;display:none}
</style>
</head>
<body>
<h1><svg viewBox="0 0 24 24" fill="#FFA22B"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5H15V3H9v2H6.5c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/></svg>
لوحة تحكم تكسي واحد عراق</h1>

<div class="card" id="login">
  <label>رمز الإدارة (ADMIN_TOKEN)</label>
  <input id="token" type="password" placeholder="الصق الرمز هنا">
  <button class="full" onclick="enter()">دخول</button>
</div>

<div id="app" style="display:none">
  <div class="tabs" id="tabbar"></div>
  <div id="tab-stats" class="tab"></div>

  <div id="tab-fees" class="tab" style="display:none">
    <div class="card">
      <h3>رسوم المنصة</h3>
      <label>نسبة العمولة من كل رحلة (%)</label>
      <input id="commission_percent" type="number" step="0.5" min="0" max="50">
      <label>رسوم الحجز الثابتة (د.ع تُضاف لكل رحلة وتعود لك)</label>
      <input id="booking_fee" type="number" step="250" min="0" max="10000">
    </div>
    <div class="card" id="tariffs"></div>
    <button class="full" onclick="saveFees()">حفظ — يسري فوراً</button>
  </div>

  <div id="tab-incentives" class="tab" style="display:none">
    <div id="plans"></div>
    <button class="full ghost" style="margin-bottom:8px" onclick="addPlan()">＋ إضافة خطة</button>
    <button class="full" onclick="savePlans()">حفظ الحوافز</button>
  </div>

  <div id="tab-complaints" class="tab" style="display:none"></div>
  <div id="tab-payments" class="tab" style="display:none"></div>
  <div id="tab-drivers" class="tab" style="display:none"></div>
</div>

<div id="msg" class="msg"></div>

<script>
const TIERS = {economy:'اقتصادي', family:'عائلي', premium:'بريميوم'};
const ICONS = {
  stats:'M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z',
  fees:'M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z',
  incentives:'M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 12 7.4 15.38 12 17 10.83 14.92 8H20v6z',
  complaints:'M19.5 3.5 18 2l-1.5 1.5L15 2l-1.5 1.5L12 2l-1.5 1.5L9 2 7.5 3.5 6 2 4.5 3.5 3 2v20l1.5-1.5L6 22l1.5-1.5L9 22l1.5-1.5L12 22l1.5-1.5L15 22l1.5-1.5L18 22l1.5-1.5L21 22V2l-1.5 1.5zM19 19.09H5V4.91h14v14.18zM6 15h12v2H6zm0-4h12v2H6zm0-4h12v2H6z',
  payments:'M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z',
  drivers:'M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z',
  wallet:'M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z',
  users:'M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z',
  check:'M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z',
  pause:'M6 19h4V5H6v14zm8-14v14h4V5h-4z',
  edit:'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z',
  clock:'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z',
};
const ico = (n,c='#fff') => `<svg viewBox="0 0 24 24" fill="${c}"><path d="${ICONS[n]}"/></svg>`;
const TABS = [['stats','الإحصائيات'],['fees','الرسوم'],['incentives','الحوافز'],['complaints','الشكاوى'],['payments','الدفعات'],['drivers','السائقون']];
const fmt = n => (n||0).toLocaleString('en') + ' د.ع';
const when = ts => new Date(ts*1000).toLocaleString('ar-IQ');
let settings=null, plans=[];

document.getElementById('tabbar').innerHTML = TABS.map(([id,name],i)=>
  `<button data-tab="${id}" class="${i===0?'active':''}" onclick="openTab('${id}')">${ico(id, i===0?'#221400':'#fff')} ${name}</button>`).join('');

function show(text, ok){
  const el = document.getElementById('msg');
  el.textContent = text; el.className = 'msg ' + (ok?'ok':'err'); el.style.display='block';
  setTimeout(()=>{el.style.display='none'}, 4000);
}

async function api(method, path, body){
  const res = await fetch(path, {method,
    headers:{'X-Admin-Token':document.getElementById('token').value,'Content-Type':'application/json'},
    body: body?JSON.stringify(body):undefined});
  const data = await res.json();
  if(!res.ok) throw new Error(data.detail||res.status);
  return data;
}

async function enter(){
  try{
    settings = await api('GET','/admin/settings');
    document.getElementById('login').style.display='none';
    document.getElementById('app').style.display='block';
    fillFees(); plans = settings.incentive_plans||[]; renderPlans();
    openTab('stats');
  }catch(e){ show('فشل الدخول: '+e.message,false); }
}

function openTab(name){
  document.querySelectorAll('.tab').forEach(t=>t.style.display='none');
  document.querySelectorAll('.tabs button').forEach(b=>{
    const on = b.dataset.tab===name;
    b.classList.toggle('active', on);
    b.querySelector('svg').setAttribute('fill', on?'#221400':'#fff');
  });
  document.getElementById('tab-'+name).style.display='block';
  ({stats:loadStats, complaints:loadComplaints, payments:loadPayments, drivers:loadDrivers})[name]?.();
}

async function loadStats(){
  try{
    const s = await api('GET','/admin/stats');
    let methods='';
    for(const [m,v] of Object.entries(s.payments_by_method))
      methods += `<div class="stat"><span>${ {cash:'نقدي',zaincash:'زين كاش',fib:'FIB',qi:'سوبر كي'}[m]||m }</span><b>${v.count} رحلة — ${fmt(v.amount)}</b></div>`;
    document.getElementById('tab-stats').innerHTML = `
      <div class="card"><h3>${ico('wallet','#34D077')} أرباحك (العمولات المحصّلة)</h3>
        <div class="stat"><span>اليوم</span><b>${fmt(s.revenue_today)}</b></div>
        <div class="stat"><span>الإجمالي</span><b>${fmt(s.revenue_total)}</b></div>
        <div class="stat"><span>إجمالي قيمة الرحلات</span><b>${fmt(s.gross_total)}</b></div></div>
      <div class="card"><h3>${ico('drivers','#34D077')} الرحلات</h3>
        <div class="stat"><span>مكتملة اليوم</span><b>${s.trips_today}</b></div>
        <div class="stat"><span>مكتملة إجمالاً</span><b>${s.trips_completed}</b></div>
        <div class="stat"><span>نشطة الآن</span><b>${s.trips_active}</b></div></div>
      <div class="card"><h3>${ico('users','#34D077')} المستخدمون</h3>
        <div class="stat"><span>الزبائن</span><b>${s.riders}</b></div>
        <div class="stat"><span>السائقون</span><b>${s.drivers}</b></div>
        <div class="stat"><span>سائقون متصلون الآن</span><b>${s.drivers_online}</b></div>
        <div class="stat"><span>بانتظار الاعتماد</span><b>${s.drivers_pending}</b></div>
        <div class="stat"><span>شكاوى مفتوحة</span><b>${s.complaints_open}</b></div></div>
      <div class="card"><h3>${ico('payments','#34D077')} الرحلات حسب طريقة الدفع</h3>${methods||'<div class="muted">لا رحلات بعد</div>'}</div>`;
  }catch(e){ show(e.message,false); }
}

function fillFees(){
  document.getElementById('commission_percent').value = settings.commission_percent;
  document.getElementById('booking_fee').value = settings.booking_fee;
  const box = document.getElementById('tariffs');
  box.innerHTML = '<h3>'+ico('fees','#34D077')+' تعرفة الفئات (د.ع)</h3>';
  for(const [tier,name] of Object.entries(TIERS)){
    const t = settings.tariffs[tier];
    box.innerHTML += `<label>${name}: أساس / لكل كم / حد أدنى</label>
      <div class="row">
        <div><input id="${tier}_base" type="number" value="${t.base}"></div>
        <div><input id="${tier}_per_km" type="number" value="${t.per_km}"></div>
        <div><input id="${tier}_minimum" type="number" value="${t.minimum}"></div>
      </div>`;
  }
}

async function saveFees(){
  try{
    const tariffs={};
    for(const tier of Object.keys(TIERS))
      tariffs[tier]={base:+document.getElementById(tier+'_base').value,
                     per_km:+document.getElementById(tier+'_per_km').value,
                     minimum:+document.getElementById(tier+'_minimum').value};
    settings = await api('PUT','/admin/settings',{
      commission_percent:+document.getElementById('commission_percent').value,
      booking_fee:+document.getElementById('booking_fee').value, tariffs});
    show('تم الحفظ — يسري على الرحلات القادمة فوراً',true);
  }catch(e){ show('فشل الحفظ: '+e.message,false); }
}

function renderPlans(){
  const box = document.getElementById('plans');
  box.innerHTML='';
  plans.forEach((p,i)=>{
    const steps = p.steps.map(s=>s.trips+':'+s.bonus).join('، ');
    box.innerHTML += `<div class="card">
      <label>عنوان الخطة</label><input id="p${i}_title" value="${p.title||''}">
      <label>الوصف</label><input id="p${i}_desc" value="${p.description||''}">
      <label>الدرجات (رحلات:مكافأة — مثال: 1:2000، 3:5000، 6:12000)</label>
      <input id="p${i}_steps" value="${steps}">
      <button class="small red" onclick="plans.splice(${i},1);renderPlans()">حذف الخطة</button>
    </div>`;
  });
}
function addPlan(){ plans.push({title:'',description:'',steps:[{trips:1,bonus:2000}]}); renderPlans(); }

async function savePlans(){
  try{
    const out = plans.map((p,i)=>({id:p.id||('plan-'+(i+1)),
      title:document.getElementById('p'+i+'_title').value,
      description:document.getElementById('p'+i+'_desc').value,
      steps:document.getElementById('p'+i+'_steps').value.split(/[,،]/).map(s=>s.trim()).filter(Boolean)
        .map(pair=>{const [t,b]=pair.split(':');return {trips:+t,bonus:+b};})}));
    settings = await api('PUT','/admin/settings',{incentive_plans:out});
    plans = settings.incentive_plans; renderPlans();
    show('تم حفظ خطط الحوافز — تظهر للسائقين فوراً',true);
  }catch(e){ show('فشل الحفظ: '+e.message,false); }
}

async function loadComplaints(){
  try{
    const list = await api('GET','/admin/complaints?only_open=false');
    const box = document.getElementById('tab-complaints');
    if(!list.length){ box.innerHTML='<div class="card muted">لا شكاوى بعد.</div>'; return; }
    box.innerHTML = '<div class="card">'+list.map(c=>`
      <div class="item">
        <span class="chip ${c.status==='open'?'open':'done'}">${c.status==='open'?'مفتوحة':'محلولة'}</span>
        <b>${c.user.role==='driver'?'سائق':'زبون'}: ${c.user.name||c.user.phone}</b>
        <div style="margin:5px 0">${c.text}</div>
        <div class="muted">${when(c.created_at)}</div>
        ${c.status==='open'?`<button class="small green" style="margin-top:7px" onclick="resolve('${c.id}')">${ico('check','#00210E')} تمت المعالجة</button>`:''}
      </div>`).join('')+'</div>';
  }catch(e){ show(e.message,false); }
}
async function resolve(id){
  try{ await api('POST','/admin/complaints/'+id+'/resolve'); loadComplaints(); show('تم حل الشكوى',true);}
  catch(e){ show(e.message,false); }
}

async function loadPayments(){
  try{
    const list = await api('GET','/admin/payments');
    const box = document.getElementById('tab-payments');
    if(!list.length){ box.innerHTML='<div class="card muted">لا دفعات إلكترونية بعد — الدفعات النقدية تظهر في الإحصائيات.</div>'; return; }
    box.innerHTML = '<div class="card">'+list.map(p=>`
      <div class="item">
        <span class="chip ${p.status==='paid'?'done':'open'}">${ {paid:'مدفوعة',pending:'معلّقة',failed:'فاشلة'}[p.status]||p.status }</span>
        <b>${ {zaincash:'زين كاش',fib:'FIB',qi:'سوبر كي'}[p.provider]||p.provider } — ${fmt(p.amount)}</b>
        <div class="muted">رحلة ${p.trip_id.slice(0,8)} · ${when(p.created_at)}</div>
      </div>`).join('')+'</div>';
  }catch(e){ show(e.message,false); }
}

function avatar(d){
  if(d.photo) return `<img class="avatar" src="${d.photo}" alt="">`;
  const initial = (d.name||d.phone||'؟').trim().charAt(0);
  return `<div class="avatar ph">${initial}</div>`;
}

async function loadDrivers(){
  try{
    const list = await api('GET','/admin/drivers');
    const box = document.getElementById('tab-drivers');
    if(!list.length){ box.innerHTML='<div class="card muted">لا سائقين مسجلين بعد.</div>'; return; }
    box.innerHTML = list.map(d=>`
      <div class="card">
        <div class="dhead">
          ${avatar(d)}
          <div style="flex:1">
            <div class="dname">${d.name||d.phone}</div>
            <div class="muted">${d.phone} · ${d.trips_completed} رحلة مكتملة</div>
            <div style="margin-top:4px">
              ${d.online?'<span class="chip done">متصل الآن</span> ':''}
              <span class="chip ${d.approved?'done':'open'}">${d.approved?'معتمد':'بانتظار الاعتماد'}</span>
            </div>
          </div>
        </div>
        <div class="carline">
          ${d.car_color?`<span class="swatch" style="background:${d.car_color}"></span>`:''}
          <span>${d.car_model||'<span class="muted">لم تُحدد السيارة</span>'}</span>
          ${d.plate?`<span class="plate">${d.plate}</span>`:''}
        </div>
        <div class="dbtns">
          <button class="small ghost" onclick="toggleEdit('${d.id}')">${ico('edit','#fff')} تعديل الملف</button>
          <button class="small ${d.approved?'red':'green'}" onclick="approve('${d.id}',${!d.approved})">
            ${d.approved?ico('pause','#330606')+' إيقاف':ico('check','#00210E')+' اعتماد'}</button>
        </div>
        <div class="editbox" id="edit-${d.id}">
          <label>الاسم</label><input id="e-${d.id}-name" value="${d.name||''}">
          <div class="row">
            <div><label>نوع السيارة</label><input id="e-${d.id}-car" value="${d.car_model||''}"></div>
            <div><label>رقم اللوحة</label><input id="e-${d.id}-plate" value="${d.plate||''}"></div>
          </div>
          <div class="row">
            <div><label>لون السيارة</label><input id="e-${d.id}-color" type="color" value="${d.car_color||'#e8e8e8'}"></div>
            <div><label>الصورة الشخصية</label><input id="e-${d.id}-photo" type="file" accept="image/*"></div>
          </div>
          <button class="small full" onclick="saveDriver('${d.id}')">${ico('check','#221400')} حفظ الملف</button>
        </div>
      </div>`).join('');
  }catch(e){ show(e.message,false); }
}

function toggleEdit(id){
  const el = document.getElementById('edit-'+id);
  el.style.display = el.style.display==='block' ? 'none' : 'block';
}

function readPhoto(input){
  return new Promise(resolve=>{
    const file = input.files && input.files[0];
    if(!file) return resolve(null);
    const reader = new FileReader();
    reader.onload = ()=>{
      const img = new Image();
      img.onload = ()=>{
        const c = document.createElement('canvas');
        const side = Math.min(img.width, img.height);
        c.width = c.height = 256;
        c.getContext('2d').drawImage(img,(img.width-side)/2,(img.height-side)/2,side,side,0,0,256,256);
        resolve(c.toDataURL('image/jpeg', .85));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

async function saveDriver(id){
  try{
    const body = {
      name: document.getElementById('e-'+id+'-name').value,
      car_model: document.getElementById('e-'+id+'-car').value,
      plate: document.getElementById('e-'+id+'-plate').value,
      car_color: document.getElementById('e-'+id+'-color').value,
    };
    const photo = await readPhoto(document.getElementById('e-'+id+'-photo'));
    if(photo) body.photo = photo;
    await api('PUT','/admin/drivers/'+id, body);
    loadDrivers();
    show('تم حفظ ملف السائق — يظهر للزبائن فوراً',true);
  }catch(e){ show('فشل الحفظ: '+e.message,false); }
}

async function approve(id, approved){
  try{ await api('POST','/admin/drivers/'+id+'/approve',{approved}); loadDrivers(); show('تم التحديث',true);}
  catch(e){ show(e.message,false); }
}
</script>
</body>
</html>"""
