<template>
  <div v-show="isShowing">
    <div v-for="audioType in audioTypes" :key="`${audioType.key}`" class="row">
      <TrackRow :mix-type="mixType" :audio-type="audioType" class="col p-0 border-bottom border-bottom"></TrackRow>

      <!--      <Spectrogram ref="specs"-->
      <!--                   :mix-type="mixType"-->
      <!--                   :spec-type="specType"-->
      <!--                   style="height: 200px;" class="col"></Spectrogram>-->

      <!--      <div class="btn-group-toggle col-sm-auto" data-toggle="buttons">-->
      <!--        <label class="btn"-->
      <!--               :class="{'btn-primary': currentSoloSpec === specType.key, 'btn-secondary': currentSoloSpec !== specType.key}">-->
      <!--          <input @click="solo(index, specType.key)" :value="specType.key" type="radio" name="solo" autocomplete="off">-->
      <!--          Solo-->
      <!--        </label>-->
      <!--      </div>-->

    </div>

    <!--    <div v-for="(specType, index) in specTypes" :key="`${currentExampleIndex}-${specType}-${currentMixType}`" class="row mb-2">-->

    <!--      <Spectrogram ref="specs"-->
    <!--                   :src-audio="`audio/${currentExampleIndex}-${specType}-${currentMixType}.mp3`"-->
    <!--                   :src-spec="`spec/${currentExampleIndex}-${specType}-${currentMixType}.png`"-->
    <!--                   :src-curves="`curve/${currentExampleIndex}-${currentMixType}.json`"-->
    <!--                   :gains="gains[currentMixType] ? gains[currentMixType][index] : null"-->
    <!--                   @seek="(a, b) => seek(a, b, index)"-->
    <!--                   @ended="audioEnded"-->
    <!--                   style="height: 200px;" class="col"></Spectrogram>-->

    <!--      <div class="btn-group-toggle col-sm-auto" data-toggle="buttons">-->
    <!--        <label class="btn"-->
    <!--               :class="{'btn-primary': currentSoloSpec === specType, 'btn-secondary': currentSoloSpec !== specType}">-->
    <!--          <input @click="solo(index, specType)" :value="specType" type="radio" name="solo" autocomplete="off"> Solo-->
    <!--        </label>-->
    <!--      </div>-->

    <!--    </div>-->
  </div>
</template>

<script>
// import Spectrogram from "@/components/Spectrogram";
import {mapState} from 'vuex'
import TrackRow from "@/components/TrackRow";

export default {
  name: 'Panel',
  props: ['mixType'],
  components: {
    TrackRow,
    // Spectrogram
  },
  computed: {
    isShowing() {
      return this.currentMixType === this.mixType.key
    },
    mix() {
      return this.$store.state.currentExample.mixes[this.mixType.key]
    },
    ...mapState(['audioTypes', 'currentExampleIndex', 'currentMixType'])
  }
}
</script>

<style scoped>

</style>