<script setup lang="ts">
import { NAlert, NButton } from 'naive-ui'

defineProps<{
  message: string
}>()

defineEmits<{
  retry: []
}>()
</script>

<template>
  <NAlert type="error" :title="message" class="error-alert">
    <div class="error-actions">
      <NButton size="small" type="error" @click="$emit('retry')">
        重试
      </NButton>
    </div>
  </NAlert>
</template>

<style scoped>
.error-alert {
  margin-bottom: 20px;
}

.error-actions {
  margin-top: 12px;
}
</style>
