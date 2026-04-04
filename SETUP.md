# 自动化部署指南

## 一、初始化仓库

```bash
# 1. 创建 GitHub 仓库（yourname.github.io）
# 2. 克隆到本地
git clone https://github.com/你的用户名/你的用户名.github.io.git
cd 你的用户名.github.io

# 3. 安装 Hexo
npm install -g hexo-cli
hexo init .
npm install

# 4. 复制我的配置
# 将 _config.yml 中的以下占位符替换：
# - YOUR_USERNAME -> 你的GitHub用户名
# - techpassive-20 / YOUR_DO_TAG / ... -> 你的联盟tag
```

## 二、手动首次部署

```bash
# 首次运行
node generate.js --count 20   # 生成20篇文章
npx hexo generate            # 生成静态文件
git add -A
git commit -m "首次发布"
git push origin main
```

然后在 GitHub Settings → Pages 中将 source 设置为 `gh-pages` branch。

## 三、自动化每日更新

### 方案A：使用 GitHub Actions（推荐）
在仓库根目录创建 `.github/workflows/auto.yml`：

```yaml
name: Daily Blog Update
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点（UTC）
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 设置 Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install hexo-cli -g
      - run: npm install
      - run: node generate.js --count 1
      - run: npx hexo generate
      - name: 部署
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

### 方案B：使用本地定时任务（cron）
在你的服务器或电脑上设置：

```bash
0 2 * * * cd /path/to/yourusername.github.io && ./deploy.sh >> /var/log/blog-deploy.log 2>&1
```

## 四、联盟账号申请（一次）

| 平台 | 佣金比例 | 推荐理由 |
|------|----------|----------|
| AWS Affiliate | 最高 $100/单 | 云服务需求大，复购率高 |
| DigitalOcean | $100/付费用户 | 开发者社区活跃 |
| Vultr | $100/付费用户 | 性价比高，容易转化 |
| ExpressVPN | 约 30% | 隐私关注人群付费意愿强 |

申请地址：
- AWS: https://affiliate-program.amazon.com/
- DigitalOcean: https://www.digitalocean.com/affiliates/
- Vultr: https://www.vultr.com/affiliate/
- ExpressVPN: https://www.expressvpn.com/affiliates

## 五、优化建议

1. 文章发布后，去 Google Search Console 提交 sitemap
2. 在社交媒体分享新文章（可自动化）
3. 关注 Analytics 数据，调整关键词
4. 每季度更新旧文章内容，保持新鲜度

## 六、预期收益

- 3个月：日均10-50访客 → 月 $10-50
- 6个月：日均50-200访客 → 月 $50-300
- 1年：日均200+访客 → 月 $300-2000+

---

**注意**：需要你完成 GitHub 账号注册和至少一个联盟账号申请后，我才能帮你填入真实链接并启动自动化。

现在请输入：
1. 你的 GitHub 用户名
2. 你选择的联盟平台（哪几个）
3. 你的收款方式（PayPal 或 Wise）

我将在你完成后为你填入配置并首次部署。