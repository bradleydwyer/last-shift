# Third-party material

Last Shift's original contributions are licensed under MIT; see `LICENSE`.
Third-party code and resources retain their own terms and are excluded from
that MIT grant.

## SCI Companion SCI 1.1 template

The supporting SCI class library, interface resources, fonts and base resource
containers in `game/` come from Phil Fortier's SCI Companion SCI 1.1 template:

- Source: https://github.com/icefallgames/SCICompanion
- Revision: `f1a603b48b1aa7abf94f78574a8f69a653e2ca62`
- Template directory: `SCICompanion/Files/TemplateGame/SCI1.1`

SCI Companion documents that decompilation of Sierra game code was used as a
base for this template: https://scicompanion.com/Documentation/decompiler.html.
The template includes Sierra-origin material; Last Shift's MIT license does
not relicense that material. Existing author credits remain in the source.

The original DOS interpreter, DOS drivers and unused template audio packs are
excluded from this project and its release archive. ScummVM runs the game.

## SIESTA fanfare instrument samples

The fanfare MIDI composition was created for Last Shift. Its WAV and SCI audio
resource were rendered with FluidSynth using the TimGM6mb SoundFont:

- Copyright 2004 Tim Brechbill and 2010 David Bolton.
- SoundFont license: GNU General Public License, version 2.
- Source: https://github.com/musescore/musescore-old/commit/90c33ef9d87b3f5ff92efd3b07d89eb455fb1fef
- Package: https://sources.debian.org/src/timgm6mb-soundfont/

The SoundFont itself is not bundled. This attribution records the source of
the instrument samples in the rendered fanfare. The GPLv2 text is included in
`LICENSES/GPL-2.0.txt`.

## External build tools and interpreter

These dependencies are installed or downloaded separately and are not bundled
in the release archive:

- SCI Companion by Philip Fortier: GPL-2.0-or-later.
  https://github.com/icefallgames/SCICompanion
- lucasartsifier by Katia Hayati: MIT, except its SCI Companion compiler port
  (`tools/scicompile`), which is GPL-2.0-or-later.
  Revision `45068351290ffd90e74186c69322d200fa60cafd`.
  https://github.com/katiahayati/lucasartsifier
- ScummVM: GNU General Public License. https://www.scummvm.org/
- FluidSynth: GNU Lesser General Public License. https://www.fluidsynth.org/

Their source checkouts and license files remain under the ignored `tools/`
directory or with the separately installed application.

## Original assets and parody

The room art, worker sprites, inventory art and SIESTA logo were generated for
this project with OpenAI image generation. Saved prompts and source images are
in `assets/source/`. Six gameplay sound effects are synthesized by
`scripts/build_assets.py`.

SIESTA is a parody of the old Sierra studio presentation. Last Shift is an
independent three-room AI experiment with no affiliation to Sierra.
