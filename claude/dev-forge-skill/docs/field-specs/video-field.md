# 视频字段处理规范

> 适用于 SB1（内容发布）、MG2-C/MG2-E（含视频字段的表单）场景。
> 视频字段 = `FileUpload` + `AsyncProcessing` 组合原语（上传 → 服务端转码 → 状态轮询）。

## 第一步：确定上传策略

| 策略 | 适用条件 | 流程 | 注意事项 |
|------|---------|------|---------|
| **简单 POST 直传** | 视频 < 50MB、无断点续传需求 | 选文件 → FormData POST → 获得任务 ID → 轮询转码状态 | 超时风险：大文件在弱网下易失败；服务端需配置 body-size-limit |
| **分片上传（Chunked）** | 视频 > 50MB 或需要断点续传 | 初始化 → 切割分片（5~20MB/片）→ 并发上传各分片 → 发送合并请求 → 获得任务 ID → 轮询转码状态 | 需服务端支持分片合并 API；前端维护分片进度和失败重试；可用 tus 协议或自定义实现 |
| **预签名 URL 直传 CDN**（推荐大文件） | 大文件、需显示上传进度、避免流量走服务端 | 请求服务端获取预签名 URL → 直接 PUT 到 CDN（OSS/S3）→ 通知服务端开始转码 → 轮询状态 | 服务端不承受视频流量；需配置 CORS；适合有 CDN/对象存储的场景 |

## 第二步：转码状态轮询（各技术栈）

上传完成后，服务端异步转码（通常 30s~5min），前端需轮询任务状态直到完成或失败：

| 技术栈 | 轮询实现 |
|--------|---------|
| UmiJS + AntD Pro | `useRequest` + `pollingInterval: 3000`，`ready` 条件为 `status === 'processing'`；`onSuccess` 中判断 `status === 'done'` 时停止 |
| Vue 3 + Element Plus | `const { data } = useQuery(['task', taskId], fetchStatus, { refetchInterval: (data) => data?.status === 'processing' ? 3000 : false })` |
| Next.js | `const { data } = useSWR(taskId ? \`/api/task/${taskId}\` : null, fetcher, { refreshInterval: (data) => data?.status === 'processing' ? 3000 : 0 })` |
| Nuxt | `const { data } = useAsyncData(...)` 配合 `setTimeout` 递归轮询；或直接用 `$fetch` + `setInterval` |
| Flutter | `Timer.periodic(Duration(seconds: 3), (timer) async { final status = await fetchStatus(taskId); if (status == 'done' \|\| status == 'failed') timer.cancel(); setState(() => _status = status); })` |
| iOS SwiftUI | `Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { timer in Task { let s = await fetchStatus(taskId); if s == .done \|\| s == .failed { timer.invalidate() }; self.status = s } }` |
| Android Kotlin/Compose | `viewModelScope.launch { while (status != "done" && status != "failed") { delay(3000); status = fetchStatus(taskId) } }` |
| React Native | `useEffect(() => { const id = setInterval(async () => { const s = await fetchStatus(taskId); if (s === 'done' \|\| s === 'failed') clearInterval(id); setStatus(s); }, 3000); return () => clearInterval(id); }, [taskId])` |
| Windows WPF | `DispatcherTimer`（`Interval = TimeSpan.FromSeconds(3)`）+ `Tick` 事件；完成后 `timer.Stop()` |
| Windows Electron | 同 Next.js，`setInterval` + `clearInterval`；或 `useSWR` |

**状态机**：`idle → uploading → processing → done / failed`；UI 应显示对应提示（上传进度条 → "转码中…" 占位 → 播放器）；转码完成前禁用表单提交。

## 第三步：编辑表单视频回填（各技术栈）

编辑场景需将服务端已有视频 URL 渲染为可预览/可替换的状态：

| 技术栈 | 回填写法 |
|--------|---------|
| UmiJS + AntD Pro | 不用 `Upload` 组件；自定义 `VideoPreview`（内嵌 `<video>`）+ "重新上传" 按钮；点击替换时重走上传+轮询流程 |
| Vue 3 + Element Plus | `<video :src="existingVideoUrl" controls />`+ `el-button` 触发替换；`ref(initialUrl)` 追踪当前值 |
| Next.js | `const [videoUrl, setVideoUrl] = useState(initialUrl)`；渲染 `<video src={videoUrl} />`；替换后 `setVideoUrl(newUrl)` |
| Nuxt | 同 Vue 3；`ref(initialUrl)` + `<video :src="videoUrl" />` + 替换逻辑 |
| Flutter | `Chewie` + `VideoPlayerController.network(url)`；替换时 `controller.dispose()` 再重建新实例 |
| iOS SwiftUI | `VideoPlayer(player: AVPlayer(url: URL(string: url)!))`；替换时更新 `@State var videoUrl: String` |
| Android Kotlin/Compose | `AndroidView` 包裹 `ExoPlayer.Builder(context).build()`；替换时 `player.setMediaItem(MediaItem.fromUri(newUrl))` |
| React Native | `<Video source={{ uri: videoUrl }} controls />`（`react-native-video`）；替换时 `setVideoUrl(newUrl)` |
| Windows WPF | `<MediaElement Source="{Binding VideoUrl}" />`；替换时更新 ViewModel `VideoUrl` 属性 |
| Windows Electron | `<video src={videoUrl} controls />`；同 Next.js |

## 第四步：封面图处理

| 情况 | 处理方式 |
|------|---------|
| **服务端自动截帧**（推荐） | 转码完成后服务端在轮询结果中返回 `cover_url`；前端直接使用，无需额外操作 |
| **用户手动上传封面** | 独立图片上传字段，遵循图片字段处理规范；与视频字段分开提交 |
| **前端截帧** | `<video>` 的 `onLoadedData` 事件后用 `canvas.drawImage(video, 0, 0)` 截取第一帧 → `canvas.toBlob()` → 上传为封面 |
