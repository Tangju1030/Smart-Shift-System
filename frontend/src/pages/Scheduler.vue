<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAppStore } from '@/store'
import { ElMessage } from 'element-plus'
import { RefreshRight, Download, CopyDocument, Edit, Delete, Plus } from '@element-plus/icons-vue'
import api from '@/api'
import type { ScheduleTable } from '@/types'

const store = useAppStore()
const loading = ref(false)
const schedule = ref<ScheduleTable | null>(null)

const weekDates = reactive({
  week_no: 11,
  mon: '',
  tue: '',
  wed: '',
  thu: '',
  fri: '',
})

const weekdays = ['周一', '周二', '周三', '周四', '周五']
const dutySlots = ['第一节', '第二节', '第三节', '第四节']
const slotTimes: Record<string, string> = {
  '第一节': '8:30-9:50', '第二节': '10:25-11:50',
  '第三节': '14:30-15:55', '第四节': '16:30-17:40',
}

onMounted(async () => {
  await store.fetchUsers()
  await store.fetchRules()
  // 根据当前日期推算默认周次
  const today = new Date()
  const monday = new Date(today)
  monday.setDate(today.getDate() - today.getDay() + 1)
  weekDates.mon = `${monday.getMonth() + 1}.${monday.getDate()}`
  const dayNames: (keyof typeof weekDates)[] = ['tue', 'wed', 'thu', 'fri']
  dayNames.forEach((k, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i + 1)
    weekDates[k] = `${d.getMonth() + 1}.${d.getDate()}`
  })
})

async function runSchedule() {
  loading.value = true
  try {
    const data = await store.generateSchedule(weekDates.week_no, {
      week_no: weekDates.week_no,
      ...weekDates,
    })
    schedule.value = data
    ElMessage.success('排班生成成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '排班生成失败')
  } finally {
    loading.value = false
  }
}

const sortedAccumulated = computed(() => {
  if (!schedule.value?.stats.accumulated_counts) return []
  return Object.entries(schedule.value.stats.accumulated_counts)
    .sort((a, b) => b[1] - a[1])
})

const summaryText = computed(() => {
  if (!schedule.value?.stats.accumulated_counts) return ''
  // 按原名单顺序输出
  const roster = [
    '曹天仪','曾启轩','陈德永','成金泽','杜昕洛','方瑜','龚恩希','郭一漫',
    '胡笑笑','黄琴斯','黎丹','刘芯伶','陆东平','马丹','蒙世龙','潘小燕',
    '庞雨君','秦子恒','邱巧丽','任凯熙','沈俊宇','宋林','覃如萍','唐思凡',
    '王译','温永福','韦谭菊','巫永贵','吴佳奕','吴嘉乐','兀泉晶','叶智仁',
    '张靖悦','张添惟','赵丽伟','朱国昱','左顺虎',
  ]
  return roster.map(n => {
    const cnt = schedule.value!.stats.accumulated_counts[n] ?? 0
    return `${n}:${cnt}`
  }).join(', ')
})

function copySummaryText() {
  const prefix = `截止第${schedule.value!.week_no}周结束已安排值班次数：\n`
  navigator.clipboard.writeText(prefix + summaryText.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

function getSlotNames(wd: string, slot: string): string[] {
  return schedule.value?.slots?.[wd]?.[slot] || []
}

// 仅重新加载当前排班结果（不重跑算法），同时更新统计数据
async function reloadSchedule() {
  if (!schedule.value) return
  const wn = schedule.value.week_no
  try {
    const [res, histRes] = await Promise.all([
      api.get('/schedule/result', { params: { week_no: wn } }),
      api.get('/users/historical-counts'),
    ])
    const results: any[] = res.data
    const histCounts: Record<string, number> = histRes.data
    // 重建 slots
    const weekdays = ['周一','周二','周三','周四','周五']
    const dutySlots = ['第一节','第二节','第三节','第四节']
    const slots: Record<string, Record<string, string[]>> = {}
    for (const wd of weekdays) { slots[wd] = {}; for (const s of dutySlots) slots[wd][s] = [] }
    const users: Record<number, string> = {}
    for (const u of store.users) users[u.id] = u.name

    const weekCounts: Record<string, number> = {}
    for (const r of results) {
      const name = users[r.user_id] || String(r.user_id)
      const wd = r.duty_date
      if (slots[wd] && slots[wd][r.period]) {
        slots[wd][r.period].push(name)
        weekCounts[name] = (weekCounts[name] || 0) + 1
      }
    }
    // 更新本地数据
    schedule.value.slots = slots
    schedule.value.stats.week_counts = weekCounts
    // 重新计算累计次数
    const accCounts: Record<string, number> = {}
    const allNames = new Set([...Object.keys(histCounts), ...Object.keys(weekCounts)])
    for (const n of allNames) accCounts[n] = (histCounts[n] || 0) + (weekCounts[n] || 0)
    schedule.value.stats.accumulated_counts = accCounts
    // 更新极差等统计
    const vals = Object.values(accCounts)
    schedule.value.stats.min_count = vals.length ? Math.min(...vals) : 0
    schedule.value.stats.max_count = vals.length ? Math.max(...vals) : 0
    schedule.value.stats.range_val = schedule.value.stats.max_count - schedule.value.stats.min_count
    schedule.value.stats.avg = vals.length ? +(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1) : 0
    schedule.value.stats.unassigned = Object.keys(histCounts).filter(n => !weekCounts[n])
    // 刷新编辑弹窗名单
    editSlot.names = getSlotNames(editSlot.wd, editSlot.period)
  } catch (e) {
    console.error('Reload failed', e)
  }
}

// ── 排班编辑 ──
const editDialogVisible = ref(false)
const editSlot = reactive({ wd: '', period: '', names: [] as string[] })
const editAction = ref<'add'|'remove'>('add')
const editUserName = ref('')

function openEditSlot(wd: string, period: string) {
  editSlot.wd = wd
  editSlot.period = period
  editSlot.names = getSlotNames(wd, period)
  editUserName.value = ''
  editAction.value = 'add'
  editDialogVisible.value = true
}

async function doEditAction() {
  if (!schedule.value || !editUserName.value.trim()) return
  const wn = schedule.value.week_no
  const payload = {
    week_no: wn,
    duty_date: editSlot.wd,
    period: editSlot.period,
    user_name: editUserName.value.trim(),
    old_user_name: '',
  }
  try {
    if (editAction.value === 'add') {
      await api.put('/schedule/slot/add', payload)
      ElMessage.success(`已添加 ${payload.user_name}`)
    } else {
      await api.delete('/schedule/slot/remove', { data: payload })
      ElMessage.success(`已移除 ${payload.user_name}`)
    }
    // 仅重新加载，不重跑算法
    await reloadSchedule()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function removePerson(name: string) {
  if (!schedule.value) return
  try {
    await api.delete('/schedule/slot/remove', {
      data: {
        week_no: schedule.value.week_no,
        duty_date: editSlot.wd,
        period: editSlot.period,
        user_name: name,
      }
    })
    ElMessage.success(`已移除 ${name}`)
    // 本地移除 + 重新加载确认
    await reloadSchedule()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

function getAvailableUsers(): { name: string }[] {
  if (!store.users.length) return []
  const assigned = new Set(getSlotNames(editSlot.wd, editSlot.period))
  return store.users.filter(u => !assigned.has(u.name)).map(u => ({ name: u.name }))
}

function downloadDocx() {
  if (!schedule.value) return
  const url = `/api/schedule/export/docx?week_no=${schedule.value.week_no}`
  const a = document.createElement('a')
  a.href = url
  a.download = `第${schedule.value.week_no}周年委值班签到表.docx`
  a.click()
}

function downloadCSV() {
  if (!schedule.value) return
  let csv = '时段,'
  weekdays.forEach(wd => {
    csv += `${wd}(${schedule.value!.week_dates[wd] || ''}),`
  })
  csv += '\n'
  dutySlots.forEach(slot => {
    csv += `${slot},`
    weekdays.forEach(wd => {
      const names = getSlotNames(wd, slot)
      csv += `${names.join('/') || '—'},`
    })
    csv += '\n'
  })
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `第${weekDates.week_no}周值班表.csv`
  a.click()
}
</script>

<template>
  <div>
    <h1 style="font-size:24px;font-weight:700;margin-bottom:24px">排班管理</h1>

    <!-- 配置区 -->
    <el-card shadow="hover" style="border-radius:12px;margin-bottom:20px">
      <template #header>
        <span style="font-weight:600">排班参数</span>
      </template>
      <el-row :gutter="12" align="middle">
        <el-col :span="4">
          <label style="font-size:13px;color:#606266">周次</label>
          <el-input-number v-model="weekDates.week_no" :min="1" :max="30" size="small" style="width:100%" />
        </el-col>
        <el-col :span="2" v-for="wd in weekdays" :key="wd">
          <label style="font-size:12px;color:#606266">{{ wd }}</label>
          <el-input v-model="weekDates[wd === '周一' ? 'mon' : wd === '周二' ? 'tue' : wd === '周三' ? 'wed' : wd === '周四' ? 'thu' : 'fri' as keyof typeof weekDates]" size="small" placeholder="如 5.12" />
        </el-col>
        <el-col :span="3">
          <label style="font-size:12px;color:#606266">&nbsp;</label>
          <el-button type="primary" :loading="loading" @click="runSchedule" :icon="RefreshRight" style="width:100%">
            生成排班
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果区 -->
    <el-card v-if="schedule" shadow="hover" style="border-radius:12px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-weight:600">第{{ schedule.week_no }}周值班安排</span>
          <div style="display:flex;gap:8px">
            <el-tag size="small" type="info">极差: {{ schedule.stats.range_val }}</el-tag>
            <el-tag size="small" type="success">已安排: {{ Object.values(schedule.stats.week_counts).reduce((a:number,b:number)=>a+b,0) }}次</el-tag>
            <el-button size="small" :icon="Download" @click="downloadCSV">导出CSV</el-button>
            <el-button size="small" type="success" :icon="Download" @click="downloadDocx">导出Word</el-button>
          </div>
        </div>
      </template>

      <el-table :data="dutySlots.map(s => ({ slot: s }))" border stripe size="small">
        <el-table-column prop="slot" label="时段" width="100" fixed>
          <template #default="{ row }">
            <div style="font-weight:600">{{ row.slot }}</div>
            <div style="font-size:11px;color:#909399">{{ slotTimes[row.slot] }}</div>
          </template>
        </el-table-column>
        <el-table-column v-for="wd in weekdays" :key="wd" :label="`${wd}(${schedule.week_dates[wd] || ''})`" align="center">
          <template #default="{ row }">
            <template v-if="schedule.week_dates[wd] === '假'">
              <el-tag type="info" size="small">放假</el-tag>
            </template>
            <template v-else>
              <div @click="openEditSlot(wd, row.slot)" style="cursor:pointer;min-height:20px" :title="'点击编辑 ' + wd + ' ' + row.slot">
                <template v-for="name in getSlotNames(wd, row.slot)" :key="name">
                  <el-tag size="small" style="margin:1px;cursor:pointer" @click.stop>{{ name }}</el-tag>
                </template>
                <span v-if="getSlotNames(wd, row.slot).length === 0" style="color:#c0c4cc;font-size:11px">点击编辑</span>
              </div>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 统计区 -->
      <el-row :gutter="12" style="margin-top:16px">
        <el-col :span="8">
          <el-card shadow="never" style="background:#f8f9fc">
            <div style="font-size:13px;color:#606266;margin-bottom:8px;font-weight:600">均衡度</div>
            <div style="font-size:12px;color:#909399">
              <div>最少: {{ schedule.stats.min_count }} / 最多: {{ schedule.stats.max_count }}</div>
              <div>平均: {{ schedule.stats.avg }} / 极差: {{ schedule.stats.range_val }}</div>
              <div>使用种子: #{{ schedule.stats.seed_used }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" style="background:#f8f9fc">
            <div style="font-size:13px;color:#606266;margin-bottom:8px;font-weight:600">本周安排</div>
            <div v-for="(cnt, name) in schedule.stats.week_counts" :key="name" v-show="cnt > 0"
                 style="display:inline-block;margin:2px 4px">
              <el-tag size="small" :type="cnt >= 2 ? 'warning' : 'success'">{{ name }}: +{{ cnt }}</el-tag>
            </div>
            <div v-if="schedule.stats.unassigned.length" style="margin-top:8px;font-size:12px;color:#F56C6C">
              未安排({{ schedule.stats.unassigned.length }}人): {{ schedule.stats.unassigned.slice(0,10).join(', ') }}{{ schedule.stats.unassigned.length > 10 ? '...' : '' }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" style="background:#f8f9fc">
            <div style="font-size:13px;color:#606266;margin-bottom:8px;font-weight:600">累计次数汇总</div>
            <div style="font-size:11px;max-height:140px;overflow-y:auto;line-height:1.8">
              <template v-for="(cnt, name) in sortedAccumulated" :key="name">
                <span style="display:inline-block;margin:1px 3px;font-family:monospace">
                  <span :style="{color: cnt >= 10 ? '#C0392B' : cnt >= 8 ? '#C07D17' : '#606266', fontWeight: cnt >= 9 ? '600' : '400'}">{{ name }}</span>
                  <span :style="{color: '#909399'}">:{{ cnt }}</span>
                </span>
              </template>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 累计次数汇总文本（可复制） -->
      <el-card v-if="schedule" shadow="never" style="margin-top:12px;background:#faf9f6">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span style="font-size:13px;color:#606266;font-weight:600">📋 累计次数汇总文本（可直接粘贴回历史次数或Python脚本）</span>
          <el-button size="small" type="primary" @click="copySummaryText">
            <el-icon><CopyDocument /></el-icon> 复制
          </el-button>
        </div>
        <div style="font-size:12px;font-family:monospace;line-height:1.8;word-break:break-all;background:#fff;padding:10px 14px;border-radius:6px;border:1px solid #e8e8e8;max-height:120px;overflow-y:auto">
          截止第{{ schedule.week_no }}周结束已安排值班次数：<br/>
          {{ summaryText }}
        </div>
      </el-card>
    </el-card>

    <el-empty v-else description="请配置参数后点击「生成排班」" style="margin-top:60px" />

    <!-- 排班编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" :title="`编辑 ${editSlot.wd} ${editSlot.period}`" width="480px" destroy-on-close>
      <!-- 当前人员 -->
      <div v-if="editSlot.names.length" style="margin-bottom:16px">
        <div style="font-size:13px;color:#606266;margin-bottom:8px">当前值班人员</div>
        <el-tag
          v-for="name in editSlot.names" :key="name"
          closable size="default"
          style="margin:2px 4px"
          @close="removePerson(name)"
        >
          {{ name }}
        </el-tag>
      </div>
      <div v-else style="margin-bottom:16px;color:#909399;font-size:13px">该时段暂无值班人员</div>

      <!-- 添加人员 -->
      <div style="border-top:1px solid #ebeef5;padding-top:16px">
        <div style="font-size:13px;color:#606266;margin-bottom:8px">添加值班人员</div>
        <div style="display:flex;gap:8px">
          <el-select
            v-model="editUserName"
            filterable
            placeholder="选择人员"
            style="flex:1"
          >
            <el-option
              v-for="u in getAvailableUsers()"
              :key="u.name"
              :label="u.name"
              :value="u.name"
            />
          </el-select>
          <el-button type="primary" :icon="Plus" @click="doEditAction" :disabled="!editUserName.trim()">
            添加
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>
