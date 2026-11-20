"""Cubical union of threshold voxels; 26-connected solid / 6-connected complement."""
import numpy as np
from scipy import ndimage


def cubical_chi(mask):
    # Each cell contributes to one set of vertices, three edge sets and three face sets.
    cells = np.pad(mask, 1)
    def incident(axes):
        occupied = cells
        for axis in axes:
            occupied = occupied | np.roll(occupied, 1, axis)
        return np.count_nonzero(occupied)
    return int(incident((0,1,2)) - sum(incident(axes) for axes in ((0,1),(0,2),(1,2)))
               + sum(incident((axis,)) for axis in range(3)) - mask.sum())


def component_topology(magnitude, fraction):
    peak = float(magnitude.max())
    if peak < 1e-10:
        return {"cells": 0, "tunnels": 0, "cavities": 0, "touches_boundary": False, "candidate": False}
    labels, _ = ndimage.label(magnitude >= fraction*peak, structure=np.ones((3,3,3), dtype=bool))
    counts = np.bincount(labels.ravel())
    number = int(np.argmax(counts[1:])+1)
    cells = labels == number
    slices = ndimage.find_objects(cells.astype(np.int8))[0]
    touches = any(s.start == 0 or s.stop == n for s,n in zip(slices, cells.shape))
    selected = cells[slices]
    _, empty = ndimage.label(~np.pad(selected, 1), structure=ndimage.generate_binary_structure(3, 1))
    cavities = empty - 1
    tunnels = 1 + cavities - cubical_chi(selected)
    return {"cells": int(counts[number]), "tunnels": tunnels, "cavities": cavities,
            "touches_boundary": touches, "candidate": tunnels == 1 and cavities == 0 and not touches}
