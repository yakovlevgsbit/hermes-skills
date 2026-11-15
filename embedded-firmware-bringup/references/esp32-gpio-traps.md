# ESP32 GPIO traps and the dual-board pin map

Choosing ESP32 pins is not "pick any free GPIO". Four classes of pin will
produce failures that look like dead hardware.

## Pins that must never be used

| Range | What it is | What happens if you use it |
|-------|-----------|---------------------------|
| GPIO 6–11 | Wired to the SPI flash | Driving one as an output stops the board booting. Looks like a dead DevKit, so you buy a replacement that also "fails". |
| GPIO 34–39 | Input-only, no internal pull-up | Cannot be outputs at all; useless as endstops too, because there is no pull-up to read a switch against. |
| GPIO 0, 2, 12, 15 | Boot strapping | Affects boot mode. GPIO12 in particular must not be pulled high at boot or the board will not start. |

Safe, general-purpose, output-capable: 4, 5, 13, 14, 16–19, 21–23, 25–27,
32, 33. For inputs that need a pull-up, 32 and 33 are the reliable pick
(input-capable *with* pull-up, and not strapping).

A useful working map for a 2-motor + 2-endstop + 1-servo machine:

| Function | ESP32 | Arduino Mega |
|----------|-------|--------------|
| Motor A STEP / DIR / EN | 25 / 26 / 27 | 2 / 5 / 8 |
| Motor B STEP / DIR / EN | 14 / 13 / 4 | 3 / 6 / 9 |
| X endstop / Y endstop | 32 / 33 | 10 / 11 |
| Servo signal | 18 | 44 |

## Power, which is the other half of the trap

- **The DevKit has no 12 V input.** Do not put the motor supply on VIN. Either
  a 12 V→5 V buck converter, or a separate 5 V supply with a common ground.
- **Do not power a servo from the board's 5 V pin.** A small hobby servo stalls
  at several hundred milliamps, which is at or past what the dev board's
  regulator will deliver — the symptom is a brownout reset that looks like a
  firmware crash.
- **Logic level.** 3.3 V outputs into a stepper driver's STEP/DIR inputs is
  normally fine (drivers accept 3.3 V logic). A level shifter is a debugging
  step, not a default purchase. Never feed 5 V into an ESP32 GPIO.
- For bench work, power the board over USB so the serial console survives, and
  tie grounds to the motor supply. Losing the console while debugging motion is
  the main avoidable cost.

## Libraries: check the exported symbol, not the package name

The Arduino ecosystem has libraries whose class name does not match the
package name. `ESP32Servo` exports a class named `Servo`, the same as
Arduino's built-in — so a single `Servo` type compiles for both targets and no
macro indirection is needed. Do not write
`#define MY_SERVO ESP32Servo`; that fails to compile because no such symbol
exists.

Check before assuming: `grep -n '^class\|typedef.*Servo' <lib>/src/*.h`.

Board-specific differences then live in `setup()` only (the ESP32 library
wants an explicit pulse range and period; the AVR one does not).

## Wiring documentation pattern

Document the pin map as a two-column table (both boards) plus a short
"why these pins" list naming the avoided ranges and the failure each one
causes. Without that note the next person "tidies" the pin map onto 6–11 and
the board stops booting.
