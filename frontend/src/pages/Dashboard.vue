<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/store'
import { UserFilled, Clock, Histogram, DataBoard } from '@element-plus/icons-vue'

const store = useAppStore()
const loading = ref(true)

onMounted(async () => {
  await Promise.all([
    store.fetchDashboard(),
    store.fetchUsers(),
    store.fetchRules(),
  ])
  loading.value = false
})

function countLevel(count: number, max: number): 'success' | 'warning' | 'danger' | 'info' {
  if (max <= 0) return 'info'
  if (count <= max * 0.6) return 'success'
  if (count <= max * 0.85) return 'warning'
  return 'danger'
}

const statsCards = computed(() => {
  const d = store.dashboard
  if (!d) return []
  return [
    { title: '在册人数', value: d.total_users, icon: UserFilled, color: '#667eea' },
    { title: '历史总记录', value: d.total_records, icon: Clock, color: '#4A9E2F' },
    { title: '极差', value: d.range, icon: Histogram, color: d.range <= 3 ? '#4A9E2F' : '#C0392B' },
    { title: '平均次数', value: d.avg_count, icon: DataBoard, color: '#2B7FD4' },
  ]
})

const sortedUsers = computed(() => {
  const d = store.dashboard
  if (!d) return []
  return Object.entries(d.user_counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
})
</script>

<template>
  <div>
    <h1 style="font-size:24px;font-weight:700;margin-bottom:24px">仪表盘</h1>

    <el-skeleton :loading="loading" animated>
      <!-- 统计卡片 -->
      <el-row :gutter="16">
        <el-col :span="6" v-for="card in statsCards" :key="card.title">
          <el-card shadow="hover" style="border-radius:12px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:16px">
              <div :style="{width:'48px',height:'48px',borderRadius:'12px',background:card.color+'20',display:'flex',alignItems:'center',justifyContent:'center'}">
                <el-icon :size="24" :color="card.color"><component :is="card.icon" /></el-icon>
              </div>
              <div>
                <div style="font-size:12px;color:#909399">{{ card.title }}</div>
                <div style="font-size:24px;font-weight:700">{{ card.value }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 统计表 -->
      <el-card shadow="hover" style="border-radius:12px">
        <template #header>
          <span style="font-weight:600">历史值班次数分布</span>
        </template>
        <el-table :data="sortedUsers" stripe max-height="480" size="small">
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="count" label="累计次数" width="120" align="center">
            <template #default="{ row }">
              <el-tag
                :type="countLevel(row.count, store.dashboard?.max_count || 0)"
                effect="light"
                size="small"
              >
                {{ row.count }} 次
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分布" align="center">
            <template #default="{ row }">
              <el-progress
                :percentage="store.dashboard ? Math.round(row.count / Math.max(store.dashboard.max_count, 1) * 100) : 0"
                :color="row.count >= (store.dashboard?.max_count || 0) ? '#C0392B' : '#667eea'"
                :stroke-width="8"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-skeleton>
  </div>
</template>
