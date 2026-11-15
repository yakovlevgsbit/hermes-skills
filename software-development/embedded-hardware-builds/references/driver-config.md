# Stepper driver configuration (step/dir modules)

Driver settings are a coupling to the firmware, not a detail: a wrong microstep
setting or current setpoint scales or starves every movement with no error
reported anywhere. **Read the driver's own datasheet or module wiki.** The
tables differ between families and the current formula depends on the module's
sense resistors, so a figure from a blog post or from a different driver is
usually wrong.

## Microstepping: the tables are NOT interchangeable

| Microsteps | TMC2209 (MS2, MS1) | A4988 (MS1, MS2, MS3) |
|---|---|---|
| 1/8 | GND, GND (default — internal pull-downs) | L, L, L |
| 1/16 | **VIO, VIO** | H, H, L |
| 1/32 | GND, VIO | H, L, H |
| 1/64 | VIO, GND | H, H, H |

The trap: on the TMC2209, **1/16 is both MS1 and MS2 HIGH**, whereas on the
A4988 it is MS1=H, MS2=H, **MS3=L**. On a TMC2209 module the config pins have
internal pull-downs, so leaving them open silently selects 1/8 — half the
intended resolution — and every commanded move lands at half the distance with
no error. Tie both to VIO for 1/16.

`SPREAD`/`MS3` selects the chopper: low = StealthChop (quiet), high =
SpreadCycle. Leave it unconnected for quiet operation (it has an internal
pull-down).

## Motor current (Vref)

The formula is module-specific because it depends on the sense resistors.

**TMC2209 on the common BTT/FYSETC-style modules (110 mΩ sense resistors):**

```
I_RMS  = Vref / √2
I_PEAK = Vref
Vref range 0.2–2.2 V;  factory default ≈1.2 V ≈ 0.85 A RMS
```

So the factory default is well below a typical NEMA17 rating. For ~1.2 A RMS
(comfortable continuous for a 1.5–1.7 A motor) set Vref ≈ **1.7 V**. A cheap
alternative is to read the module's own wiki for its stated formula rather than
trusting a generic number.

**A4988 (0.1 Ω sense resistors, the classic board):**

```
I = Vref / (8 × R_sense)   →   Vref ≈ I × 0.8 for R_sense = 0.1 Ω
```

About 1.0 V for 1.2 A. Different driver, different number — do not copy across.

**Potentiometer direction differs by module.** On BTT TMC2209 boards, turning
clockwise *reduces* Vref. Measure, do not assume.

**Procedure:** set Vref with the motor disconnected and the driver powered,
measuring at the Vref pad or the pot wiper. Then connect the motor.

## Standalone vs UART

- `PDN_UART` to GND selects **standalone** mode (no UART). This is what firmware
  that only does step/dir assumes — set it explicitly rather than relying on a
  module default.
- `CLK` is left open; the module uses its internal clock.
- `EN` is **active low** on both families: GND = outputs enabled.
- MS1/MS2 double as the UART node address when UART is enabled; if you are not
  using UART, they are free to use for microstepping.

## Coil identification

Use a multimeter: the two pins that show continuity (a few ohms) are one coil.
Wire one coil to A1/A2 and the other to B1/B2. **Getting this wrong does not
damage anything** — the motor buzzes and holds position without turning. Worth
stating, so a buzzing motor is not misdiagnosed as a dead driver or a bad board.

## Before powering anything

1. PSU off. Motors connected, drivers seated.
2. Never plug or unplug a motor while the driver is powered — that is the
   classic way to destroy a driver.
3. Vref set (see above) with the motor disconnected.
4. Power on with no motion command; only the actuators that should hold a
   position should do anything.
5. Then a short move at low speed, and confirm direction before a full program.
