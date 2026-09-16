# Research: Stitch 之外的 UI 生成与 agent skill 接入

## Summary
最值得优先验证的是 **Lovable 官方生成型 MCP**（云端新建应用）和 **Builder 官方非交互 CLI**（现有仓库设计转代码）。Figma MCP 现已不仅只读：支持设计上下文、Make 源文件读取和 Design 写工具；但不能把这些称为 Figma Make 的无人值守生成 API。Onlook/bolt.diy 可自托管，但不是现成稳定的生成服务接口。

依据本次实时抓取的官方文档；未执行产品、安装、登录或创建资源。以下“高”表示文档明确支持，不表示实际质量或可靠性已经测试。

## Parent research: Stitch and v0

- **Stitch remains a candidate:** Google’s product announcement links its MCP, SDK and skill collection. `@google/stitch-sdk` supports API-key auth (`STITCH_API_KEY`) or OAuth, project/screen management, generation, edits, variants and design systems. `getHtml()` and `getImage()` return download URLs, not persisted local artifacts; an adapter must download and record them. The Google Labs SDK and skills repositories explicitly disclaim being officially supported Google products. Sources: https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/ ; https://github.com/google-labs-code/stitch-sdk ; https://github.com/google-labs-code/stitch-skills ; https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch . This makes modernization of the repository’s older OAuth/proxy integration a viable alternative to replacement. No live generation tested.
- **v0 provides an app-generation API and an inbound MCP server:** API v2 supports chats/messages, source-file operations/download, previews, and deployment; synchronous, asynchronous and streaming workflows are documented. MCP at `https://v0.app/api/mcp` uses OAuth and supports creating/continuing builds and retrieving previews; do not assume its smaller tool list exposes every API file operation. v1 chat/version examples are not interchangeable with v2. Sources: https://v0.app/docs/api/v2 ; https://v0.app/docs/api/v2/guides/mcp-server ; https://v0.app/docs/api/v2/guides/migrating-from-v1-to-v2 . Recommendation: trial for runnable Web UI, with explicit constraints on existing components, scope and cloud resource creation. No quality benchmark or pricing claim is made.

## Findings

1. **Claim：Figma Make 是可运行原型/网页代码工具；Figma Design 才是可编辑设计图层，两者不能混为一谈。**
   - Make 可下载代码 ZIP；MCP 的 Make resources 可读取项目源文件交给 coding agent 接续开发。
   - `get_design_context` 支持 Design/Make，默认 React + Tailwind；可提示调整输出框架。这是上下文/代码转换能力，不代表 Make 原生支持任意框架生成。
   - 官方 MCP 当前有 `use_figma`：创建、编辑、删除或检查 Design/FigJam/Slides 对象；`generate_figma_design` 将运行中的网页 UI 转为 Design 图层，受客户端支持、席位及文件编辑权限限制。故“Figma MCP 只有读取工具”已不成立。
   - Make 本地代码库编辑另有 **Mac-only closed beta**，可连接本地/Git 仓库、提交和创建 PR；不能当作普遍可用 API。
   - **接入判断［研究者推断］：**适合设计输入/设计回写节点；本次未发现公开的“向 Make 发 prompt → 异步生成项目”的正式 API，不能以 MCP 读 Make 文件冒充它。
   - **Sources：**[MCP tools](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/)；[Make resources](https://developers.figma.com/docs/figma-mcp-server/bringing-make-context-to-your-agent/)；[Make 代码导出](https://help.figma.com/hc/en-us/articles/35710574222487-Beyond-the-basics-Using-Figma-Make)；[本地代码库 beta](https://help.figma.com/hc/en-us/articles/40775535020695-Make-in-your-local-codebase)。**Support：direct evidence；Confidence：高；未发现 API 属中等置信的检索结论。**

2. **Claim：Builder Fusion/Visual Copilot 有可实际编排的官方 CLI，不仅是交互网页；不要把“CLI API”误称 REST 生成 API。**
   - `npx builder.io@latest code generate` 支持 `--prompt` 非交互生成、`--cwd`、`--url`（例如 Figma）、`--index`、`--accept`。先认证到 Builder Space；文档同时覆盖 Builder Code 与 Content，命令适用范围不同。
   - `fusion launch` 主要启动交互工作环境；其 JSON 输出不等于生成结果 API。编排重点应是 `code generate`，不是 launch。
   - Visual Copilot/Generate Code 从设计或 Builder Page/Section 生成代码，可复制或 CLI 同步。官方列 React、Vue、Angular、HTML、Svelte 等；SwiftUI/Compose/Flutter 标为 Beta。该列表属于 Generate Code，不能外推为所有 Fusion 工作流均完整支持这些平台。
   - **产物：**代码及实际项目修改，不是通用 Figma 可编辑设计交付；生成 UI 不保证业务闭环。
   - **接入判断［研究者推断］：**本组最直接的本地 skill 适配候选；建议在临时分支生成 diff，验证后人工批准。CLI 非交互支持不等于已验证 CI 认证、重试/幂等及错误协议。
   - **Sources：**[CLI API](https://www.builder.io/c/docs/builder-cli-api)；[Generate Code](https://www.builder.io/c/docs/generate-code/)。**Support：direct evidence；Confidence：高。**

3. **Claim：Lovable 已有真正的官方生成型 MCP，不能仅按旧版 Build with URL 评估。**
   - 服务 `https://mcp.lovable.dev`，OAuth 登录；`create_project(initial_message)` 创建并生成应用，`send_message` 迭代；支持 `wait=false` + `get_message` 轮询；`list_files/read_file/get_diff` 检查代码；`deploy_project` 可选发布。官方提供 skill：<https://mcp.lovable.dev/skill.md>。
   - API 概览仍把 MCP 标为 **Research Preview**；工具页明确面向 agent 工作流。因此应视作官方但仍需验证稳定性的接入，而不是承诺稳定 REST API。
   - Build with URL 本身只是预填 prompt，接收者还需点击发送，不是无人值守生成。
   - **产物：**可运行应用、预览 URL、源代码；可下载 ZIP 或 Git 同步，不是 Figma 原生可编辑图层。FAQ 仍表示不能以任意已有 GitHub 代码新建项目。
   - **重要框架更新：**当前 FAQ 明确写“2026-05-13 起新建应用用 TanStack Start + SSR”；旧应用 React + Vite，样式 Tailwind。不要沿用搜索摘要中“始终 React+Vite”的结论。
   - **接入判断［研究者推断］：**优先试作“新建 UI 原型 → 读取源码/导出 → 本地验证”节点；创建资源与 deploy 必须独立授权，不自动发布。任意现有仓库持续改造不如 Builder 路线直接。
   - **Sources：**[官方 MCP 工具](https://docs.lovable.dev/integrations/lovable-mcp-server)；[API 概览](https://docs.lovable.dev/integrations/lovable-api)；[FAQ/技术栈/导出](https://docs.lovable.dev/introduction/faq)。**Support：direct evidence；Confidence：高。**

4. **Claim：Bolt 是运行代码的交互应用构建器；本次未证实其托管产品提供对外生成 API。**
   - 官方描述可 prompt/run/edit/deploy，全栈 JavaScript 框架；移动端走 Expo，不是任意原生平台代码生成承诺。
   - 支持 GitHub 自动保存/版本控制和 ZIP 导出。
   - “Connect to an MCP server”是 **Bolt 作为 MCP 客户端连接外部工具**，不能据此宣称外部 agent 可通过 Bolt MCP 驱动生成。
   - 官方文档索引提及的 `api-reference/openapi.json` 实际返回 404；不足以证明存在可用的生成 API。
   - **接入判断［研究者推断］：**暂按人工启动/导出交接方案处理；不宜把浏览器自动化包装成官方服务 API。
   - **Sources：**[产品与框架](https://support.bolt.new/building/intro-bolt)；[GitHub/ZIP](https://support.bolt.new/integrations/git)；[连接外部 MCP](https://support.bolt.new/building/using-bolt/connect-mcp)；[官方索引](https://support.bolt.new/llms.txt)。**Support：direct evidence + 明示检索限制；Confidence：高（功能），中（未找到生成 API）。**

5. **Claim：Onlook 能自托管、直接编辑真实代码，但当前开源版的可靠支持范围是 Next.js + Tailwind。**
   - 从文字/图像开始，实时运行预览、视觉编辑 DOM 并回写代码：既不是仅截图，也不是 Figma 设计文档。
   - 官方仓库把 non-NextJS、non-Tailwind 支持列为未完成；README 声明 Apache-2.0，并明确该仓库是起步的开源编辑器，新托管产品另在 early access，不能混用能力承诺。
   - 官方自托管指南含单机与 Docker Compose；需要 Supabase，沙箱及 AI 提供商等外部依赖仍须配置。自托管不自动等于全离线。
   - **接入判断［研究者推断］：**适合愿意维护部署/适配层的本地视觉编辑工作台；本次未找到稳定、官方公开的 headless 生成 API/MCP，内部 tRPC 不应当作公开契约。
   - **Sources：**[官方 README 原文](https://raw.githubusercontent.com/onlook-dev/onlook/main/README.md)；[自托管](https://docs.onlook.com/self-hosting)；[外部依赖](https://docs.onlook.com/self-hosting/external-services)。**Support：direct evidence；Confidence：高；公开 API 缺失判断为中。**

6. **Claim：bolt.diy 是额外自托管候选，但 MIT 源码不等于全部运行依赖无商业限制。**
   - 官方仓库支持本机/Docker、自选模型、NodeJS 应用生成、ZIP/Git 导出。其 MCP 集成声明不足以证明有稳定的“外部调用生成”服务 API。
   - README 明示源码 MIT，但 WebContainer API 在商业营利生产使用中需商业许可；原型/POC 例外。不能推荐为“完全免费、无限商用自托管”。
   - **Sources：**[官方 README 原文](https://raw.githubusercontent.com/stackblitz-labs/bolt.diy/main/README.md)。**Support：direct evidence；Confidence：高（仓库声明）；具体部署许可需另行确认。**

## Contradictions
- Lovable 搜索结果仍返回官方旧 FAQ 摘要“React+Vite，非 Next.js”；实际打开旧 URL <https://lovable.dev/faq/capabilities/tech-stack/lovable-nextjs-support> 已跳转/返回新版 FAQ，后者明确新项目 TanStack Start。采信抓取正文，保留旧项目区别。
- Onlook 营销 React 页面宣传更宽兼容范围；当前仓库 README 明确 non-NextJS/non-Tailwind 尚未完成。推荐开源自托管时采用仓库较窄边界，不推断所有 React 项目可用。
- Lovable API 概览称 MCP Research Preview，而专项 MCP 页展示完整工具和所有套餐可用；两者不一定冲突，但稳定性阶段未统一表述。

## Missing evidence
- 未做任何实测：生成质量、视觉还原、构建成功率、延迟、额度消耗、导出后的独立运行均未验证。没有可靠同题官方 benchmark，因此不排名视觉质量。
- Figma Make 对外生成 API、Bolt 托管生成 API、Onlook/bolt.diy 稳定 headless API 均未证实；“未找到”不等于绝对不存在。
- 不报告金额：本次未充分核验完整套餐/生成额度价格。自托管仍有模型、沙箱和运维成本。
- 对关键接口及许可证两次调用 source_check 均返回 `unclear (0.30)`，理由是未自动抽到清晰支持标记；上文改以已获取的官方正文/README 明文逐项人工核对，不把自动结果冒充独立确认。

## Sources
- **Kept：**上述产品官方文档、开发者文档及官方仓库 README——分别提供工具参数、生成/导出边界、自托管和许可证据。
- **Rejected/deprioritized：**第三方 Lovable→Next.js 转换文章、Reddit 经验——不是当前技术栈权威来源；Onlook React 营销页——范围宽于开源仓库；搜索摘要——仅用于发现；Builder 自称代码质量/速度——未作为性能事实。

## Next steps
只做两项经用户授权的小型 POC：Lovable MCP“创建→轮询→读源码，不部署”，Builder CLI“临时分支非交互生成→diff→构建”。若目标必须交付可编辑设计图层，再单独验证 Figma `use_figma`/`generate_figma_design` 的账号与客户端能力，不与 Make 混同。
