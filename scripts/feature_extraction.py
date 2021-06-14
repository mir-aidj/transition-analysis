import pandas as pd
import os
from tqdm import tqdm
from multiprocessing import Pool
from lib.feature import *

df_tlist = pd.read_csv('data/meta/tracklist.csv')


def main():
  with Pool(os.cpu_count() // 2) as pool:
    paths = [f'data/mix/{mix_id}.wav' for mix_id in df_tlist.mix_id.unique()]
    paths += ['data/track/' + filename for filename in df_tlist.filename]
    iterator = pool.imap(extract_feature, paths)
    for _ in tqdm(iterator, total=len(paths)):
      pass


def extract_feature(path):
  beat_chroma_cens(path)
  beat_mfcc(path)


if __name__ == '__main__':
  main()
