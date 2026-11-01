import unittest
from verify_sdk_inheritance import inspect_chain,since_conditions


class InheritanceTests(unittest.TestCase):
    def check(self,text):return inspect_chain([{'path':'test.d.ts','text':text}],root='ButtonAttribute',member='minFontScale')
    def test_inherited_member_and_missing_base(self):
        result=self.check('declare class ButtonAttribute extends Base {}\ndeclare class Base { minFontScale(x: number): Base; }')
        self.assertEqual(result['status'],'member_found');self.assertEqual(result['matches'][0]['owner'],'Base')
        result=self.check('declare class ButtonAttribute extends Missing {}')
        self.assertEqual(result['status'],'incomplete_inheritance_evidence')
    def test_complete_absence_does_not_include_other_components(self):
        result=self.check('declare class ButtonAttribute extends Base {}\ndeclare class Base {}\ndeclare class TextAttribute { minFontScale(x: number): TextAttribute; }')
        self.assertEqual(result['status'],'member_absent_in_complete_selected_chain')
    def test_unrelated_merging_is_not_selected_ambiguity(self):
        result=self.check('declare class ButtonAttribute {}\ninterface Other {x:number}\ninterface Other {y:number}')
        self.assertEqual(result['status'],'member_absent_in_complete_selected_chain')
        with self.assertRaisesRegex(ValueError,'Ambiguous selected'):
            self.check('declare class ButtonAttribute {}\ndeclare class ButtonAttribute {}')
    def test_cycles_fail_and_later_diagnostics_remain_visible(self):
        with self.assertRaisesRegex(ValueError,'Cyclic'):
            self.check('declare class ButtonAttribute extends Base {}\ndeclare class Base extends ButtonAttribute {}')
        result=self.check('declare class ButtonAttribute {}\ndeclare class Broken { ??? }')
        self.assertTrue(result['diagnostics']);self.assertFalse(result['whole_file_syntax_verified'])
        self.assertEqual(result['selected_chain_diagnostics'],[])
    def test_language_markers_preserved_and_unknown_not_guessed(self):
        self.assertEqual(since_conditions('23 static')['language_mode'],'static')
        self.assertEqual(since_conditions('11')['language_mode'],'unspecified')
        self.assertEqual(since_conditions("arkts {'1.1':'11','1.2':'20'}")['language_api_levels'],{'1.1':11,'1.2':20})
        self.assertEqual(since_conditions('eleven dynamic')['status'],'unresolved_annotation')
        self.assertEqual(since_conditions("arkts __import__('os')")['status'],'unresolved_annotation')


if __name__=='__main__':unittest.main()
