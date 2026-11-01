"""Minimal explicit version context for selected SDK queries; no chat/model state."""
import copy
import re
from explain_verified_samples import explain_result
from query_verified_samples import SPECS, TARGETS
from search_verified_samples import ALIASES, search_requirements

VERSION_TURN = re.compile(r'^(?:OpenHarmony\s*)?(?:换成|改成|切换到|那|用|目标版本|版本)?\s*(\d+\.\d+(?:\.\d+)?)\s*(?:版本)?(?:呢)?[？?。!！]*$', re.I)
UNKNOWN_INTENTS = (
    ('default_value', r'默认值|default value|不填.*(?:怎样|如何|什么)|省略.*(?:行为|值|结果)'),
    ('permission', r'权限|permission'),
    ('device_runtime', r'设备.*(?:支持|运行)'),
    ('migration_compatibility', r'直接替换|直接迁移|兼容吗'),
    ('overload_completeness', r'全部重载|所有重载|有哪些重载'),
    ('invocation_forms', r'Promise|callback|async/await'),
    ('type_expansion', r'枚举值|展开.*类型|类型.*(?:哪些属性|有哪些属性)|返回(?:类型|结果).*属性'),
    ('usage_sequence', r'调用顺序|如何调用|怎么调用|释放资源|最小示例|代码示例|如何导入|导入方式'),
    ('error_codes', r'错误码|error code'),
    ('earliest_history', r'最早|哪个版本新增|首次(?:出现|引入)|何时新增'),
    ('deprecation', r'废弃|替代项|官方替代'),
    ('compile_diagnosis', r'编译失败.*(?:根因|原因)|升级.*编译失败|(?:为什么|为何).*编译失败'),
)
UNKNOWN_MESSAGES = {
    'overload_completeness':'当前只核验选定声明，未核验完整重载集合。',
    'invocation_forms':'当前未核验该接口的Promise/callback调用形式或async/await适用性。',
    'type_expansion':'当前未展开关联枚举、参数或返回对象类型，不能给出完整结构。',
    'usage_sequence':'当前未核验调用指南、导入示例或资源释放流程。',
    'error_codes':'当前样本未核验这个接口的错误码解释。',
    'earliest_history':'两个选定发行快照不足以证明最早新增版本。',
    'deprecation':'当前未核验废弃说明、官方替代或替换兼容性。',
    'compile_diagnosis':'样本编译证据不能确认用户代码的编译失败根因，需要具体代码与诊断。',
}


def ambiguous_platform(text):
    return bool(re.search(r'(?<![A-Za-z])HarmonyOS(?![A-Za-z])',text,re.I)
                or ('鸿蒙' in text and 'openharmony' not in text.lower()))


def mentioned_versions(text):
    return set(re.findall(r'(?<![A-Za-z0-9_.])\d+\.\d+(?:\.\d+)?(?![\d.])',text))


def validate_state(state):
    if state is None:
        return {'schema_version': 1, 'message': '', 'release': None, 'compare_with': None}
    if not isinstance(state, dict) or set(state) != {'schema_version','message','release','compare_with'}:
        raise ValueError('Unexpected session fields')
    if type(state['schema_version']) is not int or state['schema_version'] != 1:
        raise ValueError('Unexpected session schema')
    if not isinstance(state['message'], str) or len(state['message']) > 2000:
        raise ValueError('Invalid saved requirement')
    for key in ('release','compare_with'):
        if state[key] is not None and (not isinstance(state[key], str) or state[key] not in SPECS):
            raise ValueError('Invalid saved version')
    return copy.deepcopy(state)


def handle_turn(message, release=None, compare_with=None, state=None):
    if not isinstance(message,str) or not message.strip() or len(message)>2000:
        raise ValueError('Requirement must contain 1 to 2000 characters')
    for value in (release, compare_with):
        if value is not None and not isinstance(value,str):
            raise ValueError('Version must be a string')
    previous = validate_state(state)
    current = copy.deepcopy(previous)
    text = message.strip()
    output = {'status':None,'state':current,'result':None,'retrieval':None,'clarification':None,
              'resolution':None,'model_called':False}

    def stop(status, clarification):
        output['status']=status
        output['clarification']=clarification
        return output

    def execute(requirement, selected, target, resolution, unknown_intent=None):
        if ambiguous_platform(requirement):
            current.update(message='',release=None,compare_with=None)
            return stop('needs_platform_clarification','当前只核验OpenHarmony，请先确认平台，不能与HarmonyOS混用。')
        if unknown_intent is None:
            unknown_intent=next((name for name,pattern in UNKNOWN_INTENTS if re.search(pattern,requirement,re.I)),None)
        current.update(message=requirement, release=selected, compare_with=target)
        retrieval=search_requirements(requirement,selected,target)
        result=explain_result(retrieval)
        output.update(status=result['status'],result=result,retrieval=retrieval,resolution=resolution)
        if unknown_intent and result['status']=='verified_candidates_found':
            clarification=UNKNOWN_MESSAGES.get(unknown_intent,'现有声明证据不能确认这一条件；保留已核验事实，不推断默认值、权限或设备/迁移行为。')
            result['unknowns'].append(clarification)
            output.update(status='needs_more_evidence',unknown_intent=unknown_intent,
                          clarification=clarification)
        return output

    if ambiguous_platform(text):
        current.update(message='',release=None,compare_with=None)
        return stop('needs_platform_clarification','当前只核验OpenHarmony，请先确认平台，不能与HarmonyOS混用。')

    version_turn=VERSION_TURN.fullmatch(text)
    if version_turn:
        selected=version_turn.group(1)
        if selected not in SPECS:
            current.update(release=None,compare_with=None)
            return stop('unsupported_release','该发行尚未核验，请明确选择4.1或5.0.3。')
        if not previous['message']:
            current.update(release=selected,compare_with=None)
            return stop('needs_requirement','已记录版本，请补充希望查询的功能或API名称。')
        if compare_with and compare_with not in SPECS:
            current.update(release=selected,compare_with=None)
            return stop('unsupported_release','比较目标发行尚未核验。')
        pending_target = previous['compare_with'] if previous['release'] is None else None
        target = (compare_with or None) if compare_with is not None else pending_target
        if len(mentioned_versions(previous['message'])) > 1 and not target:
            current.update(release=selected,compare_with=None)
            return stop('needs_comparison_versions','已记录起始版本，请补充比较的目标发行。')
        return execute(previous['message'],selected,target,'explicit_version_followup')

    if text in ('反过来','反向比较','交换版本'):
        if not previous['message'] or not previous['release'] or not previous['compare_with']:
            return stop('needs_comparison_versions','请明确比较的起始与目标发行版本。')
        return execute(previous['message'],previous['compare_with'],previous['release'],'reverse_explicit_comparison')

    selected=previous['release'] if release is None else release or None
    target=compare_with or None
    versions=mentioned_versions(text)
    if versions:
        if any(version not in SPECS for version in versions):
            current.update(message=text,release=None,compare_with=None)
            return stop('unsupported_release','需求中出现尚未核验的发行，请明确选择已核验版本。')
        if len(versions)>1:
            if not release or not compare_with or versions!={release,compare_with}:
                current.update(message=text,compare_with=None)
                return stop('needs_comparison_direction','请明确哪个是起始版本、哪个是目标版本。')
        else:
            mentioned=next(iter(versions))
            if release and release!=mentioned:
                current.update(message=text,release=None,compare_with=None)
                return stop('version_conflict','文字版本与显式选择不一致，请确认目标版本。')
            selected=mentioned
    if (selected and selected not in SPECS) or (target and target not in SPECS):
        current.update(message=text,release=None,compare_with=None)
        return stop('unsupported_release','该发行尚未核验，请明确选择4.1或5.0.3。')
    if text in ('对比一下','比较一下') and not target:
        return stop('needs_comparison_versions','请补充比较的目标发行版本。')
    if text in ('它呢','这个呢','它的签名呢','这个接口的签名呢'):
        if not previous['message']:
            return stop('needs_requirement','请先说明API名称或功能。')
        return execute(previous['message'],selected,target,'explicit_requirement_context')

    unknown=next((name for name,pattern in UNKNOWN_INTENTS if re.search(pattern,text,re.I)),None)
    explicit_target=any(name.lower() in text.lower() or any(alias in text for alias in ALIASES[name]) for name in TARGETS)
    requirement=text
    if unknown and not explicit_target:
        if not previous['message']:
            return stop('needs_requirement','请先说明要核对哪个API的条件。')
        requirement=previous['message']+' '+text
        if len(requirement)>2000:
            current.update(message='',compare_with=None)
            return stop('needs_requirement','连续条件已过长，请重新明确API名称与要核对的条件。')
    # New substantive requirements replace old ones even on no-match.
    return execute(requirement,selected,target,'explicit_requirement' if explicit_target else 'requirement_context' if unknown else 'new_requirement',unknown)
