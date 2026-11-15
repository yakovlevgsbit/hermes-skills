---
name: embedded-hardware-builds
description: "Use when building firmware for a physical device."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [embedded, firmware, arduino, esp32, stepper, drivers, wiring, bom, schematics, hardware, kinematics]
    related_skills: [audit-tool-validation, systematic-debugging, hermes-agent]
---

# Embedded / Hardware Builds

The user asks for a physical device — a robot, a motion rig, a controller. The
agent cannot solder, so the deliverable splits in two: **everything that can be
proven without hardware, proven**, and **the rest documented precisely enough
that assembly is mechanical**. Do not let the second half become hand-waving.

## When to Use

- Firmware for a microcontroller driving motors, servos, sensors, relays.
- A bill of materials, wiring guide, or build order for a device.
- Any request to "build a thing" that ends in physical assembly.

## The split that makes this tractable

Do this in order. The software half is fully testable with zero parts, so it
runs first and it de-risks the purchase.

1. **Ask what hardware they already own, before writing a BOM.** A board on the
   desk changes the target and the price. Never assume.
2. **Pick the architecture and say why**, with the rejected option and its
   cost. A two-option table with a stated winner beats prose.
3. **Build and test the host-side half**: kinematics, motion planning, the
   protocol, a simulator that plays the real workload end to end.
4. **Write the firmware**, then **compile it for the target** — compiling is the
   only firmware check available without a board, and it catches real errors.
5. **Generate the CAD** if there are printed parts; export and validate the
   files rather than shipping unopened sources.
6. **Generate the schematics from code** (see below).
7. **Write the BOM, wiring, and build order** last, when the design is settled.

## Firmware rules

- **One source, all targets.** Put board-specific pin maps and setup behind
  `#if defined(<BOARD>)` in a single file. Two forked copies of firmware drift,
  and the part that drifts is the pin map or the kinematics constant — the two
  things you cannot afford to have wrong.
- **Compile every supported target as part of the build, not by hand.** Add a
  make target per board and a `dist` target that runs them all. A target that
  is not compiled in CI is already broken.
- **Never `configure()` an option the library manages itself.** Some libraries
  reject self-managed options with an error and require passing them to the call
  that uses them. Read the error; do not catch it. A swallowed exception turns
  the setting into a silent no-op.
- **Refuse motion while an actuator is engaged.** A firmware-level interlock that
  prints an error and returns (rather than moving) is the cheapest way to prevent
  the failure that destroys the machine's state. Name the failure mode in the
  comment.
- **Keep blocking moves when the workload is discrete.** A general look-ahead
  planner is for continuous paths. A machine that stops between operations does
  not need one, and a blocking move keeps actuator state unambiguous.
- **Print the board identity in the boot banner** (`board: ESP32`). It is how you
  confirm you flashed the target you thought you did.
- **The host and the firmware must share every constant that couples them.**
  Steps per unit appears in both; put a comment at each site pointing at the
  other. Change one without the other and every move lands short by a factor,
  with no error anywhere.

## Pin maps: read the board's constraints first

Assigning pins from memory bricks boards. Before choosing any pin, look up the
board's restrictions and write them into the pin-map comment so the next person
does not re-derive them. The recurring classes (details and per-board notes in
`references/pin-traps.md`):

- Pins wired to the flash chip — using one stops the board booting, which looks
  exactly like a dead board.
- Input-only pins, and input pins with no internal pull-up — neither can drive an
  output, and the pull-up-less ones float as inputs.
- Boot-strapping pins, which must hold a level at reset.
- The board's logic voltage. Check the peripherals accept it before buying a
  level shifter; many driver modules do.

## Power topology

- **Separate the motor supply from the logic supply and draw the rails.** Motors
  and servos get the raw supply; logic gets a regulator. A logic board's VIN
  usually tolerates far less than the motor rail, and feeding it the motor rail
  destroys it.
- **A board that ran from the motor rail on one target may not on another.**
  Changing boards can add a regulator to the BOM; say so and price it.
- **Check the stall current of every actuator** and power it from the supply, not
  from a logic board's pin. A small servo can stall near an amp.
- **One common ground across every rail.** State it explicitly; it is the most
  common omission in a first assembly.

## Driver configuration is a coupling, not a detail

Motor driver settings are load-bearing and differ per family and per module.
Verify them from the driver's own documentation rather than from a blog post or
memory — the tables are not interchangeable between driver families, and the
current formula depends on the module's sense resistors.

- **Microstepping must match the firmware constant.** A wrong microstep setting
  silently scales every movement; nothing errors, the machine is just wrong by a
  constant factor. Note the default, because leaving the pins open often selects
  a different value than the one you want.
- **The current setpoint formula depends on the board.** Give the formula for the
  specific module and the target value, and warn that a figure copied from
  another driver is wrong.
- **Set current before connecting motors**, and say how to measure it.
- **Coil identification is by measurement** — the two pins showing continuity are
  one coil. Getting it wrong does not damage anything; the motor just sits and
  buzzes, which is worth saying so it is not mistaken for a dead driver.

See `references/driver-config.md` for the per-family microstep and current notes.

## Schematics: generate them from code

A wiring diagram is an instruction someone follows, so it must not disagree with
the firmware. Hand-drawn diagrams drift the moment a pin changes.

- **Draw them with a script** (schemdraw is a good fit) and keep the pin table at
the top, mirroring the firmware.
- **Assert the diagram's pin table equals the firmware's**, parsed from both
  files. This is a consistency check between two artifacts — follow
  `audit-tool-validation` for proving the check itself, including injecting a
  deliberate mismatch to see it fail.
- **Register every block's footprint and fail the build on overlaps.** Eyeballing
  generated sheets does not scale, and an overlap is invisible in a file-size
  check. Measure the footprint from the drawn element's own anchors rather than
  assuming a placement convention: a library that anchors an element on its first
  pin instead of its centre will make a centre-based overlap check examine the
  wrong rectangle — reporting collisions that are not there and missing the ones
  that are.
- **Emit both SVG and PNG.** SVG for the repo, PNG for previews and printing.

## Documentation set for a device

Four documents, each earning its place:

| Doc | Must contain |
|---|---|
| BOM | Every part, spec, quantity, price, and a **running subtotal**; mark what the user already owns; note what NOT to substitute and why |
| Wiring | Pin map for every supported board, why each pin was chosen, power topology, first-power-up checklist |
| Build order | Ordered phases, each with an explicit **check** before moving on; the software-first phase runs before any purchase |
| Mechanics / design notes | The constraints that make or break it, with numbers |

- **Price the BOM and total it.** A list without a total is not a budget.
- **Every phase ends with a check** the builder can actually perform. "The pieces
  are where the model says they are" is a check; "looks good" is not.
- **Give the diagnostic order for the hardest failure.** Position loss, lost
  steps, a grinding axis: name the first thing to change (usually reduce speed)
  before suspecting the expensive part.
- **State what is deliberately not built yet**, so a gap reads as a decision
  rather than an oversight.

## Physical constraints with numbers beat adjectives

Identify the one or two constraints that determine whether the device works, and
quantify them. The user is making purchase decisions from these documents.

- Give the physical law and a table of values across the plausible range (e.g.
  magnetic pull versus gap), then the design rule that follows.
- Name the tempting wrong fix and why it fails — enlarging the actuator instead
  of respecting the geometry usually introduces a second failure mode.
- Where a span will sag or flex, say so and give the support spacing.

## Simulate the motion before buying parts

The host-side half can answer the expensive questions with zero hardware. Do it
first, and make the answers reproducible (see `audit-tool-validation`).

- **Model the drive, not just the toolpath.** On any drive where two motors share
the work — CoreXY, H-bot, delta — a carriage displacement decomposes into belt
displacements, and a diagonal makes one belt travel roughly twice the carriage
distance. Estimating move time from carriage distance alone under-reports a 45°
diagonal by up to 40%, which is the difference between a two-second move and a
three-second one. Take the maximum over the carriage *and* every belt, and write
a test that locks it in.
- **Decompose a discrete workload into machine operations, including the
  special cases.** For a game-playing or pick-and-place machine, derive the
  operation sequence from the rules (captures, promotions, castling, en passant)
  rather than hand-waving "it moves the piece". The special cases are where the
  plan is wrong in a way that only shows up mid-run.
- **Report the numbers the purchase decision needs**: total travel, total time,
  and actuator cycle count (wear and failure budget) over a realistic session,
  not one move.
- **Compare strategies over an identical workload** so the difference is the
  strategy and not the workload. A sanity invariant helps: a metric that should
  not depend on the strategy must come out identical under both.
- **Validate the simulator against a runnable end-to-end case.** Play the real
  workload, emit the real output (a motion program, a job file), and check the
  final state matches the model's.

## Verify, and say what is unverified

Report the split honestly, every time:

- Verified: tests pass, firmware compiles for each target (with the sizes), the
  artifact was generated, CAD exported and its bounding boxes checked, the
  consistency checks were seen to fail on injected mismatches.
- Not verified: nothing has run on real hardware. Say it plainly and point at the
  first hardware milestone.

Never let a compiling firmware or a rendered diagram imply the device works.

## Pitfalls

- **Do not write the report before the run finishes.** Quoting expected numbers
  produces a document that is right until it is not, and both versions look
  equally plausible. Run, then paste.
- **A number quoted in two files must be corrected in both** when it changes.
- **A simulator's numbers are only data if they repeat** — see
  `audit-tool-validation` for pinning threads, avoiding humanising options, and
  seeding.
- **`elm.Ic`-style libraries anchor on the first pin, not the centre.** Check the
  placement convention before trusting any coordinate maths built on it.
- **Do not ship a stale bytecode cache.** A test that loads a module by path can
  read an old `.pyc` when the source size and mtime are unchanged; execute the
  source text instead.
- **Adding a URL to a board-manager index that 404s breaks every later
  invocation.** Remove a bad index entry rather than leaving the error noise.
