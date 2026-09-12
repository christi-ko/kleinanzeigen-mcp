import json
import unittest
from unittest.mock import patch

import server


class WebAttributeTests(unittest.TestCase):
    def test_attribute_mapping_uses_arbitrary_category_specific_names(self):
        params = server.web_search_params(
            category="217",
            location="Amtzell",
            radius_km=5,
            max_price=1800,
            query="",
            attributes={
                "fahrraeder.type_s": "rennrad",
                "pc_zubehoer_software.art_s": ["speicher", "ssd"],
            },
        )
        self.assertEqual(params["categoryId"], "217")
        self.assertEqual(params["attributeMap[fahrraeder.type_s]"], "rennrad")
        self.assertEqual(params["attributeMap[pc_zubehoer_software.art_s]"], ["speicher", "ssd"])
        self.assertNotIn("query", params)
        self.assertNotIn("keywords", params)

    def test_web_listing_parser_extracts_listing_without_silent_empty_result(self):
        html = '''
        <html><script type="application/ld+json">
        {"title":"Test Rennrad","description":"Ein Rad","offers":{"price":"799"}}
        </script>
        <article data-adid="1234567890" data-href="/s-anzeige/test/1234567890-217-1">
        <span>Test Rennrad</span><span>799 €</span>
        </article></html>
        '''
        rows = server.parse_web_listings(html, "https://www.kleinanzeigen.de")
        self.assertEqual(rows[0]["id"], "1234567890")
        self.assertEqual(rows[0]["title"], "Test Rennrad")

    @patch.object(server, "fetch_web_search")
    def test_attributes_use_web_path_and_preserve_empty_query(self, fetch):
        fetch.return_value = {"query": "", "count": 1, "listings": [{"id": "1"}]}
        result = server.search({
            "category": "217", "radius_km": 5, "max_price": 1800,
            "attributes": {"fahrraeder.type_s": "rennrad"},
        })
        fetch.assert_called_once()
        self.assertEqual(fetch.call_args.args[0]["attributeMap[fahrraeder.type_s]"], "rennrad")
        self.assertEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
