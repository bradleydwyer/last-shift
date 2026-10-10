# Validation — Last Shift 1.4

Completed 8 October 2026.

Revision 1.4 startup checks:

- Added an eight-second SIESTA studio presentation in startup script 120, with six gold emblem pictures and original digital fanfare resource 306. Distribution contains 243 native resources and seven digital sounds; resource volume is 628,988 bytes.
- Natural completion, an early keyboard skip and a late mouse skip each restored reception's palette and controls. Each path completed a wrench pickup and rendered the correct 10/60 score. Result is recorded in siesta-results.json.
- After the mouse-skip path, wrench use on the bench cell completed the blast death sequence. Restart returned reception at 0/60 within two seconds, bypassing the eight-second logo. Evidence: siesta-restart-death.png and siesta-restarted.png.
- PCM mixer captures contain the startup music and the station hum after the presentation. No SCI errors, overlapping-sample errors or unsupported transition warnings were logged. The build was also launched in native macOS ScummVM and reached reception.
- Emblem art was generated with built-in imagegen and its exact prompt is saved beside the source sheet. The included MIDI and WAV are an original composition. SQ4 reference files remain outside the project.

Evidence: siesta-complete-upright.png, siesta-sleeping.png, siesta-keyboard-skip-wrench.png, siesta-mouse-skip-wrench.png and siesta-native-reception.png.

Previous gameplay validation, revision 1.3:

- All modified sources compiled to SCI 1.1 bytecode and heap resources. Distribution contains 235 native resources and six digital sounds. Resource volume is 534,660 bytes.
- Painted worker uses eight walking phases in eight heading loops, a consistent 76-pixel base body, and native perspective scaling from 90% to 125%. Worker and interaction VIEW resources are marked scalable. Back and foreground screenshots verify the size change in ScummVM.
- Chest pickup opens the lid before awarding the wrench. Cell pickup removes the painted cell from the bench. Generator repair and insertion animate working poses before awarding progress.
- Power restoration starts a small pulsing glow animation and the generator startup sound resource. The stationary socket replaces the spinning turbine. New captures verify brightness changes within the socket.
- Door jambs use fixed foreground priority. A walk-icon click on the workshop's right floor threshold enters the pod bay.
- Matching painted inventory icons replace the older symbolic artwork. No-outcome interaction text uses dry humour with fewer explicit hints. The introduction no longer displays the controls popup.
- Touching the powered generator produces the electrical shock/collapse sequence. The death dialog shows an arrow cursor, and Restore recovers a 40/60 save with working player controls. Restart was checked in the previous revision.
- Full mouse playthrough checks room colours, score glyphs, inventory use, failed puzzle actions, transitions and the 60/60 ending. Detailed result is recorded in playthrough-results.json.
- This revision's gameplay checks use isolated Linux ScummVM. The latest build was launched in native macOS ScummVM at the introduction for user testing.
- The isolated display has no audio device, so sound playback was not audibly assessed there. Native SOL resources are encoded; existing non-death sounds previously passed PCM mixer capture.

Evidence: perspective-back.png, perspective-front.png, generator-glow-a.png, generator-glow-b.png, craft-returned-to-floor.png, exit-floor-result.png, and final playthrough screenshots.

Additional revision 1.3 checks:

- Furniture contours replace the broad rectangular floor areas. Reception back-wall clicks resolve to the floor in front of the bench; its patch and chest no longer obscure the actor.
- Only the near jamb of each door is masked down to its floor contact; the far jamb remains behind the actor. Every doorway exit and entry now crosses horizontally.
- Walker uses three-pixel increments at a two-tick delay and distance-based eight-phase cycling, with a stationary passing pose. The final integrated playthrough reached 60/60, including both directions between all adjoining rooms.
- One inventory visit switched wrench/cell four times; the final cell was used on the generator and rejected before repair, proving selection changed without closing.
- Personal paths removed from project-owned prompts, snapshot JSON, and local configs. Launcher changes working directory and stores relative game/save paths. Release ZIP excludes private diagnostics and saves.

- Kiosk hand use approaches the counter before responding. Craft hand use walks into the cabin before responding and returns to the floor on a failed departure; successful boarding reaches the 60/60 ending.
- Runtime resource snapshots remain unchanged while playing; further builds cannot invalidate an open game’s resource offsets.

- Movement now consumes elapsed SCI ticks, with a bounded catch-up after slow updates. Full playthrough passed with this timing change and the seated cabin sprite. Boarding text is positioned above the visible occupant.
- A fresh fixed-copy session opened the death dialog without the missing-script error; Restore loaded a freshly saved 40/60 game and returned control.

- Half-speed movement, physical interaction approaches, right-facing seated occupant and Walk-only doorway transitions passed the complete 60/60 playthrough. Wrench use on the reception door leaves both character position and room unchanged.

- Wrench use on the power cell while it remains on the workshop bench triggers the blast and collapse sequence, changes to the damaged workshop picture, and starts smoke above the body. Two death-dialog captures differ within the smoke plume, verifying continued animation while the message is open. Restore returned the clean workshop at 10/60 with working movement; a repeat blast followed by Restart returned clean reception at 0/60. No SCI errors were logged. Evidence: cell-blast-death-a.png, cell-blast-death-b.png, cell-blast-restored.png, cell-blast-restarted.png.

- Pod-bay window Hand response now jokes about leaving a fingerprint; Look keeps its existing stars response. SCI sources compiled successfully after this dialogue change.

- Clerk wrench use has its own response. Removed the unsupported accented word from the generic offering response. Scan of SCI source files found no remaining non-ASCII characters; modified sources compiled successfully.

- Inventory cursors now use dedicated VIEW resources with cel offsets matching their visible click points: wrench head (6,4), cell/card centre (15,12). Inventory art retains its original offsets. Cell bench target expanded to x250..298/y90..130. A fresh isolated session selected the wrench and clicked (279,127), below the previous target boundary, then approached the bench and completed the blast/death dialog without SCI errors. Evidence: cursor-fixed-bench-target.png and cursor-fixed-blast.png.
