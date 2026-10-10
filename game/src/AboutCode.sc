// Displays a message in response to a call to :func:`showAbout`.
(version 2)
(include "sci.sh")
(include "game.sh")
(include "13.shm")
(exports
    0 aboutCode
)
(use "Main")
(use "Print")
(use "System")
(script ABOUT_SCRIPT)



(instance public aboutCode of Code
    (properties)
    (method (doit)
        Prints("LAST SHIFT v1.3. Original three-room SCI adventure. Built with SCI Companion and ScummVM. SCI template library by Phil Fortier. Original artwork generated with OpenAI; original sprite and audio assets built for this game.")
    )

)
