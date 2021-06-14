import pandas as pd
from glob import glob
from collections import namedtuple
from lib.feature import *

Case = namedtuple('Case', ['features', 'key_invariant'])
CASES = [
  Case(features=['mfcc'], key_invariant=False),
  Case(features=['chroma'], key_invariant=False),
  Case(features=['chroma'], key_invariant=True),
  Case(features=['chroma', 'mfcc'], key_invariant=False),
  Case(features=['chroma', 'mfcc'], key_invariant=True),
]

df_tlist = pd.read_csv('data/meta/tracklist.csv')
df_align = pd.concat([pd.read_pickle(p) for p in glob('data/align/*.pkl')]).set_index('mix_id')
df_align['case'] = df_align.feature
df_align.loc[df_align.key_invariant, 'case'] += '-keyinv'

# Process transition data frame.
prev = df_tlist.copy()
prev = prev.rename(columns={'i_track': 'i_track_prev'})
prev['i_track_next'] = prev.i_track_prev + 1

next = df_tlist.copy()
next = next.rename(columns={'i_track': 'i_track_next'})
df_trans = prev.merge(next, on='i_track_next', suffixes=('_prev', '_next'))
# df_trans = df_trans[['i_track_prev', 'i_track_next', 'timestamp_prev', 'timestamp_next',
#                      'track_id_prev', 'track_id_next']]


def main():
  data = []
  for mix_id in ['cPo-qzbGLqE']:
    result = worker(mix_id)
    data.append(result)
  df = pd.concat(data, ignore_index=True)
  df.to_pickle('data/mix_segmentation.pkl')


def worker(mix_id):
  df_mix_trans = df_trans
  df_mix_align = df_align
  df_mix_align_prev = df_mix_align.copy()
  df_mix_align_prev.columns = df_mix_align_prev.columns + '_prev'
  df_mix_align_prev = df_mix_align_prev.rename(columns={'case_prev': 'case'})
  df_mix_align_next = df_mix_align.copy()
  df_mix_align_next.columns = df_mix_align_next.columns + '_next'
  df_mix_align_next = df_mix_align_next.rename(columns={'case_next': 'case'})
  df = df_mix_trans.merge(df_mix_align_prev).merge(df_mix_align_next)

  mix_path = f'data/mix/{mix_id}.wav'
  mix_beats = beats(mix_path)

  for i, r in df.iterrows():
    if (r.wp_prev[-1, 0] != 0) or (r.wp_next[-1, 0] != 0):
      # Some weird warping path results...
      # I guess the tracks are too long so they are considered as the longer sequence?
      print(f'=> ERROR 1: {mix_id}')
      continue

    if (r.wp_prev.max() > len(mix_beats)) or (r.wp_next.max() > len(mix_beats)):
      print(f'=> ERROR 2: {mix_id}')
      continue

    mix_cue_out_beat = r.mix_cue_out_beat_prev
    mix_cue_in_beat = r.mix_cue_in_beat_next
    mix_cue_mid_beat = (mix_cue_out_beat + mix_cue_in_beat) // 2

    mix_cue_out_time = mix_beats[mix_cue_out_beat]
    mix_cue_in_time = mix_beats[mix_cue_in_beat]
    mix_cue_mid_time = mix_beats[mix_cue_mid_beat]

    # True boundary timestamp in a transition
    timestamp_beat_prev = np.argmin(np.abs(mix_beats - r.timestamp_prev))
    timestamp_beat_next = np.argmin(np.abs(mix_beats - r.timestamp_next))

    df.loc[i, 'mix_cue_out_beat'] = mix_cue_out_beat
    df.loc[i, 'mix_cue_in_beat'] = mix_cue_in_beat
    df.loc[i, 'mix_cue_mid_beat'] = mix_cue_mid_beat
    df.loc[i, 'mix_cue_out_time'] = mix_cue_out_time
    df.loc[i, 'mix_cue_in_time'] = mix_cue_in_time
    df.loc[i, 'mix_cue_mid_time'] = mix_cue_mid_time
    df.loc[i, 'timestamp_beat_prev'] = timestamp_beat_prev
    df.loc[i, 'timestamp_beat_next'] = timestamp_beat_next

  df = df[['case', 'i_track_prev', 'i_track_next', 'track_id_prev', 'track_id_next',
           'match_rate_prev', 'match_rate_next',
           'timestamp_prev', 'timestamp_next',
           'timestamp_beat_prev', 'timestamp_beat_next',
           'mix_cue_out_time', 'mix_cue_in_time', 'mix_cue_mid_time',
           'mix_cue_out_beat', 'mix_cue_in_beat', 'mix_cue_mid_beat',
           'track_cue_in_time_prev', 'track_cue_out_time_prev',
           'track_cue_in_time_next', 'track_cue_out_time_next',
           'track_cue_in_beat_prev', 'track_cue_out_beat_prev',
           'track_cue_in_beat_next', 'track_cue_out_beat_next',
           'key_change_prev', 'key_change_next',
           'wp_prev', 'wp_next',
           'artist_prev', 'artist_next',
           'title_prev', 'title_next',
           ]]
  df['mix_id'] = mix_id

  return df


if __name__ == '__main__':
  main()
