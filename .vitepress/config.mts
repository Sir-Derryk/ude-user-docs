import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "Universal Document Engine",
  description: "Modern, high-aesthetic developer portals and API references.",
  base: "/ude-user-docs/",
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap' }]
  ],
  ignoreDeadLinks: [
    /^\/api/
  ],
  srcExclude: [
    '**/engine/**',
    '**/hugo-site/**'
  ],
  
  themeConfig: {
    logo: '/logo.svg',
    
    nav: [
      { text: 'Home', link: '/' },
      { text: 'User Guides', link: '/docs/getting-started' },
      { text: 'API Reference', link: 'https://sir-derryk.github.io/ude-user-docs/api/' }
    ],

    sidebar: {
      '/docs/': [
        {
          text: 'Chapter 1: Quick Start',
          collapsed: false,
          items: [
            { text: 'Getting Started', link: '/docs/getting-started' },
            { text: 'Target Configurations', link: '/docs/first-config' }
          ]
        },
        {
          text: 'Chapter 2: Coding Standards',
          collapsed: false,
          items: [
            { text: 'Commenting Rules', link: '/docs/commenting-rules' },
            { text: 'Exclusion Gates', link: '/docs/exclusion-gates' }
          ]
        },
        {
          text: 'Chapter 3: Config Reference',
          collapsed: false,
          items: [
            { text: 'Global Settings', link: '/docs/global-settings' },
            { text: 'Target Settings', link: '/docs/target-settings' }
          ]
        },
        {
          text: 'Chapter 4: Case Study & Deployment',
          collapsed: false,
          items: [
            { text: 'Case Study (Dogfooding)', link: '/docs/case-study' },
            { text: 'Admin Deployment', link: '/docs/admin-deployment' }
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
