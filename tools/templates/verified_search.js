'use strict';
const form = document.querySelector('#search-form');
const message = document.querySelector('#message');
const release = document.querySelector('#release');
const compare = document.querySelector('#compare');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const context = document.querySelector('#context');
let sessionState = null;
let sequence = 0;
let controller;
function reset() {
  sequence += 1;
  if (controller) controller.abort();
  results.replaceChildren();
  status.textContent = '条件已改变，请重新查询。';
}
for (const input of [message, release, compare]) input.addEventListener('input', reset);
document.querySelector('#clear-context').addEventListener('click', () => {
  reset(); sessionState = null;
  message.value = ''; release.value = ''; compare.value = '';
  context.textContent = '尚未保存查询上下文。';
  status.textContent = '上下文已清空，请重新输入需求。';
});
function line(parent, label, value, tag = 'p') {
  const element = document.createElement(tag);
  element.textContent = label + value;
  parent.append(element);
}
function citation(parent, source, label) {
  if (!source) throw new Error('Missing citation');
  const url = new URL(source.sdk_url);
  if (url.protocol !== 'https:' || url.hostname !== 'repo.huaweicloud.com') throw new Error('Invalid citation');
  const link = document.createElement('a');
  link.href = url.href;
  link.textContent = label + '（' + source.release + '）';
  link.title = source.declaration_path + ' / SHA256: ' + source.file_sha256;
  link.target = '_blank'; link.rel = 'noopener noreferrer';
  parent.append(link);
}
const messages = {
  needs_version: '请先选择明确的目标版本。',
  unsupported_release: '该版本尚未纳入已核验样本。',
  needs_intent_clarification: '需求包含否定或排除条件，请改为说明希望查询的功能。',
  no_verified_match: '当前仅支持按钮字号和音频声道布局，未找到匹配证据。',
  evidence_unavailable: '证据暂时无法核验，请稍后重试。'
};
form.addEventListener('submit', async event => {
  event.preventDefault();
  reset();
  const requestId = sequence;
  controller = new AbortController();
  const currentController = controller;
  const timer = setTimeout(() => currentController.abort(), 10000);
  const payload = {message: message.value, release: release.value, compare_with: compare.value, state: sessionState};
  status.textContent = '正在核对证据…';
  try {
    const response = await fetch('/api/verified-turn', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:currentController.signal});
    const reply = await response.json();
    if (requestId !== sequence) return;
    if (!response.ok) throw new Error('Search failed');
    if (!reply.state) throw new Error('Missing session state');
    sessionState = reply.state;
    release.value = sessionState.release || ''; compare.value = sessionState.compare_with || '';
    context.textContent = '当前上下文：' + (sessionState.message || '待补需求') + ' · ' + (sessionState.release || '待补版本') + (sessionState.compare_with ? ' → ' + sessionState.compare_with : '');
    if (reply.status !== 'verified_candidates_found' && reply.status !== 'needs_more_evidence') {
      status.textContent = reply.clarification || messages[reply.status] || '查询暂不可用。'; return;
    }
    const data = reply.query;
    if (!data) throw new Error('Missing verified result');
    const explanation = data.explanation;
    if (!explanation || explanation.generation_mode !== 'deterministic_evidence_summary' || explanation.status !== data.status) {
      throw new Error('Inconsistent explanation');
    }
    for (const candidate of data.candidates) {
      const evidence = candidate.evidence;
      const card = document.createElement('article');
      line(card, '', evidence.owner + '.' + evidence.name, 'h2');
      line(card, '发行版本：', evidence.release + ' / API ' + evidence.api_level);
      line(card, '模块：', evidence.module);
      line(card, '', evidence.signature, 'pre');
      line(card, '是否可选：', evidence.optional ? '是（不推断默认值）' : '否');
      line(card, '声明出处：', evidence.sdk_evidence.path);
      line(card, '已记录的编译：', '通过；设备运行尚未验证');
      const link = document.createElement('a');
      const source = new URL(evidence.sdk_archive_url);
      if (source.protocol === 'https:' && source.hostname === 'repo.huaweicloud.com') {
        link.href = source.href; link.textContent = '正式 SDK 来源';
        link.target = '_blank'; link.rel = 'noopener noreferrer'; card.append(link);
      }
      for (const diff of data.comparisons.filter(item => item.name === evidence.name)) {
        line(card, '比较方向：', diff.old.release + ' → ' + diff.new.release);
        const fields = Object.keys(diff.differences);
        line(card, '声明差异：', fields.length ? fields.map(key => ({metadata:'成员注释',ancestor_metadata:'父级注释',signature:'签名',optional:'可选性',parameters:'参数',declared_type:'声明类型'}[key] || key)).join('、') : '所比较字段相同');
        for (const field of fields) {
          const values = diff.differences[field];
          if (field === 'metadata' || field === 'ancestor_metadata') {
            const context = field === 'metadata' ? '成员' : '父级';
            for (const [key, title] of Object.entries({since_raw:'原始版本注释',syscap:'系统能力',systemapi:'系统接口标记',internal:'内部接口标记'})) {
              if (JSON.stringify(values.old[key]) === JSON.stringify(values.new[key])) continue;
              const format = value => Array.isArray(value) ? value.join('、') : String(value ?? '未知');
              line(card, diff.old.release + ' ' + context + title + '：', format(values.old[key]));
              line(card, diff.new.release + ' ' + context + title + '：', format(values.new[key]));
            }
          } else {
            line(card, '起始值：', JSON.stringify(values.old), 'pre');
            line(card, '目标值：', JSON.stringify(values.new), 'pre');
          }
        }
      }
      const described = explanation.candidates.find(item => item.name === evidence.owner + '.' + evidence.name);
      if (!described) throw new Error('Missing candidate explanation');
      line(card, '', '证据说明（规则整理，非 AI 回答）', 'h3');
      line(card, '', described.selection_reason);
      for (const fact of described.facts) {
        const row = document.createElement('p');
        row.textContent = fact.text + ' ';
        citation(row, explanation.sources[fact.source_id], '声明出处');
        card.append(row);
      }
      for (const diff of explanation.comparisons.filter(item => item.name === evidence.name)) {
        line(card, '起始版本 ' + diff.from_release + '：', diff.from_signature, 'pre');
        citation(card, explanation.sources[diff.source_ids[0]], '起始版本来源');
        line(card, '目标版本 ' + diff.to_release + '：', diff.to_signature, 'pre');
        citation(card, explanation.sources[diff.source_ids[1]], '目标版本来源');
        line(card, '', diff.explanation);
      }
      line(card, '仍需核实：', explanation.unknowns.join('；'));
      results.append(card);
    }
    status.textContent = reply.status === 'needs_more_evidence' ? reply.clarification : '找到 ' + data.candidates.length + ' 项已核验候选。';
  } catch (error) {
    if (requestId !== sequence) return;
    results.replaceChildren();
    status.textContent = '查询失败或等待超时，请重试。';
  } finally { clearTimeout(timer); }
});
