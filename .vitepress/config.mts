import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "Universal Document Engine",
  description: "Modern, high-aesthetic developer portals and API references.",
  base: "/ude-user-docs/",
  
  themeConfig: {
    logo: '/logo.svg',
    
    nav: [
      { text: 'Home', link: '/' },
      { text: 'User Guides', link: '/docs/user-guide' },
      { text: 'API Reference', link: '/api/' },
      { text: 'Design Specs', link: 'https://Sir-Derryk.github.io/ude-design-docs/' }
    ],

    sidebar: {
      '/docs/': [
        {
          text: 'User Guides',
          items: [
            { text: 'User Guide (Getting Started)', link: '/docs/user-guide' },
            { text: 'Admin Guide (Installation)', link: '/docs/admin-guide' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Sir-Derryk/universal-document-engine' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026-present Sir-Derryk'
    }
  }
})
