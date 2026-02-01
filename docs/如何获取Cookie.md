# Microsoft账号Cookie获取流程详解

## 概述

本文档详细说明了如何通过HTTP请求获取Microsoft账号的完整Cookie集合，这些Cookie用于HMCL（Hello Minecraft! Launcher）的自动登录功能。

## 为什么需要Cookie？

- **用途**: Cookie包含了Microsoft账号的认证信息，可以让程序在不输入密码的情况下完成登录
- **有效期**: Cookie通常有效期为数天到数周，过期后需要重新获取
- **数量**: 完整的Cookie集合包含约30个Cookie，缺少关键Cookie会导致登录失败

## Cookie获取流程（5步）

### 第1步：访问Xbox Live OAuth登录页面

**请求信息：**
```
方法: GET
URL: https://login.live.com/oauth20_authorize.srf
参数:
  - client_id: 00000000402B5328 (Xbox Live客户端ID)
  - redirect_uri: https://login.live.com/oauth20_desktop.srf
  - scope: service::user.auth.xboxlive.com::MBI_SSL
  - display: touch
  - response_type: token
  - locale: en
```

**页面特征：**
- 标题: "Sign in to Minecraft"
- 内容: Microsoft登录表单（邮箱和密码输入框）
- 页面大小: 约30KB

**需要提取的信息：**
1. **PPFT令牌** (防CSRF令牌)
   - 提取方式1: `sFTTag.*value=\\\"(.+?)\\\"`
   - 提取方式2: `"sFT":"(.+?)"`
   - 示例: `-DnYqwgvlh6GkBVXj5BP...`

2. **提交URL** (urlPost)
   - 提取方式: `"urlPost":"(.+?)"`
   - 示例: `https://login.live.com/ppsecure/post.srf?client_id=000000004...`

**Cookie状态：**
- 数量: 5-10个基础Cookie
- 包含: MSPRequ, uaid, MSPOK等基础会话Cookie

---

### 第2步：提交登录凭证

**请求信息：**
```
方法: POST
URL: {从第1步提取的urlPost}
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36

数据:
  - login: {邮箱}
  - loginfmt: {邮箱}
  - passwd: {密码}
  - PPFT: {从第1步提取的PPFT}
```

**响应特征：**
- 标题: "Continue"
- 页面大小: 约1-2KB
- 页面类型: **自动提交表单页面**

**页面内容：**
```html
<form name="fmHF" id="fmHF" action="https://account.live.com/ar/cancel?..." method="post">
  <input type="hidden" name="pprid" value="ba1a27c1f016bafb">
  <input type="hidden" name="ipt" value="-Do*FOk0ljEAzdMTLf319d3w...">
  <input type="hidden" name="uaid" value="fd75d187d20846629e84236eff9f26b3">
</form>
<script>DoSubmit();</script>
```

**判断逻辑：**
- ✅ **成功**: URL包含 `#access_token` → 直接跳到第4步
- ⚠️ **需要验证**: 页面包含 `cancel?mkt=` → 继续第3步
- ❌ **失败**: 其他情况 → 密码错误或账号被锁定

**Cookie状态：**
- 数量: 增加到约13个
- 新增: MSPAuth, WLSSC, ANON等认证Cookie

---

### 第3步：跳过安全信息更新页面

**触发条件：**
- 第2步返回的页面包含 `cancel?mkt=`
- Microsoft要求用户更新安全信息（电话号码、备用邮箱等）

**需要提取的信息：**
1. **表单字段**:
   - `ipt`: 令牌值（约200字符）
   - `pprid`: 用户ID（如 `ba1a27c1f016bafb`）
   - `uaid`: 会话ID（如 `fd75d187d20846629e84236eff9f26b3`）

2. **提交URL** (action):
   - 提取方式: `id="fmHF" action="(.+?)"`
   - 示例: `https://account.live.com/ar/cancel?mkt=EN-US&uiflavor=hostmobile...`

**第一次POST请求：**
```
方法: POST
URL: {提取的action URL}
数据:
  - ipt: {提取的ipt值}
  - pprid: {提取的pprid值}
  - uaid: {提取的uaid值}
```

**第一次响应：**
- 标题: "Did you request a security info change?"
- 页面大小: 约180KB
- 内容: 安全信息更新页面

**需要提取返回URL：**
- 提取方式: `"recoveryCancel":{"returnUrl":"(.+?)"`
- 示例: `https://login.live.com/oauth20_authorize.srf?uaid=fd75d187d2...`

**第二次GET请求：**
```
方法: GET
URL: {提取的returnUrl}
```

**第二次响应：**
- URL应包含 `#access_token`
- 页面大小: 约2KB

**Cookie状态：**
- 数量: 保持13个左右
- 可能更新某些Cookie的值

---

### 第4步：确认登录成功

**URL特征：**
```
https://login.live.com/oauth20_desktop.srf?lc=1033#access_token=EwDYA%2bpvBAAU...
```

**URL组成：**
- `access_token`: OAuth访问令牌（约2000字符，URL编码）
- `token_type`: bearer
- `expires_in`: 86400（24小时）
- `scope`: service::user.auth.xboxlive.com::MBI_SSL
- `user_id`: 用户ID（如 `ba1a27c1f016bafb`）

**页面内容：**
```html
<html dir="ltr">
<head></head>
<body>
<div class="header">
  <h1><img src="images/ms-logo-v2.jpg" class="logo" alt="Microsoft account" /></h1>
</div>
<div class="content">
  <h2>You have reached a page that is not normally shown. 
      Microsoft will never ask you to copy or share this URL.</h2>
</div>
</body>
</html>
```

**Cookie状态：**
- 数量: 15-20个
- 包含Xbox Live相关的认证Cookie

---

### 第5步：访问Microsoft 365页面获取完整Cookie

**为什么需要这一步？**
- Xbox Live登录只能获取15-20个Cookie
- 访问m365服务会触发更多Cookie的生成
- 最终获得完整的30个Cookie集合

**请求信息：**
```
方法: GET
URL: https://m365.cloud.microsoft/search/?auth=1&origindomain=Office
```

**重定向流程：**
1. 请求m365 URL
2. 自动重定向到: `https://login.live.com/oauth20_authorize.srf?client_id=4765445b-32c6-49b0-83e6-1d93765276ca...`
3. 返回自动提交表单页面（类似第2步）

**响应特征：**
- 标题: "Continue"
- 页面大小: 约2-3KB
- 又是一个自动提交表单（跳转到安全信息页面）

**关键作用：**
- 触发Microsoft 365服务的认证流程
- 生成额外的服务Cookie
- **Cookie数量从15-20个增加到30个**

**新增的Cookie类型：**
- Office相关认证Cookie
- Microsoft 365服务Cookie
- 跨域认证Cookie
- 会话管理Cookie

**最终Cookie状态：**
- 数量: **30个完整Cookie**
- 包含所有必需的认证信息
- 可用于HMCL自动登录

---

## Cookie集合说明

### 基础Cookie（第1-2步获取，约13个）
```
MSPRequ    - 请求标识
uaid       - 用户会话ID
OParams    - OAuth参数
MSPPre     - 用户前缀信息
MSPCID     - 客户端ID
JSH        - JavaScript哈希
MSCC       - 国家/地区代码
SDIDC      - 会话数据ID
MSPBack    - 返回标识
__Host-MSAAUTH - 主机认证令牌
PPLState   - 隐私策略状态
MSPAuth    - 认证状态
MSPProf    - 配置文件状态
```

### Xbox Live Cookie（第4步获取，约5-7个）
```
NAP        - 网络访问策略
ANON       - 匿名标识
WLSSC      - Windows Live SSO Cookie（最重要）
```

### Microsoft 365 Cookie（第5步获取，约10-12个）
```
OH.SID     - Office会话ID
OH.FLID    - Office流ID
OH.DCAffinity - Office数据中心亲和性
.AspNetCore.* - ASP.NET Core相关Cookie
esctx-*    - 执行上下文Cookie
esctx      - 执行上下文
fpc        - 指纹Cookie
x-ms-gateway-slice - 网关切片
stsservicecookie - STS服务Cookie
MSPVis     - 访问标识
```

---

## 成功标志

### 登录成功的判断标准：
1. ✅ URL包含 `#access_token=`
2. ✅ Cookie数量达到30个
3. ✅ 包含关键Cookie: `WLSSC`, `MSPAuth`, `__Host-MSAAUTH`

### 失败情况：
1. ❌ 密码错误 → 第2步返回错误页面
2. ❌ 账号被锁定 → 第2步返回锁定提示
3. ❌ 需要2FA → 第2步返回验证码页面（当前不支持）
4. ❌ Cookie不完整 → 未访问m365页面，Cookie数量少于25个

---

## 时间消耗

- **正常流程**: 4-8秒
  - 第1步: 1-2秒
  - 第2步: 1-2秒
  - 第3步: 2-3秒（如果需要）
  - 第4步: 0.5秒
  - 第5步: 1-2秒

- **有安全验证**: 6-10秒
  - 额外增加2-3秒处理安全信息页面

- **失败情况**: 1-3秒
  - 快速返回错误

---

## 存储格式

Cookie保存为JSON格式：
```json
{
  "MSPRequ": "id=N&lt=1769967175&co=3",
  "uaid": "aa3ca6470c1346f187e311c92e2d2d72",
  "WLSSC": "EgAgAgMAAAAMgAAAugAB2NKclWJJW518gRljVpdZrq1a...",
  ...
}
```

**文件位置：**
- 临时: `cookies/{email}.json`
- 最终: `accounts/cookies/{email}.json`

---

## 注意事项

1. **Cookie有效期**: 通常7-30天，过期后需要重新获取
2. **安全性**: Cookie包含敏感信息，不要分享给他人
3. **网络要求**: 需要稳定的网络连接，超时时间15秒
4. **SSL验证**: 代码中禁用了SSL验证（`verify=False`），生产环境应启用
5. **User-Agent**: 使用固定的User-Agent模拟浏览器
6. **重试机制**: 建议实现重试机制，处理网络波动

---

## 调试模式

启用调试模式会保存每一步的HTML页面到 `debug_cookie/` 目录：
```
debug_cookie/
  01_login_page.html          - 登录页面
  02_after_login.html         - 登录后页面
  03_after_skip_security.html - 跳过安全验证后页面
  04_after_return.html        - 返回OAuth页面
  05_m365_page.html           - m365页面
```

**使用方法：**
```bash
python get_cookie_only.py
# 输入邮箱:密码
# 调试模式? [y/N]: y
```

---

## 常见问题

### Q1: 为什么需要访问m365页面？
A: Xbox Live登录只能获取基础Cookie（13个），访问m365页面会触发Microsoft 365服务的认证，生成额外的Cookie（增加到30个），这些Cookie对HMCL自动登录是必需的。

### Q2: Cookie数量少于30个能用吗？
A: 不一定。关键是要包含 `WLSSC`、`MSPAuth`、`__Host-MSAAUTH` 等核心认证Cookie。如果缺少这些，即使有25个Cookie也无法登录。

### Q3: 为什么有时候需要跳过安全信息页面？
A: Microsoft会定期要求用户更新安全信息（电话号码、备用邮箱等）。如果账号长时间未更新，登录时会弹出这个页面。我们通过提取返回URL的方式跳过这个页面。

### Q4: access_token有什么用？
A: access_token是OAuth 2.0的访问令牌，用于访问Xbox Live API。虽然我们不直接使用它，但它的存在表明登录成功。

### Q5: Cookie会过期吗？
A: 会。Cookie通常有效期为7-30天。过期后需要重新获取。可以通过尝试登录来判断Cookie是否有效。

---

## 技术细节

### HTTP会话管理
- 使用 `requests.Session()` 保持会话
- 自动处理Cookie的存储和发送
- 自动处理重定向（`allow_redirects=True`）

### 正则表达式提取
```python
# PPFT令牌
ppft_match = re.search(r'sFTTag.*value=\\\"(.+?)\\\"', response.text, re.S)

# 提交URL
urlpost_match = re.search(r'"urlPost":"(.+?)"', response.text, re.S)

# 返回URL
return_url_match = re.search('(?<="recoveryCancel":{"returnUrl":")(.+?)(?=")', response.text)
```

### 错误处理
- 网络超时: 15秒
- 异常捕获: 所有步骤都有try-except
- 失败返回: 返回False或None

---

## 总结

Cookie获取流程包含5个步骤，每一步都有明确的目的：

1. **访问登录页面** → 获取PPFT令牌和提交URL
2. **提交登录凭证** → 验证账号密码，获取基础Cookie
3. **跳过安全验证** → 处理安全信息更新提示（如果需要）
4. **确认登录成功** → 获取access_token，确认认证完成
5. **访问m365页面** → 触发更多Cookie生成，获取完整的30个Cookie

最终获得的30个Cookie包含了所有必需的认证信息，可以用于HMCL的自动登录功能。
