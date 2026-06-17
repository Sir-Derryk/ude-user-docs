import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  title: "Universal Document Engine",
  description: "Modern, high-aesthetic developer portals and API references.",
  base: "/ude-user-docs/",
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap' }],
    ['link', { rel: 'icon', type: 'image/png', href: '/ude-user-docs/favicon.png' }]
  ],
  vite: {
    publicDir: '.vitepress/public'
  },
  ignoreDeadLinks: [
    /^\/api/
  ],
  srcExclude: [
    '**/engine/**',
    '**/hugo-site/**'
  ],
  
  themeConfig: {
    logo: '/logo.png',
    siteTitle: 'Universal Documentation Engine Operational Documentation',
    outline: {
      level: [2, 6],
      label: 'On this page'
    },
    
    nav: [
      { text: 'User Docs', link: '/docs/chapter1-quick-start', target: '_blank', rel: 'noopener noreferrer' },
      { text: 'API Reference', link: 'https://sir-derryk.github.io/ude-user-docs/api/', target: '_blank', rel: 'noopener noreferrer' }
    ],

    sidebar: {
      '/docs/': [
        {
          text: 'Chapter 1: Quick Start',
          link: '/docs/chapter1-quick-start',
          collapsed: false,
          items: [
            { text: 'Getting Started', link: '/docs/getting-started' },
            { text: 'Target Configurations', link: '/docs/first-config' }
          ]
        },
        {
          text: 'Chapter 2: Coding Standards',
          link: '/docs/chapter2-coding-standards',
          collapsed: false,
          items: [
            { text: 'Commenting Rules', link: '/docs/commenting-rules' },
            { text: 'Exclusion Gates', link: '/docs/exclusion-gates' }
          ]
        },
        {
          text: 'Chapter 3: Config Reference',
          link: '/docs/chapter3-config-reference',
          collapsed: false,
          items: [
            { text: 'Global Settings', link: '/docs/global-settings' },
            { text: 'Target Settings', link: '/docs/target-settings' }
          ]
        },
        {
          text: 'Chapter 4: Case Study & Deployment',
          link: '/docs/chapter4-case-study',
          collapsed: false,
          items: [
            { text: 'Case Study (Dogfooding)', link: '/docs/case-study' },
            { text: 'Admin Deployment', link: '/docs/admin-deployment' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Sir-Derryk/ude-user-docs' }
    ],

    footer: {
      copyright: 'Copyright © 2026'
    }
  }
}))
