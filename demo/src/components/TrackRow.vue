<template>
  <div class="row m-0">

    <div class="col p-0">

      <Spectrogram :mix-type="mixType" :audio-type="audioType"
                   style="height: 200px;" class=""></Spectrogram>


    </div>

    <div class="col-sm-auto pt-1" style="width: 160px">
      <div class="row">
        <div class="col px-2">
          <h6 class="p-0 pt-1 mb-0 d-inline-block">{{ audioType.name }}</h6>
        </div>


        <div class="p-0 mr-1 col-sm-auto btn-group-toggle" data-toggle="buttons">
          <label class="btn py0 px-2 py-0 font-weight-bold"
                 :class="{'btn-primary': currentSoloAudioType === audioType.key, 'btn-secondary': currentSoloAudioType !== audioType.key}">
            <input @click="solo" :value="audioType.key" type="radio" name="solo" autocomplete="off">
            S
          </label>
        </div>
      </div>

      <!--Knobs-->
      <div class="row-cols-1 pt-2 align-items-center">
        <div v-for="knob in this.knobs" :key="knob.gainIndex" class="col pb-1">
          <div class="row justify-content-center">
            <div class="col-6 p-0">
              <div class="row w-100 h-100 m-0 align-items-center">
                <small class="font-weight-bold col m-0 pr-2 text-right">{{ knob.name }}</small>
              </div>
            </div>

            <div class="col p-0">
              <Knob :color="knob.color" :curve="knob.curve" style="width: 45px; height: 45px"></Knob>
            </div>

          </div>
        </div>

      </div>

    </div>

  </div>
</template>

<script>
import Spectrogram from "@/components/Spectrogram";
import {mapState} from "vuex";
import Knob from "@/components/Knob";

export default {
  name: 'TrackRow',
  components: {Knob, Spectrogram},
  props: ['mixType', 'audioType'],
  data() {
    return {
      audioSource: undefined,
      gainNode: undefined,
      isAudioSourceStarted: false,
    }
  },
  computed: {
    audio() {
      return this.$store.state.currentExample.mixes[this.mixType.key].audios[this.audioType.key]
    },
    audioBuffer() {
      return this.audio.audioBuffer
    },
    curves() {
      return this.audio.curves
    },
    knobs() {
      if (!this.curves || this.mixType.key === 'dj' || this.audioType.key === 'mix') return []

      const knobs = this.mixType.key === 'eq3' ? [
        {name: 'High', curve: [], gainIndex: this.audioType.key === 'prev' ? 2 : 5},
        {name: 'Mid', curve: [], gainIndex: this.audioType.key === 'prev' ? 1 : 4},
        {name: 'Low', curve: [], gainIndex: this.audioType.key === 'prev' ? 0 : 3},
      ] : [
        {name: 'Volume', curve: [], gainIndex: this.audioType.key === 'prev' ? 0 : 1}
      ]

      const colors = this.mixType.key === 'eq3' ? ['red', 'yellow', 'lime', 'cyan', 'blue', 'magenta'] : ['yellow', 'lime']
      for (const knob of knobs) {
        knob.color = colors[knob.gainIndex]
      }

      for (const gains of this.curves) {
        for (const knob of knobs) {
          knob.curve.push(gains[knob.gainIndex])
        }
      }

      return knobs
    },
    isShowing() {
      return this.currentMixType === this.mixType.key
    },
    isSolo() {
      return this.isShowing && (this.currentSoloAudioType === this.audioType.key)
    },
    ...mapState(['audioCtx', 'isPlaying', 'currentExampleIndex', 'currentMixType', 'currentSoloAudioType',
      'startedTime', 'offsetTime'])
  },
  watch: {
    startedTime() {
      this.play()
    },
    offsetTime() {
    },
    isPlaying() {
      if (!this.isPlaying)
        this.pause()
    },
    isSolo() {
      if (this.isSolo) {
        this.unmute()
      } else {
        this.mute()
      }
    }
  },
  methods: {
    initAudio() {
      this.gainNode = this.audioCtx.createGain()
      this.refreshAudioSource()

      if (this.isSolo) {
        this.unmute()
      } else {
        this.mute()
      }
    },
    refreshAudioSource() {
      this.destroyAudioSource()
      this.audioSource = this.audioCtx.createBufferSource()
      this.audioSource.buffer = this.audioBuffer
      this.audioSource.connect(this.gainNode).connect(this.audioCtx.destination)
      this.audioSource.onended = () => {
        this.refreshAudioSource()
        this.$store.commit('ended')
      }
    },
    play() {
      if (this.isAudioSourceStarted) {
        this.refreshAudioSource()
      }
      this.audioSource.start(this.startedTime, this.offsetTime)
      this.isAudioSourceStarted = true
    },
    pause() {
      this.refreshAudioSource()
    },
    mute() {
      this.gainNode.gain.setValueAtTime(0, this.audioCtx.currentTime)
    },
    unmute() {
      this.gainNode.gain.setValueAtTime(1, this.audioCtx.currentTime)
    },
    destroyAudioSource() {
      if (this.audioSource) {
        if (this.isAudioSourceStarted) {
          this.audioSource.onended = undefined
          this.audioSource.stop()
        }
        this.audioSource.disconnect()
        this.gainNode.disconnect()
      }
      this.isAudioSourceStarted = false
    },
    solo() {
      this.$store.commit('changeSolo', {currentSoloAudioType: this.audioType.key})
    }
  },
  created() {
  },
  mounted() {
    this.initAudio()
  },
  destroyed() {
    this.destroyAudioSource()
  }
}
</script>

<style scoped>

</style>