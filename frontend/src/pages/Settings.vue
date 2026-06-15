<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ruleAPI } from '@/api/rules'
import { userAPI } from '@/api/users'
import type { RulesConfig, User } from '@/types'

const rules = reactive<RulesConfig>({
  max_weekly_shifts: 2,
  allow_consecutive_days: false,
  balance_weight: 70,
  randomness_weight: 30,
  search_iterations: 200,
  period_capacities: { '第一节': 2, '第二节': 2, '第三节': 2, '第四节': 2 },
  duty_slots: ['第一节', '第二节', '第三节', '第四节'],
  weekdays: ['周一', '周二', '周三', '周四', '周五'],
})

const users = ref<User[]>([])
const loading = ref(false)
const tabActive = ref('rules')

// 切换Tab时自动加载数据
watch(tabActive, (val) => {
  if (val === 'history') loadHistory()
})

onMounted(async () => {
  loading.value = true
  try {
    const [r, u] = await Promise.all([ruleAPI.getConfig(), userAPI.list(true)])
    Object.assign(rules, r.data)
    users.value = u.data
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
  loading.value = false
})

async function saveRules() {
  try {
    await ruleAPI.updateConfig({ ...rules })
    ElMessage.success('规则已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

// 时段人数调整
const capacityLabels: Record<string, string> = {
  '第一节': '第一节 (8:30-9:50)', '第二节': '第二节 (10:25-11:50)',
  '第三节': '第三节 (14:30-15:55)', '第四节': '第四节 (16:30-17:40)',
}

// 用户管理
const newUserName = ref('')
const newBatchNames = ref('')

async function addUser() {
  if (!newUserName.value.trim()) return
  try {
    await userAPI.create({ name: newUserName.value.trim() })
    const r = await userAPI.list(true)
    users.value = r.data
    newUserName.value = ''
    ElMessage.success('添加成功')
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

async function removeUser(id: number) {
  try {
    await userAPI.delete(id)
    users.value = users.value.filter(u => u.id !== id)
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// 历史次数
const historyText = ref('')
const historyLoading = ref(false)
const historyResult = ref<{ imported: number; not_found: string[] } | null>(null)
const currentHistory = ref<Record<string, number>>({})

async function loadHistory() {
  try {
    const res = await userAPI.getHistory()
    currentHistory.value = res.data
  } catch (e) {
    ElMessage.error('加载历史数据失败')
  }
}

async function importHistory() {
  const raw = historyText.value.trim()
  if (!raw) return
  historyLoading.value = true
  try {
    const text = raw.replace(/[,，;；\n\r]+/g, '\n')
    const lines = text.split('\n').map(l => l.trim()).filter(Boolean)
    const counts: Record<string, number> = {}
    for (const line of lines) {
      const m = line.match(/^(.+?)[=:：\s]+(\d+)$/)
      if (m) {
        const name = m[1].trim()
        const count = parseInt(m[2])
        if (name && !isNaN(count)) counts[name] = count
      }
    }
    if (Object.keys(counts).length === 0) {
      ElMessage.warning('未能解析数据，请使用「姓名:次数」格式')
      return
    }
    const res = await userAPI.importHistory(counts)
    historyResult.value = res.data
    ElMessage.success(`已导入 ${res.data.imported} 人历史次数`)
    await loadHistory()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    historyLoading.value = false
  }
}

async function batchImport() {
  if (!newBatchNames.value.trim()) return
  const names = newBatchNames.value.split(/[,，\s\n]+/).filter(Boolean)
  try {
    await userAPI.batchCreate(names)
    const r = await userAPI.list(true)
    users.value = r.data
    newBatchNames.value = ''
    ElMessage.success(`已导入 ${names.length} 人`)
  } catch (e) {
    ElMessage.error('批量导入失败')
  }
}
</script>

<template>
  <div>
    <h1 style="font-size:24px;font-weight:700;margin-bottom:24px">规则配置</h1>

    <el-tabs v-model="tabActive">
      <!-- 排班规则 Tab -->
      <el-tab-pane label="排班规则" name="rules">
        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header><span style="font-weight:600">基本规则</span></template>
          <el-form label-position="top" size="default">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="每人每周最多值班次数">
                  <el-input-number v-model="rules.max_weekly_shifts" :min="1" :max="5" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="是否允许连续天值班">
                  <el-switch v-model="rules.allow_consecutive_days" active-text="允许" inactive-text="禁止" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="多种子搜索次数">
                  <el-input-number v-model="rules.search_iterations" :min="10" :max="1000" :step="10" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>

        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header><span style="font-weight:600">评分权重</span></template>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="历史均衡权重">
                <el-slider v-model="rules.balance_weight" :min="0" :max="100" show-input />
                <div style="font-size:11px;color:#909399">数值越大，累计次数少的同学越优先</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="随机性权重">
                <el-slider v-model="rules.randomness_weight" :min="0" :max="100" show-input />
                <div style="font-size:11px;color:#909399">数值越大，排班结果多样性越高</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header><span style="font-weight:600">每时段人数上限</span></template>
          <el-row :gutter="16">
            <el-col :span="6" v-for="(label, key) in capacityLabels" :key="key">
              <el-form-item :label="label">
                <el-input-number v-model="rules.period_capacities[key]" :min="0" :max="5" style="width:100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <el-button type="primary" @click="saveRules" style="width:100%;height:44px;font-size:15px">
          保存规则配置
        </el-button>
      </el-tab-pane>

      <!-- 历史次数 Tab -->
      <el-tab-pane label="历史次数" name="history">
        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600">导入历史值班次数</span>
              <el-button size="small" @click="loadHistory">刷新当前数据</el-button>
            </div>
          </template>
          <div style="font-size:13px;color:#606266;margin-bottom:12px">
            粘贴「姓名:次数」格式数据，支持逗号、换行分隔。此操作会<strong style="color:#C0392B">覆盖</strong>所有历史记录。
          </div>
          <el-input
            v-model="historyText"
            type="textarea"
            :rows="6"
            placeholder="曹天仪:5, 曾启轩:7, 陈德永:5, 成金泽:7, 杜昕洛:7, 方瑜:5, 龚恩希:6, 郭一漫:6, 胡笑笑:6, 黄琴斯:6, 黎丹:6, 刘芯伶:7, 陆东平:5, 马丹:7, 蒙世龙:6, 潘小燕:4, 庞雨君:4, 秦子恒:6, 邱巧丽:4, 任凯熙:5, 沈俊宇:7, 宋林:7, 覃如萍:6, 唐思凡:5, 王译:7, 温永福:8, 韦谭菊:5, 巫永贵:7, 吴佳奕:6, 吴嘉乐:6, 兀泉晶:6, 叶智仁:6, 张靖悦:5, 张添惟:6, 赵丽伟:5, 朱国昱:5, 左顺虎:6"
          />
          <div style="margin-top:12px;display:flex;gap:12px">
            <el-button type="primary" @click="importHistory" :loading="historyLoading">导入历史次数</el-button>
            <el-button @click="historyText = ''">清空</el-button>
          </div>
          <div v-if="historyResult" style="margin-top:12px;font-size:13px">
            <span style="color:#4A9E2F">✓ 已导入 {{ historyResult.imported }} 人</span>
            <span v-if="historyResult.not_found?.length" style="color:#C0392B;margin-left:12px">
              未找到: {{ historyResult.not_found.join(', ') }}
            </span>
          </div>
        </el-card>

        <el-card v-if="currentHistory" shadow="hover" style="border-radius:12px">
          <template #header><span style="font-weight:600">当前历史次数</span></template>
          <div style="display:flex;flex-wrap:wrap;gap:4px">
            <el-tag v-for="(count, name) in currentHistory" :key="name" size="small"
                    :type="count >= 8 ? 'danger' : count >= 6 ? 'warning' : ''">
              {{ name }}: {{ count }}
            </el-tag>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 人员管理 Tab -->
      <el-tab-pane label="人员管理" name="users">
        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header><span style="font-weight:600">批量导入</span></template>
          <el-input
            v-model="newBatchNames"
            type="textarea"
            :rows="3"
            placeholder="粘贴姓名，用逗号、空格或换行分隔"
          />
          <el-button type="primary" @click="batchImport" style="margin-top:12px">批量导入</el-button>
        </el-card>

        <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
          <template #header>
            <div style="display:flex;gap:12px;align-items:center">
              <span style="font-weight:600">人员列表</span>
              <span style="font-size:12px;color:#909399">共 {{ users.length }} 人</span>
            </div>
          </template>
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <el-input v-model="newUserName" placeholder="输入姓名" size="small" style="width:200px" @keyup.enter="addUser" />
            <el-button type="primary" size="small" @click="addUser">添加</el-button>
          </div>
          <el-table :data="users" stripe max-height="400" size="small">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="student_id" label="学号" />
            <el-table-column prop="class_name" label="班级" />
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button type="danger" size="small" text @click="removeUser(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
