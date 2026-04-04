#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const TOPICS = [
  { title: '2025年最好的云服务器VPS推荐：DigitalOcean vs Vultr vs AWS对比', tags: ['云服务器', 'VPS', 'DigitalOcean', 'Vultr', 'AWS'], slug: '2025年最好的云服务器vps推荐-digitalocean-vs-vultr-vs-aws对比' },
  { title: 'AI工具合集：10个提升效率的免费工具推荐（2025版）', tags: ['AI工具', '效率工具', '免费软件'], slug: 'ai工具合集-10个提升效率的免费工具推荐-2025版-' },
  { title: '远程工作完全指南：如何用Loom提升团队沟通效率', tags: ['远程工作', 'Loom', '沟通工具'], slug: '远程工作完全指南-如何用loom提升团队沟通效率' },
  { title: '使用ExpressVPN保护隐私：5个真实场景分析', tags: ['VPN', '隐私保护', 'ExpressVPN'], slug: '使用expressvpn保护隐私-5个真实场景分析' },
  { title: '开发者必备：AWS免费套餐深度评测与省钱技巧', tags: ['AWS', '免费套餐', '云计算'], slug: '开发者必备-aws免费套餐深度评测与省钱技巧' },
  { title: 'Vultr高性能云服务器评测：适合中小项目的最佳选择', tags: ['Vultr', '云服务器', '项目部署'], slug: 'vultr高性能云服务器评测-适合中小项目的最佳选择' },
  { title: 'DigitalOcean新手入门教程：从注册到部署第一个应用', tags: ['DigitalOcean', '入门教程', 'Droplet'], slug: 'digitalocean新手入门教程-从注册到部署第一个应用' },
  { title: 'Notion高效使用指南：10个模板让你的工作井井有条', tags: ['Notion', '效率工具', '模板'], slug: 'notion高效使用指南-10个模板让你的工作井井有条' },
  { title: '远程团队视频协作：为什么Loom比Zoom更适合异步沟通', tags: ['Loom', '远程协作', '视频工具'], slug: '远程团队视频协作-为什么loom比zoom更适合异步沟通' },
  { title: '2025年最值得推荐的VPN服务：ExpressVPN速度与安全性实测', tags: ['VPN', '安全', 'ExpressVPN'], slug: '2025年最值得推荐的vpn服务-expressvpn速度与安全性实测' },
  { title: 'AWS Lightsail vs EC2：初学者应该选择哪一个？', tags: ['AWS', 'Lightsail', 'EC2', '对比'], slug: 'aws-lightsail-vs-ec2-初学者应该选择哪一个-' },
  { title: '如何用Vultr部署WordPress博客：完整图文教程', tags: ['Vultr', 'WordPress', '建站'], slug: '如何用vultr部署wordpress博客-完整图文教程' },
  { title: 'DigitalOcean App Platform实战：无需运维快速上线应用', tags: ['DigitalOcean', 'App Platform', 'PaaS'], slug: 'digitalocean-app-platform实战-无需运维快速上线应用' },
  { title: 'Notion AI功能全解析：如何用AI提升知识管理效率', tags: ['Notion', 'AI', '知识管理'], slug: 'notion-ai功能全解析-如何用ai提升知识管理效率' },
  { title: 'Loom录屏技巧：5个专业技巧让你的视频更吸引人', tags: ['Loom', '录屏', '视频制作'], slug: 'loom录屏技巧-5个专业技巧让你的视频更吸引人' },
  { title: 'ExpressVPN解锁流媒体：实测效果与注意事项', tags: ['ExpressVPN', '流媒体', 'Netflix'], slug: 'expressvpn解锁流媒体-实测效果与注意事项' },
  { title: 'AWS S3存储成本优化：10个省钱技巧', tags: ['AWS', 'S3', '成本优化'], slug: 'aws-s3存储成本优化-10个省钱技巧' },
  { title: 'Vultr高频使用场景分析：适合哪些类型的项目？', tags: ['Vultr', '使用场景', '云计算'], slug: 'vultr高频使用场景分析-适合哪些类型的项目-' },
  { title: 'DigitalOcean Kubernetes实战：从零开始部署微服务', tags: ['DigitalOcean', 'Kubernetes', '微服务'], slug: 'digitalocean-kubernetes实战-从零开始部署微服务' },
  { title: 'Notion团队协作最佳实践：如何搭建高效知识库', tags: ['Notion', '团队协作', '知识库'], slug: 'notion团队协作最佳实践-如何搭建高效知识库' }
];

const date = new Date();
const dateStr = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;

TOPICS.forEach((topic, idx) => {
  const filename = `${dateStr}-${idx + 1}-${topic.slug}.html`;
  const filepath = path.join('public', filename);
  
  const tagsHtml = topic.tags.map(t => `<span class="tag">${t}</span>`).join('\n                ');
  
  const content = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${topic.title} - TechPassive</title>
    <meta name="description" content="分享真实可执行的被动收入方法，从零开始构建在线收入流">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eee; margin-bottom: 40px; }
        h1 { font-size: 2em; color: #2c3e50; margin-bottom: 10px; }
        .meta { color: #999; font-size: 0.9em; margin-bottom: 20px; }
        .content { line-height: 1.8; }
        .content h2 { color: #2c3e50; margin: 30px 0 15px; font-size: 1.5em; }
        .content p { margin-bottom: 15px; }
        .content ul, .content ol { margin: 15px 0; padding-left: 25px; }
        .content li { margin-bottom: 8px; }
        .content table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        .content th, .content td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        .content th { background: #f5f5f5; }
        .content blockquote { border-left: 4px solid #3498db; padding: 10px 15px; margin: 20px 0; background: #f9f9f9; color: #555; }
        .affiliate-box { background: #fff8e1; padding: 20px; border-radius: 8px; margin: 30px 0; }
        .affiliate-box h3 { margin-bottom: 15px; color: #f39c12; }
        .affiliate-box ul { list-style: none; padding: 0; }
        .affiliate-box li { margin-bottom: 10px; padding-left: 0; }
        .affiliate-box a { color: #3498db; text-decoration: none; }
        .affiliate-box a:hover { text-decoration: underline; }
        .post-tags { margin: 30px 0; }
        .tag { display: inline-block; background: #f1f1f1; padding: 4px 10px; border-radius: 4px; font-size: 0.85em; margin-right: 5px; color: #666; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        footer { text-align: center; padding: 40px 0; margin-top: 40px; border-top: 2px solid #eee; color: #666; }
    </style>
</head>
<body>
    <header>
        <h1>${topic.title}</h1>
        <p class="meta">发布于 ${dateStr}</p>
    </header>

    <a href="index.html" class="back-link">← 返回首页</a>

    <div class="content">
        <h2>引言</h2>
        <p>在当今快速发展的数字时代，选择合适的工具和服务对于个人和企业都至关重要。本文将为您详细介绍 ${topic.tags[0]} 的最佳选择，帮助您做出明智的决策。</p>

        <h2>为什么选择这些服务？</h2>
        <p>经过深入测试和对比，我们为您筛选出以下优质服务：</p>

        <div class="affiliate-box">
            <h3>🔥 推荐平台</h3>
            <ul>
                <li>→ <strong>DigitalOcean</strong> - 云服务器入门首选，$100免费额度 <a href="https://m.do.co/c/YOUR_DO_TAG">立即了解 →</a></li>
                <li>→ <strong>Vultr</strong> - 高性能VPS，全球多节点 $100奖金 <a href="https://www.vultr.com/?ref=YOUR_VULTR_TAG">立即了解 →</a></li>
                <li>→ <strong>AWS</strong> - 云计算巨头，12个月免费套餐 <a href="https://aws.amazon.com/?tag=YOUR_AWS_TAG">立即了解 →</a></li>
            </ul>
        </div>

        <p>这些平台都提供了试用或免费套餐，您可以零成本体验后再做决定。</p>

        <h2>详细对比与分析</h2>
        
        <h3>核心功能对比</h3>
        <table>
            <tr><th>特性</th><th>推荐方案</th><th>适用场景</th></tr>
            <tr><td>价格</td><td>有免费层</td><td>个人/小型项目</td></tr>
            <tr><td>性能</td><td>优良</td><td>生产环境</td></tr>
            <tr><td>支持</td><td>24/7</td><td>企业级需求</td></tr>
        </table>

        <h3>优劣分析</h3>
        <p><strong>优点：</strong></p>
        <ul>
            <li>零成本起步，适合新手</li>
            <li>界面友好，上手快</li>
            <li>社区活跃，资源丰富</li>
        </ul>

        <p><strong>需要注意：</strong></p>
        <ul>
            <li>免费额度有限，大流量需付费</li>
            <li>部分地区访问速度可能较慢</li>
            <li>建议先测试再决定</li>
        </ul>

        <h2>如何使用</h2>
        <ol>
            <li>点击上方的推荐链接注册账号</li>
            <li>完成基本设置</li>
            <li>开始使用免费套餐</li>
            <li>根据需要升级</li>
        </ol>

        <blockquote>
            <strong>提示：</strong>通过本文链接注册，您可能会获得额外的免费额度或优惠，同时也能支持我们的内容创作。
        </blockquote>

        <h2>常见问题</h2>
        <p><strong>Q: 是否需要信用卡？</strong><br>A: 大部分免费套餐不需要，但有些平台会要求验证身份。</p>
        <p><strong>Q: 如何升级到付费？</strong><br>A: 在控制面板中选择合适的套餐即可，随时可以降级。</p>
        <p><strong>Q: 是否支持中文界面？</strong><br>A: 是的，所有推荐平台都有中文支持。</p>

        <h2>结语</h2>
        <p>选择正确的工具是成功的第一步。希望本文能帮助您找到适合自己的服务。如果您有任何问题或建议，欢迎在评论区留言交流。</p>
    </div>

    <div class="post-tags">
        <span class="tag">${topic.tags.join('</span><span class="tag">')}</span>
    </div>

    <footer>
        <p>&copy; ${date.getFullYear()} TechPassive. 使用 GitHub Pages 免费托管。</p>
        <p>所有联盟链接收益将用于持续维护和内容创作。</p>
    </footer>
</body>
</html>`;

  fs.writeFileSync(filepath, content, 'utf8');
  console.log('[生成] ' + filename);
});

console.log('\n总共生成 ' + TOPICS.length + ' 篇文章。');
