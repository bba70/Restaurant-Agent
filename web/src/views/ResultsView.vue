<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NText, NEmpty, NButton } from 'naive-ui'
import type { RecommendResponse } from '../api/types'
import RestaurantCard from '../components/RestaurantCard.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import ErrorAlert from '../components/ErrorAlert.vue'

const router = useRouter()

const loading = ref(true)
const error = ref<string | null>(null)
const data = ref<RecommendResponse['data'] | null>(null)

onMounted(() => {
  const state = history.state as { result?: RecommendResponse }
  if (state?.result?.data) {
    data.value = state.result.data
    loading.value = false
  } else {
    error.value = '未找到搜索结果，请返回首页重新搜索'
    loading.value = false
  }
})

function handleRetry() {
  router.push({ name: 'home' })
}

function handleBack() {
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="results-container">
    <div class="results-header">
      <NButton quaternary @click="handleBack">
        ← 返回首页
      </NButton>
    </div>

    <div v-if="loading" class="results-loading">
      <LoadingSpinner />
    </div>

    <div v-else-if="error" class="results-error">
      <ErrorAlert :message="error" @retry="handleRetry" />
    </div>

    <div v-else-if="data" class="results-content">
      <div class="query-summary">
        <NText strong class="summary-title">搜索结果</NText>
        <div class="summary-details">
          <span v-if="data.city">📍 {{ data.city }}</span>
          <span v-if="data.scenario">🍽️ {{ data.scenario }}</span>
          <span v-if="data.types">🏷️ {{ data.types }}</span>
          <span v-if="data.total_found">📊 找到 {{ data.total_found }} 家餐厅</span>
        </div>
      </div>

      <div v-if="data.recommendations_hard && data.recommendations_hard.length > 0" class="restaurant-section">
        <div class="section-header">
          <h3>均衡度优先推荐（严格筛选）</h3>
          <span class="badge">推荐 {{ data.recommendation_count_hard }} 家</span>
        </div>
        <div class="restaurant-grid">
          <RestaurantCard
            v-for="(restaurant, index) in data.recommendations_hard"
            :key="'hard-' + index"
            :restaurant="restaurant"
            :index="index"
          />
        </div>
      </div>

      <div v-if="data.recommendations_soft && data.recommendations_soft.length > 0" class="restaurant-section">
        <div class="section-header">
          <h3>评分优先推荐（宽松筛选）</h3>
          <span class="badge">推荐 {{ data.recommendation_count_soft }} 家</span>
        </div>
        <div class="restaurant-grid">
          <RestaurantCard
            v-for="(restaurant, index) in data.recommendations_soft"
            :key="'soft-' + index"
            :restaurant="restaurant"
            :index="index"
          />
        </div>
      </div>

      <div v-else class="empty-state">
        <NEmpty description="暂无推荐结果" />
        <NButton @click="handleBack">重新搜索</NButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.results-header {
  margin-bottom: 24px;
}

.results-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.results-error {
  margin-top: 40px;
}

.query-summary {
  background: linear-gradient(135deg, #fff7ed, #fef3c7);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.summary-title {
  font-size: 20px;
  display: block;
  margin-bottom: 12px;
}

.summary-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
  color: #6b7280;
}

.restaurant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  gap: 20px;
}

@media (max-width: 768px) {
  .restaurant-grid {
    grid-template-columns: 1fr;
  }
}
</style>
