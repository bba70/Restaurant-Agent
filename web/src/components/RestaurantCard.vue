<script setup lang="ts">
import { NCard, NText } from 'naive-ui'
import type { Restaurant } from '../api/types'
import RatingTag from './RatingTag.vue'
import CostTag from './CostTag.vue'

defineProps<{
  restaurant: Restaurant
  index: number
}>()
</script>

<template>
  <NCard
    hoverable
    class="restaurant-card"
    :style="{ animationDelay: `${index * 80}ms` }"
  >
    <div class="card-header">
      <NText class="card-name" strong>
        {{ index + 1 }}. {{ restaurant.name || '未知餐厅' }}
      </NText>
    </div>
    <div class="card-body">
      <div v-if="restaurant.address" class="card-info-item">
        <span class="card-info-label">📍 地址</span>
        <span class="card-info-value">{{ restaurant.address }}</span>
      </div>
      <div v-if="restaurant.telephone" class="card-info-item">
        <span class="card-info-label">📞 电话</span>
        <span class="card-info-value">{{ restaurant.telephone }}</span>
      </div>
      <div v-if="restaurant.type" class="card-info-item">
        <span class="card-info-label">🍽️ 类型</span>
        <span class="card-info-value">{{ restaurant.type }}</span>
      </div>
      <div class="card-tags">
        <RatingTag v-if="restaurant.rating" :rating="restaurant.rating" />
        <CostTag v-if="restaurant.cost" :cost="restaurant.cost" />
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.restaurant-card {
  animation: slideInUp 0.4s ease both;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.restaurant-card:hover {
  transform: translateY(-4px);
}

.card-header {
  margin-bottom: 12px;
}

.card-name {
  font-size: 17px;
  font-weight: 600;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-info-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.card-info-label {
  flex-shrink: 0;
  font-weight: 600;
  color: #374151;
}

.card-info-value {
  color: #6b7280;
  word-break: break-all;
}

.card-tags {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
