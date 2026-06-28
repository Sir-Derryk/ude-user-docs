import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import Breadcrumbs from './components/Breadcrumbs.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'doc-before': () => h(Breadcrumbs),
      'nav-bar-content-after': () => h(ThemeToggle)
    })
  }
}
