# HarmonyOS API 跨版本变化分析

基于 Neo4j 知识图谱的 HarmonyOS SDK API 多版本迁移分析。

## 覆盖版本

| 版本 | SDK 节点数 | 类/接口/枚举 |
|------|-----------|-------------|
| API4.1 | 6,197 | 2,025 |
| API5.0 | 15,335 | 6,152 |
| API5.1 | 16,468 | 6,715 |
| API6.0 | 16,570 | 6,741 |

## 版本变化概要

| 升级路径 | 新增类/接口 | 删除 | 特征 |
|----------|-----------|------|------|
| 4.1→5.0 | +1,729 | -64 | 框架创立期 |
| 5.0→5.1 | +158 | -6 | 增量更新 |
| 5.1→6.0 | +228 | -222 | 架构重构 |

## 文件结构

```
├── HarmonyOS_API_跨版本变化分析报告.md   # 详细分析文档（2,847 行）
├── 04_analysis_queries/
│   ├── cross_version_analysis.cypher  # 13类Cypher分析查询
│   └── run_analysis.py               # 自动化分析脚本
├── _run_import.py                     # Neo4j批量导入脚本
├── batch_extract.py                   # JSON批量提取脚本
├── extract_api_info.py               # API信息提取器
├── extract_versions.py               # 多版本文件提取
├── _run_extract.py                   # 无交互提取入口
└── _gen_report.py                     # 分析报告生成器
```

## 使用方法

### 1. 提取API定义
```bash
python _run_extract.py
```

### 2. 导入Neo4j
```bash
python _run_import.py
```

### 3. 生成分析报告
```bash
python _gen_report.py
```

### 4. 交互式查询（Neo4j Browser）
打开 `http://localhost:7474`，执行 `04_analysis_queries/cross_version_analysis.cypher` 中的查询。
