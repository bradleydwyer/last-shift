(version 2)
(include "sci.sh")
(include "game.sh")
(exports 0 StationAction 1 StationIntro 3 StationEnter)
(use "Main")
(use "Game")
(use "Actor")
(use "Print")
(use "Sound")
(use "System")
(use "Cycle")
(use "PolyPath")
(use "Controls")
(script 113)
(local destination = 0 exitSide = 0 entranceSide = 0 doorwayX = 0 doorwayY = 163 entryY = 163 toolboxActor = 0
    pendingRoom = 0 pendingTarget = 0 pendingVerb = 0 pendingToolbox = 0 pendingX = 0 pendingY = 0 pendingHeading = 0)

// Physical use reaches its target before either an action or a refusal.
(instance approachInteraction of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath pendingX pendingY self))
            )
            (case 1
                (send gEgo:setHeading(pendingHeading))
                (send gGame:handsOn())
                (self:dispose())
                StationAction(pendingRoom pendingTarget pendingVerb pendingToolbox)
            )
        )
    )
)

(procedure (DoorAction nextRoom side verb description)
    (switch verb
        (case V_WALK StationExit(nextRoom side))
        (case V_LOOK Say(description))
        (case V_DO Say("You pat the frame. The doorway remains unimpressed."))
        (case V_TALK Say("You ask the doorway for directions. It remains open to interpretation."))
        (case V_WRENCH Say("You threaten the doorway with a wrench. It wisely continues doing nothing."))
        (default Say("The doorway declines your offer. Apparently it has everything it needs."))
    )
)

// Align on the room floor, then cross every doorway horizontally without input.
(procedure (StationExit nextRoom side)
    (= destination nextRoom)
    (= exitSide side)
    (= doorwayX (if (side) 316)(else 18))
    // The workshop's right bench requires a lower crossing lane.
    (= doorwayY (if ((== gRoomNumber 111) and (side)) 178)(else 163))
    (send gRoom:setScript(exitWalk))
)
(instance exitWalk of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath
                    (if (exitSide) (if (== gRoomNumber 111) 276)(else 252))(else 64)
                    doorwayY self))
            )
            (case 1
                (send gEgo:setMotion(MoveTo doorwayX doorwayY self))
            )
            (case 2 (send gRoom:newRoom(destination)))
        )
    )
)
(procedure public (StationEnter room)
    (if (((== room 110) and (== gPreviousRoomNumber 111)) or
            ((== room 111) and (== gPreviousRoomNumber 112)))
        (= entranceSide 1)
        (= entryY (if (== room 111) 178)(else 163))
        (send gEgo:posn(316 entryY))
        (send gRoom:setScript(entryWalk))
    )(else
        (if (((== room 111) and (== gPreviousRoomNumber 110)) or
                ((== room 112) and (== gPreviousRoomNumber 111)))
            (= entranceSide 0)
            (= entryY 163)
            (send gEgo:posn(18 entryY))
            (send gRoom:setScript(entryWalk))
        )
    )
)
(instance entryWalk of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(MoveTo
                    (if (entranceSide) (if (== gRoomNumber 111) 276)(else 252))(else 64)
                    entryY self))
            )
            (case 1
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)

// A single room-owned sequence keeps input locked until the wrench is collected.
(instance takeWrench of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 133 158 self))
            )
            (case 1
                (send gEgo:setCycle(0) loop(0) cel(0))
                (send toolboxActor:cel(0) cycleSpeed(12) setCycle(EndLoop self))
            )
            (case 2
                (send gEgo:setCycle(0) view(903) loop(0) cel(0))
                (= ticks 30)
            )
            (case 3
                (if (not (send gEgo:has(INV_WRENCH)))
                    (send gEgo:get(INV_WRENCH))
                    AddToScore(10)
                    Chime(301)
                )
                (send gEgo:view(0) loop(0) cel(0) setCycle(Walk))
                Say("You open the toolbox and take the maintenance wrench. Finally, a tool qualified to work here.")
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)

// The clerk does not deliver cards across the room: approach its counter first.
(instance useKiosk of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 74 178 self))
            )
            (case 1
                (send gEgo:setCycle(0) view(0) loop(1) cel(1))
                (= ticks 24)
            )
            (case 2
                (if (Btest(F_CARD_ISSUED))
                    Say("CLERK: One emergency transit card per emergency. Please begin a separate emergency for further assistance.")
                )(else
                    (if (Btest(F_POWER))
                        (send gEgo:get(INV_CARD))
                        Bset(F_CARD_ISSUED)
                        AddToScore(10)
                        Chime(301)
                        Say("The kiosk spits out an emergency transit card. CLERK: Please rate your evacuation experience after landing.")
                    )(else Say("CLERK: Auxiliary power offline. Your emergency has been placed in a queue behind the emergency powering this queue."))
                )
                (send gEgo:view(0) loop(1) cel(1) setCycle(Walk))
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)


// Workshop tasks complete only after approaching and visibly handling the object.
(instance takeCell of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 239 174 self))
            )
            (case 1
                (send gEgo:setCycle(0) view(0) loop(0) cel(0))
                (= ticks 10)
            )
            (case 2
                (send gEgo:view(903) loop(0) cel(0))
                (= ticks 24)
            )
            (case 3
                Bset(F_CELL_TAKEN)
                (send gEgo:get(INV_CELL))
                AddToScore(10)
                Chime(301)
                (send gEgo:view(0) loop(0) cel(0) setCycle(Walk))
                Say("You take the charged cell. Its warranty excludes use in emergencies, naturally.")
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)
(instance tightenCoupling of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 135 148 self))
            )
            (case 1
                (send gEgo:setCycle(0) view(903) loop(0) cel(0))
                (= ticks 16)
            )
            (case 2
                (send gEgo:view(0) loop(0) cel(0))
                (= ticks 10)
            )
            (case 3
                (send gEgo:view(903) loop(0) cel(0))
                (= ticks 16)
            )
            (case 4
                (send gEgo:view(0) loop(0) cel(0))
                (= ticks 10)
            )
            (case 5
                (send gEgo:view(903) loop(0) cel(0))
                (= ticks 16)
            )
            (case 6
                Bset(F_REPAIRED)
                AddToScore(10)
                Chime(301)
                (send gEgo:view(0) loop(0) cel(0) setCycle(Walk))
                Say("You tighten the coupling. The generator now requires a power cell, rather than a miracle.")
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)
(instance fitPowerCell of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 135 148 self))
            )
            (case 1
                (send gEgo:setCycle(0) view(903) loop(0) cel(0))
                (= ticks 24)
            )
            (case 2
                (send gEgo:view(0) loop(0) cel(0))
                (= ticks 10)
            )
            (case 3
                (send gEgo:view(903) loop(0) cel(0))
                (= ticks 24)
            )
            (case 4
                (send gEgo:put(INV_CELL))
                Bset(F_POWER)
                AddToScore(10)
                Chime(302)
                (send gEgo:view(0) loop(0) cel(0) setCycle(Walk))
                Say("The power cell locks into place. The generator wakes up. Reception can now issue your transit card. The exposed coupling is LIVE: keep your bare hands away.")
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)

// The live coupling is safe to inspect but lethal to touch after power is restored.
(instance generatorDeath of Script
    (properties)
    (method (changeState newState)
        (var choice)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 160 148 self))
            )
            (case 1
                Chime(304)
                (send gEgo:setCycle(0) view(903) loop(0) cel(0) cycleSpeed(18) setCycle(EndLoop self))
            )
            (case 2 (= seconds 1))
            (case 3
                EndShift("You touched the live generator coupling. Your final performance review: outstanding conductivity." FALSE)
            )
        )
    )
)

// Charged cells and blunt instruments are an exceptionally final combination.
(instance cellExplosion of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(0) setCycle(0) view(903) loop(0) cel(0))
                (= ticks 18)
            )
            (case 1
                Chime(305)
                (cellBurst:posn(273 138) init() cycleSpeed(5) setCycle(EndLoop self))
            )
            (case 2
                (cellBurst:dispose())
                (send gRoom:drawPic(113 100))
                (send gEgo:view(903) loop(0) cel(0) cycleSpeed(10) setCycle(EndLoop self))
            )
            (case 3
                (bodySmoke:posn(239 174) init() cycleSpeed(12) setCycle(Forward))
                (= seconds 1)
            )
            (case 4
                EndShift("You hit the power cell with a wrench. For one glorious instant, you are the brightest employee on the station." TRUE)
            )
        )
    )
)
(instance cellBurst of Prop
    (properties view 913 loop 0 cel 0 x 273 y 138 priority 14 signal $4000)
    (method (onMe event) return 0)
)
(instance bodySmoke of Prop
    (properties view 913 loop 1 cel 0 x 239 y 174 priority 14 signal $4000)
    (method (onMe event) return 0)
)
// A modal Print normally pauses the cast. Its invisible dialog control keeps
// only the corpse smoke cycling, including while Restart/Restore is displayed.
(instance smokeDialogTicker of DText
    (properties text 0)
    (method (setSize)
        (= nsRight (+ nsLeft 1))
        (= nsBottom (+ nsTop 1))
    )
    (method (init))
    (method (cycle)
        (bodySmoke:doit())
        Animate((send gCast:elements) 0)
    )
)
(procedure (EndShift message animateSmoke)
    (var choice)
    (send gGame:setCursor(999 1))
    (= choice 0)
    (while (<> choice 1)
        (Print:posn(24 18) addTitle("LAST SHIFT - SHIFT TERMINATED") width(260)
            addText(message)
            addButton(1 "Restart" 25 40)
            addButton(2 "Restore" 155 40))
        (if (animateSmoke)
            (Print:addIcon((smokeDialogTicker:new()) 0 0 0 0))
        )
        (= choice (Print:init()))
        (if (== choice 2) (send gGame:restore()))
    )
    RestartGame()
)

(instance stationEffect of Sound
    (properties priority 15)
)
(procedure (Chime number)
    (send gMusic1:stop())
    (stationEffect:stop())
    (stationEffect:number(number) loop(1) vol(90) play())
)
(procedure (Say text)
    (Print:addTitle("LAST SHIFT") width(260) addText(text) init())
)
// Keep the cabin occupant visible beneath boarding and departure responses.
(procedure (SayAboard text)
    (Print:posn(24 18) addTitle("LAST SHIFT") width(260) addText(text) init())
)
(procedure public (StationIntro)
    Say("Your shift ended six hours ago. Unfortunately, the station's evacuation system is on its lunch break. Repair the generator, get a transit card, and leave.")
)
// Boarding is physical even when the launch interlock rejects the attempt.
// MoveTo takes over on the ramp, beyond the room's ordinary walkable floor.
(instance podBoarding of Script
    (properties)
    (method (changeState newState)
        (switch (= state newState)
            (case 0
                (send gGame:handsOff())
                (send gEgo:setMotion(PolyPath 206 174 self))
            )
            (case 1 (send gEgo:setMotion(MoveTo 223 145 self)))
            (case 2 (send gEgo:setMotion(MoveTo 239 126 self)))
            (case 3
                (send gEgo:posn(233 126) show() setCycle(0) view(912) loop(1) cel(0))
                (= ticks 18)
            )
            (case 4
                (if (Btest(F_LAUNCH_READY))
                    Bset(F_ESCAPED)
                    AddToScore(10)
                    (send gMusic1:stop())
                    Chime(303)
                    SayAboard("You climb aboard. The pod departs, leaving the station and its performance reviews behind. You are free.")
                    SayAboard("LAST SHIFT COMPLETE - 60 / 60. Your reward: dinner, sleep, and never finding out what the red button did. Thanks for playing.")
                    (send gGame:handsOn())
                    (self:dispose())
                )(else
                    SayAboard("You climb into the pod. Its launch interlock rejects your departure. The console apparently has opinions about who gets to leave.")
                    (send gEgo:view(0) loop(1) cel(0) show() setCycle(Walk) setMotion(MoveTo 223 145 self))
                )
            )
            (case 5 (send gEgo:setMotion(MoveTo 206 174 self)))
            (case 6
                (send gGame:handsOn())
                (self:dispose())
            )
        )
    )
)

(procedure public (StationAction room target verb toolbox)
    (if (Btest(F_ESCAPED))
        Say("You have escaped. A hot meal and a very long incident report await. Thanks for playing LAST SHIFT.")
        return
    )
    (if ((<> verb V_WALK) and (<> verb V_LOOK) and (<> verb V_TALK) and
        (((== room 110) and (IsOneOf(target 1 2))) or
         ((== room 111) and (IsOneOf(target 2 3))) or
         ((== room 112) and (IsOneOf(target 2 3)))))
        (= pendingRoom room)
        (= pendingTarget target)
        (= pendingVerb verb)
        (= pendingToolbox (if (>= paramTotal 4) toolbox)(else 0))
        (= pendingHeading 0)
        (switch room
            (case 110
                (= pendingX (if (== target 1) 74)(else 133))
                (= pendingY (if (== target 1) 178)(else 158))
                (if (== target 1) (= pendingHeading 270))
            )
            (case 111
                (= pendingX (if (== target 2) 135)(else 239))
                (= pendingY (if (== target 2) 148)(else 174))
            )
            (case 112
                (= pendingX (if (== target 2) 75)(else 206))
                (= pendingY (if (== target 2) 168)(else 174))
                (if (== target 2) (= pendingHeading 270))
            )
        )
        (if (> Max(Abs((- (send gEgo:x) pendingX)) Abs((- (send gEgo:y) pendingY))) 3)
            (send gRoom:setScript(approachInteraction))
            return
        )
    )
    (if (== room 110)
        (switch target
            (case 1
                (switch verb
                    (case V_LOOK Say("Reception's automated clerk. Its smile is entirely a licensing arrangement."))
                    (case V_TALK Say("CLERK: Your call is important to us. This conversation may be recorded for training and denial purposes."))
                    (case V_DO
                        (send gRoom:setScript(useKiosk))
                    )
                    (case V_WRENCH Say("The clerk scans your wrench. CLERK: Threats are processed in the order received."))
                    (default Say("The clerk examines your offering with the enthusiasm of a vending machine presented with a CV."))
                )
            )
            (case 2
                (if (== verb V_LOOK)
                    Say("A yellow toolbox. The one thing management didn't outsource.")
                )(else
                    (if (== verb V_DO)
                        (if (send gEgo:has(INV_WRENCH))
                            Say("You already took the wrench. The toolbox is considering a career as a lunchbox.")
                        )(else
                            (= toolboxActor toolbox)
                            (send gRoom:setScript(takeWrench))
                        )
                    )(else Say("The toolbox has nothing to add. Refreshing, for something associated with work."))
                )
            )
            (case 3
                DoorAction(111 1 verb "The workshop. It smells of hot metal and postponed maintenance.")
            )
            (case 4 Say("A planet. Somewhere down there, people finish work and simply go home."))
            (default Say("Reception has the comforting atmosphere of a waiting room where nobody intends to call your name."))
        )
        return
    )
    (if (== room 111)
        (switch target
            (case 1
                DoorAction(110 0 verb "Reception waits beyond the doorway. It has made an entire profession of waiting.")
            )
            (case 2
                (switch verb
                    (case V_LOOK
                        (if (Btest(F_POWER)) Say("The generator hums. Reception and launch controls have power. DANGER: the exposed coupling is now live. Touching it with your bare hand would be fatal."))
                        (else
                            (if (Btest(F_REPAIRED)) Say("The coupling is tight. The empty power-cell socket remains an impressive achievement in doing nothing."))
                            (else Say("A loose coupling rattles beside an empty power-cell socket. The maintenance log calls this FULLY SERVICED."))
                        )
                    )
                    (case V_WRENCH
                        (if (send gEgo:has(INV_WRENCH))
                            (if (Btest(F_REPAIRED)) Say("The coupling is already tight. You resist improving it into several smaller pieces."))
                            (else
                                (send gRoom:setScript(tightenCoupling))
                            )
                        )(else Say("Your imaginary wrench has excellent reach but disappointing torque."))
                    )
                    (case V_CELL
                        (if (Btest(F_POWER)) Say("One cell is quite enough. The generator is not accepting emotional support batteries."))
                        (else
                            (if (not Btest(F_REPAIRED)) Say("The loose coupling would shake the cell into expensive confetti. Perhaps give it fewer moving parts first."))
                            (else
                                (if (send gEgo:has(INV_CELL))
                                    (send gRoom:setScript(fitPowerCell))
                                )(else Say("You attempt to install a cell you are not carrying. Procurement would admire the savings."))
                            )
                        )
                    )
                    (case V_DO
                        (if (Btest(F_POWER)) (send gRoom:setScript(generatorDeath)))
                        (else Say("You consider repairing the coupling with your fingers. Your fingers would prefer a wrench."))
                    )
                    (default Say("You ask the generator about its career ambitions. It keeps its options, and its casing, open."))
                )
            )
            (case 3
                (switch verb
                    (case V_LOOK
                        (if (Btest(F_CELL_TAKEN)) Say("A workbench with a power-cell-shaped clean patch."))
                        (else Say("A charged power cell sits on the bench. It has more energy than you and considerably fewer responsibilities."))
                    )
                    (case V_DO
                        (if (Btest(F_CELL_TAKEN)) Say("You already took the cell. The clean patch is available, if you can find a way to carry it."))
                        (else (send gRoom:setScript(takeCell)))
                    )
                    (case V_WRENCH
                        (if (Btest(F_CELL_TAKEN))
                            Say("You threaten the empty bench with a wrench. It wisely keeps its charge to itself.")
                        )(else
                            (if (send gEgo:has(INV_WRENCH))
                                (send gRoom:setScript(cellExplosion))
                            )(else Say("You mime hitting the battery with an imaginary wrench. For once, lack of equipment is a safety feature."))
                        )
                    )
                    (default Say("You deliver a short speech on work-life balance. Nothing on the bench argues. You count this as progress."))
                )
            )
            (case 4
                DoorAction(112 1 verb "The escape pod bay. The word escape has seldom sounded so professional.")
            )
            (default Say("The workshop smells of hot metal and repair jobs filed under SOMEBODY ELSE. You appear to be somebody else."))
        )
        return
    )
    (switch target
        (case 1
            DoorAction(111 0 verb "The workshop doorway. Your entire repair career lies behind it.")
        )
        (case 2
            (switch verb
                (case V_LOOK Say("Launch console. The card reader is labelled AUTHORISED ESCAPING ONLY."))
                (case V_CARD
                    (if (not Btest(F_POWER)) Say("The console is dark. Apparently even fleeing for your life requires electricity."))
                    (else
                        (if (send gEgo:has(INV_CARD))
                            (if (Btest(F_LAUNCH_READY)) Say("Your departure is authorised. The console would like you to actually depart now."))
                            (else
                                Bset(F_LAUNCH_READY)
                                Chime(301)
                                Say("The card is accepted. Launch authorised. The hatch is open. Your departure has finally become somebody else's problem.")
                            )
                        )(else Say("The reader waits for a transit card. Your library privileges are unlikely to impress it."))
                    )
                )
                (case V_DO
                    (if (Btest(F_LAUNCH_READY)) Say("Launch is authorised. Further button pressing will only delay the best part of your shift."))
                    (else Say("The transit-card slot ignores your fingers. A promising sign for station security."))
                )
                (default Say("You tell the console you have had a very long day. It asks whether you have had a very long day with a transit card."))
            )
        )
        (case 3
            (if (== verb V_LOOK) Say("One escape pod, one seat, no onboard meetings. Almost suspiciously luxurious."))
            (else
                (if (== verb V_DO)
                    (send gRoom:setScript(podBoarding))
                )(else Say("The pod is an excellent listener, but an indifferent conversationalist."))
            )
        )
        (case 4
            (if (== verb V_DO)
                Say("You try to touch the stars. You leave a fingerprint. Astronomers are unlikely to name it after you.")
            )(else Say("The stars are beautiful. None of them has ever asked you to stay late."))
        )
        (default Say("An escape pod. Somewhere, an accountant is wondering whether evacuation counts as a personal trip."))
    )
)
