<template>
  <button
    class="theme-toggle-btn"
    @click="cycleTheme"
    :title="currentTitle"
    :aria-label="currentTitle"
  >
    <!-- Sun Icon (Light Mode) -->
    <svg v-if="themeMode === 'light'" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12,9c1.65,0,3,1.35,3,3s-1.35,3-3,3s-3-1.35-3-3S10.35,9,12,9 M12,7c-2.76,0-5,2.24-5,5s2.24,5,5,5s5-2.24,5-5 S14.76,7,12,7L12,7z M2,13h2c0.55,0,1-0.45,1-1s-0.45-1-1-1H2c-0.55,0-1,0.45-1,1S1.45,13,2,13z M20,13h2c0.55,0,1-0.45,1-1 s-0.45-1-1-1h-2c-0.55,0-1,0.45-1,1S19.45,13,20,13z M11,2v2c0,0.55,0.45,1,1,1s1-0.45,1-1V2c0-0.55-0.45-1-1-1S11,1.45,11,2z M11,20v2c0,0.55,0.45,1,1,1s1-0.45,1-1v-2c0-0.55-0.45-1-1-1S11,19.45,11,20z M5.99,4.58c-0.39-0.39-1.03-0.39-1.41,0 c-0.39,0.39-0.39,1.02,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0s0.39-1.02,0-1.41L5.99,4.58z M18.36,16.95 c-0.39-0.39-1.03-0.39-1.41,0c-0.39,0.39-0.39,1.02,0,1.41l1.06,1.06c0.39,0.39,1.03,0.39,1.41,0c0.39-0.39,0.39-1.02,0-1.41 L18.36,16.95z M7.05,18.36l-1.06,1.06c-0.39,0.39-0.39,1.02,0,1.41s1.02,0.39,1.41,0l1.06-1.06c0.39-0.39,0.39-1.02,0-1.41 S7.44,17.97,7.05,18.36z M19.42,5.99l-1.06-1.06c-0.39-0.39-1.02-0.39-1.41,0c-0.39,0.39-0.39,1.02,0,1.41l1.06,1.06c0.39,0.39,1.02,0.39,1.41,0C19.81,7.01,19.81,6.38,19.42,5.99z"></path>
    </svg>
    
    <!-- Moon Icon (Dark Mode) -->
    <svg v-else-if="themeMode === 'dark'" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12.1,18.55c0.41-0.03,0.72-0.41,0.65-0.82c-0.03-0.2-0.12-0.39-0.27-0.53c-0.36-0.32-0.58-0.78-0.58-1.3 c0-0.94,0.76-1.7,1.7-1.7c0.42,0,0.8,0.16,1.1,0.41c0.16,0.14,0.38,0.21,0.59,0.18c0.41-0.05,0.7-0.43,0.65-0.84 c-0.03-0.25-0.16-0.47-0.36-0.61c-0.07-0.05-0.12-0.11-0.16-0.18c-0.35-0.56-0.55-1.22-0.55-1.93c0-2,1.62-3.62,3.62-3.62 c0.54,0,1.06,0.12,1.52,0.33c0.18,0.08,0.39,0.09,0.58,0.02c0.39-0.14,0.59-0.57,0.45-0.96c-0.1-0.27-0.32-0.47-0.6-0.54 C19.26,3.6,17.47,3,15.5,3c-5.25,0-9.5,4.25-9.5,9.5c0,4.8,3.48,8.81,8.1,9.45c0.2,0.03,0.4-0.01,0.57-0.11 c0.29-0.18,0.45-0.51,0.41-0.85c-0.03-0.25-0.17-0.46-0.38-0.59c-0.54-0.34-0.9-0.95-0.9-1.63c0-1.05,0.85-1.9,1.9-1.9 C11.83,18.4,11.97,18.47,12.1,18.55z"></path>
    </svg>
    
    <!-- Monitor Icon (System/Auto Mode) -->
    <svg v-else viewBox="0 0 24 24" fill="currentColor">
      <path d="M4 3h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5v2h3a1 1 0 0 1 0 2H6a1 1 0 0 1 0-2h3v-2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm0 2v10h16V5H4z"></path>
    </svg>
  </button>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const themeMode = ref('auto') // 'light' | 'dark' | 'auto'

const currentTitle = computed(() => {
  if (themeMode.value === 'light') return 'Дневная тема'
  if (themeMode.value === 'dark') return 'Ночная тема'
  return 'Системная тема'
})

const query = typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)') : null

function updateThemeClass(mode) {
  if (typeof window === 'undefined') return
  
  const el = document.documentElement
  if (mode === 'light') {
    el.classList.remove('dark')
  } else if (mode === 'dark') {
    el.classList.add('dark')
  } else {
    // auto / system
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    if (systemDark) {
      el.classList.add('dark')
    } else {
      el.classList.remove('dark')
    }
  }
}

function cycleTheme() {
  let nextMode = 'light'
  if (themeMode.value === 'light') {
    nextMode = 'dark'
  } else if (themeMode.value === 'dark') {
    nextMode = 'auto'
  } else {
    nextMode = 'light'
  }
  
  themeMode.value = nextMode
  localStorage.setItem('vitepress-theme-appearance', nextMode)
  updateThemeClass(nextMode)
}

const handleSystemThemeChange = (e) => {
  if (themeMode.value === 'auto') {
    updateThemeClass('auto')
  }
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('vitepress-theme-appearance')
    if (saved === 'light' || saved === 'dark' || saved === 'auto') {
      themeMode.value = saved
    } else {
      themeMode.value = 'auto'
    }
    updateThemeClass(themeMode.value)
    
    if (query) {
      query.addEventListener('change', handleSystemThemeChange)
    }
  }
})

onUnmounted(() => {
  if (query) {
    query.removeEventListener('change', handleSystemThemeChange)
  }
})
</script>

<style scoped>
.theme-toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s, color 0.2s;
  margin-left: 12px;
}

.theme-toggle-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: #0f172a;
}

.dark .theme-toggle-btn {
  color: #94a3b8;
}

.dark .theme-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
}

.theme-toggle-btn svg {
  width: 20px;
  height: 20px;
}
</style>
