# TechPassive 自动化博客

零成本被动收入实战博客。使用 GitHub Pages 免费托管。

## 快速部署

### 1. 创建 GitHub 仓库

在 GitHub 上创建名为 `yaohehe.github.io` 的仓库（替换 yaohehe 为你的 GitHub 用户名）

### 2. 本地初始化

```bash
git init
git remote add origin https://github.com/yaohehe/yaohehe.github.io.git
git add -A
git commit -m "Initial commit"
git push -u origin main
```

### 3. 启用 GitHub Pages

1. 访问仓库 Settings → Pages
2. Source 选择 "Deploy from a branch"
3. Branch 选择 "main"，文件夹选择 "/ (root)"
4. 点击 Save

等待 2-3 分钟，博客将上线于：https://yaohehe.github.io

## 更新联盟链接

编辑 `public/index.html` 和其他 HTML 文件，将以下占位符替换为你的实际联盟链接：

- `YOUR_AWS_TAG` → AWS 联盟追踪码
- `YOUR_DO_TAG` → DigitalOcean 联盟链接
- `YOUR_VULTR_TAG` → Vultr 联盟链接

## 自动化更新

本项目配置了每日自动生成新文章的脚本。运行：

```bash
npm install
node genposts.js
```

## 文件结构

```
affiliate-blog/
├── public/              # 静态HTML文件（已发布）
│   ├── index.html        # 首页
│   └── *.html            # 各篇文章
├── source/               # 源文件
│   └── _posts/           # Markdown文章
├── _config.yml          # Hexo配置
├── generate.js          # 文章生成脚本
└── README.md            # 本文件
```

## 收入来源

本博客通过联盟链接产生收入：
- AWS 联盟计划
- DigitalOcean 联盟计划
- Vultr 联盟计划

佣金将支付至你的 PayPal 账户：yao_hehe@hotmail.com

## 注意事项

1. **联盟注册**：确保已在各平台注册联盟账号
2. **内容更新**：定期更新SEO文章以维持搜索排名
3. **合规性**：遵守各平台的联盟条款

---
*使用 Hexo + GitHub Pages 构建，完全零成本*
