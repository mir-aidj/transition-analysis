import numpy as np
import cvxpy as cp
import pandas as pd
import soundfile as sf
import warnings, traceback
import pytsmod as tsm
import librosa.display
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.cbook.deprecation import MatplotlibDeprecationWarning
from scipy.signal import butter, sosfiltfilt
from pydub import AudioSegment
from tqdm import tqdm
from lib.feature import *
from lib.utils import *

OUT_DIR = 'results'
CASES = [
  dict(model='base', subscale=None),
  dict(model='xfade', subscale=None),
  dict(model='eq3', subscale=True),
  # dict(model='eq3',  subscale=False),
]
MATCH_RATE_THRESHOLD = 0.4

np.set_printoptions(suppress=True)

df = pd.read_pickle('data/mix_segmentation.pkl')
df = df[df.case == 'chroma+mfcc-keyinv']
df = df[(df.match_rate_prev > MATCH_RATE_THRESHOLD) & (df.match_rate_next > MATCH_RATE_THRESHOLD)]
print(f'=> {len(df)} transitions are matched.')

df['translen_beat'] = (df.mix_cue_in_beat - df.mix_cue_out_beat).astype(int)
df['translen_time'] = df.mix_cue_in_time - df.mix_cue_out_time

df['num_beats_prev'] = df.wp_prev.apply(lambda wp: wp[0, 0])
df['num_beats_next'] = df.wp_next.apply(lambda wp: wp[0, 0])

df['avail_trans_beat_prev'] = df.num_beats_prev - df.track_cue_out_beat_prev
df['avail_trans_beat_next'] = df.track_cue_in_beat_next

df['overlap_beat'] = df.avail_trans_beat_prev + df.avail_trans_beat_next - df.translen_beat

# Use only tracks which have audio for transition parts
df = df[df.overlap_beat >= 0]
print(f'=> {len(df)} transitions have overlapping tracks.')

df = df[((df.avail_trans_beat_next - df.translen_beat) >= 0) &
        ((df.avail_trans_beat_prev - df.translen_beat) >= 0)]
print(f'=> {len(df)} transitions have both fully available tracks.')

df = df.reset_index(drop=True)
print(f'=> {len(df)} transitions will be used.')

num_mixes = df.mix_id.nunique()
num_tracks = pd.concat([df.track_id_prev, df.track_id_next]).nunique()
num_trans = len(df)
print(f'=> #mixes={num_mixes} #tracks={num_tracks}')

mix_path = mkpath('./data/mix', f'{df.mix_id.iloc[0]}.wav')
mix, _ = librosa.load(mix_path, sr=48000, mono=False)


def main():
  os.makedirs(OUT_DIR, exist_ok=True)

  for x in tqdm(df.iterrows(), total=len(df)):
    estimate_eq_curve(x)

  print('\n=> Done.\n')


def estimate_eq_curve(args, min_beats=140, sr=48000, gain_adjust_sec=4,
                      cutoff_low=180, cutoff_high=3000, order_lowhigh=2, order_mid=1):
  warnings.filterwarnings('ignore', category=MatplotlibDeprecationWarning)
  warnings.filterwarnings('ignore', category=UserWarning, message='PySoundFile failed. Trying audioread instead')

  i_trans, t = args

  result_dir = f'{OUT_DIR}/{i_trans:05}-{t.mix_id}-{t.i_track_prev:02}-{t.track_id_prev}-{t.track_id_next}'
  os.makedirs(result_dir, exist_ok=True)

  try:
    track_path_prev = mkpath('./data/track', f'{t.i_track_prev:02}-{t.track_id_prev}.wav')
    track_path_next = mkpath('./data/track', f'{t.i_track_next:02}-{t.track_id_next}.wav')

    pad_beats = max(min_beats - t.translen_beat, 0) // 2  # make the transition length at least 140 beats (70 seconds)

    track_prev, _ = librosa.load(track_path_prev, sr=sr, mono=False)
    track_next, _ = librosa.load(track_path_next, sr=sr, mono=False)

    mix_beats = beats(mix_path)
    track_beats_prev = beats(track_path_prev)
    track_beats_next = beats(track_path_next)

    start_beat_mix = int(t.mix_cue_out_beat - pad_beats)
    end_beat_mix = int(t.mix_cue_in_beat + pad_beats)
    trans_beats_mix = mix_beats[start_beat_mix:end_beat_mix]
    num_opt_beats = len(trans_beats_mix)

    trans_beat_samples_mix = librosa.time_to_samples(trans_beats_mix, sr)
    start_sample_mix, end_sample_mix = trans_beat_samples_mix[[0, -1]]
    trans_mix = mix[:, start_sample_mix:end_sample_mix]
    write_audio(result_dir + '/mix_djmixed', trans_mix, sr)

    start_beat_prev = t.track_cue_out_beat_prev - pad_beats
    end_beat_prev = start_beat_prev + num_opt_beats
    trans_beats_prev = track_beats_prev[start_beat_prev:end_beat_prev]

    end_beat_next = t.track_cue_in_beat_next + pad_beats
    start_beat_next = end_beat_next - num_opt_beats
    trans_beats_next = track_beats_next[max(start_beat_next, 0):end_beat_next]

    trans_beat_samples_prev = librosa.time_to_samples(trans_beats_prev, sr)
    trans_beat_samples_next = librosa.time_to_samples(trans_beats_next, sr)

    # TODO: Currently, I'm just ignoring segments before/after the first/last beat.
    start_sample_prev, end_sample_prev = trans_beat_samples_prev[[0, -1]]
    trans_track_prev = track_prev[:, start_sample_prev:end_sample_prev]

    start_sample_next, end_sample_next = trans_beat_samples_next[[0, -1]]
    trans_track_next = track_next[:, start_sample_next:end_sample_next]

    tsm_factor_prev = np.array([
      trans_beat_samples_prev - trans_beat_samples_prev[0],
      trans_beat_samples_mix[:len(trans_beat_samples_prev)] - trans_beat_samples_mix[0]
    ])
    trans_track_prev_tsm = tsm.wsola(trans_track_prev, tsm_factor_prev)

    tsm_factor_next = np.array([
      trans_beat_samples_next - trans_beat_samples_next[0],
      trans_beat_samples_mix[-len(trans_beat_samples_next):] - trans_beat_samples_mix[-len(trans_beat_samples_next)]
    ])
    trans_track_next_tsm = tsm.wsola(trans_track_next, tsm_factor_next)

    if trans_track_prev_tsm.shape[-1] > trans_mix.shape[-1]:
      trans_track_prev_full = trans_track_prev_tsm[:, :trans_mix.shape[-1]]
    elif trans_track_prev_tsm.shape[-1] < trans_mix.shape[-1]:
      pad_prev = np.zeros((2, trans_mix.shape[-1] - trans_track_prev_tsm.shape[-1]))
      trans_track_prev_full = np.concatenate([trans_track_prev_tsm, pad_prev], axis=1)
    else:
      trans_track_prev_full = trans_track_prev_tsm

    if trans_track_next_tsm.shape[-1] > trans_mix.shape[-1]:
      trans_track_next_full = trans_track_next_tsm[:, :trans_mix.shape[-1]]
    elif trans_track_next_tsm.shape[-1] < trans_mix.shape[-1]:
      pad_next = np.zeros((2, trans_mix.shape[-1] - trans_track_next_tsm.shape[-1]))
      trans_track_next_full = np.concatenate([pad_next, trans_track_next_tsm], axis=1)
    else:
      trans_track_next_full = trans_track_next_tsm

    # Make audio gains equal
    gain_prev = rms(trans_mix[:, :(sr * gain_adjust_sec)]) / rms(trans_track_prev[:, :(sr * gain_adjust_sec)])
    gain_next = rms(trans_mix[:, -(sr * gain_adjust_sec):]) / rms(trans_track_next[:, -(sr * gain_adjust_sec):])

    trans_track_prev_full *= gain_prev
    trans_track_next_full *= gain_next

    # Seconds per beat is 0.5 for 120 bpm song. If we assume there will be 8 controls per beat than fps is:
    fps = int(1 / (0.5 / 8))  # frames per second: 16
    hop = int(1 / fps * sr)

    trans_spec_mix = librosa.feature.melspectrogram(librosa.to_mono(trans_mix),
                                                    sr=sr, n_fft=hop * 2, hop_length=hop, n_mels=128)
    trans_spec_prev = librosa.feature.melspectrogram(librosa.to_mono(trans_track_prev_full),
                                                     sr=sr, n_fft=hop * 2, hop_length=hop, n_mels=128)
    trans_spec_next = librosa.feature.melspectrogram(librosa.to_mono(trans_track_next_full),
                                                     sr=sr, n_fft=hop * 2, hop_length=hop, n_mels=128)
    num_frames = trans_spec_mix.shape[-1]

    # ----------------------------------------------------------------------------------------
    # Iterate cases
    # ----------------------------------------------------------------------------------------
    for case in CASES:
      model = case['model']
      case_name = model + ('-subscale' if case['subscale'] else '')
      case_result_path = result_dir + f'/results-{case_name}.pkl'

      # Extract curves!
      if model == 'base':
        curves_prev = np.linspace(1, 0, num_frames).reshape(1, -1)
        curves_next = np.linspace(0, 1, num_frames).reshape(1, -1)
        probs = []
      else:
        curves_prev, curves_next, probs = extract_curves(trans_spec_mix, trans_spec_prev, trans_spec_next, **case)

      # ----------------------------------------------------------------------------------------
      # Plot results
      # ----------------------------------------------------------------------------------------
      cmap = 'magma'
      if model == 'eq3':
        colors = ['red', 'yellow', 'lime', 'cyan', 'blue', 'magenta']
        labels = ['Prev Low', 'Prev Mid', 'Prev High', 'Next Low', 'Next Mid', 'Next High']
      else:  # xfade, base
        colors = ['yellow', 'lime']
        labels = ['Prev Gain', 'Next Gain']

      linewidth_beat = 1
      linewidth_eq = 2

      beat_frames = librosa.time_to_frames(trans_beats_mix, sr=sr, hop_length=hop, n_fft=hop * 2)
      beat_frames = beat_frames - beat_frames[0]

      curves = np.concatenate([curves_prev, curves_next]).T
      fig, axes = plt.subplots(3, 1, figsize=(16, 8))

      # Previous track --------------------------------------------------------
      ax = axes[0]
      # Spectrogram
      librosa.display.specshow(librosa.power_to_db(trans_spec_prev), x_axis='frames', y_axis='mel', cmap=cmap, ax=ax)
      # Beat grid
      [ax.axvline(beat, color='black', linewidth=linewidth_beat) for beat in beat_frames]
      # Cue points
      ax.axvline(beat_frames[pad_beats], color='white', linestyle='-', linewidth=linewidth_eq)
      # Curves
      axeq = ax.twinx()  # instantiate a second axes that shares the same x-axis
      for i_curve in range(curves.shape[1] // 2):
        axeq.plot(curves[:, i_curve], color=colors[i_curve], linewidth=linewidth_eq)
      axeq.set_ylim(-0.05, 1.05)
      axeq.set_ylabel('EQ')
      # X-axis
      ax.set_xlabel(None)
      ax.set_xticks([])
      # Legends
      patches = [mpatches.Patch(color=color, label=label) for color, label in zip(colors, labels)]
      patches += [
        mpatches.Patch(color='white', label='Cue-out/-in'),
        mpatches.Patch(color='black', label='Beat')
      ]
      ax.legend(loc='upper right', handles=patches)
      # Text
      plt.text(0.01, 0.53, 'Previous Track', transform=ax.transAxes, fontsize=18, color='white',
               bbox=dict(facecolor='black', alpha=0.7, edgecolor='black'))
      text_prev = f'[{t.timestamp_prev // 60:02}:{t.timestamp_prev % 60:02}] {t.artist_prev} - {t.title_prev}'
      plt.text(0.01, 0.38, text_prev, transform=ax.transAxes, fontsize=12, color='white',
               bbox=dict(facecolor='black', alpha=0.7, edgecolor='black'))

      # Mix ---------------------------------------------------------------
      ax = axes[1]
      # Spectrogram
      librosa.display.specshow(librosa.power_to_db(trans_spec_mix), x_axis='frames', y_axis='mel', cmap=cmap, ax=ax)
      # Beat grid
      [ax.axvline(beat, color='black', linewidth=linewidth_beat) for beat in beat_frames]
      # Cue points
      ax.axvline(beat_frames[pad_beats], color='white', linestyle='-', linewidth=linewidth_eq)
      ax.axvline(beat_frames[-pad_beats], color='white', linestyle='-', linewidth=linewidth_eq)
      # Curves
      axeq = ax.twinx()  # instantiate a second axes that shares the same x-axis
      for i_curve in range(curves.shape[1]):
        axeq.plot(curves[:, i_curve], color=colors[i_curve], linewidth=linewidth_eq)
      axeq.set_ylim(-0.05, 1.05)
      axeq.set_ylabel('EQ')
      # X-axis
      ax.set_xlabel(None)
      ax.set_xticks([])
      # Text
      mix_start_time = start_sample_mix // sr
      text_mix = f'[{mix_start_time // 60:02}:{mix_start_time % 60:02}] DJ Mix'
      plt.text(0.01, 0.45, text_mix, transform=ax.transAxes, fontsize=18, color='white',
               bbox=dict(facecolor='black', alpha=0.7, edgecolor='black'))

      # Next track ------------------------------------------------------------------
      ax = axes[2]
      # Spectrogram
      librosa.display.specshow(librosa.power_to_db(trans_spec_next), x_axis='frames', y_axis='mel', cmap=cmap, ax=ax)
      # Beat grid
      [ax.axvline(beat, color='black', linewidth=linewidth_beat) for beat in beat_frames]
      # Cue points
      ax.axvline(beat_frames[-pad_beats], color='white', linestyle='-', linewidth=linewidth_eq)
      # Curves
      axeq = ax.twinx()  # instantiate a second axes that shares the same x-axis
      for i_curve in range(curves.shape[1] // 2, curves.shape[1]):
        axeq.plot(curves[:, i_curve], color=colors[i_curve], linewidth=linewidth_eq)
      axeq.set_ylim(-0.05, 1.05)
      axeq.set_ylabel('EQ')
      # X-axis
      ax.set_xticks(np.arange(0, num_frames, int(fps * 5)))  # tick every 5 seconds
      ax.set_xticklabels(librosa.frames_to_time(ax.get_xticks(), sr=sr, hop_length=hop, n_fft=hop * 2).astype(int))
      ax.set_xlabel('Time (seconds)')
      # Text
      plt.text(0.01, 0.53, 'Next Track', transform=ax.transAxes, fontsize=18, color='white',
               bbox=dict(facecolor='black', alpha=0.7, edgecolor='black'))
      text_next = f'[{t.timestamp_next // 60:02}:{t.timestamp_next % 60:02}] {t.artist_next} - {t.title_next}'
      plt.text(0.01, 0.38, text_next, transform=ax.transAxes, fontsize=12, color='white',
               bbox=dict(facecolor='black', alpha=0.7, edgecolor='black'))

      plt.subplots_adjust(wspace=0, hspace=0)
      plt.tight_layout()
      plt.savefig(result_dir + f'/viz-{case_name}.pdf')
      plt.close()

      # ----------------------------------------------------------------------------------------
      # Reproduce mixing
      # ----------------------------------------------------------------------------------------
      segments_prev = np.array_split(trans_track_prev_full, num_frames, axis=1)
      segments_next = np.array_split(trans_track_next_full, num_frames, axis=1)

      if model == 'xfade' or model == 'base':
        mixed_prev = [gain * seg for gain, seg in zip(curves_prev.flatten(), segments_prev)]
        mixed_prev = np.concatenate(mixed_prev, axis=1)

        mixed_next = [gain * seg for gain, seg in zip(curves_next.flatten(), segments_next)]
        mixed_next = np.concatenate(mixed_next, axis=1)

        mixed = mixed_prev + mixed_next

      elif model == 'eq3':
        nyq = 0.5 * sr  # sr: sampling rate (Hz)

        # Low EQ
        normal_cutoff_low = cutoff_low / nyq
        sos_low = butter(order_lowhigh, normal_cutoff_low, btype='highpass', analog=False, output='sos')

        # High EQ
        normal_cutoff_high = cutoff_high / nyq
        sos_high = butter(order_lowhigh, normal_cutoff_high, btype='lowpass', analog=False, output='sos')

        # Mid EQ
        normal_cutoff_mid = np.array([cutoff_low, cutoff_high]) / nyq
        sos_mid = butter(order_mid, normal_cutoff_mid, btype='bandstop', analog=False, output='sos')

        mixed_prev = []
        for (gain_low, gain_mid, gain_high), segment in zip(curves[:, :3], segments_prev):
          # Apply EQ filters
          if (gain_low + gain_mid + gain_high) < 0.4:
            out = np.zeros_like(segment)
          else:
            out = segment.copy()
            out = gain_low * out + (1.0 - gain_low) * sosfiltfilt(sos_low, out)
            out = gain_high * out + (1.0 - gain_high) * sosfiltfilt(sos_high, out)
            out = gain_mid * out + (1.0 - gain_mid) * sosfiltfilt(sos_mid, out)
          mixed_prev.append(out)
        mixed_prev = np.concatenate(mixed_prev, axis=1)

        mixed_next = []
        for (gain_low, gain_mid, gain_high), segment in zip(curves[:, -3:], segments_next):
          # Apply EQ filters
          if (gain_low + gain_mid + gain_high) < 0.4:
            out = np.zeros_like(segment)
          else:
            out = segment.copy()
            out = gain_low * out + (1.0 - gain_low) * sosfiltfilt(sos_low, out)
            out = gain_high * out + (1.0 - gain_high) * sosfiltfilt(sos_high, out)
            out = gain_mid * out + (1.0 - gain_mid) * sosfiltfilt(sos_mid, out)
          mixed_next.append(out)
        mixed_next = np.concatenate(mixed_next, axis=1)

        mixed = mixed_prev + mixed_next
      else:
        raise Exception(f'Unknown model: {model}')

      eval_spec_dj_power = librosa.feature.melspectrogram(librosa.to_mono(trans_mix), sr=sr)
      eval_spec_reprod_power = librosa.feature.melspectrogram(librosa.to_mono(mixed), sr=sr)
      eval_spec_dj_db = librosa.power_to_db(eval_spec_dj_power, ref=1.0)
      eval_spec_reprod_db = librosa.power_to_db(eval_spec_reprod_power, ref=1.0)

      mse_power = ((eval_spec_dj_power - eval_spec_reprod_power) ** 2).mean()
      mse_db = ((eval_spec_dj_db - eval_spec_reprod_db) ** 2).mean()
      rmse_power = np.sqrt(mse_power)
      rmse_db = np.sqrt(mse_db)

      # Write reproduced audios.
      write_audio(result_dir + f'/mix_reproduced-{case_name}', mixed, sr)
      write_audio(result_dir + f'/prev_reproduced-{case_name}', mixed_prev, sr)
      write_audio(result_dir + f'/next_reproduced-{case_name}', mixed_next, sr)

      # Prepare result series.
      result = t.copy()
      result.rename({'case': 'case_align'})
      result['i_trans'] = i_trans
      result['case'] = case_name
      result['model'] = model
      result['subscale'] = case['subscale']
      result['mse_power'] = mse_power
      result['mse_db'] = mse_db
      result['rmse_power'] = rmse_power
      result['rmse_db'] = rmse_db
      result['gain_prev'] = gain_prev
      result['gain_next'] = gain_next
      result['pad_beats'] = pad_beats
      result['num_frames'] = num_frames
      result['curves'] = curves
      result['opt_mse'] = [prob.value for prob in probs]
      result['opt_status'] = [prob.status for prob in probs]

      result.to_pickle(case_result_path)

  except Exception:
    traceback.print_exc()
    print(f'=> Error to process: {t.mix_id} {t.i_track_prev}-{t.i_track_next}')


def write_audio(path, data, sr):
  sf.write(path + '.wav', data.T, sr)
  AudioSegment.from_wav(path + '.wav').export(path + '.mp3', format='mp3', bitrate='64')
  os.remove(path + '.wav')


def extract_curves(trans_spec_mix, trans_spec_prev, trans_spec_next, model, subscale):
  if model == 'eq3':
    curves_prev, curves_next, probs = cvxopt_eq3(trans_spec_mix, trans_spec_prev, trans_spec_next, subscale)
  elif model == 'xfade':
    curves_prev, curves_next, probs = cvxopt_xfade(trans_spec_mix, trans_spec_prev, trans_spec_next)
  else:
    raise Exception(f'Unknown model: {model}')

  return curves_prev, curves_next, probs


def cvxopt_eq3(trans_spec_mix, trans_spec_prev, trans_spec_next, subscale):
  mel_cutoffs = [0, 10, 80, 128]
  losses = []
  eqs = cp.Variable(shape=(6, trans_spec_mix.shape[-1]))
  constraints = [
    0 <= eqs, eqs <= 1,
    0 >= cp.diff(eqs[:3], axis=1),
    0 <= cp.diff(eqs[3:], axis=1),
  ]

  # Normalize
  norm_factor = max(trans_spec_mix.max(), trans_spec_prev.max(), trans_spec_next.max())
  trans_spec_mix = trans_spec_mix / norm_factor
  trans_spec_prev = trans_spec_prev / norm_factor
  trans_spec_next = trans_spec_next / norm_factor

  for i_eq in range(3):
    eq_prev, eq_next = eqs[[i_eq]], eqs[[i_eq + 3]]

    mel_start, mel_end = mel_cutoffs[i_eq], mel_cutoffs[i_eq + 1]
    subband_spec_mix = trans_spec_mix[mel_start:mel_end]
    subband_spec_prev = trans_spec_prev[mel_start:mel_end]
    subband_spec_next = trans_spec_next[mel_start:mel_end]

    if subscale:
      norm_factor = max(subband_spec_mix.max(), subband_spec_prev.max(), subband_spec_next.max())
      subband_spec_mix = subband_spec_mix / norm_factor
      subband_spec_prev = subband_spec_prev / norm_factor
      subband_spec_next = subband_spec_next / norm_factor

    mixed = cp.multiply(eq_prev, subband_spec_prev) + cp.multiply(eq_next, subband_spec_next)
    loss = cp.sum_squares(mixed - subband_spec_mix)
    losses.append(loss)

  # Form and solve problem.
  obj = cp.Minimize(cp.sum(losses) / np.prod(trans_spec_mix.shape) * 10e4)
  prob = cp.Problem(obj, constraints)
  prob.solve(solver='ECOS', verbose=False)  # Returns the optimal value.

  curves_prev = eqs[:3].value
  curves_next = eqs[3:].value
  probs = [prob]

  return curves_prev, curves_next, probs


def cvxopt_xfade(trans_spec_mix, trans_spec_prev, trans_spec_next):
  # Optimize using a single crossfader.
  W = cp.Variable(shape=(2, trans_spec_mix.shape[-1]))

  constraints = [
    0 <= W, W <= 1,
    0 >= cp.diff(W[0], axis=0),
    0 <= cp.diff(W[1], axis=0),
    1 == cp.sum(W, axis=0),  # prev_volume + next_volume = 1
  ]

  # Normalize
  norm_factor = max(trans_spec_mix.max(), trans_spec_prev.max(), trans_spec_next.max())
  trans_spec_mix = trans_spec_mix / norm_factor
  trans_spec_prev = trans_spec_prev / norm_factor
  trans_spec_next = trans_spec_next / norm_factor

  mixed = cp.multiply(W[[0]], trans_spec_prev) + cp.multiply(W[[1]], trans_spec_next)
  loss = cp.sum_squares(mixed - trans_spec_mix) / np.prod(trans_spec_mix.shape)
  obj = cp.Minimize(loss)

  # Form and solve problem.
  prob = cp.Problem(obj, constraints)
  prob.solve(solver='ECOS', verbose=False)  # Returns the optimal value.

  curves_prev = W[:1].value
  curves_next = W[1:].value
  probs = [prob]

  return curves_prev, curves_next, probs


def rms(x):
  return np.sqrt(np.mean(np.abs(x) ** 2))


if __name__ == '__main__':
  main()
