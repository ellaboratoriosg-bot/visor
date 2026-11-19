const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage();
await p.goto('http://127.0.0.1:8765/test.html');await p.waitForFunction('window.ready',null,{timeout:120000});
await p.evaluate('window.D=1.75');for(const [n,a] of [['frente',0],['lado',0.75]]){const d=await p.evaluate(`shot(${a})`);fs.writeFileSync('r_'+n+'.png',Buffer.from(d.split(',')[1],'base64'))}
await b.close()})()
