import { request } from './client'
import type { RecommendRequest, RecommendResponse } from './types'

export async function recommend(query: string): Promise<RecommendResponse> {
  const body: RecommendRequest = { query }
  const result = await request<RecommendResponse>('/api/recommend', {
    method: 'POST',
    body: JSON.stringify(body),
  })

  if (!result.success) {
    throw new Error(result.message || '推荐失败，请重试')
  }

  return result
}
