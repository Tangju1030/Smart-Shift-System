import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/pages/Dashboard.vue'),
      meta: { title: '仪表盘' },
    },
    {
      path: '/scheduler',
      name: 'scheduler',
      component: () => import('@/pages/Scheduler.vue'),
      meta: { title: '排班管理' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/Settings.vue'),
      meta: { title: '规则配置' },
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('@/pages/AIAssistant.vue'),
      meta: { title: 'AI助手' },
    },
  ],
})

export default router
