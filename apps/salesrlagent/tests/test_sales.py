import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from fastapi.testclient import TestClient
from sales_agent.app import create_app
from sales_agent.catalog import requirements, retrieve
from sales_agent.features import encode, EMBED_DIM, FEATURE_DIM
from sales_agent.graph import build_graph
from sales_agent.store import Store


class SalesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(str(Path(self.tmp.name) / 'test.sqlite3'))
        self.client = TestClient(self.app)
        self.client.post('/api/session')

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def chat(self, text, request_id='request-1234'):
        return self.client.post('/api/chat', json={'text': text, 'request_id': request_id})

    def test_constraints_and_context(self):
        r = self.chat('Noise cancelling headphones under $200 for travel')
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual([p['id'] for p in r.json()['products']], ['sony-ult-wear', 'sony-whch730n'])
        r = self.chat('Actually under $100', 'request-2345')
        self.assertEqual(r.json()['products'], [])
        self.assertEqual(r.json()['requirements']['category'], 'headphones')

    def test_required_features_not_tradeoff_keywords(self):
        result = retrieve(requirements('headphones with noise cancelling under $300'))
        self.assertNotIn('studio', [p['id'] for p in result])

    def test_multiple_use_cases_influence_ranking(self):
        req = requirements('Compare a 4K TV for movies and gaming under $800')
        self.assertEqual(req['uses'], ['gaming', 'movies'])
        self.assertEqual(retrieve(req), [])  # No invented TV matches in this curated snapshot.

    def test_decline_stops_guidance(self):
        result = self.chat('No thanks, not interested').json()
        self.assertEqual(result['strategy'], 'END_CONVERSATION')
        self.assertEqual(result['actions'], [])
        self.assertEqual(result['products'], [])

    def test_idempotency_and_conflict(self):
        first = self.chat('earbuds under $150').json()
        self.assertEqual(self.chat('earbuds under $150').json()['turn_id'], first['turn_id'])
        self.assertEqual(self.chat('speakers').status_code, 409)
        self.assertEqual(len(self.client.post('/api/session').json()['messages']), 2)

    def test_feedback_is_session_scoped_and_deduplicated(self):
        turn_id = self.chat('earbuds').json()['turn_id']
        other = TestClient(self.app)
        other.post('/api/session')
        body = {'turn_id': turn_id, 'helpful': True}
        self.assertEqual(other.post('/api/feedback', json=body).status_code, 404)
        self.assertTrue(self.client.post('/api/feedback', json=body).json()['accepted'])
        self.assertFalse(self.client.post('/api/feedback', json=body).json()['accepted'])
        other.close()

    def test_cart_validates_and_prices_on_server(self):
        self.assertEqual(self.client.put('/api/cart', json={'product_id': 'fake', 'quantity': 1}).status_code, 404)
        self.assertEqual(self.client.put('/api/cart', json={'product_id': 'sony-wh1000xm5', 'quantity': -1}).status_code, 422)
        result = self.client.put('/api/cart', json={'product_id': 'sony-wh1000xm5', 'quantity': 2, 'price': 1}).json()
        self.assertEqual(result['total'], 599.98)
        result = self.client.post('/api/checkout').json()
        self.assertTrue(result['demo'])
        self.assertEqual(result['total'], 599.98)
        self.assertEqual(self.client.post('/api/checkout').status_code, 400)

    def test_delete_invalidates_session_and_feedback(self):
        turn_id = self.chat('headphones').json()['turn_id']
        self.client.post('/api/feedback', json={'turn_id': turn_id, 'helpful': True})
        old_cookie = self.client.cookies.get('sales_session')
        self.client.delete('/api/session')
        self.assertIsNone(self.app.state.store.get(old_cookie))
        self.assertEqual(self.chat('hello').status_code, 401)
        with self.app.state.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM feedback').fetchone()[0], 0)

    def test_cross_origin_and_whitespace_rejected(self):
        self.assertEqual(self.client.post('/api/session', headers={'origin': 'https://evil.example'}).status_code, 403)
        self.assertEqual(self.chat('  ').status_code, 422)
        self.assertEqual(self.client.post('/api/chat', json={'text':'x'*2001,'request_id':'request-123'}).status_code, 422)

    def test_restart_restores_completed_turn(self):
        self.chat('wireless earbuds under $130')
        sid = self.client.cookies.get('sales_session')
        state = Store(str(Path(self.tmp.name) / 'test.sqlite3')).get(sid)
        self.assertEqual(state['requirements']['budget'], 130)
        self.assertEqual(len(state['messages']), 2)
        self.assertEqual([p['id'] for p in self.client.post('/api/session').json()['products']], ['apple-airpods-5'])

    def test_no_fake_prediction_and_comparison(self):
        result = self.chat('Compare earbuds under $150').json()
        self.assertIsNone(result['prediction']['probability'])
        self.assertEqual(result['actions'][0]['type'], 'compare')
        self.assertGreaterEqual(len(result['products']), 2)
        self.assertTrue(all(p['category']=='earbuds' and p['price']<=150 for p in result['products']))
        self.assertEqual(len(result['actions'][0]['product_ids']), 2)

    def test_expiry(self):
        sid = self.client.cookies.get('sales_session')
        with self.app.state.store.connect() as db:
            db.execute('UPDATE sessions SET updated=0 WHERE id=?', (sid,))
        self.assertEqual(self.chat('headphones').status_code, 401)

    def test_feature_vector_is_finite_bounded_and_deterministic(self):
        history = [{'role':'user','content':'I want headphones under $100'}]
        a, b = encode(history), encode(history)
        self.assertEqual(a.shape, (EMBED_DIM + FEATURE_DIM,))
        self.assertTrue(np.isfinite(a).all())
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.array_equal(a, encode(history + [{'role':'user','content':'no thanks'}])))

    def test_site_assets(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        script = self.client.get('/static/app.js')
        self.assertEqual(script.status_code, 200)
        self.assertEqual(self.client.get('/static/voice-controller.js').status_code,200)
        self.assertEqual(self.client.get('/static/microphone-worklet.js').status_code,200)
        self.assertIn('CircuitWise', self.client.get('/').text)
        self.assertIn("frame-ancestors 'none'", self.client.get('/').headers['content-security-policy'])
        self.assertIn('offline_voice', self.client.get('/healthz').json())
        self.assertIn('natural_voice', self.client.get('/healthz').json())


if __name__ == '__main__':
    unittest.main()
