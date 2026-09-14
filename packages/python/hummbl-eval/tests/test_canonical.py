import json
import unittest

from hummbl_eval.canonical import CanonicalizationError, canonicalize_json, digest_bytes, load_json


class CanonicalizationTests(unittest.TestCase):
    def test_sorts_objects_recursively_and_preserves_array_order(self) -> None:
        value = {"z": [{"b": 2, "a": 1}, 3], "a": "é"}
        self.assertEqual(
            canonicalize_json(value),
            '{"a":"é","z":[{"a":1,"b":2},3]}'.encode(),
        )

    def test_rejects_float_and_unsafe_integer(self) -> None:
        for value in (1.5, 2**53):
            with self.subTest(value=value), self.assertRaises(CanonicalizationError):
                canonicalize_json({"value": value})

    def test_rejects_duplicate_keys_and_invalid_unicode(self) -> None:
        with self.assertRaises(CanonicalizationError):
            load_json('{"a":1,"a":2}')
        with self.assertRaises(CanonicalizationError):
            canonicalize_json({"bad": "\ud800"})

    def test_rejects_non_json_types_keys_and_constants(self) -> None:
        for value in ({1: "bad-key"}, {"bytes": b"no"}):
            with self.subTest(value=value), self.assertRaises(CanonicalizationError):
                canonicalize_json(value)
        for text in ("not json", '{"number":NaN}'):
            with self.subTest(text=text), self.assertRaises(CanonicalizationError):
                load_json(text)

    def test_digest_is_content_address(self) -> None:
        self.assertEqual(
            digest_bytes(b"abc"),
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_round_trip_is_stable(self) -> None:
        encoded = canonicalize_json({"b": True, "a": None})
        self.assertEqual(canonicalize_json(json.loads(encoded)), encoded)


if __name__ == "__main__":
    unittest.main()
