# Step 1-3: 截图采集

> 本文档由 cr-visual orchestrator 派遣的 **capture agent** 加载。
> 职责：建立 screen 列表 → 获取源/目标截图 → 返回截图路径映射。

## Step 1: Screen 列表 + 路由映射

从 `.allforai/experience-map/experience-map.json` 提取所有 screen，建立路由映射：

```
1. 从 experience-map 提取每个 screen 的 name、route（如有）、layout_type
2. 读 .allforai/code-replicate/visual/route-map.json（Phase 2c-visual 生成的路由→截图映射）
3. 建立配对：screen name ↔ route path ↔ 源截图文件名
   - experience-map screen 有 route → 直接匹配 route-map
   - experience-map screen 无 route → LLM 按 screen name 和 route-map 的语义相似度匹配
4. 跳过无法配对的 screen
```

## Step 1.5: 源 App 启动信息

cr-visual 需要知道怎么启动和导航源 App。信息来源（优先级）：

1. **replicate-config.json 的 `source_app` 字段**（code-replicate Phase 1 收集）：
   ```json
   "source_app": {
     "start_command": "npm run dev",
     "backend_start_command": "cd server && npm start",
     "seed_command": "npm run db:seed",
     "url": "http://localhost:3000",
     "login": {
       "username": "test@example.com",
       "password": "test123",
       "bypass_command": "设置环境变量/API调用来绕过2FA（如有）"
     },
     "platform": "web | mobile | desktop"
   }
   ```

2. **用户通过 `--source` 参数直接提供 URL**

3. **用户通过 `--screenshots` 提供已有截图**

如果 replicate-config 没有 `source_app` 且用户未传参 → AskUserQuestion 引导。

## Step 2: 源 App 截图

**方式 A（首选）— Phase 2 已采集**：
- 检查 `.allforai/code-replicate/visual/source/` 是否已有截图
- 已有 → 直接复用

**方式 B — 用户提供截图目录**：
- 读取 `--screenshots` 目录中的图片文件
- LLM 将图片文件名与 experience-map screen name 配对

**方式 C — 源 App 仍可运行**：
- 按 Phase 2c-visual 的完整协议执行（启动后端 → seed 数据 → 启动前端 → 登录 → 截图）
- 任何前置条件失败 → 不截图，报具体失败原因

**无截图可用** → 报错退出。

## Step 3: 目标 App 截图

LLM 读目标项目的技术栈 → 自行搜索并选择适合该技术栈的 UI 自动化工具 → 用 Bash 执行截图命令。不限定工具列表。

**如果 LLM 找不到可用的自动化工具** → 提示用户手动截图到 `visual/target/`。

### 多媒体防欺骗协议（截图前强制执行）

```
1. 资源加载完整性检查 — 相信网络，不信眼睛
   截图前注入全局网络监听（Playwright page.on('response')）：
   - 所有 .png/.jpg/.webp/.svg/.mp4/.webm 请求 → 记录状态码
   - 任何媒体资源返回 404/403/500 → 标记 BROKEN_MEDIA
   - BROKEN_MEDIA 的 screen → 不截图，直接判定 mismatch（占位图/破图不是"视觉差异"，是资源缺失）

2. 流媒体状态机验证
   截图前对所有 <video> 和 <audio> 标签执行 page.evaluate()：
   - readyState >= 3（HAVE_FUTURE_DATA）→ 资源已加载
   - !paused 且 currentTime > 0 → 真在播放（非卡在第一帧）
   - networkState !== 3 → 无解码错误
   任一条件不满足 → 标记 DEAD_MEDIA（视频/音频名义上存在但实际不工作）

3. 懒加载波浪式触发
   对长页面（高度 > 2 个视口）：
   - 截图前执行波浪式滚动：每次滚 500px → 停 500ms → 继续
   - 目的：触发所有 Intersection Observer 和 loading="lazy" 资源
   - 滚动完毕 → 回到顶部 → 等 network idle → 再截图
   - 不执行波浪滚动 = 页面下半部分可能全是占位符/loading 态
```

### 截图稳定性协议（所有截图必须遵守）

```
每次截图前：
1. 等待 network idle（无 pending 请求 ≥ 500ms）
2. 等待 DOM stable（无 DOM mutation ≥ 300ms）
3. 如果页面有 skeleton/spinner → 额外等待直到消失
4. 截图后检查：页面是否包含 "Loading..."/"加载中" 文字 → 是则重试

目的：防止异步加载未完成时截图 → 空数据误判
```

### 过渡态采集（关键页面）

对以下页面，除最终截图外，额外采集**过渡帧**（导航后 0.5s 和 1s 各截一帧）：

```
关键页面判定：
- 登录后首次跳转的页面（仪表盘/首页）
- 需要认证才能访问的数据页面（列表页、详情页）
- business-flows 中的第一个 screen

过渡帧用途：
- 检查是否有错误内容闪现（如 "Unauthorized"、"403"、空白页 flash）
- 检查布局抖动（content layout shift）
- 过渡帧保存到 visual/target/{screen}_transition_{0.5s|1s}.png

过渡帧中出现以下内容 = transition_issue：
- "Unauthorized"、"403"、"401"、"Not Found"
- 完全白屏（非 loading skeleton）
- 与最终截图布局结构完全不同（layout shift > 30%）
```

## 输出

返回给 orchestrator 的 JSON：
```json
{
  "screens": [
    {
      "name": "screen name",
      "source_screenshot": "visual/source/xxx.png",
      "target_screenshot": "visual/target/xxx.png",
      "transition_frames": ["visual/target/xxx_transition_0.5s.png", "visual/target/xxx_transition_1s.png"],
      "transition_issues": []
    }
  ],
  "skipped": ["screen_name_1"],
  "source_method": "phase2_existing | user_provided | live_capture",
  "target_method": "playwright | manual | other"
}
```
