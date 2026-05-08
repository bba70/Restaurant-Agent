<script setup lang="ts">
import { NTag } from 'naive-ui'
import { computed } from 'vue'

const props = defineProps<{
  rating: string
}>()

const type = computed(() => {
  const val = parseFloat(props.rating)
  if (isNaN(val)) return 'default' as const
  return val >= 4.0 ? 'warning' as const : 'default' as const
})
</script>

<template>
  <NTag :type="type" size="small" round>
    ⭐ {{ rating }}
  </NTag>
</template>
