// Copertura per Stato: che cosa c'è e che cosa manca in ogni sezione.
const fs=require("fs"),vm=require("vm");const h=fs.readFileSync(process.argv[2],"utf8");const s0=h.indexOf("<script>")+8;const js=h.slice(s0,h.indexOf("</script>",s0));
const el=()=>({innerHTML:"",value:"",style:{},dataset:{},addEventListener(){},setAttribute(){},appendChild(){},querySelectorAll(){return[]},classList:{add(){},remove(){},toggle(){}}});
const ctx={console,setTimeout,clearTimeout,encodeURIComponent,decodeURIComponent,document:{querySelector:()=>el(),getElementById:()=>null,querySelectorAll:()=>[],createElement:el,head:el(),body:el(),addEventListener(){}},location:{hash:"",protocol:"https:",hostname:"x.org"},navigator:{},localStorage:{getItem(){return null},setItem(){}},addEventListener(){},scrollTo(){},matchMedia:()=>({matches:false,addEventListener(){}})};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(js,ctx);
const r=vm.runInContext(`Object.keys(SCHEDE).map(n=>{const s=STATI[n],d=SCHEDE[n];return {n,gov:!!(d.gov&&d.gov.capo),stab:!!d.stab,ris:!!d.ris,tr:(d.tr||[]).length,nz:(d.nz||[]).length,st:(d.st||[]).length,forze:!!FORZE[n],wb:!!POPWB[n],basi:(s.items.basi||[]).length,siti:(SITI[n]||[]).length,unita:UNITA.filter(u=>u[0]===n).length,appalti:appaltiDi(n).length,pmc:pmcDi(n).length}})`,ctx);
fs.writeFileSync(process.argv[3]||"/dev/null",JSON.stringify(r));
const c=k=>r.filter(x=>!x[k]).length;
console.log("stati",r.length,"| senza: gov",c("gov"),"stab",c("stab"),"ris",c("ris"),"tr",c("tr"),"nz",c("nz"),"st",c("st"),"forze(GFP)",c("forze"),"forze e WB",r.filter(x=>!x.forze&&!x.wb).length,"basi",c("basi"),"siti",c("siti"),"unita",c("unita"),"appalti",c("appalti"),"pmc",c("pmc"));
console.log("senza forze né WB:",r.filter(x=>!x.forze&&!x.wb).map(x=>x.n).join(", "));
console.log("senza basi:",r.filter(x=>!x.basi).map(x=>x.n).join(", "));
