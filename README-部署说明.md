# Civia 安卓 APK — OTA 在线更新部署说明

## 当前生效的托管（临时免费：Cloudflare 快速隧道）

- **更新站地址**：`https://luact-nb.github.io/civia-ota/`（GitHub Pages，固定地址）
- **手机下载页**：`https://luact-nb.github.io/civia-ota/`（APK 直链 `/Civia.apk`）
- **当前版本**：APK v1.0.7（versionCode 8，内置 web 基线 v1.0.13）；线上热更 v1.0.13
- **本次修复（2026-11-23）**：修正「检查更新失败: Value <!DOCTYPE …」报错，见文末「排障」。
  ⚠️ **已安装旧版的用户必须重新下载安装本页 APK 覆盖安装**（无需卸载，数据保留），
  因为坏地址写死在旧包里，热更无法自救。
- 实现：本机 `python3 -m http.server 8942`（服务 civia-ota/）+
  `~/dev-env/bin/cloudflared tunnel --url http://127.0.0.1:8942`
- ⚠️ **临时性质**：隧道地址在 Mac 关机/睡眠断网/隧道进程退出后失效，重启后
  地址会**变**，届时需用新地址重跑 `OTA_URL=<新地址> ./civia-android/build.sh` 重装一次 APK。
  隧道断了不影响已安装 App 的本地使用（只影响热更检查和下载页）。
  长期使用请换成固定托管（自有服务器 / OSS / COS / GitHub Pages），再重打一次 APK 即可。

## 目录内容

| 文件 | 作用 |
|---|---|
| `Civia.apk` | 安卓安装包 v1.0.7（内置 web 基线 v1.0.13，已注入完整 `/version.json` 地址） |
| `index.html` | 下载页（手机浏览器打开即可下载 APK） |
| `version.json` | 热更新清单：`{version, url, notes, log}`（当前 v1.0.13，`log` 为更新记录数组，App 版本详情页展示） |
| `web.zip` | 热更新资源包 v1.0.13（index.html + assets/，约 1.2 MB） |
| `update-web.sh` | 发新热更版本时重新生成上面两项 |
| `app-icon.png` | 启动图标（同时用于下载页 logo） |

### 启动图标说明（2026-11-23 更新）
- 采用用户提供的机器人面罩特写图（1024×1024 JPG），用 PIL 生成各密度 PNG：
  `mipmap-{mdpi..xxxhdpi}/ic_launcher.png`（方形 48dp）与 `ic_launcher_fg.png`（自适应前景 108dp）
- 自适应图标（`mipmap-anydpi-v26/ic_launcher.xml`）引用 `@mipmap/ic_launcher_fg`，
  背景色 `ic_launcher_bg` 改为 `#05030C` 与图片深色背景一致
- **最终样式（按用户确认的「方形」方案）**：前景改为原图**完整铺满整个画布**，
  去掉早期「缩 86% + 边缘延展」造成的四周延展边，图标内容就是一张干净的方形照片
- ⚠️ **平台限制**：Android 8+ 桌面图标外框形状由手机 Launcher 决定，App 无法强制锁成方形；
  本包保证「Launcher 用方形遮罩时即为用户选中的效果」
- 换图标属原生层变更，覆盖安装即可生效；部分桌面有图标缓存，可重启桌面或稍等

## 一、首次部署（3 步）

1. **托管**：把整个 `civia-ota/` 目录上传到任意 HTTPS 静态托管
   （自有服务器 Nginx、阿里云 OSS、腾讯云 COS、GitHub Pages 等均可，
   需要允许直接下载 `.apk` / `.zip` 文件）。假设托管后地址为 `https://your.host/ota`。

2. **重打 APK**（把真实更新源写进 App）：

   ```bash
   OTA_URL=https://your.host/ota ./civia-android/build.sh
   ```

   `OTA_URL` 传**目录基址**即可；脚本会自动 stamp 成完整的
   `https://your.host/ota/version.json`，并同步内置 WEB_VERSION 为线上最新版本。

3. **安装**：把新的 `Civia.apk` 发到手机安装一次（这是唯一一次手动安装）。
   App 启动 3 秒后会自动检查更新：线上 `version.json` 版本高于内置版本时，
   自动下载 `web.zip`、原子替换、Toast 提示并重启页面。

## 二、以后发新版本（免安装热更）

改完 `civia-app/` 后：

```bash
./civia-ota/update-web.sh 1.0.10 https://your.host/ota
# 把生成的 civia-ota/web.zip 和 version.json 上传覆盖线上即可
```

脚本会同时 stamp **WEB_VERSION** 和**完整 version.json 地址**（两者缺一不可：
漏 stamp 地址会让热更一次后链路断掉）。手机端下次启动 App 自动生效，无需重装 APK。

## 三、什么时候需要重装 APK

日常迭代（UI / 交互 / 文案 / 布局）**只发热更即可，不用动 APK**。只有原生壳
（MainActivity、权限、图标、versionCode 等）变化、更新地址变更，
或想给新用户一个「开箱即最新」的基线包时，才需要重新构建安装 APK：

```bash
# 默认：新 APK 内置 = 线上最新 web 版，装上无需再等一次热更
OTA_URL=https://your.host/ota ./civia-android/build.sh

# 可选：把内置基线钉在较低版本，用于验证首次启动的自动热更链路
APK_WEB_VER=1.0.6 OTA_URL=https://your.host/ota ./civia-android/build.sh
```

签名密钥 `civia-android/civia-release.keystore`（密码 civia2026），
**请妥善保管，签名不一致会导致无法覆盖安装**。

## 四、热更协议（自托管参考）

`version.json`:

```json
{ "version": "1.0.10", "url": "https://your.host/ota/web.zip", "notes": "..." }
```

`web.zip` 根目录必须包含 `index.html` 和 `assets/`（即 civia-app 的内容）。

原生层 `Bridge.checkUpdate(url)` 的行为：
- `url` 可以是目录基址或完整 `version.json` 地址；不以 `.json` 结尾时自动补 `/version.json`
- 非 JSON 响应（隧道失效、地址指到下载页）给出可读错误，而不是 `Value <!DOCTYPE …`
- 把清单**包装**成 `{"ok":true,"manifest":{...}}` 再交给 JS 的 `__civiaOtaResult`；
  JS 读取 `r.ok` 与 `r.manifest.version`，缺一不可
- semver 高于内置版本才下载；下载按 Content-Length 校验完整性、超时 60s，
  截断包会被丢弃并提示重试，不会覆盖可用的 bundle
- 解压有 zip-slip 防护，原子换目录，完成后 `reloadUpdated()` 重载
- APK 升级（versionCode 变化）时会清掉 `filesDir/web` 里旧的热更包，
  避免旧包里的过期地址继续被加载

## 五、排障：检查更新失败: Value <!DOCTYPE of type java.lang.String cannot be converted…

**根因（两个叠加的 bug，2026-11-23 已修复）**：

1. **请求地址错了**：bundle 里 stamp 的是更新站**目录基址**，原生层直接 GET 它，
   拿到的是下载页 HTML（`<!DOCTYPE html>`），`new JSONObject(...)` 解析时抛错。
2. **回传结构错了**：旧原生层把 `version.json` 原文直接回传，但 JS 期望
   `{ok:true, manifest:{...}}`。即使地址修好，`r.ok` 为 undefined，更新也会静默失败。

另外还有一个隐藏问题：`startUrl()` 优先加载 `filesDir/web` 里残留的旧热更包，
所以**只发热更救不了已安装的旧 APK** —— 旧包里的坏地址会一直被加载。

**修复**：原生层规范化 URL + 包装 manifest + 友好错误 + 下载完整性校验 +
APK 升级时清理旧热更包；两个 stamp 脚本改为写入完整 `/version.json` 地址并加断言。
**用户侧动作：重新下载安装下载页的 APK 覆盖安装**（无需卸载）。

装好后验证：App 内显示 v1.0.7 → 约 3 秒后提示「发现新版本 v1.0.8，正在更新…」
→ 自动刷新为 v1.0.8；再点「版本」应提示「已是最新版本 v1.0.8」。
（v1.0.8 起「我的」页版本行图标已换成 Figma 设计稿 `icon_ai_l`。）
