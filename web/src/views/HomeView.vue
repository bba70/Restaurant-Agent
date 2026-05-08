<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NText, useMessage } from 'naive-ui'
import { recommend } from '../api'

const router = useRouter()
const message = useMessage()

const query = ref('')
const loading = ref(false)
const inputRef = ref<InstanceType<typeof NInput> | null>(null)

onMounted(() => {
  inputRef.value?.focus()
})

async function handleSearch() {
  const trimmed = query.value.trim()
  if (!trimmed) {
    message.warning('请输入搜索内容')
    return
  }

  loading.value = true
  try {
    const result = await recommend(trimmed)
    router.push({
      name: 'results',
      query: { q: trimmed },
      state: { result } as any,
    })
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : '搜索失败，请重试'
    message.error(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="home-container">
    <div class="home-content">
      <div class="brand-section">
        <h1 class="brand-title">美食推荐</h1>
        <p class="brand-description">告诉我你想吃什么，AI 为你智能推荐附近餐厅</p>
      </div>

      <div class="search-section">
        <NInput
          ref="inputRef"
          v-model:value="query"
          placeholder="例如：附近好吃的火锅、适合约会的西餐厅..."
          size="large"
          :loading="loading"
          @keyup.enter="handleSearch"
        />
        <NButton
          type="primary"
          size="large"
          :loading="loading"
          :disabled="loading"
          @click="handleSearch"
        >
          搜索推荐
        </NButton>
      </div>

      <div class="hint-section">
        <NText depth="3" class="hint-text">
          试试：川菜、咖啡厅、生日聚餐、人均100以内
        </NText>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.home-content {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.brand-section {
  text-align: center;
}

.brand-title {
  font-size: 48px;
  font-weight: 700;
  background: linear-gradient(135deg, #f97316, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
}

.brand-description {
  font-size: 18px;
  color: #6b7280;
  margin: 0;
}

.search-section {
  display: flex;
  gap: 12px;
}

.hint-section {
  text-align: center;
}

.hint-text {
  font-size: 14px;
}

@media (max-width: 768px) {
  .brand-title {
    font-size: 36px;
  }

  .brand-description {
    font-size: 16px;
  }

  .search-section {
    flex-direction: column;
  }
}
</style>
