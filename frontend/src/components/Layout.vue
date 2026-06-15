<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DataAnalysis, Calendar, Setting, ChatDotRound,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  const map: Record<string, string> = {
    dashboard: '/',
    scheduler: '/scheduler',
    settings: '/settings',
    ai: '/ai',
  }
  return map[String(route.name)] || '/'
})

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <el-container style="min-height:100vh">
    <el-aside width="220px" style="background:linear-gradient(180deg,#1d2671 0%,#1a1f4e 100%);color:#fff">
      <div style="padding:24px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.1)">
        <h2 style="font-size:18px;font-weight:700;color:#fff;letter-spacing:1px">智能年委排班</h2>
        <p style="font-size:12px;color:#a8b2d1;margin-top:6px">Scheduler System v1.0</p>
      </div>

      <el-menu
        :default-active="activeMenu"
        background-color="transparent"
        text-color="#a8b2d1"
        active-text-color="#fff"
        style="border-right:none"
      >
        <el-menu-item index="/" @click="navigate('/')">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/scheduler" @click="navigate('/scheduler')">
          <el-icon><Calendar /></el-icon>
          <span>排班管理</span>
        </el-menu-item>
        <el-menu-item index="/settings" @click="navigate('/settings')">
          <el-icon><Setting /></el-icon>
          <span>规则配置</span>
        </el-menu-item>
        <el-menu-item index="/ai" @click="navigate('/ai')">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI助手</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-main style="padding:24px;background:#f5f7fa">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.el-menu-item {
  margin: 2px 8px;
  border-radius: 8px;
}
.el-menu-item:hover {
  background: rgba(255,255,255,0.08) !important;
}
.el-menu-item.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 8px;
}
</style>
