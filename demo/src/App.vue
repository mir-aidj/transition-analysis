<template>
  <div id="app" class="h-100">
    <div v-if="!isLoading" class="container-fluid">
      <h2 class="text-center mt-2">DJ Mix Transition Analysis</h2>


      <div class="row border-bottom"></div>
      <Panel v-for="mixType in mixTypes" :key="mixType.key" :mix-type="mixType"></Panel>

      <div class="row align-items-center mt-1">
        <div class="col-sm-auto">

          <span @click="prevExample" class="btn p-0">
            <svg width="2em" height="2em" viewBox="0 0 16 16" class="bi bi-skip-start" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path fill-rule="evenodd" d="M4.5 3.5A.5.5 0 0 0 4 4v8a.5.5 0 0 0 1 0V4a.5.5 0 0 0-.5-.5z"/>
              <path fill-rule="evenodd" d="M5.696 8L11.5 4.633v6.734L5.696 8zm-.792-.696a.802.802 0 0 0 0 1.392l6.363 3.692c.52.302 1.233-.043 1.233-.696V4.308c0-.653-.713-.998-1.233-.696L4.904 7.304z"/>
            </svg>
          </span>

          <span v-show="isPlaying" @click="pauseAll" class="btn p-0">
            <svg width="3em" height="3em" viewBox="0 0 16 16" class="bi bi-pause" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-1 0V4a.5.5 0 0 1 .5-.5zm4 0a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-1 0V4a.5.5 0 0 1 .5-.5z"/>
            </svg>
          </span>

          <span v-show="!isPlaying" @click="playAll" class="btn p-0">
            <svg width="3em" height="3em" viewBox="0 0 16 16" class="bi bi-play" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path fill-rule="evenodd" d="M10.804 8L5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 0 1 0 1.392l-6.363 3.692C4.713 12.69 4 12.345 4 11.692V4.308c0-.653.713-.998 1.233-.696l6.363 3.692z"/>
            </svg>
          </span>

          <span @click="nextExample" class="btn p-0">
            <svg width="2em" height="2em" viewBox="0 0 16 16" class="bi bi-skip-end" fill="white" xmlns="http://www.w3.org/2000/svg">
              <path fill-rule="evenodd" d="M12 3.5a.5.5 0 0 1 .5.5v8a.5.5 0 0 1-1 0V4a.5.5 0 0 1 .5-.5z"/>
              <path fill-rule="evenodd" d="M10.804 8L5 4.633v6.734L10.804 8zm.792-.696a.802.802 0 0 1 0 1.392l-6.363 3.692C4.713 12.69 4 12.345 4 11.692V4.308c0-.653.713-.998 1.233-.696l6.363 3.692z"/>
            </svg>
          </span>

        </div>


        <div class="col-sm-auto">
          <div class="btn-group" role="group">
            <button v-for="(example, exampleIndex) in examples" :key="exampleIndex"
                    :class="{'btn-primary': currentExample === example, 'btn-secondary': currentExample !== example}"
                    @click="changeExample(exampleIndex)" :value="exampleIndex"
                    type="button" class="btn">
              {{ exampleIndex }}
            </button>
          </div>
        </div>


        <div class="col"></div>

        <div class="col-sm-auto">
          <div class="btn-group" role="group">
            <button v-for="mixType in mixTypes" :key="mixType.key"
                    :class="{'btn-primary': currentMixType === mixType.key, 'btn-secondary': currentMixType !== mixType.key}"
                    @click="changeMixType" :value="mixType.key"
                    type="button" class="btn">
              {{ mixType.name }}
            </button>
          </div>
        </div>


      </div>
      <div class="row">
        <div class="col-6">

        </div>
        <div class="col-6 p-0 mt-2">
          <div class="row">
            <h4>Keyboard Shortcuts</h4>
          </div>

          <div class="row">

            <div class="col-6">

              <dl class="row">

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">1</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Solo Previous Track and mute others
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">2</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Solo Mix and mute others
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">3</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Solo Next Track and mute others
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary">
                    <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-right-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12.14 8.753l-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/>
                    </svg>
                  </span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Seek forward 4 seconds
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary">
                    <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-left-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3.86 8.753l5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/>
                    </svg>
                  </span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Seek backward 4 seconds
                </dd>

              </dl>

            </div>
            <div class="col-6">

              <dl class="row">

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">Q</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Select DJ Mix
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">W</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Select Baseline
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">E</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Select Crossfader
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary px-1">R</span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Select EQ3
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary">
                    <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-up-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                      <path d="M7.247 4.86l-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"/>
                    </svg>
                  </span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Previous Example
                </dd>

                <dt class="col-sm-2 text-center p-0">
                  <span class="border border-primary rounded bg-primary">
                    <svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-caret-down-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                      <path d="M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
                    </svg>
                  </span>
                </dt>
                <dd class="col-sm-10 p-0">
                  Next Example
                </dd>

              </dl>

            </div>

          </div>


        </div>
      </div>


    </div>

    <div v-if="isLoading" class="d-flex h-100 justify-content-center align-content-center">
      <div class="align-self-center row">
        <div class="w-100 text-center">
          <div class="spinner-border" style="width: 10rem; height: 10rem;" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>

        <div class="w-100 text-center mt-4">
          <h2>{{ Math.round(numLoadedItems / totalLoadingItems * 100) || 0 }}%</h2>
        </div>
      </div>
    </div>


  </div>

</template>

<script>
import Panel from "@/components/Panel";
import {mapState} from 'vuex'

export default {
  name: 'App',
  computed: {
    ...mapState(['isLoading', 'numLoadedItems', 'totalLoadingItems', 'isPlaying', 'audioCtx', 'startedTime', 'offsetTime',
      'mixTypes', 'currentMixType', 'examples', 'currentExample'])
  },
  components: {
    Panel,
  },
  methods: {
    changeMixType(e) {
      this.$store.commit('changeMixType', {mixType: e.target.value})
    },
    playAll() {
      this.$store.commit('play')
    },
    pauseAll() {
      this.$store.commit('pause')
    },
    changeExample(exampleIndex) {
      this.$store.dispatch('fetchAndChangeExample', {exampleIndex})
          .then(() => {
            console.log(this.offsetTime)
          })
    },
    prevExample() {
      this.$store.dispatch('fetchAndSetPrevExample')

    },
    nextExample() {
      this.$store.dispatch('fetchAndSetNextExample')
    },
    handleShortcuts(event) {
      console.log(event)
      const shortcutHandlers = {
        Space: () => {
          if (this.isPlaying) {
            this.$store.commit('pause')
          } else {
            this.$store.commit('play')
          }
        },
        Digit1: () => {
          this.$store.commit('changeSolo', {currentSoloAudioType: 'prev'})
        },
        Digit2: () => {
          this.$store.commit('changeSolo', {currentSoloAudioType: 'mix'})
        },
        Digit3: () => {
          this.$store.commit('changeSolo', {currentSoloAudioType: 'next'})
        },
        KeyQ: () => {
          this.$store.commit('changeMixType', {mixType: 'dj'})
        },
        KeyW: () => {
          this.$store.commit('changeMixType', {mixType: 'base'})
        },
        KeyE: () => {
          this.$store.commit('changeMixType', {mixType: 'xfade'})
        },
        KeyR: () => {
          this.$store.commit('changeMixType', {mixType: 'eq3'})
        },
        ArrowRight: () => {
          const playedTime = this.isPlaying ? this.audioCtx.currentTime - this.startedTime : 0
          const forwardOffsetTime = this.offsetTime + playedTime + 4
          this.$store.commit('seek', {offsetTime: forwardOffsetTime})
        },
        ArrowLeft: () => {
          const playedTime = this.isPlaying ? this.audioCtx.currentTime - this.startedTime : 0
          const backwardOffsetTime = this.offsetTime + playedTime - 4
          this.$store.commit('seek', {offsetTime: backwardOffsetTime})
        },
        ArrowUp: () => {
          this.$store.dispatch('fetchAndSetPrevExample')
        },
        ArrowDown: () => {
          this.$store.dispatch('fetchAndSetNextExample')
        }
      }

      if ((event.code in shortcutHandlers) && !this.isLoading
          && !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
        shortcutHandlers[event.code]()
        event.preventDefault()
      }

    }
  },
  created() {
    this.$store.dispatch('init').then(() => {
      console.log(this.currentExample)
    })
  },
  mounted() {
    document.addEventListener('keydown', this.handleShortcuts)
  },
  destroyed() {
    // this.$store.state.audioCtx.close()
    document.removeEventListener('keydown', this.handleShortcuts)
  }
};
</script>

<style lang="scss">
$theme-colors: (
    primary: rebeccapurple,
);
@import '~bootstrap/scss/bootstrap';

html,
body {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  /*background: #111317;*/
  background: #0A0025;
  color: white;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

</style>
