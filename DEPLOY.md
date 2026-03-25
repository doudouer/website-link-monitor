# 免费部署指南（支持截图功能）

本项目已配置Docker部署，支持Chrome截图功能。以下是详细部署步骤：

---

## 🚀 推荐方案：Render + Docker

### 为什么选择这个方案？

- ✅ **免费**：每月750小时免费额度
- ✅ **支持截图**：使用Docker安装Chromium
- ✅ **自动部署**：连接GitHub自动部署
- ✅ **稳定可靠**：企业级云平台

---

## 第一步：推送代码到GitHub

确保您的GitHub仓库包含以下文件：

```
website-link-monitor/
├── web_app_complete.py
├── friendly_link_monitor.py
├── templates/
│   └── index_complete.html
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

---

## 第二步：注册Render

1. 访问 https://render.com
2. 点击 **"Get Started for Free"**
3. 使用GitHub账号登录

---

## 第三步：创建Web Service

### 方法A：使用render.yaml（推荐）

1. 点击 **"New +"** → **"Web Service"**
2. 选择 **"Deploy from Git repository"**
3. 连接您的GitHub账号
4. 选择您的仓库
5. Render会自动检测 `render.yaml` 配置
6. 点击 **"Apply"** 开始部署

### 方法B：手动配置

1. 点击 **"New +"** → **"Web Service"**
2. 选择您的GitHub仓库
3. 配置如下：

| 配置项 | 值 |
|-------|-----|
| Name | website-link-monitor |
| Region | Singapore |
| Branch | main |
| Runtime | **Docker** |
| Instance Type | Free |

4. 点击 **"Create Web Service"**

---

## 第四步：等待部署

- 首次部署约需 **5-10分钟**
- Docker会自动安装Chromium和依赖
- 部署完成后获得免费域名：
  - `https://your-app-name.onrender.com`

---

## 第五步：测试功能

访问您的域名，测试：

1. ✅ 手动输入链接检测
2. ✅ 自动爬取链接
3. ✅ **网站截图功能**
4. ✅ 风险等级评估
5. ✅ 结果展示

---

## ⚠️ 免费套餐限制

| 项目 | 限制 |
|-----|------|
| 运行时间 | 750小时/月 |
| 内存 | 512MB |
| 休眠 | 15分钟无访问后休眠 |
| 冷启动 | 休眠后首次访问需等待30秒 |

---

## 🔧 故障排除

### 截图功能不工作？

1. 检查环境变量：
   - `CHROME_BIN=/usr/bin/chromium`
   
2. 查看日志：
   - Render Dashboard → Logs

### 部署失败？

1. 检查Dockerfile语法
2. 查看构建日志
3. 确认requirements.txt依赖正确

---

## 📋 其他免费平台

如果不使用Render，也可以尝试：

### Railway（支持Docker）

1. 访问 https://railway.app
2. 使用GitHub登录
3. 选择仓库部署
4. 选择Docker运行时

### Fly.io（支持Docker）

1. 访问 https://fly.io
2. 安装flyctl命令行工具
3. 运行 `fly launch`

---

## 🎯 部署成功后

1. **分享链接**：将您的域名分享给其他人试用
2. **监控状态**：在Render Dashboard查看运行状态
3. **查看日志**：监控错误和访问日志

---

**祝您部署顺利！如有问题，请查看Render官方文档。**
