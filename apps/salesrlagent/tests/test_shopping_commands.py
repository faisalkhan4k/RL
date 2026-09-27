import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sales_agent.app import create_app
from sales_agent.catalog import requirements,retrieve

class ShoppingCommandTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.client=TestClient(create_app(str(Path(self.tmp.name)/'test.db')));self.client.post('/api/session');self.n=0
 def tearDown(self):self.client.close();self.tmp.cleanup()
 def chat(self,text,request_id=None):
  self.n+=1
  return self.client.post('/api/chat',json={'text':text,'request_id':request_id or f'command-{self.n:04d}'}).json()
 def test_budget_proximity(self):
  self.assertEqual(retrieve(requirements('phones close to 500 bucks'))[0]['id'],'google-pixel-9a')
 def test_explicit_add_is_persisted_idempotent_and_opens_cart(self):
  r=self.chat('Add two Google Pixel 9a to my cart','same-request')
  self.assertEqual(r['cart'],[{'product_id':'google-pixel-9a','quantity':2}])
  self.assertEqual(r['actions'][0]['type'],'open_cart')
  self.assertEqual(self.chat('Add two Google Pixel 9a to my cart','same-request')['cart'],r['cart'])
  self.assertEqual(self.client.post('/api/session').json()['cart'],r['cart'])
  r=self.chat('show me my cart');self.assertIn('$998',r['reply'])
  r=self.chat('close my cart');self.assertEqual(r['actions'][0]['type'],'close_panels')
  r=self.chat('remove Google Pixel 9a');self.assertEqual(r['cart'],[])
 def test_ambiguous_and_negative_requests_do_not_change_cart(self):
  self.assertEqual(self.chat('add a phone')['cart'],[])
  self.assertEqual(self.chat("don't add Google Pixel 9a")['cart'],[])
  self.assertEqual(self.chat('add six Google Pixel 9a')['cart'],[])
 def test_visible_ordinal_and_named_navigation(self):
  self.client.put('/api/view',json={'product_ids':['sony-wh1000xm5','google-pixel-9a'],'focused_product':'google-pixel-9a'})
  r=self.chat('add the second one');self.assertEqual(r['cart'][0]['product_id'],'google-pixel-9a')
  r=self.chat('show me the Pixel 9a');self.assertEqual(r['focus_product_id'],'google-pixel-9a')
  r=self.chat('next page');self.assertEqual(r['actions'][0]['type'],'navigate_products')
 def test_unknown_view_reference_rejected(self):
  self.assertEqual(self.client.put('/api/view',json={'product_ids':['fake']}).status_code,422)
 def test_joined_spoken_model_name(self):
  result=self.chat('Add Pixel9a to my cart')
  self.assertEqual(result['cart'],[{'product_id':'google-pixel-9a','quantity':1}])
 def test_category_request_immediately_shows_matching_cards(self):
  result=self.chat('Earphones under $150')
  self.assertEqual(result['strategy'],'CUSTOMER_COMMAND')
  self.assertTrue(result['products'])
  self.assertTrue(all(p['category']=='earbuds' and p['price']<=150 for p in result['products']))
  self.assertEqual(result['actions'][0]['type'],'highlight')
 def test_just_show_me_uses_active_category_and_relaxes_stale_budget(self):
  self.chat('Earphones under $150')
  self.chat("No, I'm looking for a big monitor")
  result=self.chat('Now just show me. I would like to see first.')
  self.assertTrue(result['products'])
  self.assertTrue(all(p['category']=='monitors' for p in result['products']))
  self.assertEqual(result['actions'][0]['type'],'highlight')
  self.assertNotIn("can't display",result['reply'].lower())
 def test_explicit_show_with_impossible_budget_displays_honest_alternatives(self):
  result=self.chat('Show me earbuds under $50')
  self.assertTrue(result['products'])
  self.assertTrue(all(p['category']=='earbuds' for p in result['products']))
  self.assertIn('could not find an exact',result['reply'].lower())
 def test_stop_asking_just_show_me_still_controls_the_storefront(self):
  self.chat('I want monitors under $200')
  result=self.chat("Don't ask another question, just show me")
  self.assertTrue(result['products'])
  self.assertEqual(result['actions'][0]['type'],'highlight')
