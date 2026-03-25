import axios from 'axios'
import type { TripPlan, TripPlanRequest } from '../types'

interface ErrorResponse {
  success: false
  error: string
  details?: Array<{ field?: string; message: string }>
  code?: string
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  config => {
    console.log('[API Request]', config.url, config.data)
    return config
  },
  error => Promise.reject(error)
)

api.interceptors.response.use(
  response => response,
  error => {
    const errorData = error.response?.data as ErrorResponse
    if (errorData?.error) {
      error.message = getErrorMessage(errorData)
    }
    return Promise.reject(error)
  }
)

function getErrorMessage(errorData: ErrorResponse): string {
  const { error, code, details } = errorData

  if (details && details.length > 0) {
    return details[0].message
  }

  const codeMessages: Record<string, string> = {
    VALIDATION_ERROR: '请求参数有误，请检查后重试',
    CONFIGURATION_ERROR: '服务配置异常，请联系管理员',
    EXTERNAL_API_ERROR: '外部服务暂不可用，请稍后重试',
    LLM_ERROR: '智能行程生成失败，请稍后重试',
    INTERNAL_ERROR: '系统繁忙，请稍后重试'
  }

  return codeMessages[code || ''] || error || '请求失败，请稍后重试'
}

export const generateTripPlan = async (request: TripPlanRequest): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request)

  if (!response.data || typeof response.data !== 'object') {
    throw new Error('服务返回数据格式错误')
  }

  if (!response.data.city || !response.data.days || response.data.days.length === 0) {
    throw new Error('生成结果为空，请重试')
  }

  return response.data
}

export const getConfig = async (): Promise<{ amap_web_key: string }> => {
  try {
    const response = await api.get<{ amap_web_key: string }>('/trip/config')
    return response.data
  } catch {
    throw new Error('无法获取地图配置，请检查网络连接')
  }
}

export const checkHealth = async (): Promise<{
  status: string
  services: {
    llm: boolean
    amap: boolean
    unsplash: boolean
  }
}> => {
  const response = await api.get('/health')
  return response.data
}
