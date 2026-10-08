<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { sendChat, sendAgentChat, getMessages } from '../api/index.js'

// 配置 marked：简单模式，开启换行
marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

const props = defineProps({ sessionId: { type: String, required: true } })

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const agentMode = ref(false)
const streamMode = ref(true)
const msgListRef = ref(null)

onMounted(loadHistory)

async function loadHistory() {
  try {
    const res = await getMessages(props.sessionId)
    messages.value = res.data.map(m => ({ role: m.role, content: m.content }))
  } catch (e) {
    console.error('加载历史失败', e)
  }
  scrollToBottom()
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text) { ElMessage.warning('请输入内容再发送'); return }
  if (loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  loading.value = true
  try {
    // 流式开关开启且非智能体模式：走 SSE 流式接口
    if (streamMode.value && !agentMode.value) {
      await handleSendStream(text)
      return
    }
    const res = agentMode.value
      ? await sendAgentChat(text, props.sessionId)
      : await sendChat(text, props.sessionId)

    if (res.data.code === 0) {
      let replyText = res.data.data.reply
      const tools = res.data.data.tools_used || []
      if (tools.length > 0) {
        replyText = `🔧 本轮调用了工具：${tools.join('、')}\n\n` + replyText
      }
      messages.value.push({ role: 'assistant', content: replyText })
    } else {
      ElMessage.error(res.data.message || '服务异常，请稍后再试')
    }
  } catch (err) {
    ElMessage.error('无法连接后端服务，请检查 8000 端口是否启动')
    console.error(err)
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 流式发送：fetch 逐块读取 SSE
async function handleSendStream(text) {
  messages.value.push({ role: 'assistant', content: '' })
  const idx = messages.value.length - 1

  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text, session_id: props.sessionId }),
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    for (const line of decoder.decode(value).split('\n\n')) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6)
      if (payload === '[DONE]') continue
      try { messages.value[idx].content += JSON.parse(payload).delta } catch (e) {}
      scrollToBottom()
    }
  }
}

async function scrollToBottom() {
  await nextTick()
  if (msgListRef.value) msgListRef.value.scrollTop = msgListRef.value.scrollHeight
}
</script>

<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="title">{{ agentMode ? '智能体模式（可查订单/天气/计算/时间）' : '普通对话模式' }}</span>
      <span class="header-right">
        <span class="agent-toggle">
          <el-switch v-model="streamMode" />
          <span class="agent-label">流式输出</span>
        </span>
        <span class="agent-toggle">
          <el-switch v-model="agentMode" />
          <span class="agent-label">智能体模式</span>
        </span>
      </span>
    </div>

    <div class="chat-body" ref="msgListRef">
      <div v-for="(msg, index) in messages" :key="index" class="msg-row" :class="msg.role">
        <div class="avatar">{{ msg.role === 'user' ? '🧑' : '🤖' }}</div>
        <div class="bubble" v-html="renderMarkdown(msg.content)"></div>
      </div>

      <div v-if="loading" class="msg-row assistant">
        <div class="avatar">🤖</div>
        <div class="bubble loading-bubble">
          <el-icon class="is-loading"><Loading /></el-icon> 正在思考...
        </div>
      </div>
    </div>

    <div class="chat-footer">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
        @keydown.enter.exact.prevent="handleSend"
      />
      <el-button type="primary" :loading="loading" :disabled="loading"
                 @click="handleSend" class="send-btn">发送</el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel { flex: 1; display: flex; flex-direction: column; background: #f5f7fa; min-width: 0; }
.chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: #fff; border-bottom: 1px solid #e4e7ed;
}
.chat-header .title { font-size: 14px; color: #606266; font-weight: bold; }
.header-right { display: flex; align-items: center; gap: 16px; }
.agent-toggle { display: flex; align-items: center; gap: 6px; }
.agent-label { font-size: 13px; }
.chat-body { flex: 1; overflow-y: auto; padding: 20px; }
.msg-row { display: flex; margin-bottom: 16px; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }
.avatar { font-size: 28px; margin: 0 10px; flex-shrink: 0; }
.bubble {
  max-width: 70%; padding: 10px 14px; border-radius: 10px;
  line-height: 1.6; word-break: break-word;
}
.bubble p { margin: 0 0 8px 0; }
.bubble p:last-child { margin-bottom: 0; }
.bubble ul, .bubble ol { margin: 4px 0; padding-left: 20px; }
.bubble li { margin: 2px 0; }
.bubble strong { font-weight: 600; }
.bubble code {
  background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 4px;
  font-family: Consolas, monospace; font-size: 0.9em;
}
.msg-row.assistant .bubble { background: #fff; border: 1px solid #e4e7ed; border-top-left-radius: 2px; }
.msg-row.user .bubble { background: #409eff; color: #fff; border-top-right-radius: 2px; }
.msg-row.user .bubble code { background: rgba(255,255,255,0.2); color: #fff; }
.loading-bubble { color: #909399; }
.chat-footer {
  display: flex; gap: 10px; padding: 12px 20px;
  background: #fff; border-top: 1px solid #e4e7ed;
}
.chat-footer .el-textarea { flex: 1; }
.send-btn { height: auto; }
</style>
