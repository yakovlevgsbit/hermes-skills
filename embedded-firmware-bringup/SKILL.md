---
name: embedded-firmware-bringup
description: "Use when building firmware for hardware you don't have yet."
version: 1.0.0
author: Георгий Яковлев (yakovlevgsbit), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [firmware, arduino, esp32, embedded, gcode, stepper, bringup, serial, cad]
    related_skills: [audit-tool-validation, systematic-debugging, spike]
---

# Embedded Firmware Bring-Up Without the Hardware

When the target machine does not exist yet (parts not bought, printer not
calibrated, enclosure not cut), most of the project is still buildable and
testable. The rule: **anything that is not the physical world can be verified
now**, and everything verified now is one less thing to debug while holding a
multimeter. A stub plus a plan is not the deliverable — compiled, run, and
measured artifacts are.

## When to Use

- A project needs firmware, and the board or the machine is not assembled.
- A controller must talk to a host over serial, and the protocol is yours.
- A motion/actuator machine (printer, gantry, arm, plotter, chessboard) needs
the moves planned and the numbers estimated before parts arrive.
- Someone asks "what hardware do I need?" — the answer is a BOM plus the
  firmware that proves the BOM is sufficient.

## What can be verified with no hardware at all

Do all four, in this order. Each one is cheap and each catches a different class.

1. **Compile for the real target.** Not "it should compile" — run the
   toolchain. This is the only proof the pin map, library names and API calls
   are real. Install the toolchain as needed; it is additive and reversible.
2. **Test the host-side protocol driver against a fake transport.** Write the
   serial client with an injectable factory, then drive it with a stub that
   answers like the firmware. This is where real bugs live (see pitfalls).
3. **Emit the machine program and assert its invariants in tests.** The G-code
   or command stream is data; invariants over data are testable.
4. **Simulate the machine to get the numbers.** Travel distance, cycle time,
   actuator cycles, and a comparison of planning strategies — all derivable
   from geometry plus a motion model, with no parts.

## One source, several boards

Keep a single firmware file with per-board pin maps behind a conditional, never
a forked copy per board. The duplicated file drifts, and the code that drifts is
the kinematic/mixing code — the exact part you cannot afford to have differ.

- Put the pin map and board-specific includes in `#if defined(BOARD)` blocks at
the top; keep all logic board-agnostic below.
- Print the active board in the boot banner. It is a one-line way to confirm
the target you flashed is the target you meant.
- Verify **both** targets compile on every change, and add a check to the
  project's own `check`/`doctor` command that both pin maps are still present in
  the shared source — otherwise one silently loses its config in a refactor.

## Arduino CLI toolchain

```bash
# AVR
arduino-cli core install arduino:avr

# ESP32 — needs the vendor index first
arduino-cli config add board_manager.additional_urls \
    https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32

arduino-cli lib install AccelStepper ESP32Servo
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/<sketch>
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/<sketch>
```

- **Only add board indexes you will actually use.** A wrong or stale index URL
  makes every later `arduino-cli` invocation print an init error, which trains
  you to ignore errors from the tool you depend on. Remove it if you added one
  by mistake (`arduino-cli config remove board_manager.additional_urls <url>`).
- `esp32:esp32` is a large download; run the install in the background and do
  other work, then compile.
- Report flash/RAM as a percentage of the target's limits. The headroom number
  is the argument for or against a board.

## Serial protocol pitfalls

- **A boot banner will be read as the reply to the first command.** The host
  opens the port, the board resets, the banner arrives — and a naive
  `readline()` returns it as the acknowledgement for command #1, failing every
  program on line 1. Only accept recognised reply shapes (`ok`, `error`, or the
  specific report a query command returns), skip anything else, and drain the
  port after opening.
- **A query command answers with data, not `ok`.** Compute success from the
  shape of the reply you asked for, not from a prefix check, or every status
  query reads as a failure.
- **Check every acknowledgement; stop on the first failure by default.**
  Continuing past a failed command means host and machine disagree about state,
  and the only safe move is to stop and re-home. Offer an explicit
  continue-past-errors flag for debugging only.
- Make the transport injectable (`serial_factory=...`) so the whole driver is
  testable with no port. This is the single highest-value design decision for
  firmware you cannot yet flash.

## Machine-program invariants worth asserting

For a motion program (G-code or your own command stream), test the safety
properties as properties, not by reading the file:

- **Actuator state must be legal for every move.** If a tool/magnet/clamp must
  be retracted before travel, assert it: walk the program, track actuator state,
  and fail if any travel happens in the engaged state. Exactly one drag per grip
  — no more.
- **The approach move happens with the actuator retracted**, and the engaging
  command is followed by a settle dwell before motion resumes. A grip with no
  dwell drops the part mid-flight.
- **Enforce the interlock in the firmware too**, not only in the generator.
  Refuse a travel command while the actuator is engaged and print an error.
  Redundant with the host check, deliberately: the host can be bypassed.
- **Bound every axis and refuse out-of-range targets** at the operation level,
  so a bad plan fails at construction rather than as a crash mid-move.
- Every special case of the domain needs its own test — for a board game: the
  capture, the en-passant (victim not on the destination square), both castling
  sides, and promotion. Each is a different sequence of operations.

## Simulating the machine before building it

Derive geometry once (square/unit pitch, envelope, parking/storage slots) and
compute everything from it. Then measure:

- **Estimate move time from the worst traveller, not the tool position.** In
  belt/cable drives the motors or belts move further than the carriage
  (CoreXY: `dA = dx + dy`, `dB = dx - dy`, so a 45° diagonal doubles one belt's
  travel). A naive `distance / speed` under-reports diagonals badly.
- **Compare planning strategies over an identical work sequence** so the
  comparison isolates the machine work from the domain decisions.
- **Keep a sanity invariant across strategies**: a count that must not depend on
  the strategy (e.g. actuator cycles) proves the two runs really are the same
  job. If it differs, the strategies are not comparable.
- Make the simulation reproducible before quoting numbers — see
  `audit-tool-validation` for the full rule. Numbers that change per run are
  not measurements.

## Physical constraints belong in the docs, with the mechanism

State the one or two constraints that decide the design, and *why*, in the
project's own docs — a future reader will otherwise "improve" them:

- **Magnetic coupling falls off roughly with the cube of the gap.** A thin
  coupling surface is not a preference: 3 mm pulls kilograms, 8 mm pulls
  hundreds of grams. The wrong fix (thicker surface + bigger magnet) makes the
  magnet grab neighbouring parts through their sides.
- **Steps-per-mm is duplicated between firmware and host.** Any change to
  microstepping or pulley size must be applied in both, or every move lands
  short by a constant factor. Say this where both are defined.
- **Servo/actuator inrush must not come from the dev board's regulator.** A
  small servo stalls at hundreds of milliamps; power it from the supply rail and
  tie grounds.

## BOM answers

When asked what hardware to buy, answer with a table that separates: already on
hand (cost 0, and say whether it is a *good* choice or merely adequate), must
buy, optional upgrades with the reason each matters, and consumables. Give the
subtotal and what the money is actually spent on. Note the parts where saving
money hurts (cheap linear motion turns into position error).

## Verification

Before reporting the firmware as done:

- [ ] Compiles for every supported target, with flash/RAM figures quoted.
- [ ] Host protocol driver tested against a fake transport, including the
      banner-first and query-reply cases.
- [ ] Program invariants asserted in tests (actuator state, dwells, bounds).
- [ ] Simulation reproduces identically on two consecutive runs.
- [ ] Both pin maps still present in the single shared source.
- [ ] Stated plainly which parts are verified and which need hardware.

## References

- `references/esp32-gpio-traps.md` — which ESP32 pins break the board, and why;
  the dual-board pin-map pattern.
