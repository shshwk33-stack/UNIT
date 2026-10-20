const {chromium}=require('playwright');
const fs=require('fs');const http=require('http');const path=require('path');
(async()=>{
 const data=fs.readFileSync(path.join(__dirname,'cbp-demo.html'));
 const server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});r.end(data)}).listen(0,'127.0.0.1');
 await new Promise(r=>server.once('listening',r));
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1200,height:850},deviceScaleFactor:1.5});
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  const cases=await page.evaluate(()=>{
   const scenarios=[[50,140,false,'A'],[68,140,false,'B'],[82,140,false,'C'],[93,140,false,'C'],[82,120,false,'B'],[99,140,false,null],[82,140,true,'B']];
   return scenarios.map(([cur,cap,delay,want])=>({cur,cap,delay,got:calculate(cur,cap,delay).selected,want}));
  });
  if(cases.some(r=>r.got!==r.want))throw Error(JSON.stringify(cases));
  await page.locator('#cost').fill('120');await page.locator('#cost').dispatchEvent('input');
  if(await page.locator('#winner').textContent()!=='운송안 B 추천')throw Error('Cost control did not update result');
  await page.locator('#cur').fill('99');await page.locator('#cur').dispatchEvent('input');
  if(await page.locator('#status').textContent()!=='담당자 판단 필요')throw Error('No-candidate status failed');
  console.log('7 browser scenarios and 2 UI transitions passed');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
