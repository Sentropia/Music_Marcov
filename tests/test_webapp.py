from io import BytesIO
import unittest

import pretty_midi

from webapp import app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_and_healthcheck(self):
        index_response = self.client.get("/")
        health_response = self.client.get("/healthz")

        self.assertEqual(index_response.status_code, 200)
        self.assertIn(b"Markov Music", index_response.data)
        self.assertEqual(health_response.get_json(), {"status": "ok"})

    def test_generate_returns_downloadable_midi(self):
        response = self.client.post("/api/generate", json={"order": 5})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/midi")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        midi = pretty_midi.PrettyMIDI(BytesIO(response.data))
        self.assertEqual(sum(len(item.notes) for item in midi.instruments), 240)

    def test_generate_rejects_invalid_order(self):
        response = self.client.post("/api/generate", json={"order": 11})
        self.assertEqual(response.status_code, 400)
        self.assertIn("between 3 and 9", response.get_json()["error"])

    def test_generate_requires_a_json_object(self):
        for kwargs in ({}, {"json": [5]}, {"data": "not json"}):
            with self.subTest(kwargs=kwargs):
                response = self.client.post("/api/generate", **kwargs)
                self.assertEqual(response.status_code, 400)
                self.assertIn("JSON object", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
