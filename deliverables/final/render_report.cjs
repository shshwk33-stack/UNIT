const {chromium}=require('playwright');
const fs=require('fs'),path=require('path'),http=require('http');
(async()=>{
 const server=http.createServer((req,res)=>{
  const pathname=new URL(req.url,'http://localhost').pathname;
  const target=path.join(__dirname,pathname==='/'?'cbp-final-report.html':pathname);
  if(!target.startsWith(__dirname+path.sep)){res.writeHead(403);res.end();return}
  if(!fs.existsSync(target)){res.writeHead(404);res.end();return}
  res.writeHead(200,{'Content-Type':target.endsWith('.svg')?'image/svg+xml':'text/html; charset=utf-8'});res.end(fs.readFileSync(target));
 }).listen(0,'127.0.0.1');
 await new Promise(r=>server.once('listening',r));
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1000,height:1300},deviceScaleFactor:1});
  await page.goto(`http://127.0.0.1:${server.address().port}/`,{waitUntil:'networkidle'});
  await page.emulateMedia({media:'print'});await page.evaluate(()=>document.fonts.ready);
  const audit=await page.evaluate(()=>Array.from(document.querySelectorAll('.page')).map((el,i)=>{
   const rect=el.getBoundingClientRect(),body=el.querySelector('.body').getBoundingClientRect(),foot=el.querySelector('.footer').getBoundingClientRect();
   const bad=Array.from(el.querySelectorAll('.body *')).filter(e=>{const b=e.getBoundingClientRect();return b.left<rect.left+40||b.right>rect.right-40||b.bottom>foot.top-8}).map(e=>({tag:e.tagName,text:e.textContent.slice(0,80),bottom:e.getBoundingClientRect().bottom-rect.top}));
   return {page:i+1,title:el.querySelector('h1').textContent,bodyBottom:body.bottom-rect.top,footerTop:foot.top-rect.top,chars:el.querySelector('.body').textContent.length,overflow:bad};
  }));
  fs.writeFileSync(path.join(__dirname,'layout_audit.json'),JSON.stringify(audit,null,2));
  const issues=audit.filter(p=>p.overflow.length);console.log(JSON.stringify({pages:audit.length,issues},null,2));
  if(issues.length)throw Error('Layout overflow: fix before generating PDF');
  await page.pdf({path:path.join(__dirname,'cbp-final-report.pdf'),printBackground:true,preferCSSPageSize:true,tagged:true,outline:true});
  console.log('PDF generated');
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
