const fs=require("fs"), vm=require("vm"), path=require("path"), SP=__dirname;
const ctx={console,TextDecoder,TextEncoder,Uint8Array,Int32Array,DataView,Date,Math,JSON};
ctx.window=ctx;ctx.global=ctx;ctx.self=ctx;vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(SP,"sheetjs.js"),"utf8"),ctx);
vm.runInContext(fs.readFileSync(path.join(SP,"rejilla.js"),"utf8"),ctx);
const XLSX=ctx.XLSX;
function gen(nombre, headers, rows){
  const ws=XLSX.utils.aoa_to_sheet([headers].concat(rows),{cellDates:true,dateNF:"dd/mm/yyyy"});
  ws["!cols"]=headers.map(h=>({wch:Math.min(38,Math.max(11,String(h).length+2))}));
  const wb=XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb,ws,"Datos");
  const bruto=XLSX.write(wb,{type:"array",bookType:"xlsx",compression:false});
  const con=ctx.ponerRejillaAlXlsx(bruto);
  if(!con){ console.log("FALLO en "+nombre); process.exit(1); }
  fs.writeFileSync(path.join(SP,nombre),Buffer.from(con));
  console.log("OK",nombre,con.length,"bytes");
}
// 1. masiva real: 27 columnas x 200 filas
const H27=["RADICADO","FECHA DE RADICACION","COMPARENDO","TIPO","REMITENTE DESTINATARIO","DIRECCION","CIUDAD","DEPARTAMENTO","FECHA DE ASIGNACION","ASIGNADOS A","ESTADO","TIPO DE COMPARENDO","FECHA DE COMPARENDO","COMPARENDO","INFRACCCION","FECHA DE NOTIF","RESOLUCION","FECHA Res","ANEXO","PLANTILLA","USUARIO","TIPO DE DOCUMENTO","NUMERO DE DOCUMENTO","RES. SALIDA","FECHA RES. SALIDA","PLACA","ANEXO"];
const filas=[];
for(let i=0;i<200;i++) filas.push(H27.map((h,j)=> j===1||j===12 ? "19/04/2025" : (j===4?"JOSÉ PÉREZ ÑÚÑEZ "+i:"v"+i+"-"+j)));
gen("masiva27.xlsx",H27,filas);
// 2. plantilla de agendamientos con fechas de verdad
const H15=["FECHA APERTURA","HORA","LINK AUDIENCIA","NOMBRE Y APELLIDO DEL CIUDADANO","NÚMERO DE DOCUMENTO","CORREO ELECTRONICO","NÚMERO DE COMPARENDO","PLACA","MEDIO DE SOLICITUD","FECHA DE COMPARENDO","CÓDIGO DE INFRACCIÓN","FECHA APELACION","AGENDADO POR","FECHA DIGITACION","FORMATO"];
const f15=[];
for(let i=0;i<50;i++) f15.push(["","","","CIUDADANO "+i,"188699"+i,"a@b.com","4685526"+i,"ABC12"+(i%10),"2026ER"+i,new Date(2026,3,19),"D01",new Date(2026,4,2),"MJ",new Date(2026,8,28), i%2?"AGENDAR CON PRUEBAS":"AGENDAR SIN PRUEBAS"]);
gen("agenda15.xlsx",H15,f15);
// 3. una sola fila, y cero filas
gen("una.xlsx",H15,[f15[0]]);
gen("cero.xlsx",H15,[]);
// 4. red de seguridad: entrada basura -> null, no excepción
const basura=new Uint8Array([1,2,3,4,5]).buffer;
console.log("basura ->", ctx.ponerRejillaAlXlsx(basura)===null ? "null (correcto: se descargaría el archivo normal)" : "MAL");
