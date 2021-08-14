json_str = original_obj.json_encode()
decoded_obj = self.json_decode(json_str)
self.assertEqual(original_obj, decoded_obj)
self.assertNotEqual(id(original_obj), id(decoded_obj))