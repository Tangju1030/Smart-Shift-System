import api from './index'
import type { Rule, RulesConfig } from '@/types'

export const ruleAPI = {
  list: () => api.get<Rule[]>('/rules/'),
  getConfig: () => api.get<RulesConfig>('/rules/config'),
  updateConfig: (config: RulesConfig) => api.put<RulesConfig>('/rules/config', config),
  updateOne: (key: string, value: string) => api.put<Rule>(`/rules/${key}`, { rule_value: value }),
}
