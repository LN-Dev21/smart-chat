<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SessionSidebar from './components/SessionSidebar.vue'
import ChatPanel from './components/ChatPanel.vue'
import { listSessions, createSession, deleteSession } from './api/index.js'

const sessions = ref([])
const activeId = ref('')

onMounted(async () => {
  await refreshSessions()
  if (sessions.value.length > 0) {
    activeId.value = sessions.value[0].id
  }
})

async function refreshSessions() {
  const res = await listSessions()
  sessions.value = res.data
}

async function handleCreate() {
  const res = await createSession()
  await refreshSessions()
  activeId.value = res.data.id
}

function handleSelect(id) {
  activeId.value = id
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('删除后聊天记录不可恢复，确定删除？', '提示', { type: 'warning' })
  } catch { return }
  await deleteSession(id)
  await refreshSessions()
  if (activeId.value === id) {
    activeId.value = sessions.value.length > 0 ? sessions.value[0].id : ''
  }
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="app-layout">
    <SessionSidebar
      :sessions="sessions"
      :active-id="activeId"
      @select="handleSelect"
      @create="handleCreate"
      @delete="handleDelete"
    />
    <ChatPanel v-if="activeId" :key="activeId" :session-id="activeId" />
    <div v-else class="no-session">
      <div>点击左上角「新对话」开始使用</div>
    </div>
  </div>
</template>

<style scoped>
.app-layout { display: flex; height: 100vh; width: 100vw; }
.no-session {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: #909399; font-size: 15px;
}
</style>
