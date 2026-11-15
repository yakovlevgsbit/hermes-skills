# Pin traps by board

Check the board's own documentation before assigning any pin, then write the
restrictions into the firmware's pin-map comment so the next person does not
re-derive them. The classes below recur across boards; the specifics do not.

## The four recurring classes

| Class | Consequence of getting it wrong |
|---|---|
| Wired to the flash chip | Board stops booting — indistinguishable from a dead board |
| Input-only | Cannot drive an output at all |
| Input with no internal pull-up | A switch on it floats; reads randomly |
| Boot-strapping | Board may not start, depending on the level at reset |

Plus a fifth that is not about a pin: **logic voltage**. A 3.3 V board driving a
5 V-logic peripheral needs a shifter, or a peripheral that tolerates 3.3 V.

## ESP32 (DevKit v1, 30-pin, ESP32-WROOM-32)

| Range | Restriction |
|---|---|
| 6–11 | Connected to the SPI flash. Driving one as an output stops boot. |
| 34–39 | Input-only **and** no internal pull-up — cannot be outputs, and unusable as pulled-up switch inputs. |
| 0, 2, 12, 15 | Boot-strapping. GPIO12 must not be pulled high at boot. GPIO2 also carries the onboard LED. |
| 1, 3 | UART0 TX/RX — the serial console used for flashing and debugging. |
| 5 | Strapping on some modules; verify before use. |

Notes that matter in practice:

- GPIO 32 and 33 are the good switch inputs: input-capable *with* pull-ups and
  not strapping.
- Plain output-capable, non-strapping pins: 4, 13, 14, 18, 19, 21, 22, 23, 25,
  26, 27, 32, 33.
- **No 12 V input.** VIN tolerates 5 V. A 12 V motor supply needs a buck
  converter to feed the board and any 5 V servo.
- A servo must not run from the board's 5 V pin — a small hobby servo stalls near
  700 mA, which is at the edge of the onboard regulator.
- The USB-UART bridge is a CP2102 or CH340 depending on the clone; on Linux it
  appears as `/dev/ttyUSB0`.
- Arduino core: `arduino-cli core install esp32:esp32` after adding the Espressif
  board-manager URL. FQBN: `esp32:esp32:esp32`.

## Arduino Mega 2560 (AVR)

- 14, 15, 16, 17 are hardware serial lines (Serial1/2/3); avoid them for I/O
  unless you intend to use that UART.
- 0 and 1 are the USB serial console.
- 20, 21 are I2C.
- Far more output-capable pins than the ESP32, no strapping-pin hazard, and 5 V
  logic — so it accepts 5 V peripherals without a shifter but needs level
  shifting for 3.3 V-only parts.
- 16 MHz: adequate for step/dir at modest rates, but check the achievable step
  frequency before committing to a high-resolution or high-speed axis.
- FQBN: `arduino:avr:mega`.

## One source, two boards

```cpp
#if defined(ESP32)
  static const uint8_t PIN_A_STEP = 25, PIN_A_DIR = 26, PIN_A_EN = 27;
  static const uint8_t PIN_X_MIN  = 32;   // pull-up capable, not strapping
#else
  static const uint8_t PIN_A_STEP = 2,  PIN_A_DIR = 5,  PIN_A_EN = 8;
  static const uint8_t PIN_X_MIN  = 10;
#endif
```

- Keep the `#if defined(...)` blocks minimal and put a header comment on each so
  a parser (or a human) can find the right one — a file has several such blocks
  (includes, pin map, setup) and picking the first gives an empty result.
- Serial libraries differ by board for the same class name (the ESP32 servo
  library and the AVR one both export a class called `Servo`), so one
  declaration can work on both. Verify the class name in the installed library's
  header rather than guessing it from the package name.
- The ESP32 servo library needs an explicit pulse range in `setup()`; the AVR one
  does not.

## Verify pin choices against the firmware in code

A test that parses the firmware's pin-map block and compares it to whatever
else mirrors those pins (a schematic script, a docs table) catches a silent
divergence. See the two-artifact check section of `audit-tool-validation`.
