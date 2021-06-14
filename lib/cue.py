import numpy as np


def find_cue(wp, cue_in=False, num_diag=32):
  """
  Args:
    wp
    cue_in: if True, then output cue-in points, otherwise outputs cue-out points
    num_diag
  Returns:
    (cue point in beats on mix, cue point in beats on track)
  """
  if num_diag == 0:
    if cue_in:
      return wp[-1, 1], wp[-1, 0]
    else:
      return wp[0, 1], wp[0, 0]

  x, y = wp[::-1, 1], wp[::-1, 0]
  dx, dy = np.diff(x), np.diff(y)

  with np.errstate(divide='ignore'):
    slope = dy / dx
  slope[np.isinf(slope)] = 0

  if cue_in:
    slope = slope[::-1].cumsum()
    slope[num_diag:] = slope[num_diag:] - slope[:-num_diag]
    slope = slope[::-1]
    i_diag = np.nonzero(slope == num_diag)[0]
    if len(i_diag) == 0:
      return find_cue(wp, cue_in, num_diag // 2)
    else:
      i = i_diag[0]
      return x[i], y[i]
  else:
    slope = slope.cumsum()
    slope[num_diag:] = slope[num_diag:] - slope[:-num_diag]
    i_diag = np.nonzero(slope == num_diag)[0]
    if len(i_diag) == 0:
      return find_cue(wp, cue_in, num_diag // 2)
    else:
      i = i_diag[-1]
    return x[i] + 1, y[i] + 1
