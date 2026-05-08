<script setup lang="ts">
import { NSpin } from 'naive-ui'

defineProps<{
  text?: string
}>()
</script>

<template>
  <div class="loading-container">
    <NSpin size="large" />
    <p class="loading-text">{{ text || '正在为你推荐美食...' }}</p>
  </div>
</template>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  gap: 16px;
}

.loading-text {
  color: #f97316;
  font-size: 15px;
  font-weight: 500;
}
</style>
