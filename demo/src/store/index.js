import Vue from 'vue'
import Vuex from 'vuex'

const BASE_URL = 'https://d3ta5tpotdqa0v.cloudfront.net/'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    audioCtx: new AudioContext(),
    startedTime: 0,
    offsetTime: 0,
    duration: 0,

    isLoading: true,
    isPlaying: false,
    numLoadedItems: 0,
    totalLoadingItems: 0,

    currentExample: {},
    currentExampleIndex: undefined,
    currentMixType: 'eq3',
    currentSoloAudioType: 'mix',

    examples: [],
    mixTypes: [
      {key: 'dj', name: 'DJ Mix'},
      {key: 'base', name: 'Baseline'},
      {key: 'xfade', name: 'Crossfader'},
      {key: 'eq3', name: 'EQ3'},
    ],
    audioTypes: [
      {key: 'prev', name: 'Previous Track'},
      {key: 'mix', name: 'Mix'},
      {key: 'next', name: 'Next Track'},
    ],
  },
  mutations: {
    init(state, examples) {
      state.examples = examples
      state.currentExampleIndex = Math.floor(Math.random() * state.examples.length)
      state.currentExample = state.examples[state.currentExampleIndex]
    },
    seek(state, {offsetTime}) {
      offsetTime = Math.max(0, offsetTime) // the offsetTime cannot be smaller than 0
      offsetTime = Math.min(state.duration, offsetTime) // the offsetTime cannot be larger than the audio length
      state.offsetTime = offsetTime
      if (state.isPlaying) {
        state.startedTime = state.audioCtx.currentTime
      }
    },
    play(state) {
      if (state.audioCtx.state === 'suspended') {
        state.audioCtx.resume().then(() => {
          if (!state.isPlaying) {
            state.startedTime = state.audioCtx.currentTime
          }
          state.isPlaying = true
        })
      } else {
        if (!state.isPlaying) {
          state.startedTime = state.audioCtx.currentTime
        }
        state.isPlaying = true
      }
    },
    pause(state) {
      if (state.isPlaying) {
        const previousOffsetTime = state.offsetTime
        const playedTime = state.audioCtx.currentTime - state.startedTime
        state.offsetTime = previousOffsetTime + playedTime
      }
      state.isPlaying = false
    },
    ended(state) {
      state.isPlaying = false
      state.offsetTime = 0
    },
    changeSolo(state, {currentSoloAudioType: currentSoloAudioType}) {
      state.currentSoloAudioType = currentSoloAudioType
    },
    changeMixType(state, {mixType}) {
      state.currentMixType = mixType
    },
  },
  actions: {
    async init({state, commit, dispatch}) {
      const response = await fetch(BASE_URL + 'meta.json', {mode: 'cors', cache: 'force-cache'})
      const examples = await response.json()
      commit('init', examples)
      return dispatch('fetchAndChangeExample', {exampleIndex: state.currentExampleIndex})
    },
    fetchAndChangeExample({state, dispatch}, {exampleIndex}) {
      state.isPlaying = false
      state.isLoading = true
      const example = state.examples[exampleIndex]
      state.currentExample = example
      state.currentExampleIndex = exampleIndex

      let promise
      if (example.isLoaded)
        promise = Promise.resolve(example)
      else {
        const promises = []
        example.mixes = {}
        for (const mixType of state.mixTypes) {
          const mix = example.mixes[mixType.key] = {}
          mix.audios = {}
          for (const audioType of state.audioTypes) {
            const audio = mix.audios[audioType.key] = {}

            const audioPath = `audio/${exampleIndex}-${audioType.key}-${mixType.key}.mp3`
            const fetchAudioPromise = dispatch('fetchAudio', {path: audioPath})
              .then((audioBuffer) => audio.audioBuffer = audioBuffer)
              .then(() => state.numLoadedItems++)
            state.totalLoadingItems++

            const specPath = `spec/${exampleIndex}-${audioType.key}-${mixType.key}.png`
            const fetchSpecPromise = dispatch('fetchSpec', {path: specPath})
              .then((imageUrl) => audio.specImageUrl = imageUrl)
              .then(() => state.numLoadedItems++)
            state.totalLoadingItems++

            if (mixType.key !== 'dj') {
              const curvePath = `curve/${exampleIndex}-${mixType.key}.json`
              const fetchCurvePromise = dispatch('fetchCurves', {path: curvePath})
                .then((curves) => audio.curves = curves)
                .then(() => state.numLoadedItems++)
              state.totalLoadingItems++

              promises.push(fetchCurvePromise)
            }

            promises.push(fetchAudioPromise, fetchSpecPromise)
          }
        }

        promise = Promise.all(promises)
      }
      return promise.then(() => {
        example.isLoaded = true
        state.offsetTime = 0
        state.duration = state.currentExample.mixes['dj'].audios['mix'].audioBuffer.duration
        state.isLoading = false
        return example
      })
    },
    async fetchAndSetPrevExample({state, dispatch}) {
      const prevExampleIndex = Math.max(0, state.currentExampleIndex - 1)
      if (prevExampleIndex !== state.currentExampleIndex) {
        await dispatch('fetchAndChangeExample', {exampleIndex: prevExampleIndex})
      }
    },
    async fetchAndSetNextExample({state, dispatch}) {
      const nextExampleIndex = Math.min(state.examples.length - 1, state.currentExampleIndex + 1)
      if (nextExampleIndex !== state.currentExampleIndex) {
        await dispatch('fetchAndChangeExample', {exampleIndex: nextExampleIndex})
      }
    },
    async fetchAudio({state}, {path}) {
      const response = await fetch(BASE_URL + path, {mode: 'cors', cache: 'force-cache'});
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await state.audioCtx.decodeAudioData(arrayBuffer);
      // this.gainNode = this.audioCtx.createGain()
      // this.refreshAudioSource()
      return audioBuffer
    },
    async fetchSpec(_, {path}) {
      // Fetch the spectrogram image as an arraybuffer.
      const response = await fetch(BASE_URL + path, {mode: 'cors', cache: 'force-cache'});
      const imgArrayBuffer = await response.arrayBuffer()
      // Convert the arraybuffer to a blob.
      const blob = new Blob([imgArrayBuffer], {type: 'image/png'});
      const URL = window.URL || window.webkitURL;
      const imageUrl = URL.createObjectURL(blob);

      return imageUrl
    },
    async fetchCurves(_, {path}) {
      const response = await fetch(BASE_URL + path, {mode: 'cors', cache: 'force-cache'})
      const curves = await response.json()  // shape=(#frames, #gains)

      return curves
    },
  },
  modules: {}
})
