import numpy as np
import librosa
from joblib import Memory
from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor

SR = 22050
memory = Memory('./cache', verbose=1)


@memory.cache
def beat_activations(path):
  beat_activations_ = RNNBeatProcessor()(path)
  return beat_activations_


@memory.cache
def beats(path, fps=100):
  beat_processor = BeatTrackingProcessor(fps=fps)
  beat_activations_ = beat_activations(path)
  beats_ = beat_processor(beat_activations_)
  return beats_


@memory.cache
def mfcc(path):
  sig_, sr = librosa.load(path)
  mfcc_ = librosa.feature.mfcc(sig_, sr, n_mfcc=12)
  return mfcc_


@memory.cache
def beat_mfcc(path):
  beats_ = beats(path)
  mfcc_ = mfcc(path)
  beat_mfcc_ = beat_aggregate(mfcc_, beats_)
  return beat_mfcc_


@memory.cache
def chroma_cens(path):
  sig, sr = librosa.load(path)
  chroma_cens_ = librosa.feature.chroma_cens(sig, sr)
  return chroma_cens_


@memory.cache
def beat_chroma_cens(path):
  beats_ = beats(path)
  chroma_cens_ = chroma_cens(path)
  beat_chroma_cens_ = beat_aggregate(chroma_cens_, beats_)
  return beat_chroma_cens_


def beat_aggregate(feature, beats, frames_per_beat=None):
  max_frame = feature.shape[1]
  beat_frames = librosa.time_to_frames(beats)
  beat_frames = beat_frames[beat_frames < max_frame]
  beat_feature = np.split(feature, beat_frames, axis=1)
  # Average for each beat.
  beat_feature = beat_feature[1:-1]  # only use chroma features between beats. not before or after beat
  beat_feature = [f.mean(axis=1) for f in beat_feature]  # average chroma features for each beat
  beat_feature = np.array(beat_feature).T
  return beat_feature
