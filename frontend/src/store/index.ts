import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, RulesConfig, ScheduleTable, DashboardSummary } from '@/types'
import { userAPI } from '@/api/users'
import { ruleAPI } from '@/api/rules'
import { scheduleAPI } from '@/api/schedule'

export const useAppStore = defineStore('app', () => {
  // State
  const users = ref<User[]>([])
  const rules = ref<RulesConfig | null>(null)
  const currentSchedule = ref<ScheduleTable | null>(null)
  const dashboard = ref<DashboardSummary | null>(null)
  const loading = ref(false)

  // Actions
  async function fetchUsers() {
    const res = await userAPI.list(true)
    users.value = res.data
  }

  async function fetchRules() {
    const res = await ruleAPI.getConfig()
    rules.value = res.data
  }

  async function fetchDashboard() {
    const res = await scheduleAPI.getSummary()
    dashboard.value = res.data
  }

  async function generateSchedule(weekNo: number, weekDates: any) {
    loading.value = true
    try {
      const res = await scheduleAPI.generate({
        week_no: weekNo,
        week_dates: weekDates,
      })
      currentSchedule.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  return {
    users, rules, currentSchedule, dashboard, loading,
    fetchUsers, fetchRules, fetchDashboard, generateSchedule,
  }
})
