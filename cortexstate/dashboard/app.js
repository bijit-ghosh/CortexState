'use strict';
const $ = id => document.getElementById(id);
let key = '', scope = null, selected = null, records = [], offset = 0, query = '', ranking = 'overlap';
let refreshing = false, generation = 0, confirmAction = null, pendingAddKey = null;
function notice(message, error = false) { $('notice').textContent = message; $('notice').classList.toggle('error', error); const log=document.createElement('li');log.textContent=`${new Date().toLocaleTimeString()} — ${message}`;$('activity').prepend(log);while($('activity').children.length>12)$('activity').lastChild.remove(); }
async function call(operation, payload = {}) {
  const response = await fetch(`/v1/memories/${operation}`, {method:'POST', headers:{'Authorization':`Bearer ${key}`,'Content-Type':'application/json'}, body:JSON.stringify({scope,...payload}), signal:AbortSignal.timeout(['answer','propose'].includes(operation)?60000:12000)});
  const body = await response.json();
  if (!response.ok) throw new Error(response.status === 401 ? 'Service key was rejected. Disconnect and use a valid key.' : `${body.error}${body.detail ? ': '+body.detail : ''}`);
  return body.result;
}
function date(value) { return value ? new Date(value*1000).toLocaleString() : 'Never'; }
function resetInspector() { selected=null; $('detail').hidden=true; $('empty-inspector').hidden=false; }
function render() {
  $('memories').replaceChildren();
  if (!records.length) { const empty=document.createElement('p'); empty.className='empty'; empty.textContent=query?'No matching facts. Try words from the memory or another scope.':'No memories in this scope yet. Add a confirmed fact to begin.'; $('memories').append(empty); }
  for (const record of records) {
    const row=document.createElement('button'); row.className='memory-row'+(selected?.id===record.id?' selected':'');
    const fact=document.createElement('p'); fact.textContent=record.text;
    const caption=document.createElement('small'); caption.textContent=`Revision ${record.revision} · ${date(record.updated_at)}${record.score!==undefined?' · Score '+record.score.toFixed(3):''}`;
    row.append(fact,caption); row.addEventListener('click',()=>inspect(record)); $('memories').append(row);
    if(record.signals){const signals=document.createElement('p');signals.className='signals';signals.textContent=`Lexical ${record.signals.lexical.toFixed(3)} / Semantic ${record.signals.semantic.toFixed(3)}`;row.append(signals);}
  }
  $('result-count').textContent=query?`${records.length} matching memories (up to 100)`:`${records.length} memories on this page`;
  $('page').textContent=query?'Search results':`Page ${offset/20+1}`;
  $('previous').disabled=!!query||offset===0; $('next').disabled=!!query||records.length<20;
}
async function refresh() {
  if (!key || !scope || refreshing) return;
  const token=generation, requestedQuery=query, requestedOffset=offset, requestedRanking=ranking; refreshing=true;
  try {
    const [stats, data]=await Promise.all([call('stats'),query?call('search',{query,ranking,limit:100}):call('list',{limit:20,offset})]);
    if(token!==generation||requestedQuery!==query||requestedOffset!==offset||requestedRanking!==ranking)return;
    records=data; render(); $('live-count').textContent=stats.live; $('revision-count').textContent=stats.revision_events; $('expired-count').textContent=stats.expired;
    $('sync-time').textContent=`Synced ${new Date().toLocaleTimeString()}`; $('connection').textContent='Connected'; $('connection').classList.add('connected');
    $('model-state').textContent=stats.generation_available?'Model connected. These actions send text to the configured provider and may incur usage charges.':'Model not configured. Set CORTEXSTATE_GENERATION_MODEL and OPENAI_API_KEY on the server to enable API calls.';
    if(!$('ask-form').dataset.busy)$('ask').disabled=!stats.generation_available;
    if(!$('extract-form').dataset.busy)$('extract').disabled=!stats.generation_available;
    if(selected){const current=data.find(r=>r.id===selected.id); if(current&&current.revision!==selected.revision) notice('This memory changed. Select it again to load the latest revision before editing.');}
  } catch(error) { if(token===generation){notice(error.message,true); $('connection').textContent='Connection error'; $('connection').classList.remove('connected');} }
  finally { refreshing=false; if(key&&(token!==generation||requestedQuery!==query||requestedOffset!==offset||requestedRanking!==ranking))refresh(); }
}
async function inspect(record) {
  selected=record; const token=generation; render(); $('empty-inspector').hidden=true; $('detail').hidden=false;
  $('record-id').textContent=record.id; $('record-status').textContent=`Revision ${record.revision} • Expires: ${date(record.expires_at)}`;
  $('edit-text').value=record.text; $('edit-metadata').value=JSON.stringify(record.metadata,null,2); $('history').replaceChildren();
  try {const history=await call('history',{identifier:record.id}); if(token!==generation||selected?.id!==record.id)return; for(const event of history){const item=document.createElement('li'); item.textContent=`${event.action} — revision ${event.memory.revision}`; const text=document.createElement('p');text.textContent=event.memory.text; item.append(text); $('history').append(item);}}
  catch(error){notice(error.message,true);}
}
$('connect-form').addEventListener('submit',async event=>{event.preventDefault(); key=$('key').value;scope={user:$('user').value,agent:$('agent').value,session:$('session').value};try{await call('stats');$('key').value='';$('connect-panel').hidden=true;$('console').hidden=false;notice('Connected. Select a memory to inspect it.');await refresh();}catch(error){key='';notice(error.message,true);}});
$('disconnect').addEventListener('click',()=>{generation++;key='';scope=null;records=[];resetInspector();$('memories').replaceChildren();$('console').hidden=true;$('connect-panel').hidden=false;$('connection').textContent='Disconnected';$('connection').classList.remove('connected');notice('Disconnected. The service key has been cleared from this console.');});
$('scope-form').addEventListener('submit',async event=>{event.preventDefault();generation++;scope={user:$('user').value,agent:$('agent').value,session:$('session').value};offset=0;resetInspector();notice('Scope updated.');await refresh();});
$('search-form').addEventListener('submit',event=>{event.preventDefault();query=$('query').value.trim();ranking=$('ranking').value;offset=0;refresh();});
$('clear').addEventListener('click',()=>{query='';$('query').value='';offset=0;refresh();});
$('previous').addEventListener('click',()=>{offset=Math.max(0,offset-20);refresh();});
$('next').addEventListener('click',()=>{offset+=20;refresh();});
$('new-memory').addEventListener('click',()=>{pendingAddKey=crypto.randomUUID();$('create-form').reset();$('create-error').textContent='';$('create-dialog').showModal();});
$('close-create').addEventListener('click',()=>$('create-dialog').close());
$('create-form').addEventListener('submit',async event=>{event.preventDefault();const button=event.submitter;button.disabled=true;try{const payload={text:$('new-text').value,metadata:{source:$('new-source').value||'operator-confirmed'},idempotency_key:pendingAddKey};if($('new-ttl').value)payload.ttl_seconds=Number($('new-ttl').value);await call('add',payload);$('create-dialog').close();notice('Memory stored.');await refresh();}catch(error){$('create-error').textContent=error.message;}finally{button.disabled=false;}});
$('save').addEventListener('click',async()=>{if(!selected)return; const token=generation; $('save').disabled=true;try{const updated=await call('update',{identifier:selected.id,text:$('edit-text').value,metadata:JSON.parse($('edit-metadata').value),expected_revision:selected.revision});if(token!==generation)return;await inspect(updated);notice('New revision saved.');await refresh();}catch(error){if(token===generation)notice(error.message,true);}finally{$('save').disabled=false;}});
function confirm(title,copy,action){$('confirm-title').textContent=title;$('confirm-copy').textContent=copy;confirmAction=action;$('confirm-dialog').showModal();}
$('forget').addEventListener('click',()=>{if(!selected)return;const record=selected;confirm('Forget this memory?', 'This removes the fact, revision history, and retry receipts from the active database. Backups have separate retention.', async()=>{await call('delete',{identifier:record.id,expected_revision:record.revision});resetInspector();notice('Memory forgotten.');await refresh();});});
$('purge').addEventListener('click',()=>confirm('Purge expired memories?', 'Remove expired facts and their history in the current exact scope. Live memories remain.',async()=>{const count=await call('purge-expired');notice(`Purged ${count} expired memories.`);await refresh();}));
$('cancel-confirm').addEventListener('click',()=>$('confirm-dialog').close());
$('confirm-form').addEventListener('submit',async event=>{event.preventDefault();$('confirm-action').disabled=true;try{await confirmAction();$('confirm-dialog').close();}catch(error){notice(error.message,true);$('confirm-dialog').close();}finally{$('confirm-action').disabled=false;confirmAction=null;}});
setInterval(()=>{if($('auto').checked&&!document.hidden)refresh();},3000);
function clearModelViews(){ $('answer').replaceChildren();$('proposals').replaceChildren();$('question').value='';$('conversation').value='';$('activity').replaceChildren(); }
$('scope-form').addEventListener('submit',clearModelViews);
$('disconnect').addEventListener('click',clearModelViews);
$('ask-form').addEventListener('submit',async event=>{event.preventDefault();const token=generation;$('ask-form').dataset.busy='1';$('ask').disabled=true;$('answer').textContent='Waiting for the configured model…';try{const result=await call('answer',{question:$('question').value});if(token!==generation)return;$('answer').textContent=result.answer;const evidence=document.createElement('p');evidence.className='muted';evidence.textContent=`${result.model} / ${result.memory_ids.length} memories / Input tokens: ${result.usage.input_tokens ?? 'unavailable'} / Output tokens: ${result.usage.output_tokens ?? 'unavailable'}`;$('answer').append(evidence);notice('Model answer received.');}catch(error){if(token===generation){$('answer').textContent=error.message;notice(error.message,true);}}finally{delete $('ask-form').dataset.busy;refresh();}});
$('extract-form').addEventListener('submit',async event=>{event.preventDefault();const token=generation;$('extract-form').dataset.busy='1';$('extract').disabled=true;$('proposals').textContent='Generating proposals for review…';try{const facts=await call('propose',{messages:[{role:'user',content:$('conversation').value}]});if(token!==generation)return;$('proposals').replaceChildren();if(!facts.length)$('proposals').textContent='No facts proposed.';for(const fact of facts){const box=document.createElement('div');box.className='proposal';const text=document.createElement('p');text.textContent=fact.text;const button=document.createElement('button');button.textContent='Approve and store';const retryKey=crypto.randomUUID();button.addEventListener('click',async()=>{if(token!==generation)return;button.disabled=true;try{await call('add',{text:fact.text,metadata:{source:'operator-reviewed-model-proposal',source_indices:fact.source_indices},idempotency_key:retryKey});button.textContent='Stored';notice('Approved fact stored.');await refresh();}catch(error){notice(error.message,true);button.disabled=false;}});box.append(text,button);$('proposals').append(box);}notice(`${facts.length} proposals ready for review.`);}catch(error){if(token===generation){$('proposals').textContent=error.message;notice(error.message,true);}}finally{delete $('extract-form').dataset.busy;refresh();}});
