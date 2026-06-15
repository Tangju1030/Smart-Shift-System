/** 用户类型 */
export interface User {
  id: number
  name: string
  student_id: string
  class_name: string
  enabled: boolean
}

export interface UserCreate {
  name: string
  student_id?: string
  class_name?: string
}

/** 规则配置 */
export interface RulesConfig {
  max_weekly_shifts: number
  allow_consecutive_days: boolean
  balance_weight: number
  randomness_weight: number
  search_iterations: number
  period_capacities: Record<string, number>
  duty_slots: string[]
  weekdays: string[]
}

export interface Rule {
  id: number
  rule_name: string
  rule_key: string
  rule_value: string
  description: string
}

/** 排班 */
export interface WeekDateIn {
  week_no: number
  mon: string
  tue: string
  wed: string
  thu: string
  fri: string
}

export interface ScheduleTable {
  week_no: number
  week_dates: Record<string, string>
  slots: Record<string, Record<string, string[]>>
  stats: WeekCounts
}

export interface WeekCounts {
  week_counts: Record<string, number>
  accumulated_counts: Record<string, number>
  min_count: number
  max_count: number
  range_val: number
  avg: number
  unassigned: string[]
  seed_used: number
}

/** 仪表盘 */
export interface DashboardSummary {
  total_users: number
  total_records: number
  min_count: number
  max_count: number
  avg_count: number
  range: number
  user_counts: Record<string, number>
}

/** AI */
export interface AIOptimizeRequest {
  current_rules: Record<string, any>
  history_data: Record<string, any>
  availability_summary: Record<string, any>
}

export interface AIExplainRequest {
  week_no: number
  schedule_data: Record<string, any>
  user_history: Record<string, any>
}

export interface AIChatRequest {
  message: string
  context: Record<string, any>
}

/** 课表 */
export interface AvailabilityRecord {
  user_id: number
  user_name?: string
  weekday: string
  period: string
  available: boolean
}
