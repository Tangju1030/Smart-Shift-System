import api from './index'
import type { User, UserCreate } from '@/types'

export const userAPI = {
  list: (enabledOnly = false) => api.get<User[]>('/users/', { params: { enabled_only: enabledOnly } }),
  get: (id: number) => api.get<User>(`/users/${id}`),
  create: (data: UserCreate) => api.post<User>('/users/', data),
  update: (id: number, data: Partial<User>) => api.put<User>(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
  batchCreate: (names: string[]) => api.post<User[]>('/users/batch', names),
  importHistory: (counts: Record<string, number>) => api.post('/users/historical-counts', counts),
  getHistory: () => api.get<Record<string, number>>('/users/historical-counts'),
}
