import unittest
from sales_agent.catalog import PRODUCTS, requirements, retrieve


class CatalogExpansionTests(unittest.TestCase):
    def test_new_departments_are_searchable_with_budget(self):
        for query, category in [('phone under 500','phones'), ('tablet under 500','tablets'),
                                ('monitor under 800','monitors'), ('camera under 700','cameras'),
                                ('speaker under 200','speakers'), ('laptop under 1200','laptops')]:
            with self.subTest(query=query):
                req=requirements(query)
                results=retrieve(req)
                self.assertTrue(results)
                self.assertTrue(all(p['category']==category and p['price']<=req['budget'] for p in results))

    def test_catalog_has_distinct_items_and_useful_facts(self):
        self.assertEqual(len({p['id'] for p in PRODUCTS}),len(PRODUCTS))
        self.assertGreaterEqual(len(PRODUCTS),24)
        for p in PRODUCTS:
            self.assertTrue(p['description'] and p['tradeoff'] and p['specs'])
            self.assertGreater(p['price'],0)
            self.assertTrue(p['source_url'].startswith('https://'))
            self.assertEqual(p['stock_source'],'local_demo')
