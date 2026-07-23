let rows=[],sortKey="price_change",desc=true,view="ltp";
let reloadWatchMtime = null;
const $=id=>document.getElementById(id);
const num=(v,d=2)=>v==null||Number.isNaN(Number(v))?"N/A":Number(v).toLocaleString("en-IN",{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=v=>v==null?"N/A":(v>=0?"+":"")+Number(v).toFixed(2)+"%";

function priceLabel(x){
  const value = num(x.price);
  const price = Number(x.price);
  if(!Number.isFinite(price)) return value;
  const r3 = Number(x.pivot_r3 ?? x.pivotR3 ?? x['pivot_r3']);
  const r2 = Number(x.pivot_r2 ?? x.pivotR2 ?? x['pivot_r2']);
  const r1 = Number(x.pivot_r1 ?? x.pivotR1 ?? x['pivot_r1']);
  const s3 = Number(x.pivot_s3 ?? x.pivotS3 ?? x['pivot_s3']);
  const s2 = Number(x.pivot_s2 ?? x.pivotS2 ?? x['pivot_s2']);
  const s1 = Number(x.pivot_s1 ?? x.pivotS1 ?? x['pivot_s1']);
  if(Number.isFinite(r3) && price > r3) return `${value} <span class="suffix">(<span class="suffix-label">R3</span> ↟)</span>`;
  if(Number.isFinite(r2) && price > r2) return `${value} <span class="suffix">(<span class="suffix-label">R2</span> ↟)</span>`;
  if(Number.isFinite(r1) && price > r1) return `${value} <span class="suffix">(<span class="suffix-label">R1</span> ↟)</span>`;
  if(Number.isFinite(s3) && price < s3) return `${value} <span class="suffix">(<span class="suffix-label">S3</span> ↡)</span>`;
  if(Number.isFinite(s2) && price < s2) return `${value} <span class="suffix">(<span class="suffix-label">S2</span> ↡)</span>`;
  if(Number.isFinite(s1) && price < s1) return `${value} <span class="suffix">(<span class="suffix-label">S1</span> ↡)</span>`;
  return value;
}

function prevHighLabel(x){
  const value = num(x.prevhigh,2);
  const price = Number(x.price);
  if(!Number.isFinite(price)) return value;
  const r3 = Number(x.pivot_r3 ?? x.pivotR3 ?? x['pivot_r3']);
  const r2 = Number(x.pivot_r2 ?? x.pivotR2 ?? x['pivot_r2']);
  const r1 = Number(x.pivot_r1 ?? x.pivotR1 ?? x['pivot_r1']);
  if(Number.isFinite(r3) && price > r3) return `${value} <span class="suffix">(<span class="suffix-label">R3</span> ↟)</span>`;
  if(Number.isFinite(r2) && price > r2) return `${value} <span class="suffix">(<span class="suffix-label">R2</span> ↟)</span>`;
  if(Number.isFinite(r1) && price > r1) return `${value} <span class="suffix">(<span class="suffix-label">R1</span> ↟)</span>`;
  return value;
}

function prevLowLabel(x){
  const value = num(x.prevlow,2);
  const price = Number(x.price);
  if(!Number.isFinite(price)) return value;
  const s3 = Number(x.pivot_s3 ?? x.pivotS3 ?? x['pivot_s3']);
  const s2 = Number(x.pivot_s2 ?? x.pivotS2 ?? x['pivot_s2']);
  const s1 = Number(x.pivot_s1 ?? x.pivotS1 ?? x['pivot_s1']);
  if(Number.isFinite(s3) && price < s3) return `${value} <span class="suffix">(<span class="suffix-label">S3</span> ↡)</span>`;
  if(Number.isFinite(s2) && price < s2) return `${value} <span class="suffix">(<span class="suffix-label">S2</span> ↡)</span>`;
  if(Number.isFinite(s1) && price < s1) return `${value} <span class="suffix">(<span class="suffix-label">S1</span> ↡)</span>`;
  return value;
}

async function pollReload(){
  try{
    const res = await fetch('/api/reload?'+Date.now());
    if(!res.ok) return;
    const data = await res.json();
    const mtime = Number(data.reload_mtime) || 0;
    if(reloadWatchMtime === null){
      reloadWatchMtime = mtime;
      return;
    }
    if(mtime > reloadWatchMtime){
      window.location.reload();
    }
  }catch(e){
    // ignore network or fetch errors during development
  }
}

function isTruthy(v){
  if(v==null) return false;
  if(typeof v==="boolean") return v;
  if(typeof v==="number") return v!==0;
  if(typeof v==="string"){
    const t=v.toLowerCase().trim();
    return t==="1"||t==="true"||t==="yes"||t==="y";
  }
  return Boolean(v);
}

function syncSearchClearButton(){
  const hasSearchText=$("search").value.trim().length>0;
  $("clear-search").style.display=hasSearchText?"flex":"none";
}

function syncFilterStyles(){
  document.querySelectorAll(".filters select").forEach(select=>{
    select.classList.toggle("active", select.value !== "");
  });
}

function filtered(){
  const q=$("search").value.toLowerCase().trim(), p=$("price").value,r=$("rsi").value,a=$("adx").value,c=$("cci").value,m=$("macd").value,cp=$("cpr").value,vc=$("virgin_cpr").value,ob=$("orb_filter").value;
  return rows.filter(x=>{
    if(q&&!x.symbol.toLowerCase().includes(q))return false;
    if(p==="1"&&!(x.price_change>1)||p==="2"&&!(x.price_change>2)||p==="5"&&!(x.price_change>5)||p==="-1"&&!(x.price_change<-1))return false;
    if(r==="70"&&!(x.RSI>70)||r==="60"&&!(x.RSI>60)||r==="50"&&!(x.RSI>=50&&x.RSI<=70)||r==="30"&&!(x.RSI<30))return false;
    if(a&&!(x.ADX>Number(a)))return false;
    if(c==="100"&&!(x.CCI>100)||c==="200"&&!(x.CCI>200)||c==="-100"&&!(x.CCI<-100))return false;
    if(m==="positive"&&!(x.macd_histogram>0)||m==="negative"&&!(x.macd_histogram<0))return false;
    if(cp&&x.cpr!==cp)return false;
    if(vc==="1"&& !isTruthy(x.virgin_cpr)) return false;
    if(vc==="0"&& isTruthy(x.virgin_cpr)) return false;
    if(ob&&x.orb!==ob)return false;
    return true;
  });
}

function render(){
  let a=filtered().sort((x,y)=>{
    let xv=x[sortKey]??-Infinity,yv=y[sortKey]??-Infinity;
    return desc?Number(yv)-Number(xv):Number(xv)-Number(yv);
  });
  $("count").textContent=`${a.length} stocks`;
  const symbolCount = Number.isFinite(window.apiSymbolCount) ? window.apiSymbolCount : rows.length;
  const rowCount = Number.isFinite(window.apiRowCount) ? window.apiRowCount : rows.length;
  $("dbinfo").textContent=`Total ${symbolCount} symbols · ${rowCount} database rows`;
  syncSearchClearButton();
  if(view==="orb"){
    $("body").innerHTML="";
    $("count").textContent="0 stocks";
    $("dbinfo").textContent="Total 0 symbols · 0 database rows";
    return;
  }
  $("body").innerHTML=a.map(x=>`<tr>
  <td class="symbol"><a href="https://in.tradingview.com/chart/VpHRyOhI/?symbol=NSE%3A${encodeURIComponent(x.symbol)}" target="_blank" rel="noopener noreferrer">${x.symbol}</a></td><td>₹${priceLabel(x)}</td>
  <td class="${x.price_change>=0?"positive":"negative"}">${pct(x.price_change)}</td>
  <td>${prevHighLabel(x)}</td><td>${prevLowLabel(x)}</td><td>${num(x.pivot_r1 ?? x.pivotR1 ?? x['pivot_r1'],2)}</td><td>${num(x.pivot_s1 ?? x.pivotS1 ?? x['pivot_s1'],2)}</td>
  <td class="${x.RSI>60?"positive":"negative"}">${num(x.RSI,1)}</td><td class="${x.ADX>30?"positive":"negative"}">${num(x.ADX,1)}</td><td class="${x.CCI>100?"positive":"negative"}">${num(x.CCI,1)}</td>
  <td class="${x.macd_histogram>=0?"positive":"negative"}">${num(x.macd_histogram,4)}</td>
  <td><span class="cpr ${x.cpr?.toLowerCase()||"na"}">${x.cpr||"N/A"}</span></td>
  <td class="${isTruthy(x.virgin_cpr)?"positive":"negative"}">${isTruthy(x.virgin_cpr)?"True":"False"}</td><td>${num(x.volume,0)}</td>
  <td class="orb-cell ${x.orb==="ORB-Buy"?"orb-buy":x.orb==="ORB-Sell"?"orb-sell":""}">${x.orb||""}</td></tr>`).join("");
}

async function load(){
  $("status").textContent="Refreshing database...";
  try{
    const r = await fetch("/api/results?"+Date.now()), d = await r.json();
    if(d.error){
      rows=[];
      $("status").textContent="Error: "+d.error;
      $("dbinfo").textContent="";
      render();
    }else{
      rows=d.results||[];
      window.apiSymbolCount = d.symbol_count;
      window.apiRowCount = d.row_count;
      const latestDate = d.latest_db_timestamp ? new Date(d.latest_db_timestamp) : null;
      const latestLabel = latestDate ? latestDate.toLocaleString("en-IN", {hour12:true}) : "N/A";
      $("latest-db").textContent = `Latest DB: ${latestLabel}`;
      $("status").textContent="DB refreshed: "+new Date(d.last_updated).toLocaleString("en-IN", {hour12:true});
      render();
      syncFilterStyles();
    }
  }catch(e){
    rows=[];
    $("status").textContent="Error: "+e.message;
    $("dbinfo").textContent="";
    render();
  }
}

$("clear").onclick=()=>{["price","rsi","adx","cci","macd","cpr","virgin_cpr","orb_filter"].forEach(id=>$(id).value="");$("search").value="";sortKey="price_change";desc=true;render();syncFilterStyles();};
$("clear-search").onclick=()=>{$("search").value="";render();};
$("refresh").onclick=load;
$("search").addEventListener("input",()=>{render();syncSearchClearButton()});
document.querySelectorAll(".filters select").forEach(select=>select.addEventListener("change",()=>{render();syncFilterStyles();}));
document.querySelectorAll(".filters select").forEach(select=>select.addEventListener("change",()=>render()));
document.querySelectorAll(".tab").forEach(btn=>btn.onclick=()=>{view=btn.dataset.view;document.querySelectorAll(".tab").forEach(b=>{b.classList.toggle("active",b===btn);b.setAttribute("aria-selected",b===btn?"true":"false")});render()});
document.querySelectorAll("th[data-sort]").forEach(th=>th.onclick=()=>{let k=th.dataset.sort;if(k===sortKey)desc=!desc;else{sortKey=k;desc=true}render()});
pollReload();setInterval(pollReload,2000);
load();setInterval(load,30000);
