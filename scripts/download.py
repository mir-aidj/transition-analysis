import pandas as pd
import os
import youtube_dl

os.makedirs('data/mix/', exist_ok=True)
os.makedirs('data/track/', exist_ok=True)

df = pd.read_csv('data/meta/tracklist.csv', skipinitialspace=True)
mix_url = 'https://youtu.be/' + df.iloc[0].mix_id

ydl_opts = {
  'outtmpl': f'data/mix/%(id)s.%(ext)s',
  'format': 'bestaudio/best',
  'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'wav',
  }],
}
query = mix_url
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
  ydl.download([query])

for i, track in df.iterrows():
  ydl_opts = {
    'outtmpl': f'data/track/{i:02}-%(id)s.%(ext)s',
    'format': 'bestaudio/best',
    'postprocessors': [{
      'key': 'FFmpegExtractAudio',
      'preferredcodec': 'wav',
    }],
  }
  query = 'https://youtu.be/' + track.track_id
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([query])
