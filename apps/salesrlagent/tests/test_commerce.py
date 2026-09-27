import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sales_agent.app import create_app
from sales_agent.catalog import requirements, retrieve
from sales_agent.commands import named_products
from sales_agent.commerce import call_tool, commerce_command

class CommerceTests(unittest.TestCase):
    def test_real_mcp_round_trip(self):
        async def run():
            stock = await call_tool('inventory_lookup', {'product_id':'google-pixel-9a'})
            self.assertEqual(stock['quantity'], 10)
            self.assertTrue(stock['demo'])
            order = await call_tool('order_lookup', {'order_id':'DEMO-1001'})
            self.assertEqual(order['status'], 'shipped')
            unknown = await call_tool('order_lookup', {'order_id':'PRIVATE-123'})
            self.assertFalse(unknown['found'])
            with self.assertRaises(ValueError):
                await call_tool('delete_order', {})
        asyncio.run(run())

    def test_tool_failure_is_not_an_invented_answer(self):
        state = {'cart':[], 'requirements':{}}
        with patch('sales_agent.commerce.call_tool', side_effect=TimeoutError):
            result=asyncio.run(commerce_command('Where is order DEMO-1001?',state))
        self.assertIn('cannot confirm', result['reply'])

    def test_earphones_replace_stale_speaker_category(self):
        req=requirements('show me earphones',requirements('speakers under 200'))
        self.assertEqual(req['category'],'earbuds')
        matches=retrieve(req)
        self.assertTrue(matches)
        self.assertTrue(all(p['category']=='earbuds' for p in matches))

    def test_longer_models_do_not_add_both_products(self):
        self.assertEqual([p['id'] for p in named_products('Add Apple AirPods 5 Wireless Case')],['apple-airpods-5-wireless'])
        self.assertEqual([p['id'] for p in named_products('Add Sony INZONE M10S II')],['sony-inzone-m10s-ii'])
        self.assertEqual(named_products('add the Sony'),[])

    def test_pages_and_shopping_regression(self):
        with tempfile.TemporaryDirectory() as tmp, TestClient(create_app(str(Path(tmp)/'test.db'))) as client:
            client.post('/api/session')
            for route in ['/deals','/sales','/categories','/categories/earbuds','/cart','/orders']:
                self.assertEqual(client.get(route).status_code,200)
            def chat(text, n):
                response=client.post('/api/chat',json={'text':text,'request_id':f'regression-{n}'})
                self.assertEqual(response.status_code,200,response.text)
                return response.json()
            self.assertEqual(chat('show me the sales',1)['actions'][0]['path'],'/sales')
            result=chat('add AirPods five to my cart',2)
            self.assertEqual(result['cart'],[{'product_id':'apple-airpods-5','quantity':1}])
            self.assertEqual(result['actions'][0]['type'],'open_cart')
            result=chat('show my cart',3)
            self.assertIn('$129.00',result['reply'])
            self.assertEqual(client.post('/api/session').json()['cart'],result['cart'])
            self.assertTrue(client.get('/api/integrations').json()['commerce']['read_only'])
