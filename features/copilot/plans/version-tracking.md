# Android 版本追踪方案 — 俄罗斯通讯MAX（ru-comm-max）

版本：1.0
作者：自动生成（由 Copilot 协助）
语言：中文
创建日期：2026-08-28

---

## 一、目的
为 Android 应用（ru-comm-max）建立可运营的“最新版本/更新追踪”方案，使客户端能够可靠获取最新发布元数据，支持 Play In‑App 更新与非 Play 分发（APK 下载），并支持分阶段发布（rollout）、强制更新与变更日志展示。

## 二、适用范围
- Android 客户端（上架 Google Play 或侧载）
- 用于展示更新提醒、强制更新策略、以及托管/查询发布元数据的后端或静态 metadata

## 三、版本与发布约定
- 版本号：语义化（MAJOR.MINOR.PATCH），例如 `2.1.3`
- Android 版本码（versionCode）：逐次递增的整数（例如 20103）
- 发布 Track：`stable` / `beta` / `alpha`
- 更新类型：`force`（必须更新） / `recommended`（建议） / `optional`（可选）

示例：
- 版本：2.1.3
- versionCode：20103
- track：stable
- updateType：recommended

## 四、托管元数据（可选方案）
1. 静态存储（最简单）
   - 把 `releases.json` 或单个 `latest` JSON 文件放到 HTTPS 可访问的对象存储（S3、GCS）或 GitHub Pages。
   - 优点：实现简单、成本低。缺点：不便管理回滚、分阶段发布逻辑需在客户端实现。
2. 简易 API（推荐）
   - 部署一个小型服务（Node/Express、Go、Python Flask），提供查询最新版本、按 track/rollout 返回元数据。
   - 优点：支持分阶段、用户分群、管理界面。
3. 完整发行平台
   - 带 UI 的控制台、统计、回滚、阶段性发布等（视团队规模与需求决定）。

## 五、API 规范（示例）
- GET /api/v1/releases/latest?platform=android&track=stable&appId=ru-comm-max
  - 返回 `200` 和 JSON：

```json
{
  "appId": "ru-comm-max",
  "platform": "android",
  "track": "stable",
  "version": "2.1.3",
  "versionCode": 20103,
  "releaseDate": "2026-08-27T12:00:00Z",
  "updateType": "recommended",
  "changelog": {
    "en": "- Bug fixes\n- New feature X",
    "zh": "- 修复若干问题\n- 新增功能 X",
    "ru": "- Исправлены ошибки\n- Новая функция X"
  },
  "apkUrl": "https://cdn.example.com/ru-comm-max/2.1.3/ru-comm-max.apk",
  "sizeBytes": 34567890,
  "sha256": "hexsha256...",
  "minSdkVersion": 21,
  "rolloutPercent": 10,
  "notesUrl": "https://example.com/releases/2.1.3"
}
```

字段说明：
- rolloutPercent: 0-100，表示发布面向的用户百分比（若为 100 则全量）。
- sha256: 用于校验 APK 完整性。

## 六、数据模型（示例）
releases 表（关系型或文档型）：
- id
- appId
- platform
- track
- version
- versionCode
- releaseDate
- updateType
- changelog (JSON)
- apkUrl
- sha256
- rolloutPercent
- createdBy
- notesUrl

## 七、Android 客户端检查流程（推荐）
1. 启动/用户主动检查时流程：
   - 如果上架 Google Play：优先调用 Play Core In‑App Update API（flexible 或 immediate）。这能保证签名和安装体验由 Play 管理。
   - 同时或作为备用，调用后端的 releases API 查询元数据。
   - 比较 `versionCode`：若 `remote.versionCode > currentVersionCode` 则认为有更新。
   - 根据 `updateType` 做不同处理：
     - force -> 弹出不可取消对话并引导用户��新（若 Play 可用则触发 Play immediate 更新；否则提示下载 APK 并安装）。
     - recommended -> 展示对话（变更日志 + 立即更新/稍后），支持静默下载 + 提示安装。
     - optional -> 在设置或通知中显示“有可用更新”。
   - 如果 `rolloutPercent` < 100：使用客户端生成的用户标识（例如 userId 或 deviceId hash）决定该用户是否属于被推送分组（hash % 100 < rolloutPercent）。
2. 非 Play 分发注意事项：
   - APK 下载完成后进行 sha256 校验并验证 APK 签名（与原始发布签名一致）。
   - 在 Android 11+ 侧载安装需要用户授权并遵守平台策略。

## 八、Android 客户端示例（Kotlin 伪码）

```kotlin
// Data class (示意)
@Serializable
data class Release(
  val appId: String,
  val platform: String,
  val track: String,
  val version: String,
  val versionCode: Int,
  val updateType: String,
  val changelog: Map<String,String>,
  val apkUrl: String?,
  val sha256: String?,
  val rolloutPercent: Int? = 100
)

suspend fun fetchLatestRelease(client: HttpClient, url: String): Release? {
  val text = client.get(url).bodyAsText()
  return Json.decodeFromString(Release.serializer(), text)
}

fun isInRollout(userSalt: String, rolloutPercent: Int): Boolean {
  val hash = (MessageDigest.getInstance("SHA-256")
    .digest(userSalt.toByteArray())
    .fold(0L) { acc, b -> (acc shl 8) + (b.toInt() and 0xFF) })
  return (hash % 100) < rolloutPercent
}

fun isUpdateAvailable(currentVersionCode: Int, remote: Release): Boolean =
  remote.versionCode > currentVersionCode
```

Play In-App Update 建议：使用 Play Core 的 `AppUpdateManager` 查询更新并启动 `startUpdateFlowForResult`（immediate 或 flexible）。

## 九、CI/CD 自动化建议（GitHub Actions 示例思路）
- 在打 release tag / 在主分支合并时触发 workflow：
  1. 构建 APK（assembleRelease）
  2. 对 APK 签名并生成 sha256
  3. 上传 APK 到对象存储（S3/GCS/私有 CDN）或 Google Play（使用 Google Play Publisher API）
  4. 更新 releases.json（或调用后端 API 创建 release 记录）

简要 GitHub Actions 伪配置节选：
```yaml
name: Publish Release
on:
  push:
    tags:
      - 'v*.*.*'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up JDK
        uses: actions/setup-java@v4
      - name: Build release
        run: ./gradlew assembleRelease
      - name: Upload to S3
        run: aws s3 cp app-release.apk s3://my-bucket/ru-comm-max/${{ github.ref_name }}/app-release.apk
      - name: Update metadata
        run: |-
          # 生成 releases.json 并上传到 S3 或调用 API
```

如果你使用 Google Play，推荐在 workflow 中使用 `r0adkll/upload-google-play` 或官方 Google Play Publisher API 来上传 Artifact。

## 十、渐进发布（Rollout）策略
- 使用 `rolloutPercent` 字段控制目标用户比例（0-100）
- 客户端使用稳定的用户标识（userId / deviceId 如果可用）做哈希判定
- 后端保存每次发布记录与回滚选项，支持随时把 rolloutPercent 调整回滚到 0

## 十一、安全与隐私要点
- 所有元数据与 APK 必须通过 HTTPS 提供
- 非 Play 安装时，校验 sha256 与确认 APK 签名
- 强制更新仅在安全/兼容性必要时使用，界面需说明原因与时间
- 合规：注意 GDPR、俄罗斯本地法规对于用户数据收集与通知的要求

## 十二、可交付物与时间估计（建议）
- Minimal（S3/json + 客户端集成）：2–4 天
- Standard（简单 API + CI 自动化 + Play In‑App 集成）：1–2 周
- Full（控制台、逐步发布 UI、统计）：3–6 周

## 十三、后续动作（我可以为你完成）
- 在本仓库创建本文件（已由你授权） —— 我会把文件放在 `features/copilot/plans/version-tracking.md`（或你指定的路径）。
- 如需：生成更详尽的 Kotlin 示例（含完整 Play Core 集成代码）、后端 API 模板（Node/Express）或 GitHub Actions 完整配置，我可以继续添加。

---

附：如果你希望文档为英文或俄文，或需要把文件创建在不同路径/分支，请告知。
