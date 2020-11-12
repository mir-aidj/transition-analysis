<template>
  <div>
    <canvas ref="canvas" class="w-100 h-100"></canvas>
  </div>
</template>

<script>
import {mapState} from "vuex";

export default {
  name: 'Knob',
  props: ['color', 'curve'],
  computed: mapState(['startedTime', 'offsetTime', 'isPlaying', 'audioCtx', 'duration']),
  watch: {
    startedTime() {
      this.animate()
    },
    offsetTime() {
      this.draw()
    },
  },
  methods: {
    animate() {
      this.draw()
      if (this.isPlaying) {
        requestAnimationFrame(this.animate)
      }
    },
    draw() {
      const playedTime = this.isPlaying ? this.audioCtx.currentTime - this.startedTime : 0
      const currentFrame = Math.min(
          Math.floor((playedTime + this.offsetTime) / this.duration * this.curve.length),
          this.curve.length - 1)
      const level = this.curve[currentFrame]

      const canvas = this.$refs.canvas
      const width = canvas.width = 100
      const height = canvas.height = 100
      const margin = 0.2
      const startAngle = (0.5 + margin) * Math.PI
      const endAngle = (0.5 - margin) * Math.PI

      const centerX = width / 2
      const centerY = height / 2

      const ctx = canvas.getContext('2d');
      const lineWidth = ctx.lineWidth = 8
      const radius = (width / 2) - lineWidth

      // Draw white arc on the back
      ctx.strokeStyle = '#6c757d'
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, startAngle, endAngle)
      ctx.stroke()

      const gainAngle = (0.5 + margin + 2 * level * (1 - margin)) * Math.PI
      ctx.strokeStyle = this.color
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, startAngle, gainAngle)
      ctx.stroke()

      var x = centerX + Math.cos(gainAngle) * radius;
      var y = centerY + Math.sin(gainAngle) * radius;
      ctx.strokeStyle = '#6c757d'
      ctx.lineWidth = lineWidth * 1.5
      ctx.lineCap = 'round'
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.lineTo(x, y)
      ctx.stroke()

      ctx.fillStyle = this.color
      ctx.beginPath()
      ctx.arc(centerX, centerY + radius - 4, 1. * lineWidth, 0, 2 * Math.PI)
      ctx.fill()
    }
  },
  mounted() {
    this.draw()
  }
}
</script>

<style scoped>

</style>