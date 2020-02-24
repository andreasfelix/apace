import apace as ap


def test_tune(fodo_ring):
    import numpy as np
    from scipy.fftpack import fft

    n_particles = 10
    n_turns = 10000

    dist = ap.distribution(n_particles, x_dist="uniform", x_width=0.02, x_center=0.01)
    matrix_tracking = ap.MatrixTracking(fodo_ring, dist, turns=n_turns, watch_points=0)
    period_time = fodo_ring.length / 299_792_458
    freq = np.linspace(0.0, 1.0 / (2.0 * period_time), n_turns // 2)
    tmp = matrix_tracking.particle_trajectories[:, 0, -1]
    fft_tracking = 2.0 / n_turns * np.abs(fft(tmp))[: n_turns // 2]
    tune_khz = freq[np.argmax(fft_tracking)] / 1e3
    tune_fractional = tune_khz * period_time * 1e3
    assert 643 == round(tune_khz)
    assert 0.8970 == round(1 - tune_fractional, 4)


def test_particle_trajectory(fodo_ring):
    """Compare particle trajectory from matrix tracking x(s) with particle trajectory
    from beta functions x(s) = sqrt(beta_x * e) * cos(psi_x + psi_x0).
    """
    from math import sqrt, cos
    import numpy as np

    n_particles = 1
    n_turns = 1

    dist = ap.distribution(n_particles, x_dist="uniform", x_center=0.01)
    matrix_tracking = ap.MatrixTracking(
        fodo_ring, dist, turns=n_turns, watch_points=None
    )
    twiss = ap.Twiss(fodo_ring)
    x = matrix_tracking.x
    beta_x = twiss.beta_x
    psi_x = twiss.psi_x

    low, high = 0, x.shape[0]
    np.random.seed(0)
    # for pos_1 in np.random.randint(low, high, 10):
    #     for pos_2 in np.random.randint(low, high, 10):
    pos_2 = 5
    breakpoint()
    for pos_1 in range(twiss.n_points):
        # for pos_2 in range(twiss.n_points):
        term_1 = x[pos_1, 0] * sqrt(beta_x[pos_2]) * cos(psi_x[pos_2])
        term_2 = x[pos_2, 0] * sqrt(beta_x[pos_1]) * cos(psi_x[pos_1])
        assert abs(term_1 - term_2) < 0.001  # TODO: use smaller diff
