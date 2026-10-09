#!/usr/bin/env python3
"""Comprehensive test suite for OpenHarmony Official Document RAG system.

Tests:
1. DocParser Unit Tests:
   - clean_sup: version & deprecation superscripts and text tags
   - split_table_row: escaped pipes
   - parse_c_decl: C-style variable and pointer declarations
   - extract_metadata_from_text: supports colon inside and outside asterisks
   - parse_sample_doc: function, interface, property, permissions, syscap, examples
   - parser_empty_and_minimal_inputs: empty or blank doc handling
   - dedicated_container_doc: Interface/Class file (AudioRenderer.md) container chunk & method parent assignment
   - c_api_struct_and_header: C-API member variables & header function descriptions
2. DocIndexer and DocRetriever Integration Tests:
   - database_stats: chunk count & version distribution
   - search_by_name_exact: createHttp, createHttp() with parentheses, http.createHttp dotted
   - search_by_name_property: HttpRequestOptions.usingProxy, AudioRenderer.state
   - search_by_keyword: Chinese BM25, English BM25, and special characters/operators (AND/OR/NOT/quotes/brackets)
   - search_by_condition: permissions, deprecation
   - compare_api_new_in_v6_1: HttpInterceptor version detection
   - compare_api_property_additions: HttpRequestOptions new properties in 6.1
   - compare_api_exact_vs_substring: createHttp does not match createHttpResponseCache
   - search_non_existent_api: graceful empty result handling
"""

import os
import shutil
import tempfile
import unittest
from doc_rag.models import DocChunk
from doc_rag.parser import DocParser, clean_sup, split_table_row, parse_c_decl, extract_metadata_from_text
from doc_rag.indexer import DocIndexer, tokenize_for_search
from doc_rag.retriever import DocRetriever, parse_api_query


class TestDocParser(unittest.TestCase):
    def test_clean_sup(self):
        # Normal version superscript
        text, since, dep = clean_sup("requestInStream<sup>10+</sup>")
        self.assertEqual(text, "requestInStream")
        self.assertEqual(since, "10+")
        self.assertFalse(dep)

        # Deprecated superscript
        text, since, dep = clean_sup("on('headerReceive')<sup>(deprecated)</sup>")
        self.assertEqual(text, "on('headerReceive')")
        self.assertTrue(dep)

        # Version and deprecated combined
        text, since, dep = clean_sup("oldMethod<sup>8+(deprecated)</sup>")
        self.assertEqual(text, "oldMethod")
        self.assertEqual(since, "8+")
        self.assertTrue(dep)

        # Text deprecation
        text, since, dep = clean_sup("legacyApi(deprecated)")
        self.assertEqual(text, "legacyApi")
        self.assertTrue(dep)

    def test_split_table_row_escaped_pipe(self):
        row = r"| fieldName | string \| Object \| ArrayBuffer | 否 | 是 | 描述说明 |"
        cols = split_table_row(row)
        self.assertEqual(len(cols), 5)
        self.assertEqual(cols[0], "fieldName")
        self.assertEqual(cols[1], "string | Object | ArrayBuffer")
        self.assertEqual(cols[4], "描述说明")

    def test_parse_c_decl(self):
        # Basic variable
        name, ptype = parse_c_decl("uint32_t priority")
        self.assertEqual(name, "priority")
        self.assertEqual(ptype, "uint32_t")

        # Pointer variable
        name, ptype = parse_c_decl("const char *method")
        self.assertEqual(name, "method")
        self.assertEqual(ptype, "const char *")

        # Markdown linked type with pointer
        name, ptype = parse_c_decl("[Http_Headers](capi-netstack-http-headers.md) *headers")
        self.assertEqual(name, "headers")
        self.assertEqual(ptype, "Http_Headers *")

    def test_extract_metadata_colon_inside_and_outside(self):
        # Colon inside bold asterisks
        text_inside = """
**需要权限：** ohos.permission.INTERNET
**系统能力：** SystemCapability.Test.SysCap
**起始版本：** 11+
**原子化服务API：** 从API version 11开始支持
**废弃：** 自API version 12开始废弃
"""
        meta1 = extract_metadata_from_text(text_inside)
        self.assertEqual(meta1["permission"], "ohos.permission.INTERNET")
        self.assertEqual(meta1["syscap"], "SystemCapability.Test.SysCap")
        self.assertEqual(meta1["since"], "11+")
        self.assertIn("11", meta1["atomic_service"])
        self.assertTrue(meta1["deprecated"])

        # Colon outside bold asterisks
        text_outside = """
**需要权限**：ohos.permission.LOCATION
**系统能力**：SystemCapability.Location
**起始版本**：9
"""
        meta2 = extract_metadata_from_text(text_outside)
        self.assertEqual(meta2["permission"], "ohos.permission.LOCATION")
        self.assertEqual(meta2["syscap"], "SystemCapability.Location")
        self.assertEqual(meta2["since"], "9")

    def test_parse_sample_doc(self):
        sample_md = """# @ohos.net.sample (示例模块)

<!--Kit: Network Kit-->
<!--Subsystem: Communication-->

本模块提供示例功能。

## 导入模块

```ts
import { sample } from '@kit.NetworkKit';
```

## sample.doAction

doAction(param: string): void

执行特定操作。

**需要权限：** ohos.permission.INTERNET

**系统能力：** SystemCapability.Communication.NetStack

**原子化服务API：** 从API version 11开始，该接口支持在原子化服务中使用。

**参数：**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| param | string | 是 | 操作参数。 |

**返回值：**

| 类型 | 说明 |
| :--- | :--- |
| void | 无返回值。 |

**错误码：**

| 错误码ID | 错误信息 |
| :--- | :--- |
| 401 | Parameter error. |

**示例：**

```ts
sample.doAction('test');
```

## SampleOptions

操作配置参数。

| 名称 | 类型 | 只读 | 可选 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| timeout<sup>9+</sup> | number | 否 | 是 | 超时时间。 |
| enableTls<sup>12+</sup> | boolean | 否 | 是 | 是否启用TLS加密。 |
"""
        parser = DocParser(version="vTest")
        chunks = parser.parse_file_content("test/sample.md", sample_md)

        # Check total chunks (overview + 导入模块 + doAction + SampleOptions + timeout prop + enableTls prop)
        self.assertGreater(len(chunks), 4)

        # Find doAction
        action_chunks = [c for c in chunks if c.api_name == "doAction"]
        self.assertEqual(len(action_chunks), 1)
        action = action_chunks[0]
        self.assertEqual(action.category, "function")
        self.assertEqual(action.signature, "doAction(param: string): void")
        self.assertEqual(action.permission, "ohos.permission.INTERNET")
        self.assertEqual(action.syscap, "SystemCapability.Communication.NetStack")
        self.assertIn("API version 11", action.atomic_service)
        self.assertIn("param", action.parameters_summary)
        self.assertIn("void", action.return_summary)
        self.assertIn("401", action.error_codes_summary)
        self.assertIn("doAction('test')", action.example)

        # Find timeout property
        timeout_chunks = [c for c in chunks if c.api_name == "timeout"]
        self.assertEqual(len(timeout_chunks), 1)
        prop = timeout_chunks[0]
        self.assertEqual(prop.category, "property")
        self.assertEqual(prop.parent_title, "SampleOptions")
        self.assertEqual(prop.since, "9+")
        self.assertEqual(prop.signature, "timeout: number")

    def test_parser_empty_and_minimal_inputs(self):
        parser = DocParser(version="vTest")
        self.assertEqual(parser.parse_file_content("empty.md", ""), [])
        self.assertEqual(parser.parse_file_content("blank.md", "   \n\n  "), [])

        one_line = parser.parse_file_content("one.md", "Just a line of text without headings.")
        self.assertEqual(len(one_line), 0)

    def test_dedicated_container_audio_renderer(self):
        audio_path = "official/docs-OpenHarmony-v6.0.0.1-Release-zh-cn-application-dev-reference/zh-cn/application-dev/reference/apis-audio-kit/arkts-apis-audio-AudioRenderer.md"
        if not os.path.exists(audio_path):
            self.skipTest("AudioRenderer doc file not found")

        with open(audio_path, "r", encoding="utf-8") as fp:
            content = fp.read()

        parser = DocParser(version="v6.0.0.1-Release")
        chunks = parser.parse_file_content("apis-audio-kit/arkts-apis-audio-AudioRenderer.md", content)

        # 1. Container chunk should exist
        container_chunks = [c for c in chunks if c.api_name == "AudioRenderer" and c.category == "interface"]
        self.assertEqual(len(container_chunks), 1)

        # 2. Methods should have parent_title = AudioRenderer
        methods = [c for c in chunks if c.category == "method" and c.parent_title == "AudioRenderer"]
        self.assertGreater(len(methods), 20)

        # 3. Property state should have parent_title = AudioRenderer
        state_prop = [c for c in chunks if c.api_name == "state" and c.parent_title == "AudioRenderer"]
        self.assertEqual(len(state_prop), 1)
        self.assertEqual(state_prop[0].category, "property")

        # 4. Method parameters (like callback) must NOT be extracted as properties
        callback_props = [c for c in chunks if c.api_name == "callback" and c.parent_title == "getRendererInfo"]
        self.assertEqual(len(callback_props), 0)

    def test_c_api_struct_and_header(self):
        # 1. C-API struct
        struct_path = "official/docs-OpenHarmony-v6.0.0.1-Release-zh-cn-application-dev-reference/zh-cn/application-dev/reference/apis-network-kit/capi-netstack-http-requestoptions.md"
        if os.path.exists(struct_path):
            with open(struct_path, "r", encoding="utf-8") as fp:
                c_content = fp.read()
            parser = DocParser(version="v6.0.0.1-Release")
            chunks = parser.parse_file_content("capi-netstack-http-requestoptions.md", c_content)
            props = [c for c in chunks if c.category == "property" and c.parent_title == "Http_RequestOptions"]
            self.assertGreater(len(props), 5)
            prop_names = [p.api_name for p in props]
            self.assertIn("method", prop_names)
            self.assertIn("priority", prop_names)

        # 2. C-API header function
        header_path = "official/docs-OpenHarmony-v6.0.0.1-Release-zh-cn-application-dev-reference/zh-cn/application-dev/reference/apis-network-kit/capi-net-http-h.md"
        if os.path.exists(header_path):
            with open(header_path, "r", encoding="utf-8") as fp:
                h_content = fp.read()
            parser = DocParser(version="v6.0.0.1-Release")
            chunks = parser.parse_file_content("capi-net-http-h.md", h_content)
            func = [c for c in chunks if c.api_name == "OH_Http_CreateHeaders"][0]
            self.assertTrue(bool(func.description))
            self.assertTrue(bool(func.return_summary))


class TestDocIndexerAndRetriever(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_doc_rag.db")
        cls.indexer = DocIndexer(db_path=cls.db_path)

        # Ingest v6.0.0.1-Release network and audio kit docs
        v6_dir = "official/docs-OpenHarmony-v6.0.0.1-Release-zh-cn-application-dev-reference/zh-cn/application-dev/reference"
        if os.path.exists(v6_dir):
            cls.indexer.ingest_directory(
                doc_dir=v6_dir,
                version="v6.0.0.1-Release",
                kit_filter=["apis-network-kit", "apis-audio-kit"],
            )

        # Ingest v6.1-LTS network kit docs from zip
        v6_1_zip = "official/docs-OpenHarmony-v6.1-LTS-zh-cn-application-dev-reference.zip"
        if os.path.exists(v6_1_zip):
            cls.indexer.ingest_zip(
                zip_path=v6_1_zip,
                version="v6.1-LTS",
                kit_filter=["apis-network-kit"],
            )

        cls.retriever = DocRetriever(indexer=cls.indexer)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_database_stats(self):
        stats = self.indexer.get_stats()
        self.assertGreater(stats["total_chunks"], 1000)
        self.assertIn("v6.0.0.1-Release", stats["by_version"])
        self.assertIn("v6.1-LTS", stats["by_version"])
        self.assertGreater(stats["distinct_apis"], 500)

    def test_search_by_name_exact(self):
        # 1. Search for createHttp
        results = self.retriever.search_by_name("createHttp", version="v6.0.0.1-Release")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top.chunk.api_name, "createHttp")
        self.assertEqual(top.chunk.signature, "createHttp(): HttpRequest")
        self.assertEqual(top.chunk.version, "v6.0.0.1-Release")

        # 2. Search with trailing parentheses: createHttp()
        res_paren = self.retriever.search_by_name("createHttp()", exact=True, version="v6.0.0.1-Release")
        self.assertGreater(len(res_paren), 0)
        self.assertEqual(res_paren[0].chunk.api_name, "createHttp")

        # 3. Search with module prefix: http.createHttp
        res_dotted = self.retriever.search_by_name("http.createHttp", exact=True, version="v6.0.0.1-Release")
        self.assertGreater(len(res_dotted), 0)
        self.assertEqual(res_dotted[0].chunk.api_name, "createHttp")

        # 4. Search for HttpRequest.request
        req_results = self.retriever.search_by_name("HttpRequest.request", version="v6.0.0.1-Release")
        self.assertGreater(len(req_results), 0)
        self.assertTrue(any("request" in r.chunk.api_name for r in req_results))

    def test_search_by_name_property(self):
        # 1. Search for property usingProxy
        results = self.retriever.search_by_name("usingProxy", version="v6.0.0.1-Release")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top.chunk.api_name, "usingProxy")
        self.assertEqual(top.chunk.parent_title, "HttpRequestOptions")
        self.assertEqual(top.chunk.since, "10+")

        # 2. Search for AudioRenderer.state
        state_res = self.retriever.search_by_name("AudioRenderer.state", exact=True, version="v6.0.0.1-Release")
        self.assertGreater(len(state_res), 0)
        self.assertEqual(state_res[0].chunk.api_name, "state")
        self.assertEqual(state_res[0].chunk.parent_title, "AudioRenderer")

    def test_search_by_keyword(self):
        # 1. Search Chinese keyword: 证书锁定
        results = self.retriever.search_by_keyword("证书锁定")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("certificatePinning" in r.chunk.api_name or "certificatepinning" in r.chunk.file_path for r in results))

        # 2. Search English keyword: brotli
        results_brotli = self.retriever.search_by_keyword("brotli")
        self.assertGreater(len(results_brotli), 0)

        # 3. Search HTTP请求
        results_http = self.retriever.search_by_keyword("HTTP请求")
        self.assertGreater(len(results_http), 0)

    def test_fts_special_characters_and_operators(self):
        # Operators like AND, OR, NOT, NEAR must not raise sqlite3.OperationalError
        res_ops = self.retriever.search_by_keyword("AND OR NOT NEAR")
        self.assertIsInstance(res_ops, list)

        # Unbalanced quotes
        res_quotes = self.retriever.search_by_keyword('"""')
        self.assertIsInstance(res_quotes, list)

        # Parentheses and special symbols
        res_sym = self.retriever.search_by_keyword("((:::*:::))")
        self.assertIsInstance(res_sym, list)

    def test_search_by_condition(self):
        # Filter by permission
        results = self.retriever.search_by_condition(
            permission="ohos.permission.INTERNET",
            version="v6.0.0.1-Release",
            limit=10,
        )
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("ohos.permission.INTERNET", r.chunk.permission)

        # Filter by deprecated
        results_dep = self.retriever.search_by_condition(
            deprecated=True,
            version="v6.0.0.1-Release",
            limit=10,
        )
        self.assertGreater(len(results_dep), 0)
        for r in results_dep:
            self.assertTrue(r.chunk.deprecated)

    def test_compare_api_new_in_v6_1(self):
        # HttpInterceptor is added in v6.1-LTS, not in v6.0.0.1-Release
        comp = self.retriever.compare_api_across_versions("HttpInterceptor")
        self.assertIn("v6.0.0.1-Release", comp.missing_versions)
        self.assertIn("v6.1-LTS", comp.found_versions)
        self.assertEqual(comp.differences["version_status"]["v6.0.0.1-Release"], "NOT_FOUND")
        self.assertEqual(comp.differences["version_status"]["v6.1-LTS"], "AVAILABLE")
        self.assertTrue(any("首次引入" in ch for ch in comp.differences["changes_detected"]))

    def test_compare_api_property_additions(self):
        # HttpRequestOptions has new properties in v6.1-LTS (maxRedirects, sniHostName, pathPreference, customMethod)
        comp = self.retriever.compare_api_across_versions("HttpRequestOptions")
        self.assertIn("v6.0.0.1-Release", comp.found_versions)
        self.assertIn("v6.1-LTS", comp.found_versions)
        self.assertTrue(any("新增属性" in ch for ch in comp.differences["changes_detected"]))
        added_props = [ch for ch in comp.differences["changes_detected"] if "新增属性" in ch][0]
        self.assertIn("maxRedirects", added_props)
        self.assertIn("sniHostName", added_props)

    def test_compare_api_exact_vs_substring(self):
        # Comparing createHttp must ONLY match createHttp, never createHttpResponseCache
        comp = self.retriever.compare_api_across_versions("createHttp")
        v6_chunks = comp.by_version["v6.0.0.1-Release"]
        api_names = set(c.api_name for c in v6_chunks)
        self.assertEqual(api_names, {"createHttp"})
        self.assertNotIn("createHttpResponseCache", api_names)

    def test_search_non_existent_api(self):
        results = self.retriever.search_by_name("NonExistentFakeAPI12345")
        self.assertEqual(len(results), 0)

        comp = self.retriever.compare_api_across_versions("NonExistentFakeAPI12345")
        self.assertEqual(len(comp.found_versions), 0)
        self.assertEqual(len(comp.missing_versions), len(comp.target_versions))


if __name__ == "__main__":
    unittest.main()
