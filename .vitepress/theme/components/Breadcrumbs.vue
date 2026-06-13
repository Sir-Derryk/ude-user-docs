<script setup lang="ts">
import { computed } from 'vue'
import { useData, useRoute, withBase } from 'vitepress'

const { theme, page } = useData()
const route = useRoute()

const breadcrumbs = computed(() => {
  // Normalize current path to avoid trailing slashes/extensions matching issues
  const currentPath = route.path.replace(/\.html$/, '').replace(/\/$/, '')
  
  // If we are on the home page or layout is home, hide breadcrumbs
  if (!currentPath || currentPath === '' || currentPath === '/index' || page.value.frontmatter?.layout === 'home') {
    return []
  }

  const list = []

  // Add Home link
  list.push({ text: 'Home', link: withBase('/') })

  // Search in VitePress sidebar
  const sidebar = theme.value.sidebar
  if (sidebar) {
    // VitePress sidebar can be an array or an object keyed by route prefix
    if (Array.isArray(sidebar)) {
      // Simple array sidebar (global)
      for (const group of sidebar) {
        if (group.items) {
          for (const item of group.items) {
            const itemPath = item.link.replace(/\.html$/, '').replace(/\/$/, '')
            if (itemPath === currentPath) {
              if (group.text) {
                list.push({ text: group.text, link: null })
              }
              list.push({ text: item.text, link: withBase(item.link) })
              return list
            }
          }
        }
      }
    } else {
      // Multi-sidebar (keyed by path prefix)
      for (const key in sidebar) {
        // Match the current route prefix (e.g. '/docs/')
        if (currentPath.startsWith(key.replace(/\/$/, ''))) {
          const groups = sidebar[key]
          for (const group of groups) {
            if (group.items) {
              for (const item of group.items) {
                const itemPath = item.link.replace(/\.html$/, '').replace(/\/$/, '')
                if (itemPath === currentPath) {
                  if (group.text) {
                    list.push({ text: group.text, link: null })
                  }
                  list.push({ text: item.text, link: withBase(item.link) })
                  return list
                }
              }
            }
          }
        }
      }
    }
  }

  // Fallback: If not matched in sidebar but we have a page title, use it
  if (list.length === 1 && page.value.title) {
    list.push({ text: page.value.title, link: null })
  }

  return list
})
</script>

<template>
  <nav v-if="breadcrumbs.length > 0" id="ude-breadcrumbs" class="ude-breadcrumbs" aria-label="Breadcrumb">
    <ol class="breadcrumbs-list">
      <li v-for="(crumb, index) in breadcrumbs" :key="index" class="breadcrumb-item">
        <!-- Separator -->
        <span v-if="index > 0" class="breadcrumb-separator" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-right"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </span>
        
        <!-- Crumb Content -->
        <template v-if="index === 0">
          <a :href="crumb.link" class="breadcrumb-link home-link">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-home home-icon"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            <span class="home-text">{{ crumb.text }}</span>
          </a>
        </template>
        <template v-else-if="crumb.link && index < breadcrumbs.length - 1">
          <a :href="crumb.link" class="breadcrumb-link">{{ crumb.text }}</a>
        </template>
        <template v-else-if="!crumb.link && index < breadcrumbs.length - 1">
          <span class="breadcrumb-text intermediate">{{ crumb.text }}</span>
        </template>
        <template v-else>
          <span class="breadcrumb-text current" aria-current="page">{{ crumb.text }}</span>
        </template>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.ude-breadcrumbs {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  padding: 0;
  display: block;
}

.breadcrumbs-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 0.25rem;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  font-family: var(--vp-font-family-base);
  font-size: 13px;
  line-height: 1.5;
  color: var(--vp-c-text-2);
}

.breadcrumb-separator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0 0.5rem;
  color: var(--vp-c-text-3);
  opacity: 0.7;
}

.breadcrumb-separator svg {
  width: 12px;
  height: 12px;
}

.breadcrumb-link {
  color: var(--vp-c-text-2);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s ease;
  display: inline-flex;
  align-items: center;
}

.breadcrumb-link:hover {
  color: var(--vp-c-brand-1);
}

.home-link {
  gap: 0.35rem;
}

.home-icon {
  color: var(--vp-c-text-3);
  transition: color 0.2s ease;
}

.home-link:hover .home-icon {
  color: var(--vp-c-brand-1);
}

.breadcrumb-text {
  font-weight: 500;
}

.breadcrumb-text.intermediate {
  color: var(--vp-c-text-2);
  opacity: 0.8;
}

.breadcrumb-text.current {
  color: var(--vp-c-text-1);
  font-weight: 600;
  letter-spacing: -0.01em;
}

@media (max-width: 768px) {
  .ude-breadcrumbs {
    margin-top: 1rem;
    margin-bottom: 0.75rem;
  }
}
</style>
