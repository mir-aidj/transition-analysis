# DJ Mix Transition Analysis [[LIVE WEB DEMO]](https://mir-aidj.github.io/transition-analysis/)
> Taejun Kim, Yi-Hsuan Yang and Juhan Nam  
> "Reverse-Engineering The Transition Regions of Real-World DJ Mixes using Sub-band Analysis with Convex Optimization"  
> _Proceedings of the New Interfaces for Musical Expression (NIME)_, 2021

> Code for **WEB DEMO** can be found [here](demo).

In this example, we are going to use the awesome mix below by Palms Trax since it is one of the author's favorite mixes.
`data/meta/tracklist.csv` contains the tracklist of the mix which is manually collected by the author from YouTube comments.

[![Palms Trax | Boiler Room: Streaming From Isolation | #11](https://img.youtube.com/vi/cPo-qzbGLqE/0.jpg)](https://www.youtube.com/watch?v=cPo-qzbGLqE)

> NOTE: This study and repository are extensions of our previous 
> [study](https://arxiv.org/abs/2008.10267) 
> and [repository](https://github.com/mir-aidj/djmix-analysis), 
> mix-to-track subsequence alignment, a preprocessing step of this transition analysis.

## Outputs
You can get visualizations of transition analysis as shown below after running scripts:

![Transition Visualization](img/viz.png?raw=true "Transition Visualization")

and audio files reproduced by the algorithm under `results` directory:
```sh
# An example directory of result outputs of the first transition
results/00000-cPo-qzbGLqE-05-RocnNoPCZDw-urJv3U_fgCY
├── mix_djmixed.mp3  # transition by the DJ (Palms Trax)
├── mix_reproduced-base.mp3  # transition by baseline
├── mix_reproduced-eq3-subscale.mp3  # transition by our method (EQ-3) 
├── mix_reproduced-xfade.mp3  # transition by previous method (crossfade)
├── next_reproduced-base.mp3  # baseline only applied to the next track
├── next_reproduced-eq3-subscale.mp3  # our method only applied to the next track
├── next_reproduced-xfade.mp3  # previous method only applied to the next track
├── prev_reproduced-base.mp3  # baseline only applied to the previous track
├── prev_reproduced-eq3-subscale.mp3  # our method only applied to the previous track
├── prev_reproduced-xfade.mp3  # previous method only applied to the previous track
├── viz-base.pdf  # visualization of baseline
├── viz-eq3-subscale.pdf  # visualization of our method
└── viz-xfade.pdf  # visualization of previous method
```

## Installing python packages
> NOTE: This repo is written and tested on Python `3.8.10`.

You can install required Python packages using the code below: 
```sh
pip install -r requirements.txt
pip install madmom==0.16.1  # madmom should be installed after installing cython
```


## Running scripts
The scripts should be run in order as described below:
1. `python scripts/download.py` downloads audio files from YouTube.
2. `python scripts/feature_extraction.py` extracts features and saves them under `cache/` using disk-caching of [joblib](https://joblib.readthedocs.io/).
3. `python scripts/alignment.py` performs mix-to-track subsequence DTW and saves the alignment results.
4. `python scripts/segmentation.py` performs mix segmentation and saves the results.
5. `python scripts/reproduce_mixing.py` finally performs transition analysis using convex optimization.


