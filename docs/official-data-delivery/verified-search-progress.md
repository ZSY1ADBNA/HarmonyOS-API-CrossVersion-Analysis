# 中文需求检索小样本进展

2026-10-14，执行与自查完成；负责人和验收人待确认。

新增本地只读检索入口，将中文需求或精确名称匹配到已核验候选，再读取真实声明、签名、出处和编译记录。范围为OpenHarmony 4.1/API11与5.0.3/API15中的ButtonAttribute.fontSize和AudioStreamInfo.channelLayout，共四条声明。中文别名仅用于召回候选，不代表所有需求或平台条件均已满足。

使用示例（仓库根目录执行）：

```text
python tools/search_verified_samples.py --message "设置按钮字号" --release 4.1
python tools/search_verified_samples.py --message "音频声道布局" --release 4.1 --compare-with 5.0.3
python -m unittest discover -s tools -p test_verified_sample_search.py
python tools/evaluate_verified_search.py
```

缺少版本返回needs_version；未经核验发行返回unsupported_release；无匹配返回no_verified_match；否定或排除表达返回needs_intent_clarification；证据指纹或加载异常返回evidence_unavailable。无匹配只表示当前样本范围未命中，不证明SDK不存在此API。输出使用ASCII转义JSON，解析后中文不变。

检查中发现：若只匹配成员名，TextAttribute.fontSize可能被当作按钮成员。已校验完整限定名，并加入错误所属类型、伪造前缀和正确限定名的回归。候选名称有相似后缀也不命中。出错时不会留下部分候选或暴露本地异常路径。

Python 3.12环境实际执行6项新检索回归和3项已有证据查询回归，共9项通过。16道固定开发题实际查询符合逐题预期，来源文件指纹未改变；每题结果、证据和耗时见verified-search-dev-results.json，预期见verified-search-dev-cases.json。预期以此前已核验声明和版本差异为依据，仍待成员审阅，不代替总体计划28题或独立验收。工具不推断默认值、设备行为或可直接迁移兼容性。

尚未接模型回答、HTTP或网页，未修改共享数据库或部署；本批未上传。GitHub发布单独恢复，保留原查询五文件载荷。下一步在本地隔离入口验证请求边界与错误状态，再接页面。
