import pandas as pd
import os
from collections import namedtuple
from lib.feature import *
from lib.cue import find_cue

Case = namedtuple('Case', ['features', 'key_invariant'])
CASES = [
  Case(features=['mfcc'], key_invariant=False),
  Case(features=['chroma'], key_invariant=False),
  Case(features=['chroma'], key_invariant=True),
  Case(features=['chroma', 'mfcc'], key_invariant=False),
  Case(features=['chroma', 'mfcc'], key_invariant=True),
]

df_tlist = pd.read_csv('data/meta/tracklist.csv')


def main():
  os.makedirs('data/align', exist_ok=True)
  for case in CASES:
    alignment('cPo-qzbGLqE', features=case.features, key_invariant=case.key_invariant)


def alignment(mix_id, features=['chroma', 'mfcc'], key_invariant=True):
  feature_id = feature = '+'.join(features)
  result_path = f'data/align/{mix_id}-{feature_id}'
  if key_invariant:
    result_path += '-key_invariant'
  result_path += '.pkl'
  if os.path.isfile(result_path):
    print(f'=> Skip processing: {result_path}')
    return pd.read_pickle(result_path)

  mix_path = f'data/mix/{mix_id}.wav'
  mix_feature = extract_feature(mix_path, features)
  mix_beats = beats(mix_path)

  data = []
  for _, track in df_tlist.iterrows():
    track_path = f'data/track/{track.filename}'
    track_feature = extract_feature(track_path, features)

    pitch_shifts = np.arange(12) if key_invariant else [0]
    best_cost = np.inf
    best_key_change = np.nan
    best_wp = None
    costs = []
    for pitch_shift in pitch_shifts:
      if pitch_shift == 0:
        X, Y = track_feature, mix_feature
      else:
        X, Y = track_feature.copy(), mix_feature.copy()
        X[:12] = np.roll(X[:12], pitch_shift, axis=0)  # circular pitch shifting

      # Subsequence DTW.
      D, wp = librosa.sequence.dtw(X, Y, subseq=True)

      # Compute the cost and keep the results if they are the best.
      matching_function = D[-1, :] / wp.shape[0]
      cost = matching_function.min()
      costs.append(cost)
      if cost < best_cost:
        best_cost = cost
        best_key_change = pitch_shift
        best_wp = wp

    # Compute match rate
    x = best_wp[:, 1][::-1]
    y = best_wp[:, 0][::-1]
    dydx = np.diff(y) / np.diff(x)
    match_rate = (dydx == 1).sum() / len(dydx)

    # Compute cue_points
    track_beats = beats(track_path)

    mix_cue_in_beat, track_cue_in_beat = find_cue(best_wp, cue_in=True)
    mix_cue_out_beat, track_cue_out_beat = find_cue(best_wp, cue_in=False)
    mix_cue_in_time, track_cue_in_time = mix_beats[mix_cue_in_beat], track_beats[track_cue_in_beat]
    mix_cue_out_time, track_cue_out_time = mix_beats[mix_cue_out_beat], track_beats[track_cue_out_beat]

    data.append((
      mix_id, track.track_id, feature, key_invariant, match_rate, best_key_change, best_cost, costs, best_wp,
      mix_cue_in_time, mix_cue_out_time, track_cue_in_time, track_cue_out_time,
      mix_cue_in_beat, mix_cue_out_beat, track_cue_in_beat, track_cue_out_beat,
    ))

  df_result = pd.DataFrame(data, columns=[
    'mix_id', 'track_id', 'feature', 'key_invariant', 'match_rate', 'key_change', 'best_cost', 'costs', 'wp',
    'mix_cue_in_time', 'mix_cue_out_time', 'track_cue_in_time', 'track_cue_out_time',
    'mix_cue_in_beat', 'mix_cue_out_beat', 'track_cue_in_beat', 'track_cue_out_beat',
  ])
  df_result.to_pickle(result_path)
  print(f'=> Saved: {result_path}')
  return df_result


def extract_feature(path, feature_names):
  combined_feature = []
  for feature_name in feature_names:
    if feature_name == 'chroma':
      f = beat_chroma_cens(path).astype('float32')
    elif feature_name == 'mfcc':
      f = beat_mfcc(path).astype('float32')
    else:
      raise Exception(f'Unknown feature: {feature_name}')
    f = (f - f.mean()) / f.std()
    combined_feature.append(f)
  combined_feature = np.concatenate(combined_feature, axis=0)
  return combined_feature


if __name__ == '__main__':
  main()
