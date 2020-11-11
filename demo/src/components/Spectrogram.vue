<template>
  <div style="position: relative;">

    <div class="canvas-container" style="z-index: 0;">
      <canvas ref="spec" class="w-100 h-100"></canvas>
    </div>

    <div class="canvas-container" style="z-index: 1;">
      <canvas ref="curves" class="w-100 h-100"></canvas>
    </div>

    <div class="canvas-container" style="z-index: 2;">
      <canvas ref="bar" class="w-100 h-100"></canvas>
    </div>

  </div>
</template>

<script>
import colormap from 'colormap'
import {mapState} from 'vuex'

export default {
  name: 'Spectrogram',
  props: ['mixType', 'audioType'],
  computed: {
    audio() {
      return this.$store.state.currentExample.mixes[this.mixType.key].audios[this.audioType.key]
    },
    audioDuration() {
      return this.audio.audioBuffer.duration
    },
    curves() {
      return this.audio.curves
    },
    isShowing() {
      return this.currentMixType === this.mixType.key
    },
    ...mapState(['audioCtx', 'isLoading', 'isPlaying', 'currentExampleIndex', 'currentMixType', 'currentSoloAudioType',
      'startedTime', 'offsetTime'])
  },
  watch: {
    startedTime() {
      this.animate()
    },
    offsetTime() {
      this.drawBar()
    },
    isPlaying() {
    },
    isShowing() {
      if (this.isShowing) {
        this.drawCurves()
        this.drawBar()
      }
    }
  },
  methods: {
    drawSpec() {
      return new Promise(resolve => {
        const imageUrl = this.audio.specImageUrl
        // Create an image and draw it when it's loaded.
        const img = new Image();
        img.onload = () => {
          const colors = colormap({
            colormap: 'electric',
            nshades: 256,
            format: 'rgb',
          })
          const canvas = this.$refs.spec
          const ctx = canvas.getContext('2d')

          canvas.width = img.width
          canvas.height = img.height

          ctx.drawImage(img, 0, 0);

          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          // Iterate through every pixel
          for (let i = 0; i < imageData.data.length; i += 4) {
            const [r, g, b] = colors[imageData.data[i]]
            // Modify pixel data
            imageData.data[i + 0] = r     // R value
            imageData.data[i + 1] = g     // G value
            imageData.data[i + 2] = b     // B value
            // Make the spectrogram transparent if the RGB is the minimum.
            imageData.data[i + 3] = (r + g + b) > 4 ? 255 : 0  // A value
          }
          ctx.putImageData(imageData, 0, 0);
          resolve()
        }
        img.src = imageUrl
      })
    },
    drawCurves() {
      if (this.curves === undefined) return

      const resolution = 1.5
      const linewidth = resolution * 1.5
      const margin = 15
      const colors = ['red', 'yellow', 'lime', 'cyan', 'blue', 'magenta']

      const curves = this.curves
      const canvas = this.$refs.curves
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()
      const width = canvas.width = curves.length * resolution  // multiply resolution for high-resolution
      const height = canvas.height = width * (rect.height / rect.width)
      ctx.lineWidth = linewidth

      // Compute gain indices.
      const numGains = curves[0].length
      const allGains = Array.from(Array(numGains).keys())
      let gains
      if (this.audioType.key === 'prev') {
        gains = allGains.slice(0, numGains / 2)
      } else if (this.audioType.key === 'next') {
        gains = allGains.slice(numGains / 2, numGains)
      } else { // DJ mix
        gains = allGains
      }

      // Draw the curves on the canvas
      for (const iGain of gains) {
        ctx.beginPath()
        ctx.strokeStyle = colors[iGain]
        ctx.moveTo(0, margin + (1 - curves[0][iGain]) * (height - 2 * margin))
        for (let iFrame = 0; iFrame < curves.length; iFrame++) {
          const gain = curves[iFrame][iGain]
          ctx.lineTo(iFrame / curves.length * width, margin + (1 - gain) * (height - 2 * margin));
        }
        ctx.stroke();
      }
    },
    animate() {
      this.drawBar()
      // TODO: Stop animation when it's paused
      if (this.isPlaying) {
        requestAnimationFrame(this.animate)
      }
    },
    drawBar(x) {
      if (this.isLoading) return

      const canvas = this.$refs.bar
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()
      const width = canvas.width = rect.width  // multiply resolution for high-resolution
      const height = canvas.height = canvas.width * (rect.height / rect.width)

      let currentX
      if (x !== undefined) {
        currentX = x
      } else {
        const playedTime = this.isPlaying ? this.audioCtx.currentTime - this.startedTime : 0
        currentX = (playedTime + this.offsetTime) / this.audioDuration * width

        // TODO: knobs!
        // const progress = (playedTime + this.offsetTime) / this.$parent.$data.audioBuffer.duration
        // const curveFrame = Math.floor(progress * this.curves.length)
        // console.log(progress, this.curves[curveFrame])
      }

      ctx.strokeStyle = 'white'
      ctx.lineWidth = 1.5
      ctx.clearRect(0, 0, width, height)
      ctx.beginPath()
      ctx.moveTo(currentX, 0)
      ctx.lineTo(currentX, height)
      ctx.stroke()
    },
  },
  created() {
  },
  mounted() {
    if (this.mixType.key !== 'dj') {
      this.drawCurves()
    }

    this.drawSpec()
        .then(() => {
          this.drawBar(0)

          this.$refs.bar.addEventListener('mousedown', (event) => {
            const rect = this.$refs.bar.getBoundingClientRect()
            const offsetTime = this.audioDuration * event.offsetX / rect.width
            this.$store.commit('seek', {offsetTime})
            this.drawBar()
          })
        })
  },
  destroyed() {
  }
}
</script>

<style scoped>
.canvas-container {
  width: 100%;
  height: 100%;

  position: absolute;
  padding-left: inherit;
  padding-right: inherit;
  left: 0;
  right: 0;
}
</style>