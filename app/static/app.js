const form = document.querySelector('#lead-form');
if (form) form.addEventListener('submit', async (event) => {
  event.preventDefault(); const message = document.querySelector('#form-message');
  const button = form.querySelector('button'); button.disabled = true; message.textContent = 'Sending…'; message.className = 'message';
  try { const data = Object.fromEntries(new FormData(form)); const response = await fetch('/api/leads', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Unable to submit your enquiry.');
    message.textContent = `Thanks, ${body.name}. Your enquiry has been received. Our team will be in touch.`; message.className = 'message success'; form.reset();
  } catch (e) { message.textContent = e.message; message.className = 'message error'; } finally { button.disabled = false; }
});
const csvForm = document.querySelector('#csv-form');
if (csvForm) csvForm.addEventListener('submit', async (event) => {
  event.preventDefault(); const message = document.querySelector('#csv-message'); const button = csvForm.querySelector('button'); button.disabled=true; message.textContent='Importing…';
  try { const response=await fetch('/api/leads/import',{method:'POST',body:new FormData(csvForm)}); const data=await response.json(); if(!response.ok) throw new Error(data.detail||'Import failed.');
    message.innerHTML=`<strong>${data.successfully_imported} imported</strong> · ${data.total_rows} rows · ${data.duplicates} duplicates · ${data.invalid_rows} invalid · ${data.failed_rows} failed${data.row_errors.length?'<br>'+data.row_errors.map(x=>`Row ${x.row}: ${escapeHtml(x.error)}`).join('<br>'):''}`; message.className='message success'; csvForm.reset();
  } catch(e){message.textContent=e.message;message.className='message error';} finally{button.disabled=false;}
});
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
const statsEl=document.querySelector('#stats');
if(statsEl){
  const statDefs=[['total_leads','Total leads'],['new_leads','New leads'],['contacted_leads','Contacted'],['qualified_leads','Qualified'],['converted_leads','Converted'],['lost_leads','Lost'],['website_leads','Website leads'],['csv_leads','CSV leads'],['duplicate_count','Duplicates'],['invalid_count','Invalid rows']];
  const fmtDate=s=>new Date(s).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
  async function refresh(){
    const [sr,lr,gr]=await Promise.all([fetch('/api/stats'),fetch(`/api/leads?q=${encodeURIComponent(document.querySelector('#search').value)}&status=${encodeURIComponent(document.querySelector('#status-filter').value)}`),fetch('/api/logs?limit=12')]);
    const stats=await sr.json(), leads=await lr.json(), logs=await gr.json();
    statsEl.innerHTML=statDefs.map(([key,label],i)=>`<article class="stat ${i===0?'featured':''}"><span>${label}</span><strong>${stats[key]??0}</strong></article>`).join('');
    const tbody=document.querySelector('#leads-body'); tbody.innerHTML=leads.map(x=>`<tr><td class="person">${escapeHtml(x.name)}</td><td>${escapeHtml(x.email)}</td><td>${escapeHtml(x.company)}</td><td><span class="source ${x.source.toLowerCase()}">${escapeHtml(x.source)}</span></td><td><span class="status ${x.status.toLowerCase()}">${escapeHtml(x.status)}</span></td><td>${fmtDate(x.created_at)}</td></tr>`).join('');
    document.querySelector('#empty').hidden=leads.length>0;
    document.querySelector('#logs').innerHTML=logs.map(x=>`<div class="log-row"><span class="log-dot ${x.status}"></span><div><strong>${escapeHtml(x.action.replaceAll('_',' '))}</strong><p>${escapeHtml(x.message)}</p></div><time>${fmtDate(x.created_at)}</time></div>`).join('')||'<p class="muted">No activity yet.</p>';
  }
  document.querySelector('#search').addEventListener('input',refresh); document.querySelector('#status-filter').addEventListener('change',refresh); refresh();
}
