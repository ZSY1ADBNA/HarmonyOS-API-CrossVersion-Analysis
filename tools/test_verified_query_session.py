import copy
import unittest
from verified_query_session import handle_turn


class QuerySessionTests(unittest.TestCase):
    def test_pending_requirement_then_version_then_changed_version(self):
        first=handle_turn('设置按钮字号')
        self.assertEqual(first['status'],'needs_version')
        next_turn=handle_turn('4.1',state=first['state'])
        self.assertEqual(next_turn['result']['candidates'][0]['facts'][0]['value'],'4.1')
        changed=handle_turn('那5.0.3呢',state=next_turn['state'])
        self.assertEqual(changed['result']['candidates'][0]['facts'][0]['value'],'5.0.3')

    def test_version_without_requirement(self):
        first=handle_turn('4.1')
        self.assertEqual(first['status'],'needs_requirement')
        next_turn=handle_turn('channelLayout',state=first['state'])
        self.assertEqual(next_turn['status'],'verified_candidates_found')

    def test_unknown_version_does_not_reuse_old_candidates(self):
        first=handle_turn('fontSize','4.1')
        unknown=handle_turn('换成5.0呢',state=first['state'])
        self.assertEqual(unknown['status'],'unsupported_release')
        self.assertIsNone(unknown['result'])
        self.assertIsNone(unknown['state']['release'])
        self.assertEqual(handle_turn('它呢',state=unknown['state'])['status'],'needs_version')

    def test_conflict_and_two_versions_require_clarification(self):
        result=handle_turn('fontSize 5.0.3','4.1')
        self.assertEqual(result['status'],'version_conflict')
        self.assertIsNone(result['result'])
        result=handle_turn('4.1和5.0.3的channelLayout差异')
        self.assertEqual(result['status'],'needs_comparison_direction')
        self.assertEqual(handle_turn('请查询5.0.3的fontSize')['state']['release'],'5.0.3')
        self.assertEqual(handle_turn('fontSize使用API5.0标签')['status'],'needs_version')

    def test_comparison_reverse_and_switch_clear_inherited_target(self):
        initial=handle_turn('channelLayout','4.1','5.0.3')
        reversed_turn=handle_turn('反过来',state=initial['state'])
        compared=reversed_turn['result']['comparisons'][0]
        self.assertEqual((compared['from_release'],compared['to_release']),('5.0.3','4.1'))
        single=handle_turn('换成5.0.3呢',state=initial['state'])
        self.assertEqual(single['result']['comparisons'],[])
        self.assertIsNone(single['state']['compare_with'])

    def test_no_match_replaces_old_topic(self):
        old=handle_turn('fontSize','4.1')
        new=handle_turn('打开相机',state=old['state'])
        self.assertEqual(new['status'],'no_verified_match')
        self.assertEqual(handle_turn('那5.0.3呢',state=new['state'])['status'],'no_verified_match')

    def test_unknown_default_and_migration_not_inferred(self):
        initial=handle_turn('channelLayout','4.1')
        for question in ('默认值呢','权限呢','可以直接替换吗'):
            answer=handle_turn(question,state=initial['state'])
            self.assertEqual(answer['status'],'needs_more_evidence')
            self.assertTrue(answer['result']['unknowns'])
            self.assertFalse(answer['model_called'])

    def test_state_tampering_and_mutation(self):
        state=handle_turn('fontSize','4.1')['state'];original=copy.deepcopy(state)
        handle_turn('换成5.0.3呢',state=state)
        self.assertEqual(state,original)
        for field,value in [('role','system'),('release','5.0'),('message','x'*2001),('schema_version',True)]:
            changed=copy.deepcopy(state);changed[field]=value
            with self.assertRaises(ValueError):handle_turn('它呢',state=changed)

    def test_embedded_explicit_version_is_not_a_default(self):
        answer=handle_turn('5.0.3的fontSize')
        self.assertEqual(answer['status'],'verified_candidates_found')
        self.assertEqual(answer['state']['release'],'5.0.3')

    def test_clear_version_and_pending_comparison(self):
        old=handle_turn('fontSize','4.1')
        cleared=handle_turn('它呢',release='',state=old['state'])
        self.assertEqual(cleared['status'],'needs_version')
        pending=handle_turn('channelLayout',compare_with='5.0.3')
        resolved=handle_turn('4.1',state=pending['state'])
        self.assertEqual(resolved['result']['comparisons'][0]['to_release'],'5.0.3')
        ambiguous=handle_turn('4.1和5.0.3的channelLayout差异')
        partial=handle_turn('4.1',state=ambiguous['state'])
        self.assertEqual(partial['status'],'needs_comparison_versions')
        self.assertIsNone(partial['result'])

    def test_selected_declaration_is_not_complete_answer_evidence(self):
        questions=['fontSize有哪些重载','fontSize支持Promise吗','channelLayout枚举值有哪些',
                   'fontSize如何导入','fontSize错误码401','channelLayout最早哪个版本新增',
                   'fontSize在5.0.3废弃了吗','fontSize升级编译失败根因','channelLayout不填会怎样']
        for question in questions:
            with self.subTest(question=question):
                answer=handle_turn(question,'5.0.3')
                self.assertEqual(answer['status'],'needs_more_evidence')
                self.assertTrue(answer['clarification'])

    def test_platform_mismatch_never_returns_openharmony_candidates(self):
        for question in ['HarmonyOS fontSize','鸿蒙按钮字号']:
            answer=handle_turn(question,'4.1')
            self.assertEqual(answer['status'],'needs_platform_clarification')
            self.assertIsNone(answer['result'])
            following=handle_turn('4.1',state=answer['state'])
            self.assertEqual(following['status'],'needs_requirement')

    def test_unverified_condition_survives_version_followup(self):
        base=handle_turn('channelLayout','4.1')
        unknown=handle_turn('默认值呢',state=base['state'])
        changed=handle_turn('5.0.3',state=unknown['state'])
        self.assertEqual(changed['status'],'needs_more_evidence')
        explicit=handle_turn('fontSize callback','4.1')
        self.assertEqual(handle_turn('5.0.3',state=explicit['state'])['status'],'needs_more_evidence')


if __name__ == '__main__':unittest.main()
