# Deadlock Parry Practice

Randomly punches you every few minutes. When you hear the sound, press F.

## Usage

Run `deadlock_parry.exe`, with some optional args to control delays / timing.

```
Usage: deadlock_parry.exe [OPTIONS]

Options:
  -m, --delay-min INTEGER     The minimum delay before a random punch, in
                              seconds (Default: 15)
  -x, --delay-max INTEGER     The max delay before a random punch, in seconds
                              (Default: 240)
  -w, --parry-window INTEGER  The max duration for parrying before being hit,
                              in milliseconds (Default: 600)
  -k, --parry-key TEXT        The key binding for parry
  -v, --verbose               Enable verbose debug logging
  --help                      Show this message and exit.
```

See success rate and average response time.

```
...
Parry success: 430ms
5 / 7 (71.43%), average response: 392ms
Parry success: 429ms
6 / 8 (75.00%), average response: 398ms
Parry failed, you died.
6 / 9 (66.67%), average response: 398ms
```

## Building

To build deadlock_parry.exe from source, run:

```
$ pyinstaller deadlock_parry.spec
```
