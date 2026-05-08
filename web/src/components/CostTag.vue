<script setup lang="ts">
import { NTag } from 'naive-ui'
import { computed } from 'vue'

const props = defineProps<{
  cost: string
}>()

const type = computed(() => {
  const val = parseFloat(props.cost)
  if (isNaN(val)) return 'default' as const
  if (val <= 50) return 'success' as const
  if (val <= 150) return 'warning' as const
  return 'error' as const
})
</script>

<template>
  <NTag :type="type" size="small" round>
    💰 ¥{{ cost }}/人
  </NTag>
</template>
