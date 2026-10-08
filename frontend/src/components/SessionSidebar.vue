<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'

defineProps({
  sessions: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['select', 'create', 'delete'])
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="logo">🤖 智聊助手</span>
      <el-button type="primary" size="small" :icon="Plus" @click="emit('create')">
        新对话
      </el-button>
    </div>

    <div class="session-list">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === activeId }"
        @click="emit('select', s.id)"
      >
        <span class="session-title">{{ s.title }}</span>
        <el-icon class="delete-icon" @click.stop="emit('delete', s.id)">
          <Delete />
        </el-icon>
      </div>
      <div v-if="sessions.length === 0" class="empty-tip">暂无会话</div>
    </div>

    <div class="sidebar-footer">智聊 SmartChat v2.0</div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px; flex-shrink: 0;
  display: flex; flex-direction: column;
  background: #1d1e22; color: #e5eaf3;
}
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 12px; border-bottom: 1px solid #33353a;
}
.logo { font-weight: bold; font-size: 15px; }
.session-list { flex: 1; overflow-y: auto; padding: 8px; }
.session-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; margin-bottom: 4px; border-radius: 8px;
  cursor: pointer; font-size: 13px; color: #cfd3dc;
}
.session-item:hover { background: #2a2b30; }
.session-item.active { background: #409eff; color: #fff; }
.session-title {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.delete-icon { display: none; flex-shrink: 0; margin-left: 6px; }
.session-item:hover .delete-icon { display: block; }
.sidebar-footer {
  padding: 10px; text-align: center; font-size: 12px;
  color: #6b6e76; border-top: 1px solid #33353a;
}
</style>
