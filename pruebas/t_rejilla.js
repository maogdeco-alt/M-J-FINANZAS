// Prueba del generador de Excel CON CUADRÍCULA, fuera del navegador.
const fs = require("fs");
const vm = require("vm");
const path = require("path");
const SP = __dirname;
const ctx = { console, TextDecoder, TextEncoder, Uint8Array, Int32Array, DataView, Date, Math, JSON };
ctx.window = ctx; ctx.global = ctx; ctx.self = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(SP,"sheetjs.js"),"utf8"), ctx, {filename:"sheetjs.js"});
vm.runInContext(fs.readFileSync(path.join(SP,"rejilla.js"),"utf8"), ctx, {filename:"rejilla.js"});
const XLSX = ctx.XLSX;
console.log("SheetJS version:", XLSX.version);

const headers = ["RADICADO","FECHA DE RADICACION","COMPARENDO","NOMBRE","FECHA DE NOTIF","PLACA"];
const rows = [
  ["2026ER1", new Date(2026,3,19), "46855268", "JOSE PÉREZ CASTAÑEDA", "", "ABC123"],
  ["2026ER2", new Date(2026,4,2),  "46855269", "MARÍA ÑÚÑEZ",           new Date(2026,4,1), "XYZ12D"],
];
const wsData = [headers].concat(rows);
const ws = XLSX.utils.aoa_to_sheet(wsData, {cellDates:true, dateNF:"dd/mm/yyyy"});
ws["!cols"] = headers.map(h => ({wch: Math.min(38, Math.max(11, h.length+2))}));
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, "Datos");
const bruto = XLSX.write(wb, {type:"array", bookType:"xlsx", compression:false});
fs.writeFileSync(path.join(SP,"sin_rejilla.xlsx"), Buffer.from(new Uint8Array(bruto)));
const con = ctx.ponerRejillaAlXlsx(bruto);
if(!con){ console.log("FALLO: ponerRejillaAlXlsx devolvió null"); process.exit(1); }
fs.writeFileSync(path.join(SP,"con_rejilla.xlsx"), Buffer.from(con));
console.log("OK: archivo con rejilla escrito,", con.length, "bytes (sin rejilla:", bruto.byteLength, ")");
