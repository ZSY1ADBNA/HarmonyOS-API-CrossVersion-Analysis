import unittest
from pilot_document_structure import heading_spans, layout_candidates


class StructurePilotTests(unittest.TestCase):
    def test_full_coverage_and_fenced_heading(self):
        text='preamble\n# Button\n## 属性\n### fontSize\n```ts\n# Fake\n```\nbody\n'
        sections=heading_spans(text)
        self.assertEqual(''.join(s['text'] for s in sections),text)
        self.assertFalse(any(s['heading']=='Fake' for s in sections))
        member=layout_candidates('arkui_button',sections)[0]
        self.assertEqual(member['owner'],'Button')
        self.assertEqual(member['line'],4)

    def test_no_h2_and_no_heading_are_not_dropped(self):
        for text in ('# Events\nCOMMON_EVENT_BOOT_COMPLETED\n','plain text\n'):
            sections=heading_spans(text)
            self.assertEqual(len(sections),1)
            self.assertEqual(sections[0]['text'],text)

    def test_enum_owner_and_symbolic_assignment_are_preserved(self):
        text='# H\n## 枚举类型说明\n### OH_IPC_ErrorCode\n| OH_IPC_SUCCESS = 0 | OK |\n| OH_IPC_ERROR = OH_IPC_BASE + 1 | Error |\n'
        rows=layout_candidates('c_api_ipc_enum',heading_spans(text))
        self.assertEqual([r['name'] for r in rows],['OH_IPC_SUCCESS','OH_IPC_ERROR'])
        self.assertEqual(rows[1]['assignment'],'OH_IPC_BASE + 1')
        self.assertTrue(all(r['owner']=='OH_IPC_ErrorCode' for r in rows))

    def test_guide_is_not_assigned_api_semantics(self):
        sections=heading_spans('# Guide\n## 属性\n### fontSize\n')
        self.assertEqual(layout_candidates('application_guide',sections),[])
        self.assertEqual(layout_candidates('arkui_button',sections),[])

    def test_example_call_does_not_create_an_attribute_declaration(self):
        text='# Button\n## 示例\n```ts\nButton().fontSize(20)\n```\n'
        self.assertEqual(layout_candidates('arkui_button',heading_spans(text)),[])


if __name__=='__main__': unittest.main()
