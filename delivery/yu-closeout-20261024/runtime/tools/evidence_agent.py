"""Reuse the frozen member Agent loop with version-bound, read-only evidence tools."""
import copy,hashlib,importlib.util,json,re,sqlite3,subprocess
from pathlib import Path
from evidence_tools import TOOL_SCHEMAS

def validate_model_response(response):
    """Validate provider JSON before handing it to the frozen member loop."""
    if not isinstance(response,dict):raise ValueError('Expected response object')
    choices=response.get('choices')
    if not isinstance(choices,list) or not choices:raise ValueError('Missing choices')
    if not isinstance(choices[0],dict):raise ValueError('Invalid choice')
    message=choices[0].get('message')
    if not isinstance(message,dict):raise ValueError('Invalid message')
    if message.get('content') is not None and not isinstance(message['content'],str):raise ValueError('Invalid content')
    calls=message.get('tool_calls',[])
    if calls is None:calls=[]
    if not isinstance(calls,list):raise ValueError('Invalid tool calls')
    for call in calls:
        if not isinstance(call,dict) or not isinstance(call.get('id'),str) or not call['id']:raise ValueError('Missing call ID')
        function=call.get('function')
        if not isinstance(function,dict) or not isinstance(function.get('name'),str):raise ValueError('Invalid function')
        if not isinstance(function.get('arguments'),str):raise ValueError('Invalid arguments')
        if not isinstance(json.loads(function['arguments']),dict):raise ValueError('Expected argument object')
    return response

def normalize_computed_clang_locations(value):
    """Keep raw official excerpts intact; remove host roots from computed type labels only."""
    pattern=re.compile(r'\((anonymous|unnamed)(?: (struct|union|enum|class|namespace))? at ((?:[A-Za-z]:[\\/]|/)[^\r\n]*?):(\d+):(\d+)\)')
    metadata={'name','owners','signature','return_type','type','type_expression','related_types'}
    originals={'original_declaration','raw_content','original_text','candidate_text','comment','jsdoc','tags'}
    count=0
    def clean(text,source_path):
        def replace(match):
            nonlocal count
            location=match[3].replace('\\','/');relative=None
            if source_path and location.casefold().endswith('/'+source_path.casefold()):relative=source_path
            if relative is None:
                known=re.search(r'/(?:raw-sdk/[0-9a-f]{64}/|sources/[0-9a-f]{64}/content/)(.+)$',location)
                relative=known[1] if known else '<compiler-source>'
            count+=1;kind=' '+match[2] if match[2] else ''
            return f'({match[1]}{kind} at {relative}:{match[4]}:{match[5]})'
        return pattern.sub(replace,text)
    def walk(node,source_path=None,computed=False):
        if isinstance(node,dict):
            evidence=node.get('evidence')
            if isinstance(evidence,dict) and isinstance(evidence.get('path'),str):source_path=evidence['path'].replace('\\','/')
            for key,item in list(node.items()):
                if key in originals:continue
                node[key]=walk(item,source_path,key in metadata)
        elif isinstance(node,list):return [walk(item,source_path,computed) for item in node]
        elif isinstance(node,str) and computed:return clean(node,source_path)
        return node
    walk(value)
    if count:value['computed_clang_locations_normalized']=count
    return value


def model_payload(result,budget=24000):
    value=copy.deepcopy(result)
    normalize_computed_clang_locations(value)
    def size():return len(json.dumps(value,ensure_ascii=False))
    # Remove complete records, never cut a serialized JSON string or a source URL.
    for key in ('records','results','examples','documents','declarations','candidates'):
        rows=value.get(key)
        if isinstance(rows,list):
            while rows and size()>budget:
                rows.pop();value['model_payload_truncated']=True
    if size()>budget:
        value={k:value[k] for k in ('ok','tool','delivery_id','source_release','coverage','unknown_conditions','truncation_status') if k in value}
        value.update(model_payload_truncated=True,records=[],note='Result exceeded model budget; narrow the query. No omitted evidence may be inferred.')
    if len(json.dumps(value,ensure_ascii=False))>budget:
        value=dict(ok=False,error='Evidence envelope exceeded model budget',source_release=result.get('source_release'),model_payload_truncated=True)
    return json.dumps(value,ensure_ascii=False)

def completed_history(history):
    """Only completed user/assistant pairs are context, never an unanswered backlog."""
    pairs=[];pending=None
    for item in history if isinstance(history,list) else []:
        if not isinstance(item,dict) or not isinstance(item.get('content'),str):continue
        role=item.get('role');content=item['content'].strip()
        if role=='user':pending=content if content else None
        elif role=='assistant':
            if pending and content:pairs.extend([dict(role='user',content=pending[:4000]),dict(role='assistant',content=content[:4000])])
            pending=None
    return pairs[-8:]

def run(question,version,tools,ai_caller,agent_path,expected_sha256,history=None,history_version=None):
    def canonical(value):
        if hasattr(tools,'version'):return tools.version(value)
        if not isinstance(value,str):raise ValueError('Explicit source release required')
        normalized=value.removeprefix('OpenHarmony-').removesuffix('-Release').removeprefix('API')
        if normalized not in ('4.1','5.0.3','5.1.0','6.0','6.1'):raise ValueError('Unknown source release')
        return normalized
    try:selected_release=canonical(version)
    except (ValueError,TypeError):
        return dict(status='invalid_request',answer=None,source_release=version,evidence=[],ai_acceptance_passed=False)
    retained_history=[]
    if history:
        try:same_release=canonical(history_version)==selected_release
        except (ValueError,TypeError):same_release=False
        if same_release:retained_history=completed_history(history)
    path=Path(agent_path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_sha256:raise ValueError('Member Agent source changed')
    spec=importlib.util.spec_from_file_location('isolated_evidence_agent',path);agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
    # A separate module per request avoids global cross-user/version mutation.
    agent.TOOLS=copy.deepcopy(TOOL_SCHEMAS)
    agent.AGENT_SYSTEM_PROMPT=('你是官方原文证据助手。当前发行是'+version+'。必须先调用证据工具再回答API问题，引用返回出处。'
        '未知条件、覆盖不足、候选关系必须明确说明；无匹配不代表API不存在，不得编造签名或新增删除。'
        '示例静态关联不代表SDK编译通过。比较必须显式指定两个发行。'
        '编译器生成的匿名类型标签仅用于定位，不能当作正式API名称。'
        '本轮只回答最后一条用户问题；历史仅用于理解指代，不是待补答清单。用户换了主题时不要继续上一题。'
        '若当前问题需要的统计或工具能力不存在，直接说明当前问题的能力边界，不用旧问题的答案填充。'
        '面向使用者简明回答，不罗列内部记录ID、解析状态、处理脚本或文件指纹；保留固定来源链接、发行和影响使用的未知条件，用中文解释这些条件。')
    captured=[];delivery=[]
    def execute(name,args):
        args=dict(args)
        try:
            if name not in [s['function']['name'] for s in TOOL_SCHEMAS]:raise ValueError('Unsupported evidence tool')
            if name!='compare':
                if canonical(args.get('version',version))!=selected_release:raise ValueError('Selected version differs from tool request')
                args['version']=version
            else:
                left=args.get('from_version',args.get('old_version'));right=args.get('to_version',args.get('new_version'))
                if selected_release not in (canonical(left),canonical(right)):raise ValueError('Selected release must be a comparison endpoint')
            result=tools.call(name,args)
            result.setdefault('ok',True)
        except sqlite3.OperationalError as exc:
            interrupted='interrupted' in str(exc)
            result=dict(ok=False,error='证据查询超时，请缩小范围后重试。' if interrupted else '证据查询暂时无法完成。',
                        error_code='query_timeout' if interrupted else 'evidence_unavailable',source_release=version)
        except Exception as exc:result=dict(ok=False,error=str(exc),source_release=version)
        captured.append(result)
        step=dict(tool=name,args=args,ok=result.get('ok',False),rows=result.get('results',result.get('records',[])),evidence=result)
        payload=model_payload(result);visible=json.loads(payload)
        records_visible=any(visible.get(k) for k in ('records','results','examples','documents','declarations','candidates'))
        delivery.append(dict(ok=result.get('ok',False),truncated=bool(visible.get('model_payload_truncated')),records_visible=records_visible))
        return step,payload
    agent.execute_tool=execute
    failure=[];protocol_retry_used=False;last_final=None
    def guarded_caller(messages,tools):
        nonlocal protocol_retry_used,last_final
        while True:
            try:
                response=ai_caller(messages,tools=tools)
                if response is None:return None
                validated=validate_model_response(response)
            except (subprocess.TimeoutExpired,TimeoutError):failure.append('model_timeout');return None
            except (ValueError,TypeError):
                if protocol_retry_used:failure.append('invalid_model_response');return None
                protocol_retry_used=True
                messages=copy.deepcopy(messages)
                messages[0]['content']+=' 上次响应未通过JSON格式校验；请重新生成完整合法JSON，不得截断，不改变当前问题。'
                continue
            except Exception:failure.append('model_unavailable');return None
            message=validated['choices'][0]['message']
            last_final=message.get('content') if not message.get('tool_calls') else None
            return validated
    # Retain bounded text only for the same explicit release; each answer still needs new tool evidence.
    result=agent.run_agent(question,retained_history,guarded_caller)
    if result is None:
        return dict(status=failure[-1] if failure else 'model_unavailable',answer=None,source_release=version,evidence=captured,ai_acceptance_passed=False)
    if not captured or not any(r.get('ok') for r in captured):
        return dict(status='no_verified_tool_result',answer=None,source_release=version,evidence=captured,ai_acceptance_passed=False)
    if not last_final or not last_final.strip():
        return dict(status='query_incomplete',answer=None,source_release=version,evidence=captured,
                    note='本轮查询未形成最终回答，请缩小范围重试；失败问题不会带入下一轮。',ai_acceptance_passed=False)
    if any(d['ok'] and d['truncated'] for d in delivery) and not any(d['ok'] and d['records_visible'] for d in delivery):
        return dict(status='evidence_requires_narrower_query',answer=None,source_release=version,evidence=captured,
                    model_payload_truncated=True,note='所有证据记录超出模型预算，请缩小查询范围后重试。',ai_acceptance_passed=False)
    if all(r.get('tool') in ('search','detail','examples') and r.get('results')==[] for r in captured):
        return dict(status='no_matching_evidence',answer='当前覆盖范围内没有匹配证据，不能据此断言API不存在。',source_release=version,evidence=captured,ai_acceptance_passed=False)
    result.update(status='model_answer_with_tool_results',source_release=version,evidence=captured,ai_acceptance_passed=False)
    return result
