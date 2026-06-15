import api from './index'
import type { ScheduleTable, WeekDateIn, DashboardSummary } from '@/types'

export const scheduleAPI = {
  generate: (data: { week_no: number; week_dates: WeekDateIn }) =>
    api.post<ScheduleTable>('/schedule/generate', data),
  getResult: (weekNo?: number) =>
    api.get('/schedule/result', { params: { week_no: weekNo } }),
  getSummary: () =>
    api.get<DashboardSummary>('/schedule/summary'),
  exportCSV: (weekNo?: number) =>
    api.get('/schedule/export/csv', { params: { week_no: weekNo }, responseType: 'text' }),
}
