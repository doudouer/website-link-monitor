# 网站外链检测系统

**GitHub地址**: https://github.com/wangjiuchen2017-dot/website-link-monitor

---

## 快速开始

### 环境要求

- Python 3.8+
- Chrome浏览器（用于截图功能）
- ChromeDriver（自动匹配Chrome版本）

### 方法一：命令行运行

```bash
# 1. 克隆项目
git clone https://github.com/wangjiuchen2017-dot/website-link-monitor.git

# 2. 进入项目目录
cd website-link-monitor

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行项目
python web_app_complete.py

# 5. 访问
# 打开浏览器访问 http://127.0.0.1:5001
```

### 方法二：使用启动脚本（Mac）

```bash
# 1. 克隆项目
git clone https://github.com/wangjiuchen2017-dot/website-link-monitor.git

# 2. 进入项目目录
cd website-link-monitor

# 3. 安装依赖
pip install -r requirements.txt

# 4. 双击启动脚本
# 双击 "启动服务.command" 文件
```

### 方法三：Docker运行

```bash
# 1. 克隆项目
git clone https://github.com/wangjiuchen2017-dot/website-link-monitor.git

# 2. 进入项目目录
cd website-link-monitor

# 3. 构建Docker镜像
docker build -t website-link-monitor .

# 4. 运行容器
docker run -p 5001:5001 website-link-monitor

# 5. 访问
# 打开浏览器访问 http://127.0.0.1:5001
```

---

## 功能特性

### 1. 智能链接提取
- **截图识别**：上传网页截图，框选友情链接区域，自动识别链接
- **手动输入**：支持批量粘贴URL地址
- **自动爬取**：输入网站地址，自动提取所有外部链接

### 2. 多维度风险检测
- **内容安全检测**：赌博、成人、诈骗、钓鱼等内容识别
- **域名状态检测**：WHOIS信息查询、域名过期监控
- **跳转行为检测**：HTTP重定向、JavaScript跳转检测

### 3. 风险等级评估

| 风险等级 | 分数范围 | 说明 |
|---------|---------|------|
| CRITICAL | ≥100分 | 严重风险，需立即处理 |
| HIGH | 70-99分 | 高风险，建议尽快处理 |
| MEDIUM | 40-69分 | 中等风险，需要关注 |
| LOW | <40分 | 低风险，可正常访问 |

### 4. 网站截图
- 自动获取网站首页截图
- 截图展示便于人工审核
- 点击可查看大图

### 5. 可视化结果展示
- 统计卡片展示各风险等级数量
- 详细表格展示检测结果
- 风险因素一目了然

---

## 使用场景

### 场景一：定期巡检
网站管理员定期（如每周/每月）对网站所有外链进行检测，及时发现新增风险链接。

### 场景二：新增链接审核
在添加新的友情链接前，先使用系统检测目标网站的安全性，避免引入问题链接。

### 场景三：应急响应
收到用户投诉或监管部门通知后，快速定位问题链接并处理。

### 场景四：合规审计
配合网站安全合规审计，提供外链安全检测报告。

---

## 技术架构

- **前端**：Bootstrap 5 + 现代化UI设计
- **后端**：Python Flask
- **检测引擎**：多维度风险评估算法
- **截图服务**：Selenium + ChromeDriver

---

## 注意事项

1. **人工审核**：系统检测结果仅供参考，最终决策需人工审核确认
2. **网络环境**：部分网站可能因网络原因无法访问，建议多次检测确认
3. **合法合规**：请确保检测行为符合相关法律法规要求
4. **隐私保护**：系统不会存储被检测网站的用户数据

---

## 常见问题

### Q: 截图功能不工作？
A: 请确保已安装Chrome浏览器和ChromeDriver。Mac用户可以使用：
```bash
brew install chromedriver
```

### Q: 如何安装Python依赖？
A: 运行以下命令：
```bash
pip install -r requirements.txt
```

### Q: 端口被占用怎么办？
A: 修改 `web_app_complete.py` 中的端口号，或使用以下命令查找并关闭占用端口的进程：
```bash
lsof -ti:5001 | xargs kill -9
```

---

## 更新日志

### v1.0.0 (2024-03)
- 初始版本发布
- 支持链接检测、风险评估、网站截图
- 现代化UI界面
- 多维度风险检测算法

---

*网站外链检测系统 - 保障网站安全，从外链管理开始*
