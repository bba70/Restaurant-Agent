export interface RecommendRequest {
  query: string
}

export interface Restaurant {
  name?: string
  address?: string
  location?: string
  telephone?: string
  type?: string
  rating?: string
  cost?: string
}

export interface RecommendData {
  query?: string
  scenario?: string
  types?: string
  city?: string
  location?: string
  filters_applied?: Record<string, unknown>
  total_found?: number
  recommendation_count_hard?: number
  recommendation_count_soft?: number
  recommendations_hard?: Restaurant[]
  recommendations_soft?: Restaurant[]
  search_mode?: string
  fallback?: string | null
  locations?: Array<{ name: string; lnglat: string }>
  location_count?: number
  recommendation_count?: number
  recommendations?: Restaurant[]
  errors?: string[]
}

export interface RecommendResponse {
  success: boolean
  message: string
  data?: RecommendData
}
