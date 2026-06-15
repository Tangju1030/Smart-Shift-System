<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { aiAPI } from '@/api/ai'
import { useAppStore } from '@/store'
import { Promotion, User } from '@element-plus/icons-vue'

const store = useAppStore()
const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([
  { role: 'assistant', content: '你好！我是智能排班AI助手。\n\n你可以问我：\n• 帮我优化排班规则\n• 解释当前的排班结果\n• 如何提高公平性？\n\n请先确保已在环境变量中配置了 AI_API_KEY。' },
])
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref<HTMLElement>()

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true

  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }

  try {
    // 构建上下文
    const context: Record<string, any> = {}
    if (store.dashboard) context.dashboard = store.dashboard
    if (store.rules) context.rules = store.rules
    if (store.currentSchedule) {
      context.current_schedule = {
        week_no: store.currentSchedule.week_no,
        stats: store.currentSchedule.stats,
      }
    }

    const res = await aiAPI.chat({ message: text, context })
    messages.value.push({ role: 'assistant', content: res.data.reply })
  } catch (e: any) {
    const errMsg = e.response?.status === 503
      ? 'AI服务未配置。请在环境变量中设置 AI_PROVIDER 和 AI_API_KEY。'
      : (e.response?.data?.detail || 'AI 请求失败，请检查 API Key 配置')
    messages.value.push({ role: 'assistant', content: errMsg })
  } finally {
    loading.value = false
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }
}

async function quickAction(action: string) {
  inputText.value = action
  await sendMessage()
}
</script>

<template>
  <div>
    <h1 style="font-size:24px;font-weight:700;margin-bottom:24px">AI 助手</h1>

    <el-card shadow="hover" style="border-radius:12px;height:calc(100vh - 140px);display:flex;flex-direction:column">
      <!-- 快捷操作 -->
      <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap">
        <el-button size="small" @click="quickAction('请帮我优化当前的排班规则')" :icon="Promotion">
          优化规则
        </el-button>
        <el-button size="small" @click="quickAction('请解释最近一周的排班结果')">
          解释排班
        </el-button>
        <el-button size="small" @click="quickAction('如何提高排班的公平性？')">
          公平性建议
        </el-button>
      </div>

      <!-- 对话区 -->
      <div ref="chatContainer" style="flex:1;overflow-y:auto;padding:8px 0;margin-bottom:12px">
        <div v-for="(msg, i) in messages" :key="i"
             :style="{
               display:'flex', gap:'10px', marginBottom:'16px',
               justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
             }">
          <el-avatar v-if="msg.role === 'assistant'" :size="32" :icon="Promotion"
                     style="background:linear-gradient(135deg,#667eea,#764ba2);flex-shrink:0" />
          <div :style="{
            maxWidth:'70%', padding:'10px 14px', borderRadius:'12px', fontSize:'14px', lineHeight:'1.6',
            background: msg.role === 'user' ? 'linear-gradient(135deg,#667eea,#764ba2)' : '#f0f2f5',
            color: msg.role === 'user' ? '#fff' : '#303133',
            whiteSpace:'pre-wrap', wordBreak:'break-word',
          }">
            {{ msg.content }}
          </div>
          <el-avatar v-if="msg.role === 'user'" :size="32" :icon="User"
                     style="background:#a8b2d1;flex-shrink:0" />
        </div>

        <div v-if="loading" style="display:flex;gap:10px;align-items:center;padding:8px">
          <el-avatar :size="32" :icon="Promotion"
                     style="background:linear-gradient(135deg,#667eea,#764ba2)" />
          <span style="color:#909399;font-size:13px">思考中...</span>
        </div>
      </div>

      <!-- 输入区 -->
      <div style="display:flex;gap:8px;border-top:1px solid #ebeef5;padding-top:12px">
        <el-input
          v-model="inputText"
          placeholder="输入你的问题..."
          @keyup.enter="sendMessage"
          :disabled="loading"
          size="large"
        />
        <el-button type="primary" @click="sendMessage" :loading="loading" :disabled="!inputText.trim()" size="large">
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>
