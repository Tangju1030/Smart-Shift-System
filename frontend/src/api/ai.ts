import api from './index'
import type { AIOptimizeRequest, AIExplainRequest, AIChatRequest } from '@/types'

export const aiAPI = {
  optimizeRule: (data: AIOptimizeRequest) =>
    api.post<{ suggestion: string }>('/ai/optimize-rule', data),
  explainSchedule: (data: AIExplainRequest) =>
    api.post<{ explanation: string }>('/ai/explain-schedule', data),
  chat: (data: AIChatRequest) =>
    api.post<{ reply: string }>('/ai/chat', data),
}
