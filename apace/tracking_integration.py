import math
import itertools
import numpy as np
from .classes import Drift, Dipole, Quadrupole, Sextupole
from pyprofilers import profile_by_line, simple_timer


# @profile_by_line
def runge_kutta_4(y0, t, h, element):
    k1 = h * y_prime(y0, t, element)
    k2 = h * y_prime(y0 + k1 / 2, t + h / 2, element)
    k3 = h * y_prime(y0 + k2 / 2, t + h / 2, element)
    k4 = h * y_prime(y0 + k3, t + h, element)
    return y0 + (k1 + 2 * k2 + 2 * k3 + k4) / 6, t + h


@profile_by_line
def y_prime(y, t, element):
    out = np.zeros(y.shape)
    # TODO: is a copy needed here?
    out[0] = y[1]
    out[2] = y[3]
    if isinstance(element, Drift):
        out[1] = 0
        out[3] = 0
    elif isinstance(element, Dipole):
        out[1] = -element.k0 / (1 + y[5])
        out[3] = 0
        h = 1 + element.k0 * y[0]
        out[1] *= h ** 2
        out[1] += h * element.k0
        out[3] *= h ** 2
    elif isinstance(element, Quadrupole):
        out[1] = -element.k1 * y[0] / (1 + y[5])
        out[3] = element.k1 * y[2] / (1 + y[5])
    elif isinstance(element, Sextupole):
        out[1] = -element.k2 * (y[0] ** 2 - y[2] ** 2) / (1 + y[5])
        out[3] = 2 * element.k2 * y[0] * y[2] / (1 + y[5])
    else:
        raise Exception(f"Unsupported type {type(element)}.")

    return out


# TODO: this is still experimental and is not well tested!!!
class Tracking:
    def __init__(self, lattice):
        self.lattice = lattice

    def track(self, initial_distribution, step_size_max=0.01, n_turns=1, watchers=None):
        n_particles = initial_distribution.shape[1]
        if watchers is None:
            watchers = np.linspace(0, self.lattice.length)

        n_watchers = len(watchers)
        n_steps = n_watchers * n_turns
        s = np.empty(n_steps)
        trajectory = np.empty((n_steps, 6, n_particles))

        dist = initial_distribution

        for turn in range(n_turns):
            pos = end = 0
            watchers_iter = enumerate(iter(watchers))
            i, watcher = next(watchers_iter)
            for element in self.lattice:
                end += element.length
                while pos < end:
                    watcher_dist = watcher - pos
                    element_dist = end - pos
                    step_size = min(watcher_dist, element_dist, step_size_max)
                    dist, pos = runge_kutta_4(dist, pos, step_size, element)
                    if watcher <= pos:
                        if watcher == pos:
                            j = turn * n_watchers + i
                            trajectory[j] = dist
                            s[j] = pos + turn * self.lattice.length

                        i, watcher = next(watchers_iter, (None, math.inf))

        return s, trajectory
