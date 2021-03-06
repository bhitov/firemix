import colorsys
import random

from lib.raw_preset import RawPreset
from lib.colors import uint8_to_float, float_to_uint8
from lib.color_fade import ColorFade
from lib.parameters import FloatParameter, IntParameter, HLSParameter


class Fungus(RawPreset):
    """
    Spreading fungus
    Illustrates use of Scene.get_pixel_neighbors.

    Fungal pixels go through three stages:  Growing, Dying, and then Fading Out.
    """

    _growing = []
    _alive = []
    _dying = []
    _fading_out = []

    # Configurable parameters
    _spontaneous_birth_probability = 0.0001

    # Internal parameters
    _time = {}
    _population = 0
    _fader = None
    
    _growth_time = 0.6    
    _life_time = 0.5
    _isolated_life_time = 1.0
    _death_time = 3.0
    _birth_rate = 0.05
    _spread_rate = 0.25
    _fade_out_time = 2.0
    _mass_destruction_countdown = 2.0
    _mass_destruction_threshold = 150
    _population_limit = 500
    _alive_color = (1.0, 1.0, 1.0)
    _dead_color = (0.0, 0.5, 1.0)
    _black_color = (0.0, 0.0, 1.0)

    def setup(self):
        self._population = 0
        self._time = {}
        self.add_parameter(FloatParameter('growth-time', self._growth_time))
        self.add_parameter(FloatParameter('life-time', self._life_time))
        self.add_parameter(FloatParameter('isolated-life-time', self._isolated_life_time))
        self.add_parameter(FloatParameter('death-time', self._death_time))
        self.add_parameter(FloatParameter('birth-rate', self._birth_rate))
        self.add_parameter(FloatParameter('spread-rate', self._spread_rate))
        self.add_parameter(FloatParameter('fade-out-time', self._fade_out_time))
        self.add_parameter(FloatParameter('mass-destruction-time', self._mass_destruction_countdown))
        self.add_parameter(IntParameter('mass-destruction-threshold', self._mass_destruction_threshold))
        self.add_parameter(IntParameter('pop-limit', self._population_limit))
        self.add_parameter(HLSParameter('alive-color', self._alive_color))
        self.add_parameter(HLSParameter('dead-color', self._dead_color))
        self.add_parameter(HLSParameter('black-color', self._black_color))
        self.parameter_changed(None)

    def reset(self):
        self._current_time = 0
        self._growing = []
        self._alive = []
        self._dying = []
        self._fading_out = []
        self._population = 0
        self._time = {}
        self.parameter_changed(None)

    def parameter_changed(self, parameter):
        self._setup_colors()
        self._growth_time = self.parameter('growth-time').get()
        self._life_time = self.parameter('life-time').get()
        self._isolated_life_time = self.parameter('isolated-life-time').get()
        self._death_time = self.parameter('death-time').get()
        self._birth_rate = self.parameter('birth-rate').get()
        self._spread_rate = self.parameter('spread-rate').get()
        self._fade_out_time = self.parameter('fade-out-time').get()
        self._mass_destruction_countdown = self.parameter('mass-destruction-time').get()
        self._mass_destruction_threshold = self.parameter('mass-destruction-threshold').get()
        self._population_limit = self._population_limit

    def _setup_colors(self):
        self._alive_color = self.parameter('alive-color').get()
        self._dead_color = self.parameter('dead-color').get()
        self._black_color = self.parameter('black-color').get()
        fade_colors = [self._black_color, self._alive_color, self._dead_color, self._black_color]
        self._fader = ColorFade(fade_colors, tick_rate=self._mixer.get_tick_rate())

    def draw(self, dt):

        self._current_time += dt
        self._mass_destruction_countdown -= dt
    
        # Ensure that empty displays start up with some seeds
        p_birth = (1.0 - self._spontaneous_birth_probability) if self._population > 5 else 0.5

        # Spontaneous birth: Rare after startup
        if (self._population < self._population_limit) and random.random() > p_birth:
            address = ( random.randint(0, self._max_strand - 1),
                        random.randint(0, self._max_fixture - 1),
                        random.randint(0, self._max_pixel - 1))
            if address not in (self._growing + self._alive + self._dying + self._fading_out):
                self._growing.append(address)
                self._time[address] = self._current_time
                self._population += 1

        # Color growth
        for address in self._growing:
            neighbors = self.scene().get_pixel_neighbors(address)
            p, color = self._get_next_color(address, self._growth_time, self._current_time)
            if p >= 1.0:
                self._growing.remove(address)
                self._alive.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

            # Spread
            if (self._population < self._population_limit) and (random.random() < self._spread_rate * dt):
                for spread in neighbors:
                    if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                        self._growing.append(spread)
                        self._time[spread] = self._current_time
                        self._population += 1

        # Lifetime
        for address in self._alive:
            neighbors = self.scene().get_pixel_neighbors(address)
            live_neighbors = [i for i in neighbors if i in self._alive]
            lt = self._life_time
            if len(neighbors) < 2:
                lt = self._isolated_life_time

            if len(live_neighbors) < 2 and ((self._current_time - self._time[address]) / lt) >= 1.0:
                self._alive.remove(address)
                self._dying.append(address)
                self._time[address] = self._current_time
                self._population -= 1

            self.setPixelHLS(address, self._alive_color)

            # Spread
            if (self._population < self._population_limit) and random.random() < self._birth_rate * dt:
                for spread in neighbors:
                    if spread not in (self._growing + self._alive + self._dying + self._fading_out):
                        self._growing.append(spread)
                        self._time[spread] = self._current_time
                        self._population += 1

        # Color decay
        for address in self._dying:
            p, color = self._get_next_color(address, self._death_time, self._current_time)
            if p >= 1.0:
                self._dying.remove(address)
                self._fading_out.append(address)
                self._time[address] = self._current_time
            self.setPixelHLS(address, color)

        # Fade out
        for address in self._fading_out:
            p, color = self._get_next_color(address, self._fade_out_time, self._current_time)
            if p >= 1.0:
                self._fading_out.remove(address)
            self.setPixelHLS(address, color)

        # Mass destruction
        if (self._population == self._population_limit) or \
                (self._population > self._mass_destruction_threshold and self._mass_destruction_countdown <= 0):
            for i in self._alive:
                if random.random() > 0.95:
                    self._alive.remove(i)
                    self._dying.append(i)
                    self._population -= 1
            for i in self._growing:
                if random.random() > 0.85:
                    self._growing.remove(i)
                    self._dying.append(i)
                    self._population -= 1
            self._mass_destruction_countdown = self.parameter('mass-destruction-time').get()

    def _get_next_color(self, address, time_target, current_time):
        """
        Returns the next color for a pixel, given the pixel's current state
        """
        progress = (current_time - self._time[address]) / time_target

        if progress > 1.0:
            progress = 1.0
        elif current_time == self._time[address]:
            progress = 0.0

        idx = progress / 3.0
        if time_target == self._death_time:
            idx += (1.0 / 3.0)
        elif time_target == self._fade_out_time:
            idx += (2.0 / 3.0)

        return (progress, self._fader.get_color(idx))
