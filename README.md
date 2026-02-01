# Minecraft Auto Login

🎮 Microsoft 账号自动化管理系统，用于批量管理 Minecraft 账号的登录和 Cookie 管理。

## ✨ 功能特点

- 📦 批量导入和管理 Microsoft 账号
- 🍪 自动获取和保存登录 Cookie
- 🚀 自动登录 HMCL（Hello Minecraft Launcher）
- 🔄 支持批量操作
- 🐛 调试模式支持
- 📊 账号状态追踪

## 📋 系统要求

- Python 3.7+
- macOS / Linux / Windows
- 网络连接

## 🚀 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r results/requirements.txt
```

### 2. 使用账号管理器

```bash
python3 main.py
```

功能菜单：
- **1** - 导入账号（粘贴文本）
- **2** - 从文件导入账号
- **3** - 查看所有账号
- **4** - 查看账号详情
- **5** - 批量获取 Cookie
- **6** - 批量登录 HMCL
- **7** - 单个账号登录
- **8** - 删除账号
- **9** - 导出账号
- **10** - Cookie 管理

### 3. 单独获取 Cookie

```bash
python3 get_cookie_only.py
```

### 4. 自动登录 HMCL

```bash
python3 auto_login_http.py
```

## 📁 项目结构

```
.
├── main.py                 # 主程序 - 账号管理系统
├── get_cookie_only.py      # Cookie 获取工具
├── auto_login_http.py      # 自动登录工具
├── accounts/
│   ├── accounts.json       # 账号数据库（自动生成）
│   └── cookies/            # Cookie 存储目录
├── debug/                  # 调试文件目录
└── results/
    └── requirements.txt    # Python 依赖
```

## 🔧 工作流程

```
1. 导入账号 → 2. 获取 Cookie → 3. 自动登录
```

### 详细流程

1. **导入账号**
   - 支持多种格式：`email:password` 或完整的 Hypixel 格式
   - 自动解析等级、MC 名称、Hypixel 数据等

2. **获取 Cookie**
   - 自动登录 Microsoft 账号
   - 处理额外验证步骤
   - 保存登录 Cookie

3. **自动登录**
   - 使用保存的 Cookie
   - 提交设备代码到 HMCL
   - 自动完成登录流程

## 📝 账号格式示例

### 简单格式
```
email@example.com:password123
```

### 完整格式（带 Hypixel 数据）
```
[50]email@example.com:password123 |McName:PlayerName [Hypixel:Level:100 Coins:50000] [Capes:Optifine,Migrator]
```

## ⚙️ 配置说明

### 账号数据结构

```json
{
  "email@example.com": {
    "password": "密码",
    "level": 50,
    "mcname": "游戏名",
    "hypixel": {"Level": "100", "Coins": "50000"},
    "capes": ["Optifine", "Migrator"],
    "cookie_status": "valid",
    "last_login": "2026-02-01T12:00:00"
  }
}
```

## 🐛 调试模式

启用调试模式可以保存登录过程中的 HTML 页面：

```bash
# 在提示时输入 'y' 启用调试模式
调试模式? [y/N]: y
```

调试文件保存在 `debug/` 目录。

## ⚠️ 注意事项

1. **安全性**
   - 账号密码以明文存储，请妥善保管 `accounts.json`
   - 不要将包含真实账号的文件提交到公共仓库
   - Cookie 文件包含敏感信息，已在 `.gitignore` 中排除

2. **使用限制**
   - 请遵守 Microsoft 服务条款
   - 避免频繁请求导致账号被限制
   - 仅用于个人账号管理

3. **兼容性**
   - 主要针对 HMCL 启动器
   - 需要稳定的网络连接
   - 可能需要根据 Microsoft 登录页面更新调整代码

## 🔄 更新日志

### v1.0.0
- ✅ 基础账号管理功能
- ✅ Cookie 自动获取
- ✅ HMCL 自动登录
- ✅ 批量操作支持
- ✅ 调试模式

## 📄 许可证

本项目仅供学习和个人使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚡ 常见问题

**Q: Cookie 获取失败怎么办？**
A: 启用调试模式查看详细日志，检查网络连接和账号密码是否正确。

**Q: 支持双因素认证吗？**
A: 目前不支持双因素认证（2FA），请使用未启用 2FA 的账号。

**Q: 可以用于其他启动器吗？**
A: 理论上可以，但需要根据具体启动器的登录流程调整代码。

---

⭐ 如果这个项目对你有帮助，请给个 Star！
