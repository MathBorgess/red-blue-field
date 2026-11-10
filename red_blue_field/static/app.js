'use strict';
// Tokens remain in memory and never enter URLs, storage, or exported evidence.
let token = '', current = null, catalog = [], activeTab = 'traces', busy = false, realTargetAvailable = false, targetState = null;
const $ = id => document.getElementById(id);
const text = (node, value) => { node.textContent = value ?? ''; };
const json = value => JSON.stringify(value, null, 2);
const refs = id => $(id).value.split(',').map(x => x.trim()).filter(Boolean);
function notice(message) { text($('notice'), message); $('notice').hidden = false; setTimeout(() => $('notice').hidden = true, 9000); }
async function api(path, method = 'GET', body) {
  const response = await fetch(path, {method, headers: {'X-Control-Token': token, 'Content-Type': 'application/json'}, body: body === undefined ? undefined : JSON.stringify(body)});
  if (!response.ok) { const value = await response.json().catch(() => ({})); throw new Error(json(value.detail || value)); }
  if (response.headers.get('content-type')?.includes('application/json')) return response.json();
  return response.blob();
}
async function download(path, name) { const blob = await api(path); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
const base = () => '/api/runs/' + current.id;
function button(label, handler, style = '') { const b = document.createElement('button'); text(b, label); b.className = style; b.addEventListener('click', () => handler().catch(e => notice(e.message))); return b; }
function pretty(container, value) { const pre = document.createElement('pre'); text(pre, json(value)); container.append(pre); }
async function refresh() {
  if (!token || busy) return;
  busy = true;
  try {
    const [runs, campaigns] = await Promise.all([api('/api/runs'), api('/api/campaigns')]);
    $('runs').replaceChildren();
    for (const run of runs.slice().reverse().slice(0, 30)) { const b = button(run.scenario_id + ' · ' + run.profile + ' · ' + run.status, async () => { current = run; await refreshRun(); }, 'run-item'); const small = document.createElement('small'); text(small, run.id.slice(0, 12) + ' · ' + run.record_kind); b.append(small); $('runs').append(b); }
    $('campaigns').replaceChildren();
    for (const c of campaigns.slice().reverse().slice(0, 5)) { const item = document.createElement('div'); item.className = 'campaign'; text(item, `${c.id.slice(0, 10)} · ${c.status} · ${c.runs.length}/${c.scheduled} episódios`); if (['scheduled', 'running'].includes(c.status)) item.append(button('Interromper', () => api('/api/campaigns/' + c.id + '/stop', 'POST'), 'quiet')); $('campaigns').append(item); }
    if (current) await refreshRun();
  } catch (e) { notice(e.message); } finally { busy = false; }
}
async function refreshRun() {
  current = await api(base()); $('empty').hidden = true; $('episode').hidden = false;
  text($('run-id'), current.id); text($('run-title'), current.scenario_id + ' · ' + current.title); text($('status'), current.status);
  text($('context'), `${current.record_kind} · ${current.context.environment_kind} · perfil ${current.profile} · ${current.request.benign ? 'controle benigno' : 'entrada adversarial'}`);
  const ep = current.episode;
  $('metrics').replaceChildren();
  for (const [label, value] of [['Passos', current.tool_calls], ['Chamadas ao modelo', current.model_calls], ['Hipóteses', current.hypothesis_count], ['Resultado', ep?.outcome || 'Em estudo']]) { const div = document.createElement('div'); div.className = 'metric'; const strong = document.createElement('strong'); text(strong, value); const span = document.createElement('span'); text(span, label); div.append(strong, span); $('metrics').append(div); }
  text($('limitations'), current.error || current.limitations.join(' '));
  const closed = ['complete', 'invalid', 'interrupted'].includes(current.status);
  for (const id of ['start', 'step', 'finish', 'stop', 'blue', 'run-tool']) $(id).disabled = closed;
  $('export').disabled = !closed;
  const liveTarget = current.request.target_driver === 'openai_external';
  $('target-panel').hidden = !liveTarget;
  if (liveTarget) {
    targetState = await api(base() + '/target');
    const deadline = targetState.valid_until ? Date.parse(targetState.valid_until) : Date.parse(current.created_at) + current.request.budget.wall_time_seconds * 1000;
    const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    const stages = {idle: 'Aguardando proposta do operador', awaiting_model: 'Aguardando liberação de chamada', waiting_target: 'Chamada autorizada; aguardando alvo', submitted: 'Chamada em andamento', awaiting_tool: 'Função proposta; aguardando sua liberação', applying_tool: 'Tentativa registrada; confira os eventos antes de continuar', completed: 'Resposta concluída', interrupted: 'Interrompido', blocked: 'Bloqueado para conferência'};
    text($('target-status'), `${stages[targetState.status] || targetState.status} · ${targetState.model || 'modelo registrado no episódio'}${Number.isFinite(remaining) ? ' · prazo: ' + remaining + 's' : ''}`);
    const spending = targetState.spending, money = value => 'US$ ' + Number(value || 0).toFixed(4).replace('.', ',');
    text($('target-budget'), spending ? `Piloto: ${spending.requests}/${spending.max_requests} chamadas · uso estimado ${money(spending.spent_usd)} · reservado ${money(spending.reserved_usd)} · teto US$ 1,00. Episódio: ${spending.episode?.requests || 0}/${spending.episode?.max_requests || 4} chamadas · teto US$ 0,20.${spending.blocked ? ' Novas chamadas bloqueadas: é necessário conferir o registro.' : ''}` : 'Orçamento indisponível; confira o registro antes de continuar.');
    text($('target-observation'), targetState.pending_tool || targetState.last_output ? json({proposta: targetState.pending_tool || null, resposta_publica: targetState.last_output || null, uso: targetState.usage || null}) : spending?.episode?.requests ? 'Nenhuma resposta pública disponível. Confira o estado da chamada nos eventos antes de continuar.' : 'Nenhuma resposta ou função proposta. O modelo ainda não foi chamado.');
    $('target-model').disabled = closed || !targetState.can_advance_model;
    $('target-tool').disabled = closed || !targetState.can_advance_tool;
  } else { targetState = null; }
  const reviews = await api(base() + '/reviews'); const pending = reviews.filter(r => r.status === 'pending');
  $('reviews-panel').hidden = pending.length === 0; $('reviews').replaceChildren();
  for (const r of pending) { const div = document.createElement('div'); div.className = 'review'; pretty(div, r.operation); const hash = document.createElement('p'); text(hash, 'Operação vinculada: ' + r.operation_hash); hash.className = 'muted'; div.append(hash); for (const [label, decision] of [['Aprovar', 'approve'], ['Negar', 'deny']]) div.append(button(label, async () => { const reason = prompt('Registre a justificativa da decisão:'); if (!reason) return; await api(base() + '/reviews/' + r.id, 'POST', {decision, operation_hash: r.operation_hash, reason}); await refreshRun(); }, 'secondary')); $('reviews').append(div); }
  if (activeTab === 'traces') { const events = await api(base() + '/events'); const opened = new Set(Array.from($('events').querySelectorAll('details[open]')).map(d => d.dataset.sequence)); $('events').replaceChildren(); text($('event-count'), events.length + ' eventos'); for (const e of events.slice(-150).reverse()) { const details = document.createElement('details'); details.dataset.sequence = String(e.sequence); details.open = opened.has(String(e.sequence)); const summary = document.createElement('summary'); const actor = document.createElement('span'); actor.className = 'actor ' + e.actor; text(actor, e.actor); summary.append(actor, document.createTextNode(String(e.sequence).padStart(3, '0') + ' · ' + e.event_type)); details.append(summary); pretty(details, e); $('events').append(details); } }
  if (activeTab === 'hypotheses') { const h = await api(base() + '/hypotheses'); $('nodes').replaceChildren(); for (const n of h.nodes) { const d = document.createElement('div'); d.className = 'node'; d.style.marginLeft = (n.depth * 12) + 'px'; const title = document.createElement('strong'); text(title, n.hypothesis_id + ' · ' + n.status); const p = document.createElement('p'); text(p, n.claim); const small = document.createElement('small'); text(small, 'Evidências: ' + (n.evidence_refs.join(', ') || 'pendentes')); d.append(title, p, small); $('nodes').append(d); } text($('frontier'), json(h.frontier)); }
  if (activeTab === 'state') text($('snapshot'), json(await api(base() + '/state')));
  if (activeTab === 'assessment') text($('assessments'), json(await api(base() + '/assessments')));
}
$('connect').addEventListener('submit', async e => { e.preventDefault(); token = $('token').value; try { const r = await api('/api/readiness'); realTargetAvailable = Boolean(r.real_target_enabled); catalog = (await api('/api/scenarios')).scenarios; $('scenario').replaceChildren(...catalog.map(s => { const o = document.createElement('option'); o.value = s.id; text(o, s.id + ' · ' + s.title); return o; })); describe(); $('login').hidden = true; $('workspace').hidden = false; $('token').value = ''; text($('ready'), `Serviços locais prontos · workers ${r.workers_configured ? 'configurados' : 'pendentes'} · alvo real ${realTargetAvailable ? 'habilitado' : 'não habilitado'}`); await refresh(); } catch (error) { token = ''; notice(error.message); } });
function describe() { const s = catalog.find(s => s.id === $('scenario').value); text($('scenario-description'), s?.legitimate_task); const realOption = $('target-driver').querySelector('[value="openai_external"]'); realOption.disabled = !realTargetAvailable || $('scenario').value !== 'S02'; if (realOption.disabled) $('target-driver').value = 'scripted'; targetDriverChanged(false); }
function targetDriverChanged(resetBudget = true) {
  const real = $('target-driver').value === 'openai_external';
  if (real) $('mode').value = 'manual';
  $('mode').disabled = real;
  if (resetBudget) { $('deadline').value = real ? '1200' : '120'; $('steps').value = real ? '8' : '40'; }
  text($('target-description'), real ? 'Alvo real separado do operador. Cada chamada e função dependem de liberação; teto do piloto US$ 1,00, até US$ 0,20 por episódio.' : 'O fixture valida o mecanismo; não mede a robustez de um modelo.');
}
$('scenario').addEventListener('change', describe);
$('target-driver').addEventListener('change', () => targetDriverChanged());
$('disconnect').addEventListener('click', () => { token = ''; current = null; $('workspace').hidden = true; $('login').hidden = false; });
$('new-run').addEventListener('submit', async e => { e.preventDefault(); try { const real = $('target-driver').value === 'openai_external'; current = await api('/api/runs', 'POST', {scenario_id: $('scenario').value, profile: $('profile').value, mode: $('mode').value, target_driver: $('target-driver').value, benign: $('benign').checked, budget: {max_steps: Number($('steps').value), wall_time_seconds: Number($('deadline').value), ...(real ? {max_model_calls: 4, max_total_tokens: 56000, monetary_cap_usd: 0.20} : {})}}); await refresh(); } catch (error) { notice(error.message); } });
for (const [id, stage] of [['target-model', 'model'], ['target-tool', 'tool']]) $(id).addEventListener('click', async () => {
  if (!targetState || !current) return;
  const question = stage === 'model' ? 'Liberar uma chamada do modelo dentro do orçamento deste episódio?' : 'Tentar a função proposta, mantendo a decisão de autorização no backend?';
  if (!confirm(question)) return;
  $(id).disabled = true;
  try { await api(base() + '/target/advance', 'POST', {expected_revision: targetState.revision, stage}); await refreshRun(); } catch (e) { notice(e.message); }
});
for (const name of ['start', 'step', 'finish', 'stop']) $(name).addEventListener('click', async () => { try { await api(base() + '/' + name, 'POST'); await refresh(); } catch (e) { notice(e.message); } });
$('export').addEventListener('click', () => download(base() + '/export', current.id + '.zip').catch(e => notice(e.message)));
$('learning').addEventListener('click', () => download(base() + '/learning-report', current.id + '-aprendizado.md').catch(e => notice(e.message)));
document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => { activeTab = b.dataset.tab; document.querySelectorAll('.tab').forEach(t => t.hidden = t.id !== activeTab); document.querySelectorAll('[data-tab]').forEach(t => t.classList.toggle('active', t === b)); refreshRun().catch(e => notice(e.message)); }));
$('proposal').addEventListener('submit', async e => { e.preventDefault(); try { await api(base() + '/hypotheses', 'POST', {action: JSON.parse($('action').value), claim: $('claim').value, falsification: $('falsification').value, parent_id: $('parent').value || null}); await refreshRun(); } catch (error) { notice(error.message); } });
$('blue').addEventListener('click', async () => { const reason = prompt('Qual evidência justifica a intervenção?'); if (!reason) return; try { await api(base() + '/blue', 'POST', {response: $('blue-response').value, reason}); await refreshRun(); } catch (e) { notice(e.message); } });
$('credentials').addEventListener('click', async () => { try { text($('tool-result'), json(await api(base() + '/credentials'))); } catch (e) { notice(e.message); } });
$('run-tool').addEventListener('click', async () => { try { text($('tool-result'), 'Executando no worker…'); text($('tool-result'), json(await api(base() + '/tools', 'POST', {profile: $('tool-profile').value}))); await refreshRun(); } catch (e) { notice(e.message); } });
$('finding').addEventListener('submit', async e => { e.preventDefault(); try { const status = $('finding-status').value; await api(base() + '/findings', 'POST', {status, reason: $('finding-reason').value, evidence_refs: refs('finding-refs'), severity: status === 'confirmed' ? $('severity').value : null, decisive_unknown: status === 'needs_validation' ? 'Verificação independente pendente' : null, validation_plan: status === 'needs_validation' ? 'Reproduzir em episódio novo e comparar o perfil protegido.' : null}); notice('Revisão registrada.'); } catch (error) { notice(error.message); } });
$('assessment-form').addEventListener('submit', async e => { e.preventDefault(); try { await api(base() + '/assessments', 'POST', {competency: $('competency').value, level: $('level').value, explanation: $('explanation').value, evidence_refs: refs('assessment-refs'), assistance: $('assistance').value, gaps: $('gaps').value}); await refreshRun(); } catch (error) { notice(error.message); } });
$('campaign-form').addEventListener('submit', async e => { e.preventDefault(); try { await api('/api/campaigns', 'POST', {scenarios: refs('campaign-scenarios'), profiles: ['A', 'B', 'C'], repetitions: 1, paired_benign: true, mode: 'scripted'}); await refresh(); } catch (error) { notice(error.message); } });
setInterval(refresh, 1800);
