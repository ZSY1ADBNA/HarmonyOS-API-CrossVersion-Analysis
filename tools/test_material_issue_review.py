"""Keep scope exclusions and ambiguous decoding distinct from repairs."""
import unittest
from review_material_issues import classify_link, encoding_candidates


class IssueReviewTests(unittest.TestCase):
    def link(self,path,paths=(),target=None):
        paths=set(paths);folded={p.casefold():[p] for p in paths}
        return classify_link({'target':target or path,'resolved_path':path},paths,folded,{'guide'})[0]

    def test_scope_exclusion_is_not_missing_file(self):
        self.assertEqual(self.link('en/README.md',['en/README.md']),'exists_outside_collected_scope')

    def test_case_directory_and_expansion_are_separate(self):
        self.assertEqual(self.link('Button.md',['button.md']),'case_mismatch')
        self.assertEqual(self.link('guide'),'directory_target')
        self.assertEqual(self.link('overview',['overview.md']),'site_path_expansion_candidate')
        self.assertEqual(self.link('missing.md'),'target_absent_in_fixed_repository_tree')

    def test_syntax_and_site_root_are_not_guessed(self):
        self.assertEqual(self.link('file(foo',target='file(foo'),'link_syntax_requires_review')
        self.assertEqual(self.link('root.md',target='/root.md'),'root_relative_base_requires_review')

    def test_multiple_lossless_decodings_are_not_an_encoding_declaration(self):
        raw='测试用例'.encode('gbk'); candidates=encoding_candidates(raw)
        chinese=next(c for c in candidates if c['text']=='测试用例')
        self.assertEqual(chinese['equivalent_codecs'],['gbk','gb18030'])
        self.assertGreater(len(candidates),1)
        for c in candidates:
            for codec in c['equivalent_codecs']: self.assertEqual(c['text'].encode(codec),raw)


if __name__=='__main__': unittest.main()
