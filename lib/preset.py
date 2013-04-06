import unittest

from lib.commands import SetAll, SetStrand, SetFixture, SetPixel


class Preset:
    """Base Preset.  Does nothing."""

    def __init__(self, mixer):
        self._mixer = mixer
        self._cmd = []
        self._tickers = []
        self._ticks = 0
        self.setup()

    def setup(self):
        """
        Override this method to initialize your tickers.
        """
        pass

    def can_transition(self):
        """
        Override this method to define clear points at which the mixer can
        transition to or from the preset.  By default, the mixer can
        transition at any time.
        """
        return True

    def add_ticker(self, ticker, priority=0):
        """
        Adds a ticker. Tickers are run every tick and can yield any number of
        (lights, color) tuples.

        lights is one of:
            an empty tuple                    (to change all strands)
            a (strand) tuple                  (to change all addresses on the strand)
            a (strand, address) tuple         (to change all pixels on the strand)
            a (strand, address, pixel) tuple  (to change a single pixel)
            a list of any of the above tuples

        color is an (r, g, b) tuple where r, g, and b are either:
            integers between 0 and 255
            floats between 0 and 1

        Tickers get a two arguments: the number of ticks that have
        passed since this preset started, and the approximate amount of time
        this preset has been running for, in seconds.

        The optional priority arguments is used to determine the order in which
        tickers are run. High priorities are run after lower priorities, allowing
        them to override the lower-priority tickers.
        """
        self._tickers.append((ticker, priority))
        return ticker

    def remove_ticker(self, ticker):
        for (t, p) in self._tickers:
            if t == ticker:
                self._tickers.remove((t, p))

    def tick(self):
        time = self._ticks * (1.0 / self.tick_rate())
        for ticker, priority in sorted(self._tickers, key=lambda x: x[1]):
            for lights, color in ticker(self._ticks, time):

                if lights is not None:
                    color = self._convert_color(color)

                    if type(lights) == tuple:
                        lights = [lights]

                    for light in lights:
                        if len(light) == 0:
                            self.add_cmd(SetAll(color))
                        elif len(light) == 1:
                            self.add_cmd(SetStrand(light[0], color))
                        elif len(light) == 2:
                            self.add_cmd(SetFixture(light[0], light[1], color))
                        elif len(light) == 3:
                            self.add_cmd(SetPixel(light[0], light[1], light[2], color))

        self._ticks += 1

    def tick_rate(self):
        return self._mixer.get_tick_rate()

    def clr_cmd(self):
        self._cmd = []

    def get_cmd_packed(self):
        return [cmd.pack() for cmd in self._cmd]

    def add_cmd(self, cmd):
        self._cmd.append(cmd)

    def _convert_color(self, color):
        if (type(color[0]) == float) or (type(color[1]) == float) or (type(color[2]) == float):
            return tuple([int(c*255) for c in color])
        else:
            return color

    def scene(self):
        return self._mixer.scene()


class TestPreset(unittest.TestCase):

    pass