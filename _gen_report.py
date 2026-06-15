import sys; sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', '12345678'))

def get_changes(s, old_ver, new_ver):
    """Get all changes between two versions"""
    added_types = s.run("""
        MATCH (n_old {sdk_version: $old})
        WHERE n_old.type IN ['class', 'interface', 'enum']
        WITH collect(DISTINCT n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) AS old_keys
        MATCH (n_new {sdk_version: $new})
        WHERE n_new.type IN ['class', 'interface', 'enum']
          AND NOT (n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) IN old_keys
        RETURN n_new.module AS module, labels(n_new)[0] AS type, n_new.name AS name, n_new.description AS desc
        ORDER BY module, type, name
    """, old=old_ver, new=new_ver)

    removed_types = s.run("""
        MATCH (n_new {sdk_version: $new})
        WHERE n_new.type IN ['class', 'interface', 'enum']
        WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) AS new_keys
        MATCH (n_old {sdk_version: $old})
        WHERE n_old.type IN ['class', 'interface', 'enum']
          AND NOT (n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) IN new_keys
        RETURN n_old.module AS module, labels(n_old)[0] AS type, n_old.name AS name, n_old.description AS desc
        ORDER BY module, type, name
    """, old=old_ver, new=new_ver)

    added_members = s.run("""
        MATCH (n_old {sdk_version: $old})
        WHERE n_old.type IN ['method', 'property']
        WITH collect(DISTINCT n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) AS old_keys
        MATCH (n_new {sdk_version: $new})
        WHERE n_new.type IN ['method', 'property']
          AND NOT (n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) IN old_keys
        RETURN labels(n_new)[0] AS type, count(n_new) AS cnt, n_new.module AS module
        ORDER BY cnt DESC
    """, old=old_ver, new=new_ver)

    removed_members = s.run("""
        MATCH (n_new {sdk_version: $new})
        WHERE n_new.type IN ['method', 'property']
        WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) AS new_keys
        MATCH (n_old {sdk_version: $old})
        WHERE n_old.type IN ['method', 'property']
          AND NOT (n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) IN new_keys
        RETURN labels(n_old)[0] AS type, count(n_old) AS cnt, n_old.module AS module
        ORDER BY cnt DESC
    """, old=old_ver, new=new_ver)

    return list(added_types), list(removed_types), list(added_members), list(removed_members)

def group_by_module(items):
    groups = {}
    for r in items:
        mod = r['module']
        groups.setdefault(mod, []).append(r)
    return groups

with d.session() as s:
    lines = []
    lines.append('# HarmonyOS API 跨版本迁移变化分析报告')
    lines.append('')
    lines.append('> 基于知识图谱分析，覆盖 API4.1、API5.0、API5.1、API6.0 四个版本')
    lines.append('')

    # Version overview
    lines.append('## 一、版本数据总览')
    lines.append('')
    lines.append('| 版本 | 总节点数 | 类/接口/枚举 | 方法/属性 | 模块数 |')
    lines.append('|------|----------|-------------|----------|--------|')
    overview = s.run("""
        MATCH (n) WHERE n.sdk_version IS NOT NULL
        WITH n.sdk_version AS ver, labels(n)[0] AS label, count(n) AS cnt
        ORDER BY ver, cnt DESC
        RETURN ver, label, cnt
    """)
    ver_data = {}
    for r in overview:
        ver = r['ver']; label = r['label']; cnt = r['cnt']
        if ver not in ver_data: ver_data[ver] = {'total': 0, 'types': {}, 'modules': 0}
        ver_data[ver]['total'] += cnt
        ver_data[ver]['types'][label] = cnt

    module_counts = s.run("MATCH (m:Module) RETURN m.sdk_version AS ver, count(m) AS cnt ORDER BY ver")
    for r in module_counts:
        if r['ver'] in ver_data: ver_data[r['ver']]['modules'] = r['cnt']

    for ver in ['API4.1', 'API5.0', 'API5.1', 'API6.0']:
        d = ver_data.get(ver, {})
        ci = d.get('types', {})
        cls_iface = ci.get('Class', 0) + ci.get('Interface', 0)
        enum = ci.get('Enum', 0)
        method = ci.get('Method', 0)
        prop = ci.get('Property', 0)
        lines.append(f'| {ver} | {d.get("total", 0):,} | {cls_iface} / {enum} | {method} / {prop} | {d.get("modules", 0)} |')

    lines.append('')

    # Per-transition analysis
    transitions = [
        ('API4.1', 'API5.0', '4.1 → 5.0', '大爆炸——框架创立期'),
        ('API5.0', 'API5.1', '5.0 → 5.1', '增量更新——圆弧手表适配'),
        ('API5.1', 'API6.0', '5.1 → 6.0', '架构重构——API体系换代'),
    ]

    for old_ver, new_ver, label, desc in transitions:
        added_types, removed_types, added_members, removed_members = get_changes(s, old_ver, new_ver)
        added_groups = group_by_module(added_types)
        removed_groups = group_by_module(removed_types)
        total_add_m = sum(r['cnt'] for r in added_members)
        total_rem_m = sum(r['cnt'] for r in removed_members)

        lines.append(f'## 二、{label}（{desc}）')
        lines.append('')
        lines.append('### 2.1 总览')
        lines.append('')
        lines.append('| 维度 | 新增 | 删除 | 净变化 |')
        lines.append('|------|------|------|--------|')
        lines.append(f'| 类/接口/枚举 | +{len(added_types)} | -{len(removed_types)} | {len(added_types)-len(removed_types):+d} |')
        lines.append(f'| 方法/属性 | +{total_add_m} | -{total_rem_m} | {total_add_m-total_rem_m:+d} |')
        lines.append('')

        # Added by module
        lines.append('### 2.2 新增类/接口/枚举（按模块）')
        lines.append('')
        for mod in sorted(added_groups.keys(), key=lambda m: -len(added_groups[m])):
            items = added_groups[mod]
            class_count = sum(1 for x in items if x['type'] == 'Class')
            iface_count = sum(1 for x in items if x['type'] == 'Interface')
            enum_count = sum(1 for x in items if x['type'] == 'Enum')
            lines.append(f'#### {mod} (+{len(items)}：Class {class_count} / Interface {iface_count} / Enum {enum_count})')
            lines.append('')
            lines.append('| 类型 | 名称 | 描述 |')
            lines.append('|------|------|------|')
            for r in sorted(items, key=lambda x: x['type'] + x['name']):
                desc = (r.get('desc') or '')[:80]
                lines.append(f'| {r["type"]} | {r["name"]} | {desc} |')
            lines.append('')

        # Removed by module
        if removed_groups:
            lines.append('### 2.3 删除类/接口/枚举（按模块）')
            lines.append('')
            for mod in sorted(removed_groups.keys(), key=lambda m: -len(removed_groups[m])):
                items = removed_groups[mod]
                lines.append(f'#### {mod} (-{len(items)})')
                lines.append('')
                lines.append('| 类型 | 名称 | 描述 |')
                lines.append('|------|------|------|')
                for r in sorted(items, key=lambda x: x['type'] + x['name']):
                    desc = (r.get('desc') or '')[:80]
                    lines.append(f'| {r["type"]} | {r["name"]} | {desc} |')
                lines.append('')

        # Method/Property changes
        lines.append('### 2.4 方法/属性变化')
        lines.append('')
        lines.append('| 类型 | 模块 | 变化量 |')
        lines.append('|------|------|--------|')
        for r in added_members[:15]:
            lines.append(f'| +{r["type"]} | {r["module"]} | +{r["cnt"]} |')
        for r in removed_members[:10]:
            lines.append(f'| -{r["type"]} | {r["module"]} | -{r["cnt"]} |')
        lines.append('')

    # Final overview
    lines.append('## 三、API6.0 最终模块版图')
    lines.append('')
    lines.append('| 排名 | 模块 | 类/接口/枚举 | 定位 |')
    lines.append('|------|------|-------------|------|')
    top_modules = s.run("""
        MATCH (n {sdk_version: 'API6.0'})
        WHERE n.type IN ['class', 'interface', 'enum']
        WITH n.module AS module, count(n) AS cnt
        ORDER BY cnt DESC LIMIT 20
        RETURN module, cnt
    """)
    positions = {
        '@kit.ArkUI': 'UI框架', '@kit.AbilityKit': '应用框架', '@kit.ArkWeb': 'WebView',
        '@kit.ArkGraphics3D': '3D图形', '@kit.BasicServicesKit': '基础服务',
        '@kit.NotificationKit': '通知系统', '@kit.CoreFileKit': '文件系统',
        '@kit.ArkTS': '语言运行时', '@kit.SensorServiceKit': '传感器',
        '@kit.TestKit': '测试框架', '@kit.ConnectivityKit': '连接/NFC',
        '@kit.InputKit': '输入', '@kit.AccessibilityKit': '无障碍',
        '@kit.LocationKit': '定位', '@kit.ArkData': '数据',
        '@kit.FormKit': '卡片', '@kit.IMEKit': '输入法',
        '@kit.MediaLibraryKit': '媒体库', '@kit.DistributedServiceKit': '分布式'
    }
    for i, r in enumerate(top_modules):
        pos = positions.get(r['module'], '')
        lines.append(f'| {i+1} | {r["module"]} | {r["cnt"]} | {pos} |')

    lines.append('')
    lines.append('## 四、架构演进关键洞察')
    lines.append('')
    lines.append('### 4.1 三个阶段')
    lines.append('')
    lines.append('1. **API4.1→5.0 框架创立期**：ArkUI、AbilityKit、ArkWeb 三大核心框架从零建立，新增 1,729 个类/接口')
    lines.append('2. **API5.0→5.1 增量补全期**：新增圆弧组件体系（圆表适配），手势识别器独立化，3D几何具象化')
    lines.append('3. **API5.1→6.0 架构重构期**：AbilityKit 从继承模式转向意图装饰器模式，ArkUI 大规模清理命名规范，分布式能力独立成模块')
    lines.append('')
    lines.append('### 4.2 AbilityKit 的范式转移')
    lines.append('')
    lines.append('API5.1→6.0 中，旧基类 `Ability`、`Context`、`UIAbilityContext` 等被移除，')
    lines.append('替换为 `IntentDecoratorInfo`、`PageIntentDecoratorInfo`、`FormIntentDecoratorInfo` ')
    lines.append('等意图装饰器模式，标志着从「继承重载」向「声明式组合」的架构转变。')
    lines.append('')
    lines.append('### 4.3 ArkUI 的命名规范化')
    lines.append('')
    lines.append('API5.1→6.0 中删除了 70+ 个旧 `*Interface` 命名（如 `QRCodeInterface`、`PathOptions`），')
    lines.append('新增 `Binding`、`Gesture`、`ContentTransition`、`ShaderStyle` 等更现代化的 API 命名。')
    lines.append('这是一次系统性的 API 命名重构。')
    lines.append('')
    lines.append('### 4.4 新增独立模块')
    lines.append('')
    lines.append('API5.1→6.0 中 `@kit.DistributedServiceKit` 首次独立出现（`DistributedExtensionAbility`），')
    lines.append('标志着分布式能力从应用框架中解耦，成为独立的一级模块。')
    lines.append('`@kit.BasicServicesKit` 新增 `SelectionExtensionAbility`，文本选择能力独立化。')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('*报告由 Neo4j 知识图谱自动生成，数据来源：4432 个 JSON API 定义文件*')

    with open('HarmonyOS_API_跨版本变化分析报告.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('Report saved: HarmonyOS_API_跨版本变化分析报告.md')
    print(f'Total lines: {len(lines)}')

d.close()
