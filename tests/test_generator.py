from io import BytesIO
import random
import unittest

import pretty_midi

import music_generator


class MusicGeneratorTests(unittest.TestCase):
    def test_validate_order_accepts_supported_range(self):
        self.assertEqual(music_generator.validate_order("5"), 5)
        for invalid_order in (None, True, 2, 5.5, 10, "five"):
            with self.assertRaises(ValueError):
                music_generator.validate_order(invalid_order)

    def test_generate_midi_bytes_contains_expected_notes_and_tempo(self):
        midi_data = music_generator.generate_midi_bytes(5, seed=1234)
        midi = pretty_midi.PrettyMIDI(BytesIO(midi_data))
        note_count = sum(len(instrument.notes) for instrument in midi.instruments)
        tempi = midi.get_tempo_changes()[1]

        self.assertEqual(note_count, music_generator.NUMBER_OF_STATES)
        self.assertAlmostEqual(float(tempi[0]), music_generator.TEMPO_BPM, places=2)

    def test_seed_makes_generation_reproducible(self):
        self.assertEqual(
            music_generator.generate_midi_bytes(5, seed=99),
            music_generator.generate_midi_bytes(5, seed=99),
        )


if __name__ == "__main__":
    unittest.main()
