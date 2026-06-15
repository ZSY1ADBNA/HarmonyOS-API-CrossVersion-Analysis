// ============================================================================
// HarmonyOS API 跨版本迁移变化分析
// 使用方法：在 Neo4j Browser 中逐段执行，或通过 python 脚本批量执行
// ============================================================================

// ============================================================================
// 1. 版本概览 —— 各版本节点/关系总数
// ============================================================================
MATCH (n)
RETURN n.sdk_version AS version,
       labels(n)[0] AS label,
       count(n) AS nodes
ORDER BY version, nodes DESC;

// 各版本总节点数
MATCH (n)
WHERE n.sdk_version IS NOT NULL
RETURN n.sdk_version AS version, count(n) AS total_nodes
ORDER BY version;

// ============================================================================
// 2. 各版本模块数量对比
// ============================================================================
MATCH (m:Module)
RETURN m.sdk_version AS version, count(m) AS module_count
ORDER BY version;

// ============================================================================
// 3. 新增 API —— 在某版本中存在但前一个版本中不存在的节点
//    方法：按 name+type 匹配，找出较高版本独有的节点
// ============================================================================

// 3a. 通用：对比任意两个版本，找出 version2 比 version1 新增的节点
// 示例：API5.1 比 API5.0 新增了哪些 API
MATCH (n1 {sdk_version: 'API5.0'})
WITH collect(DISTINCT n1.name + '|' + labels(n1)[0]) AS old_keys
MATCH (n2 {sdk_version: 'API5.1'})
WHERE NOT (n2.name + '|' + labels(n2)[0]) IN old_keys
  AND n2.type IN ['class', 'interface', 'method', 'property', 'enum', 'function']
RETURN labels(n2)[0] AS type, n2.name AS name, n2.module AS module,
       n2.description AS description, n2.since AS since_version
ORDER BY type, name;

// 3b. 按模块统计新增节点数
MATCH (n1 {sdk_version: 'API5.0'})
WITH collect(DISTINCT n1.name + '|' + labels(n1)[0] + '|' + n1.parent_name) AS old_keys
MATCH (n2 {sdk_version: 'API5.1'})
WHERE NOT (n2.name + '|' + labels(n2)[0] + '|' + n2.parent_name) IN old_keys
  AND n2.type IN ['class', 'interface', 'method', 'property', 'enum', 'function']
RETURN n2.module AS module, labels(n2)[0] AS type, count(n2) AS new_count
ORDER BY new_count DESC;

// ============================================================================
// 4. 删除/废弃的 API —— 前一版本存在但后一版本不存在的节点
// ============================================================================

// 4a. API5.0 中有但 API5.1 中已移除的 API
MATCH (n1 {sdk_version: 'API5.0'})
WITH collect(DISTINCT n1.name + '|' + labels(n1)[0]) AS new_keys
MATCH (n2 {sdk_version: 'API5.1'})
WHERE NOT (n2.name + '|' + labels(n2)[0]) IN new_keys
  AND n2.type IN ['class', 'interface', 'method', 'property', 'enum', 'function']
RETURN labels(n2)[0] AS type, n2.name AS name, n2.module AS module,
       n2.description AS description
ORDER BY type, name;

// Wait... that query is wrong. Let me think again.

// ============================================================================
// 4. 删除/废弃的 API（修正版）
//    API5.1 中有但 API5.0 中不存在的 = 新增（不是删除）
//    API5.0 中有但 API5.1 中不存在的 = 删除
// ============================================================================

// 4a. 从 API5.0 到 API5.1 被删除的 API
MATCH (n_new {sdk_version: 'API5.1'})
WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) AS new_keys
MATCH (n_old {sdk_version: 'API5.0'})
WHERE NOT (n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) IN new_keys
  AND n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
RETURN labels(n_old)[0] AS type, n_old.name AS name, n_old.module AS module,
       n_old.description AS description
ORDER BY type, name;

// 4b. 按模块统计删除数量
MATCH (n_new {sdk_version: 'API5.1'})
WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name, '')) AS new_keys
MATCH (n_old {sdk_version: 'API5.0'})
WHERE NOT (n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name, '')) IN new_keys
  AND n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
RETURN n_old.module AS module, labels(n_old)[0] AS type, count(n_old) AS removed_count
ORDER BY removed_count DESC;

// ============================================================================
// 5. 所有版本的批量新增/删除对比（自动生成变化矩阵）
// ============================================================================

// 5a. 按版本分组，用 collect 找出每个类/接口的新增和消失
// 注意：这里用 parent_name+name+type 作为复合键（同一父级下的同名同类才算同一API）
MATCH (n)
WHERE n.type IN ['class', 'interface', 'method', 'property', 'enum', 'function']
  AND n.sdk_version IS NOT NULL
WITH n.sdk_version AS ver, n.name AS name, labels(n)[0] AS type,
     coalesce(n.parent_name, '') AS parent, n.module AS module, n
ORDER BY ver, parent, name
WITH collect(DISTINCT {ver: ver, name: name, type: type, parent: parent,
            key: parent + '::' + name + '|' + type, module: module}) AS entries
UNWIND entries AS e
WITH e
ORDER BY e.key, e.ver
WITH e.key AS api_key, collect(e.ver) AS versions, collect(e) AS details
WITH api_key, versions, details,
     reduce(s = '', v IN versions | s + v + ',') AS ver_list
WHERE size(versions) = 1
RETURN details[0].type AS type,
       details[0].name AS name,
       details[0].parent AS parent,
       details[0].module AS module,
       details[0].ver AS only_in_version,
       CASE WHEN details[0].ver = 'API4.1' THEN '最早版本'
            WHEN details[0].ver = 'API6.0' THEN '最新版本'
            ELSE '仅特定版本存在'
       END AS note
ORDER BY only_in_version, type, name;

// ============================================================================
// 6. 版本间变化摘要表
// ============================================================================

// 6a. 列出所有版本对的新增/删除统计
// 手动对比每对版本
MATCH (n_old {sdk_version: 'API4.1'})
WHERE n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
MATCH (n_new {sdk_version: 'API5.0'})
WHERE n_new.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH old_keys,
     collect(DISTINCT coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0]) AS new_keys
WITH old_keys, new_keys,
     [k IN new_keys WHERE NOT k IN old_keys] AS added,
     [k IN old_keys WHERE NOT k IN new_keys] AS removed
RETURN 'API4.1 -> API5.0' AS version_pair,
       size(added) AS added_count,
       size(removed) AS removed_count,
       size(old_keys) AS old_total,
       size(new_keys) AS new_total;

// 6b. 所有版本对的批量统计
WITH [
  {from: 'API4.1', to: 'API5.0'},
  {from: 'API5.0', to: 'API5.1'},
  {from: 'API5.1', to: 'API6.0'},
  {from: 'API4.1', to: 'API6.0'}
] AS version_pairs
UNWIND version_pairs AS pair
MATCH (n_old {sdk_version: pair.from})
WHERE n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH pair, collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
MATCH (n_new {sdk_version: pair.to})
WHERE n_new.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH pair, old_keys,
     collect(DISTINCT coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0]) AS new_keys
RETURN pair.from + ' -> ' + pair.to AS version_pair,
       size(old_keys) AS from_total,
       size(new_keys) AS to_total,
       size([k IN new_keys WHERE NOT k IN old_keys]) AS added,
       size([k IN old_keys WHERE NOT k IN new_keys]) AS removed
ORDER BY version_pair;

// ============================================================================
// 7. 新增模块 —— 之前版本不存在的模块
// ============================================================================

// 7a. API5.1 比 API5.0 新增了哪些模块
MATCH (m1:Module {sdk_version: 'API5.0'})
WITH collect(DISTINCT m1.name) AS old_modules
MATCH (m2:Module {sdk_version: 'API5.1'})
WHERE NOT m2.name IN old_modules
RETURN m2.name AS new_module, m2.description AS description
ORDER BY m2.name;

// ============================================================================
// 8. 某模块在各版本间的演变（以 @ohos.bluetooth 为例）
// ============================================================================
MATCH (n {module: '@ohos.bluetooth'})
WHERE n.sdk_version IS NOT NULL
RETURN n.sdk_version AS version,
       labels(n)[0] AS type,
       count(n) AS api_count
ORDER BY version, type;

// 蓝牙模块新增的类/接口（API5.1 vs API5.0）
MATCH (n_old {sdk_version: 'API5.0', module: '@ohos.bluetooth'})
WITH collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
MATCH (n_new {sdk_version: 'API5.1', module: '@ohos.bluetooth'})
WHERE NOT (coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0]) IN old_keys
RETURN labels(n_new)[0] AS type, n_new.name AS name, n_new.description AS description
ORDER BY type, name;

// ============================================================================
// 9. API `since` 版本分布 —— 哪些 API 是在哪个 since 版本引入的
// ============================================================================
MATCH (n)
WHERE n.since IS NOT NULL AND n.since <> ''
  AND n.type IN ['class', 'interface', 'method', 'property', 'enum']
RETURN n.since AS since_version, labels(n)[0] AS type, count(n) AS count
ORDER BY since_version, count DESC;

// ============================================================================
// 10. SystemCapability 分布 —— 系统能力标签
// ============================================================================
MATCH (n)
WHERE n.syscap IS NOT NULL AND n.syscap <> ''
RETURN n.syscap AS system_capability, count(n) AS api_count
ORDER BY api_count DESC
LIMIT 30;

// ============================================================================
// 11. 找出两个版本间签名变化的节点（同名同父但描述/返回值/参数数量不同）
// ============================================================================

// 11a. 方法签名变化（返回值类型不同）
MATCH (m1:Method {sdk_version: 'API5.0'})
MATCH (m2:Method {sdk_version: 'API5.1'})
WHERE m1.name = m2.name
  AND coalesce(m1.parent_name, '') = coalesce(m2.parent_name, '')
  AND m1.return_type <> m2.return_type
RETURN m1.parent_name AS parent, m1.name AS method,
       m1.return_type AS old_return, m2.return_type AS new_return,
       m1.sdk_version AS old_ver, m2.sdk_version AS new_ver;

// 11b. 描述文本不同的节点（可能表示行为变化）
MATCH (n1 {sdk_version: 'API5.0'})
MATCH (n2 {sdk_version: 'API5.1'})
WHERE n1.name = n2.name
  AND labels(n1) = labels(n2)
  AND coalesce(n1.parent_name, '') = coalesce(n2.parent_name, '')
  AND n1.description <> n2.description
  AND n1.description <> ''
  AND n2.description <> ''
RETURN labels(n1)[0] AS type, n1.name AS name,
       n1.description AS old_desc, n2.description AS new_desc
LIMIT 50;

// ============================================================================
// 12. 类成员变化 —— 某 Class/Interface 在版本间增减了哪些 Method/Property
// ============================================================================

// 12a. 以 @ohos.multimedia.audio 为例，列出其类/接口在各版本的成员数
MATCH (parent:Interface {module: '@ohos.multimedia.audio'})
MATCH (child)-[:HAS_PARENT]->(parent)
WHERE child.sdk_version = parent.sdk_version
RETURN parent.sdk_version AS version, parent.name AS interface_name,
       count(child) AS member_count
ORDER BY interface_name, version;

// 12b. 某类的成员在不同版本间的详细增减
// 示例：AudioRenderer 在 API5.0→API5.1 的变化
MATCH (n_new {sdk_version: 'API5.1', parent_name: 'AudioRenderer'})
WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0]) AS new_members
MATCH (n_old {sdk_version: 'API5.0', parent_name: 'AudioRenderer'})
RETURN labels(n_old)[0] AS type, n_old.name AS name,
       CASE WHEN (n_old.name + '|' + labels(n_old)[0]) IN new_members
            THEN 'kept' ELSE 'removed' END AS status
ORDER BY status, type, name;

// ============================================================================
// 13. 导出所有变化结果（用于外部报告）
// ============================================================================

// 13a. 版本升级路线图：API4.1->API5.0->API5.1->API6.0 中每一步的变化
// 返回每一步的 added、removed 列表
WITH [
  {from: 'API4.1', to: 'API5.0'},
  {from: 'API5.0', to: 'API5.1'},
  {from: 'API5.1', to: 'API6.0'}
] AS pairs
UNWIND pairs AS pair
MATCH (n_old {sdk_version: pair.from})
WHERE n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH pair, collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
MATCH (n_new {sdk_version: pair.to})
WHERE n_new.type IN ['class', 'interface', 'method', 'property', 'enum']
WITH pair, old_keys,
     collect(DISTINCT {key: coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0],
                       name: n_new.name, type: labels(n_new)[0], module: n_new.module}) AS new_entries
WITH pair, old_keys, new_entries,
     [e IN new_entries WHERE NOT e.key IN old_keys] AS added_list,
     size([e IN new_entries WHERE NOT e.key IN old_keys]) AS added_count,
     size([k IN old_keys WHERE NOT k IN [e IN new_entries | e.key]]) AS removed_count
RETURN pair.from + ' -> ' + pair.to AS upgrade_path,
       added_count, removed_count,
       size(old_keys) AS base_count, size(new_entries) AS new_count
ORDER BY pair.from;
