<template>
  <div style="position: relative">
    <canvas ref="spec" style="position: absolute; z-index: 0; width: 100%; height: 100%"></canvas>
    <canvas ref="curves" style="position: absolute; z-index: 1; width: 100%; height: 100%"></canvas>
    <canvas ref="bar" style="position: absolute; z-index: 2; width: 100%; height: 100%"></canvas>
  </div>
</template>

<script>
import colormap from 'colormap'
import {mapState} from 'vuex'

export default {
  name: 'Spectrogram',
  props: ['srcAudio', 'srcSpec', 'srcCurves', 'gains'],
  data() {
    return {
      audio: undefined,
      isPlaying: false,
      arrayBuffer: undefined,
    }
  },
  computed: mapState(['audioCtx']),
  watch: {
    srcAudio(value){
      console.log(value)
    }
  },
  methods: {
    play() {
      // this.audio.muted = false
      this.audio.play()
      this.isPlaying = true
    },
    pause() {
      this.audio.pause()
      this.isPlaying = false
    },
    mute() {
      this.audio.muted = true
      // this.audio.volume = 0
    },
    unmute() {
      this.audio.muted = false
      // this.audio.volume = 1
      this.$emit('click', this.audio.currentTime)
    },
    seek(time) {
      this.audio.currentTime = time
    }
  },
  created() {
    console.log('CREATED', this.$options.name, this.srcAudio)

    // async function getFile(audioContext, filepath) {
    //   const response = await fetch(filepath, {mode: 'cors', cache});
    //   const arrayBuffer = await response.arrayBuffer();
    //   const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    //   return audioBuffer;
    // }
  },
  mounted() {
    // async function getFile(audioContext, filepath) {
    //   const response = await fetch(filepath, {mode: 'cors', cache});
    //   const arrayBuffer = await response.arrayBuffer();
    //   const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    //   return audioBuffer;
    // }
    console.log('MOUNTED', this.$options.name, this.srcAudio)

    this.audio = new Audio(this.srcAudio)

    const colors = colormap({
      colormap: 'inferno',
      nshades: 256,
      format: 'rgb',
    })

    const canvas = this.$refs.spec
    const ctx = canvas.getContext('2d')


    const img = new Image();
    img.onload = () => {
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
        imageData.data[i + 3] = 255;  // A value
      }
      ctx.putImageData(imageData, 0, 0);
    }
    img.src = this.srcSpec


    fetch(this.srcCurves, {cache: 'force-cache'})
        .then(res => res.json())
        .then((data) => {
          const resolution = 4
          const linewidth = resolution * 1.5
          const margin = 15
          const colors = ['red', 'yellow', 'lime', 'cyan', 'blue', 'magenta']

          const canvas = this.$refs.curves
          const ctx = canvas.getContext('2d')
          const rect = canvas.getBoundingClientRect()

          canvas.width = data.length * resolution  // multiply resolution for high-resolution
          canvas.height = canvas.width * (rect.height / rect.width)
          ctx.lineWidth = linewidth

          const width = canvas.width
          const height = canvas.height

          const gains = this.gains ? this.gains : Array.from(Array(data[0].length).keys());
          for (const iGain of gains) {
            ctx.beginPath()
            ctx.strokeStyle = colors[iGain]
            ctx.moveTo(0, margin + (1 - data[0][iGain]) * (height - 2 * margin))
            for (let iFrame = 0; iFrame < data.length; iFrame++) {
              const gain = data[iFrame][iGain]
              ctx.lineTo(iFrame / data.length * width, margin + (1 - gain) * (height - 2 * margin));
            }
            ctx.stroke();
          }
        })

    setTimeout(() => {
      const canvas = this.$refs.bar
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()

      const resolution = 4
      const WIDTH = canvas.width = rect.width * resolution  // multiply resolution for high-resolution
      const HEIGHT = canvas.height = canvas.width * (rect.height / rect.width)
      ctx.strokeStyle = 'white'
      ctx.lineWidth = resolution * 1.5

      let x = 10;
      let duration = 60 * 1000; // in ms
      let nextX = WIDTH - 10;
      let startTime;

      const anim = (time) => {
        if (!startTime) // it's the first frame
          startTime = time || performance.now();

        // deltaTime should be in the range [0 ~ 1]
        let deltaTime = (time - startTime) / duration;
        // currentPos = previous position + (difference * deltaTime)
        let currentX = x + ((nextX - x) * deltaTime);

        currentX = this.audio.currentTime / this.audio.duration * WIDTH
        draw(currentX);
        requestAnimationFrame(anim); // do it again
        // console.log('asdf', audio.currentTime / audio.duration)

        // if (deltaTime >= 1) { // this means we ended our animation
        //   x = nextX; // reset x variable
        //   startTime = null; // reset startTime
        //   draw(x); // draw the last frame, at required position
        // } else {
        //   draw(currentX);
        //   requestAnimationFrame(anim); // do it again
        // }
      }

      function draw(x) {
        ctx.clearRect(0, 0, WIDTH, HEIGHT)
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, HEIGHT)
        ctx.stroke()
      }

      anim()


      canvas.addEventListener('mousedown', (event) => {
        const rect = canvas.getBoundingClientRect()
        this.audio.currentTime = this.audio.duration * event.offsetX / rect.width
        this.$emit('click', this.audio.currentTime)
        this.play()
      })
    })
  },
  destroyed() {
    this.pause()
    this.audio.src = ''
  }
}
</script>

<style scoped>

</style>