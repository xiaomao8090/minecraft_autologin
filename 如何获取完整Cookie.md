# 如何获取完整 Cookie 用于自动登录

## 问题说明

自动登录需要**完整的 Cookie**，包含 Microsoft 账号的授权状态。

- ❌ `get_cookie_only.py` 只能获取基本登录 Cookie（3-5个）
- ✅ 需要从浏览器中提取完整 Cookie（15-19个）

## 方法一：使用浏览器扩展（推荐）

### 步骤：

1. **安装 Cookie 导出扩展**
   - Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
   - 或其他 Cookie 导出工具

2. **在浏览器中完成授权**
   - 打开 HMCL 启动器
   - 点击"微软登录"
   - 在浏览器中输入设备代码
   - 登录你的 Microsoft 账号
   - **点击"接受"授权 HMCL**
   - 等待 HMCL 显示登录成功

3. **导出 Cookie**
   - 访问 `https://login.live.com`
   - 点击浏览器扩展图标
   - 导出 Cookie（选择 JSON 格式）
   - 保存为 `你的邮箱.json`

4. **放入 cookies 文件夹**
   ```bash
   cp 你的邮箱.json "auto login/accounts/cookies/"
   ```

## 方法二：使用 import_browser_cookies.py

### 前提条件：
- 已在 Chrome 中登录 Microsoft 账号
- 已完成一次 HMCL 授权
- Chrome 浏览器已关闭

### 步骤：

```bash
cd "auto login"
python3 import_browser_cookies.py chrome 你的邮箱@gmail.com
```

## 验证 Cookie 是否完整

完整的 Cookie 应该包含以下字段：

### 必需字段（2个）：
- `WLSSC`
- `__Host-MSAAUTH`

### 重要字段（应该有大部分）：
- `IPT` ⭐ 最重要
- `MSPAuth`
- `MSPOK`
- `MSPRequ`
- `uaid`
- `OParams`
- `MSPPre`
- `MSPCID`
- `MSPVis`
- `MSPBack`
- `mkt`
- `amsc`
- `NAP`
- `ANON`
- `PPLState`

### 检查方法：

```bash
cd "auto login/accounts/cookies"
cat 你的邮箱.json | python3 -m json.tool | grep -E '"(IPT|WLSSC|__Host-MSAAUTH)"'
```

如果看到这3个字段，说明 Cookie 基本完整。

## 为什么需要完整 Cookie？

1. **基本 Cookie**（3-5个）：只能证明你登录了 Microsoft 账号
2. **完整 Cookie**（15-19个）：包含了 HMCL 的授权状态

没有授权状态，自动登录会卡在"同意页面"，需要手动点击"接受"。

## 常见问题

### Q: 为什么 get_cookie_only.py 获取的 Cookie 不能用？
A: 因为它只获取登录 Cookie，不包含 HMCL 授权状态。

### Q: 每个账号都需要手动授权一次吗？
A: 是的，第一次使用时必须在浏览器中授权。授权后 Cookie 会记住，以后就能自动登录。

### Q: Cookie 会过期吗？
A: 会的，通常几周到几个月。过期后需要重新获取。

### Q: 能不能自动化这个授权过程？
A: 不能。Microsoft 的同意页面是 JavaScript 渲染的，无法通过 HTTP 请求自动化。这是安全机制。
