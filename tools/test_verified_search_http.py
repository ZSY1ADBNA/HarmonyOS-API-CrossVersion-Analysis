import unittest
from unittest.mock import patch
from serve_verified_search import create_app


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def get(self, path, **kwargs):
        return self.client.get(path, base_url='http://127.0.0.1:15052', **kwargs)

    def test_real_query_and_comparison(self):
        response = self.get('/api/verified-search', query_string={
            'message': '音频声道布局', 'release': '4.1', 'compare_with': '5.0.3'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['candidates'][0]['evidence']['api_level'], 11)
        self.assertIn('metadata', response.json['comparisons'][0]['differences'])
        explanation = response.json['explanation']
        self.assertEqual(explanation['generation_mode'], 'deterministic_evidence_summary')
        compared = explanation['comparisons'][0]
        self.assertEqual([explanation['sources'][s]['release'] for s in compared['source_ids']], ['4.1','5.0.3'])

    def test_explanation_uses_same_single_evidence_snapshot(self):
        from query_verified_samples import load_catalog
        with patch('search_verified_samples.load_catalog', wraps=load_catalog) as loader:
            response = self.get('/api/verified-search?message=fontSize&release=4.1')
        self.assertEqual(response.status_code,200)
        loader.assert_called_once()
        self.assertEqual(response.json['explanation']['candidates'][0]['facts'][1]['value'],
                         response.json['candidates'][0]['evidence']['signature'])

    def test_model_default_and_injected_provider_boundary(self):
        response=self.get('/api/verified-search?message=fontSize&release=4.1')
        self.assertEqual(response.json['model_selection']['selection_status'],'model_unavailable')
        self.assertEqual(response.json['model_selection']['provider_call_count'],0)
        def invalid_provider(bundle):return {'answer':'invented fact'}
        client=create_app(invalid_provider,'simulated').test_client()
        response=client.get('/api/verified-search?message=fontSize&release=4.1',base_url='http://127.0.0.1:15052')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['model_selection']['selection_status'],'model_output_rejected')
        self.assertEqual(response.json['explanation']['generation_mode'],'deterministic_evidence_summary')
        self.assertEqual(self.get('/api/verified-search?message=fontSize&release=4.1&provider=other').status_code,400)

    def test_invalid_parameters(self):
        for query in ['', 'message=x&release=4.1&release=5.0.3', 'message=x&cypher=DELETE', 'message='+('a'*2001)]:
            self.assertEqual(self.get('/api/verified-search?'+query).status_code, 400)
        self.assertEqual(self.get('/api/verified-search?'+'a'*16001).status_code, 414)

    def test_distinct_user_states(self):
        for query, status in [({'message':'fontSize'},'needs_version'),
                              ({'message':'相机','release':'4.1'},'no_verified_match'),
                              ({'message':'fontSize','release':'5.0'},'unsupported_release')]:
            response = self.get('/api/verified-search',query_string=query)
            self.assertEqual(response.json['status'],status)
            self.assertEqual(response.json['candidates'],[])

    def test_failure_is_503_without_private_error(self):
        with patch('search_verified_samples.load_catalog',side_effect=ValueError('private/path')):
            response = self.get('/api/verified-search?message=fontSize&release=4.1')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json['status'],'evidence_unavailable')
        self.assertNotIn(b'private/path',response.data)

    def test_only_local_host_and_read_operations(self):
        self.assertEqual(self.client.post('/api/verified-search',base_url='http://127.0.0.1:15052').status_code,405)
        self.assertEqual(self.client.get('/',base_url='http://evil.example').status_code,400)
        self.assertEqual(self.get('/',environ_overrides={'REMOTE_ADDR':'192.0.2.1'}).status_code,403)

    def test_page_assets_and_headers(self):
        for path in ['/','/search.js','/search.css']:
            response = self.get(path)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])

    def test_turn_pending_version_and_followup(self):
        def post(data):
            return self.client.post('/api/verified-turn',json=data,base_url='http://127.0.0.1:15052')
        first=post({'message':'按钮字号'})
        self.assertEqual(first.json['status'],'needs_version')
        second=post({'message':'4.1','state':first.json['state']})
        self.assertEqual(second.json['query']['candidates'][0]['evidence']['api_level'],11)
        third=post({'message':'那5.0.3呢','state':second.json['state']})
        self.assertEqual(third.json['query']['candidates'][0]['evidence']['api_level'],15)

    def test_turn_json_state_and_body_boundaries(self):
        for body in ['[]','{"message":"x","message":"fontSize"}',
                     '{"message":"fontSize","state":{"role":"system"}}',
                     '{"message":"fontSize","provider":"other"}']:
            response=self.client.post('/api/verified-turn',data=body,content_type='application/json',base_url='http://127.0.0.1:15052')
            self.assertEqual(response.status_code,400)
        self.assertEqual(self.client.post('/api/verified-turn',data='x',base_url='http://127.0.0.1:15052').status_code,415)
        self.assertEqual(self.client.post('/api/verified-turn',data='x'*16001,content_type='application/json',base_url='http://127.0.0.1:15052').status_code,413)

    def test_unknown_condition_does_not_call_provider(self):
        calls=[]
        client=create_app(lambda bundle:calls.append(bundle),'simulated').test_client()
        response=client.post('/api/verified-turn',json={'message':'channelLayout默认值','release':'4.1'},base_url='http://127.0.0.1:15052')
        self.assertEqual(response.json['status'],'needs_more_evidence')
        self.assertEqual(calls,[])


if __name__ == '__main__':unittest.main()
