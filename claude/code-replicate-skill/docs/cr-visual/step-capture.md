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

## 输出

返回给 orchestrator 的 JSON：
```json
{
  "screens": [
    {
      "name": "screen name",
      "source_screenshot": "visual/source/xxx.png",
      "target_screenshot": "visual/target/xxx.png"
    }
  ],
  "skipped": ["screen_name_1"],
  "source_method": "phase2_existing | user_provided | live_capture",
  "target_method": "playwright | manual | other"
}
```
