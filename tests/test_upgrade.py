from pathlib import Path
import tempfile
import unittest
from cortexstate import Memory, Scope


class UpgradeTests(unittest.TestCase):
    def test_bm25_prefers_rare_terms_and_keeps_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Memory(Path(directory) / 'test.db')
            scope = Scope('a', 'alice')
            rare = memory.add('project uses zirconium', scope=scope)
            for i in range(5):
                memory.add('project uses ordinary materials ' + str(i), scope=scope)
            memory.add('zirconium zirconium', scope=Scope('b', 'alice'))
            results = memory.search('project zirconium', scope=scope, ranking='bm25')
            self.assertEqual(results[0]['id'], rare['id'])
            self.assertTrue(all(0 < r['score'] < 1 for r in results))
            self.assertEqual(memory.search('absent', scope=scope, ranking='bm25'), [])
            with self.assertRaises(ValueError):
                memory.search('project', scope=scope, ranking='unknown')

    def test_stats_expiry_and_revision_count(self):
        with tempfile.TemporaryDirectory() as directory:
            now = [100]
            memory = Memory(Path(directory) / 'test.db', clock=lambda: now[0])
            scope = Scope('a', 'alice')
            record = memory.add('temporary', scope=scope, ttl_seconds=1)
            memory.update(record['id'], 'corrected', scope=scope, expected_revision=1)
            now[0] = 102
            stats = memory.stats(scope=scope)
            self.assertEqual((stats['total'],stats['live'],stats['expired'],stats['revision_events']), (1,0,1,2))
            self.assertEqual(memory.stats(scope=Scope('b','alice'))['total'], 0)
            memory.purge_expired(scope=scope)
            self.assertEqual(memory.stats(scope=scope)['revision_events'], 0)
