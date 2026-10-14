import copy
import unittest
from rehearse_sample_bridge import plan_bridge


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.records=[{'name':name,'owner':owner,'module':module,'signature':signature,'optional':optional,'sample_identity':name,'candidate_uid':name} for name,owner,module,signature,optional in [
            ('fontSize','ButtonAttribute','ArkUI globals','fontSize(value: Length): ButtonAttribute;',False),
            ('channelLayout','AudioStreamInfo','@ohos.multimedia.audio','channelLayout?: AudioChannelLayout;',True)]]
        self.old={'名称':'channelLayout','上级':'AudioStreamInfo','类型':'property','版本':'API4.1','属性类型':'AudioChannelLayout','所属模块':'未知模块'}
        self.legacy={'fontSize':[],'channelLayout':[self.old]}

    def test_conflicting_fields_rejected(self):
        for key,value in [('上级','OtherOwner'),('类型','method'),('版本','API5.1'),('属性类型','number'),('所属模块','other'),('签名','channelLayout: number;'),('optional',False),('optional','true')]:
            with self.subTest(key=key,value=value):
                legacy=copy.deepcopy(self.legacy);legacy['channelLayout'][0][key]=value
                with self.assertRaises(ValueError):plan_bridge(self.records,legacy)

    def test_duplicates_refused(self):
        legacy=copy.deepcopy(self.legacy);legacy['channelLayout'].append(self.old)
        with self.assertRaisesRegex(ValueError,'Ambiguous'):plan_bridge(self.records,legacy)

    def test_other_release_refused(self):
        with self.assertRaises(ValueError):plan_bridge(self.records,self.legacy,'OpenHarmony-6.1-Release')

    def test_plan_preserves_original_and_missing_status(self):
        before=copy.deepcopy(self.legacy);plan=plan_bridge(self.records,self.legacy)
        self.assertEqual(before,self.legacy)
        self.assertEqual(plan[0]['action'],'add_shadow_missing_legacy')
        self.assertEqual(plan[1]['action'],'add_shadow_and_link_legacy')
        plan[1]['legacy']['名称']='changed'
        self.assertEqual(self.old['名称'],'channelLayout')


if __name__=='__main__':unittest.main()
