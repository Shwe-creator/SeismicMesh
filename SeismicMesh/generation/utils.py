import copy

import numpy as np
import scipy.sparse as spsparse


def odd(r):
    odds = []
    for i in range(r):
        if i % 2 != 0:
            odds.append(i)
    return odds


def create_staggered_grid(h0, dim, bbox):
    points = np.mgrid[tuple(slice(min, max + h0, h0) for min, max in bbox)].astype(
        float
    )
    odds_rows = odd(points[0].shape[0])
    odds_cols = odd(points[1].shape[0])
    points[1][odds_rows] += h0 / 2
    if dim == 3:
        points[2][odds_cols] += h0 / 2
    points = points.reshape(dim, -1).T
    return points


def make_init_points(bbox, rank, size, axis, h0, dim):
    """Create a structured grid in parallel of the entire domain
    Each processor owns a part of the domain.
    """
    _bbox = copy.deepcopy(bbox)

    for i in range(dim):
        if i == axis:
            new_lims = np.linspace(_bbox[i, 0], _bbox[i, 1], size + 1)
            _bbox[i, :] = new_lims[rank : rank + 2]
            if rank != 0:
                # starting point must be lasts + h0
                prev_lims = new_lims[rank - 1 : rank - 1 + 2]
                tmp = np.mgrid[slice(prev_lims[0], prev_lims[1] + h0, h0)]
                _bbox[i, 0] = tmp[-1] + h0

    points = create_staggered_grid(h0, dim, _bbox)
    return points


def dense(Ix, J, S, shape=None, dtype=None):
    """
    Similar to MATLAB's SPARSE(I, J, S, ...), but instead returning a
    dense array.
    """

    # Advanced usage: allow J and S to be scalars.
    if np.isscalar(J):
        x = J
        J = np.empty(Ix.shape, dtype=int)
        J.fill(x)
    if np.isscalar(S):
        x = S
        S = np.empty(Ix.shape)
        S.fill(x)

    # Turn these into 1-d arrays for processing.
    S = S.flat
    II = Ix.flat
    J = J.flat
    return spsparse.coo_matrix((S, (II, J)), shape, dtype).toarray()
