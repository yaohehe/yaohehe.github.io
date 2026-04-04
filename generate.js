#!/usr/bin/env node

/**
 * 自动化联盟营销内容生成器
 * 功能：批量生成SEO文章，嵌入联盟链接，提交到GitHub Pages
 * 使用：node generate.js [--count N] [--dry-run]
 */

const fs = require('fs');
const path = require('path');

// 联盟链接配置（需要你填入）
const AFFILIATE = {
  aws: 'https://aws.amazon.com/?tag=YOUR_AWS_TAG',
  digitalocean: 'https://m.do.co/c/YOUR_DO_TAG',
  vultr: 'https://www.vultr.com/?ref=YOUR_VULTR_TAG',
  expressvpn: 'https://expressvpn.com/?a_fid=YOUR_VPN_TAG',
  notion: 'https://www.notion.so/?ref=YOUR_NOTION_TAG',
  loom: 'https://www.loom.com/?ref=YOUR_LOOM_TAG'
};

// 文章关键词库（高转化方向）
const TOPICS = [
  { title: '2025年最好的云服务器VPS推荐：DigitalOcean vs Vultr vs AWS对比', tags: ['云服务器', 'VPS', 'DigitalOcean', 'Vultr', 'AWS'], affiliate: ['digitalocean', 'vultr', 'aws'] },
  { title: 'AI工具合集：10个提升效率的免费工具推荐（2025版）', tags: ['AI工具', '效率工具', '免费软件'], affiliate: ['notion', 'loom'] },
  { title: '远程工作完全指南：如何用Loom提升团队沟通效率', tags: ['远程工作', 'Loom', '沟通工具'], affiliate: ['loom'] },
  { title: '使用ExpressVPN保护隐私：5个真实场景分析', tags: ['VPN', '隐私保护', 'ExpressVPN'], affiliate: ['expressvpn'] },
  { title: '开发者必备：AWS免费套餐深度评测与省钱技巧', tags: ['AWS', '免费套餐', '云计算'], affiliate: ['aws'] },
  { title: 'Vultr高性能云服务器评测：适合中小项目的最佳选择', tags: ['Vultr', '云服务器', '项目部署'], affiliate: ['vultr'] },
  { title: 'DigitalOcean新手入门教程：从注册到部署第一个应用', tags: ['DigitalOcean', '入门教程', 'Droplet'], affiliate: ['digitalocean'] },
  { title: 'Notion高效使用指南：10个模板让你的工作井井有条', tags: ['Notion', '效率工具', '模板'], affiliate: ['notion'] },
  { title: '远程团队视频协作：为什么Loom比Zoom更适合异步沟通', tags: ['Loom', '远程协作', '视频工具'], affiliate: ['loom'] },
  { title: '2025年最值得推荐的VPN服务：ExpressVPN速度与安全性实测', tags: ['VPN', '安全', 'ExpressVPN'], affiliate: ['expressvpn'] },
  { title: 'AWS Lightsail vs EC2：初学者应该选择哪一个？', tags: ['AWS', 'Lightsail', 'EC2', '对比'], affiliate: ['aws'] },
  { title: '如何用Vultr部署WordPress博客：完整图文教程', tags: ['Vultr', 'WordPress', '建站'], affiliate: ['vultr'] },
  { title: 'DigitalOcean App Platform实战：无需运维快速上线应用', tags: ['DigitalOcean', 'App Platform', 'PaaS'], affiliate: ['digitalocean'] },
  { title: 'Notion AI功能全解析：如何用AI提升知识管理效率', tags: ['Notion', 'AI', '知识管理'], affiliate: ['notion'] },
  { title: 'Loom录屏技巧：5个专业技巧让你的视频更吸引人', tags: ['Loom', '录屏', '视频制作'], affiliate: ['loom'] },
  { title: 'ExpressVPN解锁流媒体：实测效果与注意事项', tags: ['ExpressVPN', '流媒体', 'Netflix'], affiliate: ['expressvpn'] },
  { title: 'AWS S3存储成本优化：10个省钱技巧', tags: ['AWS', 'S3', '成本优化'], affiliate: ['aws'] },
  { title: 'Vultr高频使用场景分析：适合哪些类型的项目？', tags: ['Vultr', '使用场景', '云计算'], affiliate: ['vultr'] },
  { title: 'DigitalOcean Kubernetes实战：从零开始部署微服务', tags: ['DigitalOcean', 'Kubernetes', '微服务'], affiliate: ['digitalocean'] },
  { title: 'Notion团队协作最佳实践：如何搭建高效知识库', tags: ['Notion', '团队协作', '知识库'], affiliate: ['notion'] }
];

// 生成文章内容模板
function generateContent(topic, index) {
  const date = new Date();
  const dateStr = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;

  // 构建联盟链接插入位置
  const affiliateLinks = topic.affiliate.map(platform => {
    const link = AFFILIATE[platform];
    const name = platform.charAt(0).toUpperCase() + platform.slice(1);
    return `- 推荐使用 [${name}](${link}) 获取更多信息`;
  }).join('\n');

  const content = `---
title: "${topic.title}"
date: ${dateStr}
tags: [${topic.tags.map(t => `'${t}'`).join(', ')}]
---

## 引言

在当今快速发展的数字时代，选择合适的工具和服务对于个人和企业都至关重要。本文将为您详细介绍 ${topic.tags[0] || '相关服务'} 的最佳选择，帮助您做出明智的决策。

## 为什么选择这些服务？

经过深入测试和对比，我们为您筛选出以下优质服务：

${affiliateLinks}

这些平台都提供了试用或免费套餐，您可以零成本体验后再做决定。

## 详细对比与分析

### 核心功能对比

| 特性 | 推荐方案 | 适用场景 |
|------|----------|----------|
| 价格 | 有免费层 | 个人/小型项目 |
| 性能 | 优良 | 生产环境 |
| 支持 | 24/7 | 企业级需求 |

### 优劣分析

**优点：**
- 零成本起步，适合新手
- 界面友好，上手快
- 社区活跃，资源丰富

**需要注意：**
- 免费额度有限，大流量需付费
- 部分地区访问速度可能较慢
- 建议先测试再决定

## 如何使用

1. 点击上方的推荐链接注册账号
2. 完成基本设置
3. 开始使用免费套餐
4. 根据需要升级

> **提示**：通过本文链接注册，您可能会获得额外的免费额度或优惠，同时也能支持我们的内容创作。

## 常见问题

**Q: 是否需要信用卡？**  
A: 大部分免费套餐不需要，但有些平台会要求验证身份。

**Q: 如何升级到付费？**  
A: 在控制面板中选择合适的套餐即可，随时可以降级。

**Q: 是否支持中文界面？**  
A: 是的，所有推荐平台都有中文支持。

## 结语

选择正确的工具是成功的第一步。希望本文能帮助您找到适合自己的服务。如果您有任何问题或建议，欢迎在评论区留言交流。

---

*本文定期更新，最后更新于 ${dateStr}。所有链接均为联盟链接，我们可能会从中获得佣金，但这不会影响您的购买价格，同时能帮助我们持续产出优质内容。*
`;

  return {
    filename: `${dateStr}-${index + 1}-${topic.title.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]/g, '-').substring(0, 50)}.md`,
    content
  };
}

// 主函数
function main() {
  const args = process.argv.slice(1);
  const count = args.includes('--count') ? parseInt(args[args.indexOf('--count') + 1]) || 20 : 20;
  const dryRun = args.includes('--dry-run');

  if (!fs.existsSync('source/_posts')) {
    fs.mkdirSync('source/_posts', { recursive: true });
  }

  const selectedTopics = TOPICS.slice(0, count);
  let generated = 0;

  selectedTopics.forEach((topic, idx) => {
    const { filename, content } = generateContent(topic, idx);
    const filepath = path.join('source/_posts', filename);

    if (!dryRun) {
      fs.writeFileSync(filepath, content, 'utf8');
      console.log(`[生成] ${filename}`);
    } else {
      console.log(`[预览] ${filename} (未写入)`);
    }
    generated++;
  });

  if (!dryRun) {
    console.log(`\n总共生成 ${generated} 篇文章。`);
    console.log('请运行 `hexo generate` 预览，然后 `hexo deploy` 发布到 GitHub Pages。');
  } else {
    console.log(`\n模拟生成 ${generated} 篇文章（dry-run模式）。`);
  }
}

main();