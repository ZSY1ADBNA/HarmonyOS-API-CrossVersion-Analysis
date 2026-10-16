// Script-level simulation only: no browser or layout validation is claimed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, 'templates/verified_search.js'), 'utf8');
class Element {
  constructor() { this.handlers = {}; this.children = []; this.value = ''; this.textContent = ''; }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  set innerHTML(_) { throw Error('Unsafe HTML rendering'); }
}
function setup() {
  const elements = Object.fromEntries(['search-form','message','release','compare','status','results','context','clear-context'].map(id=>[id,new Element()]));
  elements.message.value='fontSize'; elements.release.value='4.1';
  const requests = [], timers = [];
  vm.runInNewContext(source, {
    document: {querySelector: selector=>elements[selector.slice(1)], createElement:()=>new Element()},
    AbortController, URL, URLSearchParams,
    setTimeout: callback=>{timers.push(callback); return timers.length-1;}, clearTimeout: ()=>{},
    fetch: (url, options)=>new Promise(resolve=>requests.push({url, signal:options.signal, body:JSON.parse(options.body), resolve}))
  });
  const submit = ()=>elements['search-form'].handlers.submit({preventDefault(){}});
  return {elements, requests, timers, submit};
}
const response = data=>({ok:true,json:async()=>({status:data.status,clarification:data.clarification||null,
  state:data.state||{schema_version:1,message:'fontSize',release:data.candidates?.[0]?.evidence.release||null,compare_with:null},query:data})});
const candidate = name=>({name,evidence:{owner:'ButtonAttribute',name,release:'4.1',api_level:11,module:'ArkUI globals',
  signature:'fontSize(value: Length): ButtonAttribute;',optional:false,sdk_evidence:{path:'ets/component/button.d.ts'},
  sdk_archive_url:'https://repo.huaweicloud.com/openharmony/os/4.1-Release/ohos-sdk-windows_linux-public.tar.gz'}});
const found = name=>({status:'verified_candidates_found',candidates:[candidate(name)],comparisons:[],
  explanation:{status:'verified_candidates_found',generation_mode:'deterministic_evidence_summary',
    candidates:[{name:'ButtonAttribute.'+name,selection_reason:'fixture',facts:[{text:'fixture fact',source_id:'source'}]}],
    comparisons:[],unknowns:['device not verified'],sources:{source:{release:'4.1',sdk_url:candidate(name).evidence.sdk_archive_url,
      declaration_path:'ets/component/button.d.ts',file_sha256:'fixture-hash'}}}});
(async()=>{
  const checks = [];
  {
    const s=setup(); const old=s.submit(); const newer=s.submit();
    assert.equal(s.requests[0].signal.aborted,true);
    s.timers[0](); assert.equal(s.requests[1].signal.aborted,false);
    s.requests[1].resolve(response(found('new'))); await newer;
    s.requests[0].resolve(response(found('old'))); await old;
    assert.equal(s.elements.results.children[0].children[0].textContent,'ButtonAttribute.new');
    checks.push('old_timer_and_old_response_do_not_affect_new_query');
  }
  {
    const s=setup(); const pending=s.submit();
    s.elements.release.value='5.0.3';s.elements.release.handlers.input();
    s.requests[0].resolve(response(found('stale')));await pending;
    assert.equal(s.elements.results.children.length,0);
    assert.match(s.elements.status.textContent,/重新查询/);
    checks.push('version_change_clears_and_rejects_stale_response');
  }
  {
    const s=setup();const pending=s.submit();
    s.requests[0].resolve({ok:false,json:async()=>({status:'evidence_unavailable'})});await pending;
    assert.equal(s.elements.results.children.length,0);assert.match(s.elements.status.textContent,/失败/);
    checks.push('http_failure_has_no_candidate');
  }
  {
    const s=setup();const pending=s.submit();s.requests[0].resolve(response(found('<img src=x onerror=alert(1)>')));await pending;
    assert.equal(s.elements.results.children[0].children[0].textContent,'ButtonAttribute.<img src=x onerror=alert(1)>');
    checks.push('untrusted_text_not_rendered_as_html');
  }
  {
    const s=setup();s.elements.release.value='';const pending=s.submit();
    s.requests[0].resolve(response({status:'needs_version'}));await pending;
    assert.equal(s.elements.results.children.length,0);assert.match(s.elements.status.textContent,/版本/);
    s.elements.message.value='4.1';const next=s.submit();
    assert.equal(s.requests[1].body.state.message,'fontSize');
    s.requests[1].resolve(response(found('fontSize')));await next;
    checks.push('pending_requirement_is_sent_when_version_is_supplied');
  }
  {
    const s=setup();const pending=s.submit();const payload=found('fontSize');
    delete payload.explanation.sources.source;
    s.requests[0].resolve(response(payload));await pending;
    assert.equal(s.elements.results.children.length,0);assert.match(s.elements.status.textContent,/失败/);
    checks.push('missing_citation_rejects_explanation_and_partial_cards');
  }
  {
    const s=setup();const pending=s.submit();const payload=found('fontSize');
    payload.explanation.sources.source.sdk_url='javascript:alert(1)';
    s.requests[0].resolve(response(payload));await pending;
    assert.equal(s.elements.results.children.length,0);assert.match(s.elements.status.textContent,/失败/);
    checks.push('untrusted_citation_url_rejected');
  }
  {
    const s=setup();const pending=s.submit();
    s.elements['clear-context'].handlers.click();
    s.requests[0].resolve(response(found('stale')));await pending;
    assert.equal(s.elements.results.children.length,0);
    assert.equal(s.elements.release.value,'');
    assert.match(s.elements.status.textContent,/清空/);
    checks.push('clear_context_rejects_inflight_response');
  }
  console.log(JSON.stringify({scope:'Node script simulation; not browser validation',passed:true,checks}));
})().catch(error=>{console.error(error);process.exitCode=1;});
