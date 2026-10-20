// Create the reviewed test workbook with live, traceable unit/FX formulas.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const payload = JSON.parse(await fs.readFile('outputs/test_run_2025_records.json', 'utf8'));
const rows = payload.records;
assert.equal(rows.length, 25);
const wb = Workbook.create();
const result = wb.worksheets.add('Results');
const source = wb.worksheets.add('Source data');
const last = rows.length + 6;
const navy = '#173A50', teal = '#087E8B', pale = '#EDF5F7', ink = '#173042';
const numeric = '#,##0.00;(#,##0.00);0.00';

function text(sheet, cell, value) { sheet.getRange(cell).values = [[value]]; }
function heading(sheet, range, value, size=12, fill=navy) {
  sheet.mergeCells(range); text(sheet, range.split(':')[0], value);
  sheet.getRange(range).format = {fill, font:{name:'Arial',size,bold:true,color:'#FFFFFF'},verticalAlignment:'center'};
}
function base(sheet, endCol) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${endCol}${last}`).format = {font:{name:'Arial',size:11,color:ink},verticalAlignment:'center',wrapText:true};
  sheet.getRange(`A6:${endCol}6`).format = {fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:42};
  sheet.freezePanes.freezeRows(6); sheet.freezePanes.freezeColumns(2);
  sheet.getRange('A1:A1').format.rowHeight = 35;
  sheet.getRange('A2:A4').format.rowHeight = 24;
  sheet.getRange(`A7:${endCol}${last}`).format.rowHeight = 42;
  for(let r=7;r<=last;r++) if(r%2===0) sheet.getRange(`A${r}:${endCol}${r}`).format.fill = pale;
  sheet.tabColor = teal;
}
base(result,'I'); base(source,'X');
heading(result,'A1:I1',`Public companies | Fiscal years ending in ${payload.year}`,18);
result.mergeCells('A2:I2'); text(result,'A2','Ranked by revenue in CAD • Full-dollar figures • Reported consolidated net income / loss');
result.mergeCells('A3:I3'); text(result,'A3',`USD conversion: Bank of Canada, ${payload.fx_date}; 1 USD = ${payload.usdcad} CAD. Same year-end rate for all three metrics.`);
result.mergeCells('A4:I4'); text(result,'A4','Original annual statements; no estimates. Source data contains reported figures, page references and net income explanations.');
result.getRange('A2:I4').format.font = {name:'Arial',size:10,color:'#466275'};
result.getRange('A6:I6').values = [['Rank','Company','Stock symbol','Revenue (CAD)','Reported net income (CAD)','Total assets (CAD)','Converted from USD?','Fiscal year end','Review status']];

heading(source,'A1:L1','Source data | Original reported figures and conversion trail',18);
text(source,'A2','CAD per USD'); text(source,'B2',Number(payload.usdcad));
text(source,'C2','Rate date'); text(source,'D2',new Date(`${payload.fx_date}T00:00:00Z`));
source.getRange('D2').setNumberFormat('yyyy-mm-dd');
source.mergeCells('E2:L2'); text(source,'E2',payload.fx_source_url);
source.getRange('B2').setNumberFormat('0.0000');
source.getRange('B2').format = {fill:'#DCEFF0',font:{bold:true,color:'#005F73',size:12}};
source.mergeCells('A3:L3'); text(source,'A3','Reported values × source unit multiplier × applied FX rate = full CAD value. CAD sources use 1.00. Calendar December 31 rate is used even for non-calendar fiscal years.');
source.mergeCells('A4:L4'); text(source,'A4','PDF references are 1-based PDF pages. HTML references use printed page/section locators. Auditor report date is not asserted to be publication date. Source rounding remains after unit expansion.');
source.getRange('A6:X6').values = [['Company','Fiscal year end','Reported currency','Unit multiplier','Reported revenue','Reported net income','Reported assets','Converted from USD?','Applied CAD rate','Revenue (CAD)','Net income (CAD)','Assets (CAD)','Revenue / income source','Assets source','Auditor evidence','Auditor report date','Exact reported line labels','Net income explanation','Review notes','', 'Reviewed source URL','Canonical issuer report URL','Input rank','Stock symbol']];

function locator(record, metric) {
  const item=record[metric];
  return item.source_locator || (item.pdf_page ? `PDF page ${item.pdf_page}` : 'Needs manual input');
}
const sourceValues = rows.map(record => [
  record.company_name,new Date(`${record.fiscal_year_end}T00:00:00Z`),record.revenue.currency,
  record.revenue.unit_multiplier,record.revenue.value,record.net_income.value,record.total_assets.value,
  record.converted_from_usd?'Yes':'No',null,null,null,null,
  locator(record,'revenue'),locator(record,'total_assets'),
  record.auditor_evidence_locator || `PDF page ${record.auditor_evidence_pdf_page}`,
  new Date(`${record.auditor_report_date}T00:00:00Z`),
  `Revenue: ${record.revenue.source_label}\nNet income: ${record.net_income.source_label}\nAssets: ${record.total_assets.source_label}`,
  record.net_income_derivation,record.review_notes,null,record.source_url,record.original_report_url,record.input_rank,record.stock_symbol
]);
source.getRange(`A7:X${last}`).values = sourceValues;
for(let index=0;index<rows.length;index++) {
  const r=index+7, record=rows[index];
  source.getRange(`I${r}:L${r}`).formulas = [[
    `=IF(C${r}="USD",$B$2,IF(C${r}="CAD",1,"Needs manual input"))`,
    ...['E','F','G'].map(col=>`=IF(AND(ISNUMBER(${col}${r}),ISNUMBER(I${r})),${col}${r}*D${r}*I${r},"Needs manual input")`)
  ]];
  result.getRange(`A${r}:I${r}`).formulas = [[
    `=IF(ISNUMBER(D${r}),RANK(D${r},$D$7:$D$${last},0),"Needs manual input")`,
    `='Source data'!A${r}`,`='Source data'!X${r}`,
    `='Source data'!J${r}`,`='Source data'!K${r}`,`='Source data'!L${r}`,
    `='Source data'!H${r}`,`='Source data'!B${r}`,
    `=IF(AND(ISNUMBER(D${r}),ISNUMBER(E${r}),ISNUMBER(F${r})),"Ready","Needs manual input")`
  ]];
}

for(const [col,width] of Object.entries({A:7,B:39,C:24,D:23,E:23,F:23,G:13,H:15,I:15})) result.getRange(`${col}:${col}`).format.columnWidth=width;
for(const [col,width] of Object.entries({A:39,B:15,C:12,D:14,E:21,F:21,G:21,H:14,I:14,J:23,K:23,L:23,M:48,N:48,O:48,P:16,Q:45,R:95,S:85,T:3,U:68,V:68,W:10,X:25})) source.getRange(`${col}:${col}`).format.columnWidth=width;
source.getRange(`A7:X${last}`).format.rowHeight=132;
source.getRange(`A7:I${last}`).format.font = {name:'Arial',size:11,color:'#1D4C8C'};
source.getRange(`D7:G${last}`).setNumberFormat('#,##0;(#,##0);0');
rows.forEach((record,index)=>['revenue','net_income','total_assets'].forEach((key,j)=>{
  if(!Number.isInteger(record[key].value)) source.getRange(`${['E','F','G'][j]}${index+7}`).setNumberFormat('#,##0.0##;(#,##0.0##);0');
}));
source.getRange(`I7:I${last}`).setNumberFormat('0.0000');
source.getRange(`J7:L${last}`).setNumberFormat(numeric);
source.getRange(`B7:B${last}`).setNumberFormat('yyyy-mm-dd');
source.getRange(`P7:P${last}`).setNumberFormat('yyyy-mm-dd');
result.getRange(`H7:H${last}`).setNumberFormat('yyyy-mm-dd');
result.getRange(`D7:F${last}`).setNumberFormat(numeric);
result.getRange(`A7:A${last}`).format.font = {name:'Arial',size:12,bold:true,color:teal};
source.getRange(`U7:V${last}`).format.font = {name:'Arial',size:10,color:'#1D4C8C'};
// Fixed report ordering is regenerated by the Python revenue sort on each run.

function verifyAmounts(rate) {
  const actual=result.getRange(`D7:F${last}`).values;
  rows.forEach((record,i)=>['revenue','net_income','total_assets'].forEach((key,j)=>{
    const item=record[key];
    const expected=item.value*item.unit_multiplier*(item.currency==='USD'?rate:1);
    assert.equal(typeof actual[i][j],'number',`${record.company_name} ${key} must be numeric`);
    assert.ok(Math.abs(actual[i][j]-expected)<0.001,`${record.company_name} ${key}: ${actual[i][j]} vs ${expected}`);
  }));
}
// Exercise actual formula dependencies, restoring the verified rate before export.
text(source,'B2',1); wb.recalculate(); verifyAmounts(1);
text(source,'B2',Number(payload.usdcad)); wb.recalculate(); verifyAmounts(Number(payload.usdcad));
const ranks=result.getRange(`A7:A${last}`).values.map(row=>row[0]);
assert.deepEqual(ranks,Array.from({length:rows.length},(_,i)=>i+1));
assert.equal(result.getRange(`G7:G${last}`).values.filter(row=>row[0]==='Yes').length,16);
const revenues=result.getRange(`D7:D${last}`).values.flat();
assert.ok(revenues.every((amount,i)=>i===0 || revenues[i-1]>=amount));
console.log((await wb.inspect({kind:'table',range:'Results!A6:I10',include:'values,formulas',tableMaxRows:5,tableMaxCols:9,maxChars:3500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Final formula error scan'});
console.log(errors.ndjson);
await fs.mkdir('tmp/workbook_previews',{recursive:true});
for(const [name,sheet,range] of [['results','Results','A1:I16'],['source_values','Source data','A1:L10'],['source_explanations','Source data','M6:S9']]) {
  const preview=await wb.render({sheetName:sheet,range,scale:1,format:'png'});
  await fs.writeFile(`tmp/workbook_previews/${name}.png`,new Uint8Array(await preview.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save('outputs/financials_2025_test.xlsx');
await fs.writeFile('outputs/test_run_2025_checks.json',JSON.stringify({companies:25,verified_metric_values:75,usd_converted:16,cad_unchanged:9,fx_date:payload.fx_date,usdcad:payload.usdcad,formula_sensitivity_checked:true,revenue_sort_checked:true,all_ready:true},null,2)+'\n');
console.log('Saved outputs/financials_2025_test.xlsx; checked all 75 amounts and all 25 ranks.');
