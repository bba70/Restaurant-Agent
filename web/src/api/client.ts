const API_BASE = import.meta.env.DEV ? '' : ''

export async function request<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`请求失败 (${response.status})`)
    }

    const data: T = await response.json()
    return data
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('网络连接失败，请检查网络或后端服务是否启动')
    }
    throw error
  }
}
