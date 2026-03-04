# Next.js 套路（web-customer 类）

> C 端页面交互类型较少，主要是消费者浏览+操作场景。

| 交互类型 | 套路 |
|---------|------|
| 商品列表/搜索 | Server Component 首屏 SSR + TanStack Query 客户端分页/筛选 |
| 商品详情 | SSR + 客户端交互（加购/收藏/关注） |
| 表单提交（下单/评价/工单） | React Hook Form / 原生 form → `useMutation` → 成功跳转 |
| 用户中心列表（订单/收藏/积分） | TanStack Query `useInfiniteQuery` 无限滚动或分页 |
| 状态操作（取消订单/申请退款） | 确认弹窗 → `useMutation` → `queryClient.invalidateQueries` |
| 个人设置（地址/资料） | `useQuery` 加载 → 表单回填 → `useMutation` 保存 |
| i18n | `useTranslations` hook（next-intl），翻译文件 `src/messages/{locale}.json` |
| 状态管理 | Zustand store（全局状态）+ TanStack Query（服务端缓存） |

## CT1 Feed 流

```
数据获取: useInfiniteQuery({ queryKey, queryFn: ({ pageParam }) => fetchFeed(pageParam) })
渲染: IntersectionObserver 监听末尾哨兵元素 → fetchNextPage()
骨架屏: loading 状态下渲染 <SkeletonCard /> 列表
互动: useMutation → optimistic update（like/follow 先更新本地，失败回滚）
特征: 无分页器，纯滚动加载；Server Component 首屏 SSR，客户端接管后续分页
```

## EC1 商品详情页

```
数据获取: generateStaticParams + revalidate（ISR，商品数据变化低频）
SKU 矩阵状态:
  const [selected, setSelected] = useState<Record<string, string>>({})
  const currentSku = useMemo(() => skus.find(s => matchSpec(s.spec, selected)), [skus, selected])
  → 联动价格/库存/图片展示，无效规格组合置灰
加购: useMutation → POST /api/cart/items → queryClient.invalidateQueries(['cart'])
图片: next/image + 主图轮播（swiper） + 缩放（react-medium-image-zoom）
特征: 规格选择是核心状态，不同于普通详情页
```

## EC2 购物车

```
本地状态: Zustand store（cartStore）← 离线缓存，持久化到 localStorage
服务端同步: useQuery(['cart']) 拉取服务端最新（登录后合并本地 → 服务端）
库存校验: 实时轮询或加购时后端返回最新库存，超库存行项标红
数量操作: optimistic update（本地先改，debounce 500ms 后同步后端）
结算: form → POST /api/orders → redirect to /checkout/[orderId]
特征: 本地 state 与服务端 state 双轨并行，需明确 merge 策略
```

## WK1 IM 对话

```
WebSocket: const ws = new WebSocket(url)，封装为 useChatSocket() hook
消息列表: useInfiniteQuery 加载历史（反向分页）+ AppendOnlyStream 追加新消息
  → 合并为单一消息数组，按 timestamp 排序
自动滚底: useEffect(() => { listRef.current?.scrollToBottom() }, [messages])
发送: useMutation → optimistic add（pending 气泡）→ 服务端确认 → 更新 id/status
重连: useEffect cleanup 监听 ws.onclose → setTimeout 重连
特征: 历史加载（反向无限滚动）+ 实时追加，两种数据流合并
```
