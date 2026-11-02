<template>
  <aside class="sidebar" :class="{ 'sidebar-open': isMobileOpen, 'sidebar-collapsed': isCollapsed }">
    <div class="sidebar-header">
      <div class="brand">
        <div class="brand-mark">CC</div>
        <div class="brand-text" v-if="!isCollapsed">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <LanguageSwitcher v-if="!isCollapsed" />
      <button
        class="collapse-toggle"
        :aria-label="isCollapsed ? t('sidebar.expand') : t('sidebar.collapse')"
        :title="isCollapsed ? t('sidebar.expand') : t('sidebar.collapse')"
        @click="toggleCollapse"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" :style="{ transform: isCollapsed ? 'rotate(180deg)' : 'none' }">
          <path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: route.path === item.path }"
        :title="isCollapsed ? t(item.labelKey) : null"
        @click="closeMobile"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label" v-if="!isCollapsed">{{ t(item.labelKey) }}</span>
        <span v-if="isCollapsed" class="nav-tooltip">{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>

  <!-- Mobile overlay -->
  <div v-if="isMobileOpen" class="sidebar-overlay" @click="closeMobile"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

defineEmits(['show-profile-details', 'show-tasks'])

const route = useRoute()
const { t } = useI18n()

const isMobileOpen = ref(false)
const isCollapsed = ref(false)

onMounted(() => {
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved) isCollapsed.value = JSON.parse(saved)
})

const navItems = [
  {
    path: '/',
    labelKey: 'nav.overview',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 10L10 3L17 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 8.5V16.5C5 16.776 5.224 17 5.5 17H8V13C8 12.448 8.448 12 9 12H11C11.552 12 12 12.448 12 13V17H14.5C14.776 17 15 16.776 15 16.5V8.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/inventory',
    labelKey: 'nav.inventory',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 6L10 2.5L17 6M3 6L10 9.5M3 6V14L10 17.5M17 6L10 9.5M17 6V14L10 17.5M10 9.5V17.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/orders',
    labelKey: 'nav.orders',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="4" y="3" width="12" height="15" rx="1.5" stroke="currentColor" stroke-width="1.6"/><path d="M7 2.5H13V4.5C13 4.776 12.776 5 12.5 5H7.5C7.224 5 7 4.776 7 4.5V2.5Z" stroke="currentColor" stroke-width="1.6"/><path d="M7 9H13M7 12H13M7 15H10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
  },
  {
    path: '/spending',
    labelKey: 'nav.finance',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2.5" y="5" width="15" height="11" rx="1.5" stroke="currentColor" stroke-width="1.6"/><path d="M2.5 8.5H17.5" stroke="currentColor" stroke-width="1.6"/><circle cx="14" cy="12" r="1.25" fill="currentColor"/></svg>'
  },
  {
    path: '/demand',
    labelKey: 'nav.demandForecast',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2.5 16.5L7 11L10.5 14L17.5 6.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M12.5 6.5H17.5V11.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/restocking',
    labelKey: 'nav.restocking',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M17 10C17 13.866 13.866 17 10 17C6.134 17 3 13.866 3 10C3 6.134 6.134 3 10 3C12.21 3 14.18 4.024 15.465 5.625" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M15 2.5V6H11.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  },
  {
    path: '/reports',
    labelKey: 'nav.reports',
    icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M5.5 2.5H11.5L15 6V16.5C15 17.052 14.552 17.5 14 17.5H5.5C4.948 17.5 4.5 17.052 4.5 16.5V3.5C4.5 2.948 4.948 2.5 5.5 2.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M11.5 2.5V6H15" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M7 10H12M7 12.5H12M7 15H9.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
  }
]

const toggleMobile = () => {
  isMobileOpen.value = !isMobileOpen.value
}

const closeMobile = () => {
  isMobileOpen.value = false
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', isCollapsed.value)
}

defineExpose({ toggleMobile, isCollapsed })
</script>

<style scoped>
.sidebar {
  width: 256px;
  min-width: 256px;
  height: 100vh;
  position: sticky;
  top: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 110;
  transition: var(--transition-smooth, all 0.2s cubic-bezier(0.4, 0, 0.2, 1));
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-toggle {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: var(--transition-smooth, all 0.2s cubic-bezier(0.4, 0, 0.2, 1));
  flex-shrink: 0;
}

.collapse-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
}

.collapse-toggle svg {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.brand-mark {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.02em;
  transition: var(--transition-smooth, all 0.2s cubic-bezier(0.4, 0, 0.2, 1));
}

.brand:hover .brand-mark {
  transform: scale(1.05) rotate(-2deg);
  box-shadow: var(--shadow-md, 0 4px 10px -2px rgba(15, 23, 42, 0.15));
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-text h1 {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.688rem;
  color: #94a3b8;
  font-weight: 500;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
    color 0.2s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #0f172a;
  transform: translateX(2px);
}

.nav-item:active {
  transform: translateX(2px) scale(0.98);
}

.nav-item:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.nav-item.active {
  background: #dbeafe;
  color: #1e40af;
  font-weight: 600;
}

.nav-item.active:hover {
  transform: translateX(0);
}

.nav-item::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #1e40af;
  transform: scaleY(0);
  transform-origin: center;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item.active::before {
  transform: scaleY(1);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item:hover .nav-icon {
  transform: scale(1.1) rotate(-4deg);
}

.nav-icon :deep(svg) {
  display: block;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-tooltip {
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%) translateX(-4px);
  background: #0f172a;
  color: #ffffff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  z-index: 120;
  box-shadow: var(--shadow-md, 0 4px 10px -2px rgba(15, 23, 42, 0.15));
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.2s cubic-bezier(0.4, 0, 0.2, 1),
    visibility 0.2s;
}

.nav-item:hover .nav-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(0);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e2e8f0;
}

.sidebar-footer :deep(.profile-menu) {
  width: 100%;
}

.sidebar-footer :deep(.profile-button) {
  width: 100%;
}

.sidebar-overlay {
  display: none;
}

/* Icons-only collapsed mode */
.sidebar.sidebar-collapsed {
  width: 72px;
  min-width: 72px;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar.sidebar-collapsed .sidebar-header {
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  gap: 10px;
}

.sidebar.sidebar-collapsed .brand {
  justify-content: center;
}

.sidebar.sidebar-collapsed .collapse-toggle {
  position: static;
}

.sidebar.sidebar-collapsed .sidebar-nav {
  padding: 16px 8px;
  align-items: center;
}

.sidebar.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 12px;
  width: 48px;
}

.sidebar.sidebar-collapsed .nav-item::before {
  left: -8px;
}

.sidebar.sidebar-collapsed .sidebar-footer {
  padding: 16px 8px;
  display: flex;
  justify-content: center;
}

.sidebar.sidebar-collapsed .sidebar-footer :deep(.profile-button) {
  width: auto;
  padding: 8px;
  justify-content: center;
}

.sidebar.sidebar-collapsed .sidebar-footer :deep(.profile-name),
.sidebar.sidebar-collapsed .sidebar-footer :deep(.chevron) {
  display: none;
}

.sidebar.sidebar-collapsed .sidebar-footer :deep(.dropdown-menu) {
  left: 100%;
  margin-left: 8px;
  top: 0;
}

@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: -256px;
    top: 0;
    height: 100vh;
    box-shadow: var(--shadow-lg, 0 10px 24px -6px rgba(15, 23, 42, 0.2));
    transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar.sidebar-open {
    left: 0;
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: 105;
    animation: overlay-fade-in 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
}

@keyframes overlay-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
