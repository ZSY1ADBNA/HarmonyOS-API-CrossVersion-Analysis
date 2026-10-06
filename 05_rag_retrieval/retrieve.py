"""中文需求 -> 候选 API 检索原型。

模式：
  naive  英文 BM25 打原始文本，不做任何中文处理（"先跑一版"的典型做法）
  zh     BM25F 分字段打分 + 中文别名扩展 + 类型先验 + 族入口先验 + 家族去重

用法:
  python retrieve.py "怎么发通知" [--version API5.1] [--mode zh] [--topk 10]
"""
import json, re, math, sys, argparse, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'

# ── 中文 -> 英文领域词表 ────────────────────────────────────────────────
# 这是一份人工受控词表，按鸿蒙领域常识写（不是针对测试集逐题调的）。
# 通用词（系统/应用/接口/怎么…）刻意留空，避免引入噪声。
ZH_ALIAS = {
    '通知': ['notification', 'notify', 'notificationManager'],
    '消息': ['notification', 'message'], '提醒': ['notification', 'reminder'],
    '震动': ['vibrat'], '振动': ['vibrat'], '抖动': ['vibrat'], '震': ['vibrat'], '马达': ['vibrat'],
    '网络': ['net', 'network', 'connection'], '请求': ['request', 'http'], '联网': ['net', 'connection'],
    '有没有网': ['connection', 'getDefaultNet'], '断网': ['connection', 'net'],
    '文件': ['file', 'fs', 'fileIo'], '读取': ['read'], '读': ['read'], '写入': ['write'], '写': ['write'],
    '沙箱': ['file', 'fs', 'context'], '文本': ['text', 'string'],
    '存储': ['preferences', 'relationalStore', 'storage'], '本地': ['preferences', 'relationalStore', 'local'],
    '设置': ['preferences', 'setting'], '偏好': ['preferences'],
    '数据库': ['relationalStore', 'rdb', 'database', 'store'], '建表': ['relationalStore', 'rdb', 'table'],
    '结构化': ['relationalStore', 'rdb'], '查询': ['query', 'resultSet'],
    '相机': ['camera'], '摄像头': ['camera'], '拍照': ['camera', 'photo', 'capture'],
    '扫码': ['camera', 'scan', 'barcode'], '二维码': ['barcode', 'scan', 'qrcode'],
    '权限': ['permission', 'abilityAccessCtrl', 'grant'], '申请': ['request', 'grant'],
    '跳转': ['router', 'pushUrl', 'navigate'], '页面': ['router', 'navigation'], '路由': ['router'],
    '提示': ['prompt', 'toast'], '弹窗': ['prompt', 'dialog'], '轻提示': ['toast', 'prompt'],
    '剪贴板': ['pasteboard', 'clipboard'], '复制': ['pasteboard', 'copy'],
    '蓝牙': ['bluetooth'], '传感器': ['sensor'], '加速度': ['accelerometer', 'sensor'],
    '定位': ['location', 'geoLocation'], '地理': ['location', 'geo'],
    '图片': ['image', 'pixelmap'], '解码': ['decode', 'image'], '位图': ['pixelmap', 'image'],
    '音频': ['audio', 'media', 'avplayer'], '视频': ['video', 'media', 'avplayer'], '播放': ['player', 'media'],
    '下载': ['download', 'request'], '上传': ['upload', 'request'],
    '网页': ['web', 'webview'], '窗口': ['window'], '亮度': ['brightness'],
    '屏幕': ['display', 'screen', 'window'], '设备': ['device'], '型号': ['deviceinfo', 'model'],
    '指纹': ['userAuth', 'fingerprint'], '人脸': ['userAuth', 'face'], '认证': ['userAuth', 'auth'],
    '登录': ['userAuth', 'auth', 'login'],
    '怎么': [], '如何': [], '什么': [], '哪个': [], '哪些': [], '区别': [], '用哪': [], '该用': [],
    '支持': [], '能做': [], '实现': [], '接口': [], '系统': [], '应用': [], '功能': [], '一下': [],
    '用户': [], '时候': [], '之后': [], '然后': [], '想要': [], '需要': [], '里面': [], '当前': [],
}

STOP = set('a an the of to for is are be in on at by with and or not it this that do does how what which i you we my our can could should would please get set use using used new'.split())
SUFFIX = ('ation', 'tion', 'sion', 'ing', 'ers', 'er', 'ies', 'ed', 'es', 's')

# 字段权重（BM25F）
FIELD_W = {'file': 5.0, 'name': 6.0, 'ctx': 2.5, 'desc': 1.2, 'aux': 0.35}
K1 = 1.2


PREFIX = 5       # 前缀归一长度：vibration/vibrator/vibrate -> 'vibra'；notify/notification -> 'notif'


def key(w):
    """词形归一：长词取前 PREFIX 个字符当 key，短词原样。
    比后缀词干化稳，不会把 vibration->vibr 而 vibrator 不变这种切法搞岔。"""
    return w[:PREFIX] if len(w) >= PREFIX else w


def tokenize(text):
    """先拆驼峰，再把 @ . _ - / 当分隔符，小写取词，再归一。
    @ohos.notificationManager -> ['ohos','notif','manag']；createHttp -> ['creat','http']"""
    t = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text or '')
    return [key(w) for w in re.findall(r'[a-z0-9]+', t.lower())
            if len(w) > 1 and w not in STOP]


def expand_query(q):
    """中文需求 -> (英文检索词, 命中的中文词)"""
    ext, hit = [], []
    for zh in sorted(ZH_ALIAS, key=len, reverse=True):     # 长词优先，避免"有没有网"被"网"拆散
        if zh in q:
            hit.append(zh)
            for e in ZH_ALIAS[zh]:
                if e and e not in ext:
                    ext.append(e)
    for t in tokenize(q):
        if t not in ext:
            ext.append(t)
    out = []
    out = []
    for e in ext:
        out += tokenize(e)                  # 别名统一走 tokenize，保证与正文同一套 key
    return list(dict.fromkeys(out)), hit


def fields_of(d):
    return {
        'file': f"{d['file']}",
        'name': f"{d['name']}",
        'ctx': f"{d['parent']} {d['module']}",
        'desc': d['desc'],
        'aux': f"{d['comments']} {d['params']} {d['ret_desc']} {d['errs']} {d['syscap']}",
    }


class BM25F:
    def __init__(self, docs):
        self.docs = docs
        self.tf = []          # 每篇：{field: Counter}
        self.len = []         # 每篇：{field: len}
        self.avg = collections.defaultdict(float)
        self.df = collections.Counter()
        BINARY = ('file', 'name', 'ctx')     # 这几个字段看重「有没有命中」，不看重次数
        for d in docs:
            f = fields_of(d)
            toks = {k: tokenize(v) for k, v in f.items()}
            self.tf.append({k: (collections.Counter(set(t)) if k in BINARY else collections.Counter(t))
                            for k, t in toks.items()})
            self.len.append({k: len(t) for k, t in toks.items()})
            allt = set()
            for t in toks.values():
                allt |= set(t)
            for t in allt:
                self.df[t] += 1
        self.N = len(docs) or 1
        for k in FIELD_W:
            self.avg[k] = (sum(l[k] for l in self.len) / self.N) or 1

    def idf(self, t):
        n = self.df.get(t, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def score(self, terms, i):
        tf, ln = self.tf[i], self.len[i]
        s = 0.0
        for t in terms:
            norm = 0.0
            for k, w in FIELD_W.items():
                f = tf[k].get(t, 0)
                if not f:
                    continue
                b = 0.30 if k in ('name', 'file') else 0.75      # 名字短，少做长度惩罚
                norm += w * f / (1 - b + b * ln[k] / self.avg[k])
            if norm > 0:
                s += self.idf(t) * norm / (K1 + norm)
        return s


TYPE_W = {
    'namespace': 1.30, 'class': 1.20, 'interface': 1.15, 'enum': 1.10,
    'method': 1.00, 'type_alias': 0.80, 'struct': 0.80,
    'property': 0.45, 'enum_member': 0.25, 'call_signature': 0.35,
}


def is_family_entry(d):
    """该节点是不是它所在 .d.ts 的主声明（族入口）。
    例：@ohos.notificationManager 里的 namespace notificationManager。"""
    if d['type'] not in ('namespace', 'class', 'interface', 'enum'):
        return False
    return d['name'].lower() in d['file'].lower()


def load(path):
    return [json.loads(l) for l in open(path, encoding='utf-8')]


def field_hit(d, terms):
    """候选自己声明里（API 名 / 文件名 / 所属模块）是否直接命中查询词。
    这是比分数更可靠的判据：分数高的常常只是"描述里提过这个词"。"""
    own = set(tokenize(d['name'])) | set(tokenize(d['file'])) | set(tokenize(d['module']))
    return len(own & set(terms))


try:
    FILE_INV = json.load(open(DATA / 'file_inventory.json', encoding='utf-8'))
except Exception:
    FILE_INV = {}


OFFICIAL = ('@ohos.', '@system.', '@kit.')


def data_gap(query, version, mode='zh'):
    """数据缺口检测。
    只看"正式 API 文件"(@ohos.* / @system.* / @kit.*)，找查询词在文件名上命中最多的那一档；
    若这一档在目标版本里全部是空的，说明该域数据被提取截断，应回答"该版本无此能力"而不是硬凑答案。"""
    if not version or not FILE_INV:
        return None
    terms = set(expand_query(query)[0] if mode == 'zh' else tokenize(query))
    ranked = []
    for f, per in FILE_INV.items():
        if version not in per or not f.startswith(OFFICIAL):
            continue
        h = len(set(tokenize(f)) & terms)
        if h >= 1:
            ranked.append((h, f, per[version]))
    if not ranked:
        return None
    ranked.sort(key=lambda x: -x[0])
    top_hit = ranked[0][0]
    top = [x for x in ranked if x[0] == top_hit]
    if all(c == 0 for _, _, c in top):
        names = '、'.join(x[1] for x in top[:3])
        return f'{names} 在 {version} 中存在，但 0 个可用 API 节点（提取被截断）'
    return None


def gate(query, cands, mode='zh', min_score=3.0, version=None):
    """判断是否该回复"检索不足"。返回 (是否弃答, 理由)"""
    if not cands:
        return True, '没有任何候选'
    g = data_gap(query, version, mode)
    if g:
        return True, '数据缺口：' + g
    terms = expand_query(query)[0] if mode == 'zh' else tokenize(query)
    top = cands[:5]
    if not any(field_hit(d, terms) for _, d in top):
        return True, f'前 5 个候选都没有在 API 名/文件名上命中查询词（top1 分数 {cands[0][0]:.2f}）'
    if cands[0][0] < min_score:
        return True, f'top1 分数 {cands[0][0]:.2f} 低于阈值 {min_score}'
    return False, ''


class Retriever:
    def __init__(self, docs, mode='zh', version=None):
        if version:
            docs = [d for d in docs if d['ds'] == version]
        self.docs = docs
        self.mode = mode
        self.version = version
        self.bm = BM25F(docs)

    def rank(self, query, deep=200):
        if self.mode == 'zh':
            terms, _ = expand_query(query)
        else:
            terms = tokenize(query)
        out = []
        for i, d in enumerate(self.docs):
            s = self.bm.score(terms, i) * TYPE_W.get(d['type'], 0.8)
            if s > 0:
                if is_family_entry(d):
                    s *= 1.35
                out.append((s, d))
        out.sort(key=lambda x: -x[0])
        # 家族去重：(文件, 名称) 只保留最高分
        seen, uniq = set(), []
        for s, d in out:
            key = (d['file'], d['name'])
            if key in seen:
                continue
            seen.add(key)
            uniq.append((s, d))
            if len(uniq) >= deep:
                break
        return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('query')
    ap.add_argument('--version', default=None)
    ap.add_argument('--corpus', default=str(DATA / 'corpus_versions.jsonl'))
    ap.add_argument('--mode', default='zh', choices=['zh', 'naive'])
    ap.add_argument('--topk', type=int, default=10)
    a = ap.parse_args()
    docs = load(a.corpus)
    if a.version:
        docs = [d for d in docs if d['ds'] == a.version]
    r = Retriever(docs, mode=a.mode)
    print(f'查询: {a.query}   模式={a.mode}  版本={a.version or "全部"}  语料={len(docs)} 条')
    if a.mode == 'zh':
        terms, hit = expand_query(a.query)
        print(f'扩展检索词: {terms}')
        print(f'命中的中文词: {hit}')
    print()
    for rank, (s, d) in enumerate(r.rank(a.query, a.topk), 1):
        print(f'{rank:2}. [{s:6.2f}] {d["name"][:30]:32} <- {d["file"][:36]:38} {d["type"]:10} {d["ds"]}')
        if d['desc']:
            print(f'          {d["desc"][:108]}')


if __name__ == '__main__':
    main()
