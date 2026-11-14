import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from cortexstate.providers import OpenAIModels
from cortexstate.extraction import propose


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.provider = OpenAIModels(embedding_model='embedding-test', generation_model='generation-test', client=self.client)

    def test_embedding_delegates_to_official_sdk_surface(self):
        self.client.embeddings.create.return_value = SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])])
        self.assertEqual(self.provider.embed('tea'), [1.0,0.0])
        self.client.embeddings.create.assert_called_once_with(model='embedding-test', input='tea', encoding_format='float')

    def test_proposals_are_validated_and_not_written(self):
        self.client.responses.create.return_value = SimpleNamespace(status='completed', output_text=json.dumps([{'text':'Prefers tea','source_indices':[0]}]))
        facts = propose([{'role':'user','content':'I prefer tea'}], extractor=self.provider.extract)
        self.assertEqual(facts[0]['status'], 'needs_review')
        self.assertFalse(self.client.responses.create.call_args.kwargs['store'])

    def test_incomplete_and_invalid_outputs_fail_closed(self):
        for response in (SimpleNamespace(status='incomplete',output_text='[]'), SimpleNamespace(status='completed',output_text='not json')):
            self.client.responses.create.return_value = response
            with self.assertRaises(ValueError):
                self.provider.extract([{'role':'user','content':'tea'}])

    def test_answer_keeps_evidence_and_reported_usage(self):
        self.client.responses.create.return_value = SimpleNamespace(status='completed', output_text='Tea.', usage=SimpleNamespace(input_tokens=12, output_tokens=3))
        result = self.provider.answer('What drink?', {'data':'[]','memory_ids':['evidence-id']})
        self.assertEqual(result['usage'], {'input_tokens':12, 'output_tokens':3})
        self.assertEqual(result['memory_ids'], ['evidence-id'])
        self.assertEqual(result['answer'], 'Tea.')
