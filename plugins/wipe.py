import numpy as np
import math

from lib.transition import Transition
from lib.buffer_utils import BufferUtils


class Wipe(Transition):
    """
    Implements a simple wipe
    """

    def __init__(self, app):
        Transition.__init__(self, app)

    def __str__(self):
        return "Wipe"

    def setup(self):
        self.num_strands, self.num_pixels = BufferUtils.get_buffer_size(self._app)
        self.mask = np.tile(False, (self.num_strands, self.num_pixels, 3))

        midpoints = [f.midpoint() for f in self._app.scene.fixtures()]
        self.min_x = min([mp[0] for mp in midpoints])
        max_x = max([mp[0] for mp in midpoints])
        self.min_y = min([mp[1] for mp in midpoints])
        max_y = max([mp[1] for mp in midpoints])
        self.span_x = max_x - self.min_x
        self.span_y = max_y - self.min_y

        angle = np.random.random() * np.pi * 2.0
        self.wipe_vector = np.zeros((2))

        self.wipe_vector[0] = math.cos(angle)
        self.wipe_vector[1] = math.sin(angle)

        self.locations = []
        for f in self._app.scene.fixtures():
            for p in range(f.pixels):
                self.locations.append((f.strand, f.address, p, self._app.scene.get_pixel_location((f.strand, f.address, p))))

    def get(self, start, end, progress):
        """
        Simple wipe
        """

        for strand, address, pixel, location in self.locations:
            if location[0] < (self.min_x + (progress * self.span_x)):
                _, pixel = BufferUtils.get_buffer_address(self._app, (strand, address, pixel))
                self.mask[strand][pixel][:] = True

        start[self.mask] = 0.0
        end[np.invert(self.mask)] = 0.0
        return start + end

    def _is_point_inside_wipe(self, point, progress):
        return np.dot((point - self.wipe_point), self.wipe_vector) >= 0