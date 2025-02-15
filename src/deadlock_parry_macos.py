from __future__ import annotations

import logging
import os.path
import random
import statistics
import time

import click
from pynput import keyboard
import os
import subprocess

__version__ = "1.0.4"

_file_dir = os.path.dirname(__file__)

LOG = logging.getLogger()
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)

DEFAULT_DELAY_MIN = 3
DEFAULT_DELAY_MAX = 5
DEFAULT_PARRY_WINDOW = 600

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

# delay after failing to parry before the app is deactivated
FINISH_PUNCH_DELAY = 600


class ParryResult(object):
    def __init__(self, success: bool, response_time: int | None = None):
        self.success = success
        self.response_time = response_time

    def to_string(self) -> str:
        if self.success:
            return f"Parry success: {self.response_time}ms"
        elif self.response_time is not None:
            return f"Parry failed: {self.response_time}ms"
        else:
            return f"Parry failed, you died."

    def has_response_time(self) -> bool:
        return self.response_time is not None


class ParryTrainer(object):
    PUNCH_SOUND = "punch"
    PARRY_SOUND = "parry"
    HIT_SOUND = "hit"

    def __init__(self):
        # minimum delay between punches, in seconds
        self.delay_min = DEFAULT_DELAY_MIN
        # maximum delay between punches, in seconds
        self.delay_max = DEFAULT_DELAY_MAX
        # the maximum number of milliseconds allowed before the parry fails
        self.parry_window = DEFAULT_PARRY_WINDOW
        # the key binding for parry
        self.parry_key = "f"

        self.listener = None
        self.parry_input_pressed = False

        # the next time a punch should be triggered
        self._next_punch_time = -1
        # the actual time at which a punch started
        self._punch_start_time = -1
        # is a punch currently happening?
        self._is_punching = False
        # did the player miss the parry window for the current punch?
        self._parry_failed = False

        # self._window: pygame.Surface | None = None
        # self._hwnd = None
        # self._last_active_hwnd = None

        # a record of all results
        self.results: list[ParryResult] = []

        # init pygame immediately, so that key codes and other options can be configured
        # pygame.init()
        # pygame.mixer.init()

    def set_parry_key(self, name: str):
        try:
            self.parry_key = pygame.key.key_code(name)
        except ValueError:
            LOG.warning(f"Unknown key name: {name}")
            pass

    def play_sound(self, name):
        path = os.path.join(_file_dir, "audio", f"{name}.wav")
        subprocess.Popen(["afplay", path])


    def start(self):
        LOG.info(f"Starting Parry Trainer")
        LOG.info(f"Delay: {self.delay_min}..{self.delay_max}s")
        LOG.info(f"Parry Window: {self.parry_window}ms")
        # LOG.info(f"Parry Key: {pygame.key.name(self.parry_key)}")
        LOG.info(f"Press Ctrl + C to quit.")

        # create a display to capture input
        # self._window = pygame.display.set_mode()
        # self._window.fill(0)
        # self._hwnd = pygame.display.get_wm_info()["window"]
        # pygame.display.set_caption("Deadlock Parry Trainer")

        # make window transparent
        # if os.name == "nt":
        #     win32gui.SetWindowLong(
        #         self._hwnd,
        #         win32con.GWL_EXSTYLE,
        #         win32gui.GetWindowLong(self._hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED,
        #     )
        #
        #     # from 0..255
        #     transparency = 1
        #     win32gui.SetLayeredWindowAttributes(self._hwnd, 0, transparency, win32con.LWA_ALPHA)


        # start minimized
        self.deactivate_window()

        # clock = pygame.time.Clock()

        run = True
        while run:
            # rate limit when not punching, keeps the app responsive to exit inputs, etc
            # clock.tick(360 if self._is_punching else 2)

            # listen for parry input
            self.parry_input_pressed = False
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         run = False
            #     elif event.type == pygame.KEYDOWN:
            #         if event.key == pygame.K_ESCAPE:
            #             self.deactivate_window()
            #         elif event.key == pygame.K_c:
            #             if event.mod & pygame.KMOD_CTRL:
            #                 LOG.info(f"Received Ctrl + C, exiting...")
            #                 run = False
            #         elif event.key == self.parry_key:
            #             parry_input_pressed = True
            #         LOG.debug(f"KEYDOWN: {event.dict}")

            if not self._is_punching:
                if self._next_punch_time < 0:
                    self.schedule_punch()

                # wait for next punch
                if time.time() >= self._next_punch_time:
                    self.punch()

            if self._is_punching:
                elapsed_time_ms = round((time.time() - self._punch_start_time) * 1000)

                if not self._parry_failed:
                    # still time left to parry
                    if self.parry_input_pressed:
                        self.parry()
                        self.finish_punch(True, elapsed_time_ms)
                    elif elapsed_time_ms >= self.parry_window:
                        # don't finish punch yet, allow for late input
                        self.fail_parry()
                else:
                    # failed the parry, just wait for late input or finish the punch
                    if self.parry_input_pressed:
                        self.finish_punch(False, elapsed_time_ms)
                    elif elapsed_time_ms >= self.parry_window + FINISH_PUNCH_DELAY:
                        self.finish_punch(False, None)

    def activate_window(self):
        # os.system("open -a \"Python\"")
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            suppress=False)
        self.listener.start()
        print("started listening for key")
        # print(f"{self.listener.IS_TRUSTED}")

    def deactivate_window(self):
        # restore focus to the previously focused window
        if self.listener is not None:
            self.listener.stop()
            print("stopped listening for key")

    def on_key_press(self, key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key.char))

            if key.char == "f":
                print("parried!")
                self.parry_input_pressed = True
                # self.parry()f
                # self.finish_punch(True, 1)
        except AttributeError:
            print('special key {0} pressed'.format(
                key))

    def schedule_punch(self):
        # do a quick initial delay for the first punch
        if self._punch_start_time < 0:
            self._next_punch_time = time.time() + 5
        else:
            random_delay = random.uniform(self.delay_min, self.delay_max)
            self._next_punch_time = time.time() + random_delay

        LOG.debug(f"Next punch in {self._next_punch_time - time.time():.2f}s")

    def punch(self):
        # activate game window
        self.activate_window()

        self.play_sound(self.PUNCH_SOUND)
        self._is_punching = True
        self._punch_start_time = time.time()

        LOG.debug(f"Punch")

    def reset_punch(self):
        self._is_punching = False
        self._parry_failed = False
        self._next_punch_time = -1
        # hide the game window
        self.deactivate_window()

    def parry(self):
        self.play_sound(self.PARRY_SOUND)

    def fail_parry(self):
        self._parry_failed = True
        self.play_sound(self.HIT_SOUND)

    def finish_punch(self, success: bool, response_time: int | None):
        result = ParryResult(success, response_time)
        self.results.append(result)
        LOG.info(result.to_string())

        self.reset_punch()
        self.log_results_summary()

    def log_results_summary(self):
        successful_results = [r for r in self.results if r.success]
        num_total = len(self.results)
        num_success = len(successful_results)
        avg_response = 0
        responded_results = [r for r in self.results if r.has_response_time()]
        if responded_results:
            avg_response = round(statistics.fmean([r.response_time for r in responded_results]))
        success_rate = num_success / float(num_total)
        LOG.info(f"{num_success} / {num_total} ({success_rate * 100:.2f}%), average response: {avg_response}ms")


@click.command()
@click.option(
    "-m",
    "--delay-min",
    type=int,
    default=DEFAULT_DELAY_MIN,
    help=f"The minimum delay before a random punch, in seconds (Default: {DEFAULT_DELAY_MIN})",
)
@click.option(
    "-x",
    "--delay-max",
    type=int,
    default=DEFAULT_DELAY_MAX,
    help=f"The max delay before a random punch, in seconds (Default: {DEFAULT_DELAY_MAX})",
)
@click.option(
    "-w",
    "--parry-window",
    type=int,
    default=DEFAULT_PARRY_WINDOW,
    help=f"The max duration for parrying before being hit, in milliseconds (Default: {DEFAULT_PARRY_WINDOW})",
)
@click.option(
    "-k",
    "--parry-key",
    default="f",
    help="The key binding for parry",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose debug logging",
)
def main(delay_min, delay_max, parry_window, parry_key, verbose):
    if verbose:
        LOG.setLevel(logging.DEBUG)

    trainer = ParryTrainer()
    trainer.delay_min = delay_min
    trainer.delay_max = delay_max
    trainer.parry_window = parry_window
    # trainer.set_parry_key(parry_key)
    trainer.start()


if __name__ == "__main__":
    main()
