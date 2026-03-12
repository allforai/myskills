# 图片字段处理规范

> 适用于 MG2-C（新建表单）、MG2-E（编辑表单）、SB1（内容发布）中包含图片上传字段的场景。
> 图片字段 = `FormWithValidation` + `FileUpload` 组合原语。

## 第一步：确定上传策略

| 策略 | 流程 | 适用条件 | 注意事项 |
|------|------|---------|---------|
| **预签名 URL 直传 CDN**（推荐大图） | 请求服务端获取预签名 URL → 前端直接 PUT 到 CDN（OSS/S3）→ 获得图片 URL → 表单提交只传 URL | 图片 > 1MB、有 CDN/对象存储、需显示上传进度 | 服务端不承受图片流量；需配置 CORS；孤儿文件处理同预上传 |
| **预上传至服务端** | 选图 → POST 到服务端 → 服务端转存 CDN → 返回 URL → 表单提交只传 URL | 图片中等大小、无直接访问对象存储权限 | 流量经过服务端；孤儿文件：用 TTL 定期清理或提交时对比差异 |
| **随表单提交（Multipart）** | 选图 → 暂存 File 对象 → 表单提交时 multipart 一起 POST | 图片小（< 500KB）、简单场景、避免孤儿文件问题 | 自定义 `customRequest` 阻止组件自动上传；表单提交逻辑需处理 File 对象 |

## 第二步：编辑表单图片回填（各技术栈）

编辑场景必须将服务端返回的图片 URL 列表转换为各组件可识别的格式：

| 技术栈 | 回填写法 |
|--------|---------|
| UmiJS + AntD Pro | `form.setFieldsValue({ images: urls.map((url, i) => ({ uid: String(i), name: url.split('/').pop(), status: 'done', url })) })` |
| Vue 3 + Element Plus | `:file-list="existingUrls.map((url, i) => ({ uid: i, name: url.split('/').pop(), url, status: 'success' }))"` |
| Next.js (react-hook-form) | `setValue('images', urls.map(url => ({ id: url, url, isExisting: true })))` → 渲染时区分已有图和新图 |
| Nuxt (vue-query) | 同 Vue 3 + Element Plus，`useQuery` 加载后 `fileList.value = ...` |
| Flutter | `final imageItems = existingUrls.map((url) => ImageItem(url: url, isLocal: false)).toList();` → 渲染 `NetworkImage` |
| iOS SwiftUI | `@State var images: [ImageItem] = urls.map { ImageItem(remoteUrl: $0) }` → 显示 `AsyncImage` |
| Android Kotlin/Compose | `val images = remember { mutableStateListOf(*urls.map { ImageItem(url = it, isLocal = false) }.toTypedArray()) }` |
| React Native | `const [images, setImages] = useState(urls.map(url => ({ uri: url, isExisting: true })))` |
| Windows WPF | `Images = new ObservableCollection<ImageItem>(urls.Select(url => new ImageItem { Url = url, IsUploaded = true }))` |
| Windows Electron | `const [images, setImages] = useState(urls.map(url => ({ src: url, isExisting: true })))` |

## 第三步：多图管理行为规则

| 场景 | 规则 |
|------|------|
| **删除已有图片** | 标记删除（本地记录 `deletedIds`），不立即调 DELETE API；提交表单时一并告知服务端（避免用户取消后图片已删） |
| **删除新上传图片**（预上传策略） | 立即调 DELETE API 清理孤儿文件，或提交时对比原始列表与当前列表差异批量清理 |
| **图片排序** | 维护本地 `order` 数组，提交时带上排序字段；不依赖上传顺序 |
| **数量上限** | 达到 `maxCount` 时隐藏或禁用上传入口（不仅禁用，还要视觉上移除入口，避免用户困惑） |
| **格式/大小校验** | 在 `beforeUpload` / `:before-upload` / `fileImporter` 回调中拦截，给出明确提示（"仅支持 JPG/PNG，最大 5MB"），不触发上传 |
| **单图 vs 多图** | 头像/封面等单图场景用替换模式（选新图后旧图直接替换）；内容图等多图场景用追加+删除模式 |

## 第四步：移动端选图入口（原生平台专属）

Web 端点击 `<input type="file" accept="image/*">` 即可；原生端需显式触发系统选图/拍照 API：

| 平台 | 相册选图 | 相机拍照 | 备注 |
|------|---------|---------|------|
| iOS SwiftUI | `PHPickerViewController`（iOS 14+，无需权限申请） | `UIImagePickerController(sourceType: .camera)` + `NSCameraUsageDescription` | 多选用 `PHPickerConfiguration.selectionLimit` |
| Android Kotlin/Compose | `ActivityResultContracts.GetContent("image/*")` 或 `PickVisualMedia` | `ActivityResultContracts.TakePicture()` + `CAMERA` 权限 | Android 13+ 用 Photo Picker，无需 READ_EXTERNAL_STORAGE |
| Flutter | `image_picker` 插件：`ImagePicker().pickImage(source: ImageSource.gallery)` | `ImagePicker().pickImage(source: ImageSource.camera)` | 同时支持多图：`pickMultiImage()` |
| React Native | `launchImageLibrary({ mediaType: 'photo' })`（`react-native-image-picker`） | `launchCamera({ mediaType: 'photo' })` | 需在 Info.plist / AndroidManifest 声明权限 |

**选图后统一入上传队列**，走第一步选定的上传策略；拍照临时文件在上传完成或用户取消后及时清理。

## 第五步：图片显示尺寸规格（URL 参数等比缩放）

> 同一张图在不同位置以不同尺寸展示，由**服务端 URL 参数**处理，不依赖 CDN 图片变换。
> 规则：只传 `w`（限制最大宽度）或 `h`（限制最大高度），服务端等比缩放，不裁剪，不同时传两者。

**常用规格约定：**

| 使用场景 | 参数 | 说明 |
|---------|------|------|
| 列表缩略图 | `?w=200` | 横图/方图均适用 |
| 头像 | `?w=128` | 含 2× Retina 缓冲（64px 显示位） |
| 详情主图 | `?w=800` | 适配常规内容区宽度 |
| 封面/Banner | `?w=1280` | 宽屏全宽图 |
| 竖版图（海报等） | `?h=600` | 高度限制，宽自适应 |
| 全屏 Lightbox | 不带参数 | 原图 |

**各技术栈渲染写法（通用：拼接参数到 URL）：**

| 技术栈 | 用法 |
|--------|------|
| UmiJS + AntD Pro | `<Image src={`${url}?w=200`} />`（列表列）；`<Image src={`${url}?w=800`} />`（详情） |
| Vue 3 + Element Plus / Nuxt | `<el-image :src="`${url}?w=200`" />`；封装为 `useImageUrl(url, { w: 200 })` composable |
| Next.js | 用普通 `<img src={`${url}?w=200`} />`（服务端自行处理，不走 next/image CDN 管道） |
| Flutter | `CachedNetworkImage(imageUrl: '$url?w=200')` |
| iOS SwiftUI | `AsyncImage(url: URL(string: "\(url)?w=200")!)` |
| Android Kotlin/Compose | `AsyncImage(model = "$url?w=200", contentDescription = ...)` （Coil） |
| React Native | `<Image source={{ uri: `${url}?w=200` }} />` |
| Windows WPF | `BitmapImage` URI 拼参数；或 `IValueConverter` 统一处理 |
| Windows Electron | `<img src={`${url}?w=200`} />` |

**design.json 字段标注**：image 类型字段在 `data_models[].fields` 中加 `display_sizes`，描述各展示场景的规格参数：

```json
{
  "name": "cover_image",
  "type": "string",
  "note": "存储原图 URL",
  "display_sizes": {
    "list": "?w=200",
    "detail": "?w=800",
    "lightbox": ""
  }
}
```
