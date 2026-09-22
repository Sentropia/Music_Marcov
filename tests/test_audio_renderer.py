from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

import music_generator


class _Samples:
    def tobytes(self):
        return b"\x00\x00\x00\x00"


class _Synth:
    def __init__(self, **_kwargs):
        self.deleted = False

    def sfload(self, _path):
        return 1

    def program_select(self, *_args):
        return 0

    def noteon(self, *_args):
        return None

    def noteoff(self, *_args):
        return None

    def get_samples(self, _count):
        return _Samples()

    def delete(self):
        self.deleted = True


class _Encoder:
    def set_bit_rate(self, _value): pass
    def set_in_sample_rate(self, _value): pass
    def set_channels(self, _value): pass
    def set_quality(self, _value): pass
    def encode(self, _pcm): return b"ID3encoded"
    def flush(self): return b""


class AudioRendererTests(unittest.TestCase):
    def test_renderer_encodes_generated_midi_without_temp_files(self):
        fake_modules = {
            "fluidsynth": SimpleNamespace(Synth=_Synth),
            "lameenc": SimpleNamespace(Encoder=_Encoder),
        }
        with tempfile.NamedTemporaryFile() as soundfont, \
             patch.dict(sys.modules, fake_modules), \
             patch.object(music_generator, "soundfont_path", return_value=Path(soundfont.name)):
            mp3_data = music_generator.midi_to_mp3_bytes(music_generator.generate_midi(5, seed=8))

        self.assertTrue(mp3_data.startswith(b"ID3"))


if __name__ == "__main__":
    unittest.main()
