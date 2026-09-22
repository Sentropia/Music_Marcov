# Third-party runtime assets

The Render container installs Ubuntu's `fluid-soundfont-gm` package, which
provides `FluidR3_GM.sf2` for FluidSynth at runtime. The package is distributed
by Ubuntu as a freely redistributable SoundFont; its package copyright and
license notices are installed in the image under
`/usr/share/doc/fluid-soundfont-gm/copyright`.

No SoundFont binary is committed to this repository. The application uses that
runtime-provided piano SoundFont only to render its generated MIDI in memory.
