# Flutter 套路（mobile-native 类）

| 交互类型 | 套路 |
|---------|------|
| 列表浏览 | ListView.builder + Riverpod `AsyncNotifierProvider`（分页加载） |
| 详情查看 | `FutureProvider` / `AsyncNotifier` → 单实体 fetch |
| 表单提交 | Form + TextFormField + `controller.text = oldValue` 回填 |
| 枚举选择 | `DropdownButtonFormField` |
| 状态操作 | `showDialog` 确认 → API → `ref.invalidate()` |
| 删除 | `showDialog` 确认 → API → `ref.invalidate()` / `context.pop()` |
| 配置页 | `AsyncNotifier` 加载 → Form 回填 → 保存 |
| i18n | flutter_localizations + `.arb` 文件 |

## CT1 Feed 流

```
Provider: AsyncNotifierProvider<FeedNotifier, List<Post>>
加载更多: ListView.builder + ScrollController → _controller.addListener(() {
    if (_controller.position.pixels >= _controller.position.maxScrollExtent - 200) {
      ref.read(feedProvider.notifier).loadMore();
    }
  })
下拉刷新: RefreshIndicator → ref.read(feedProvider.notifier).refresh()
互动: optimistic update → ref.read(feedProvider.notifier).toggleLike(postId)
特征: Riverpod AsyncNotifier 管理分页游标，loading/error/data 三态
```

## EC1 商品详情页

```
数据: FutureProvider.family<Product, String>((ref, id) => api.getProduct(id))
SKU 状态: StateProvider<Map<String, String>>（规格选择） + 派生 Provider 计算当前 SKU
  final currentSkuProvider = Provider((ref) {
    final selected = ref.watch(selectedSpecProvider);
    final product = ref.watch(productProvider(id)).value;
    return product?.skus.firstWhere((s) => matchSpec(s.spec, selected));
  });
图片: PageView.builder + photo_view（缩放）
加购: ref.read(cartProvider.notifier).add(skuId, quantity)
特征: 派生 Provider 实现规格→价格/库存的响应式联动
```

## WK1 IM 对话

```
WebSocket: web_socket_channel → StreamBuilder<WebSocketMessage>
消息: StateNotifierProvider<ChatNotifier, ChatState>
  → 历史消息: 首次加载 → state = ChatState(messages: history)
  → 新消息: StreamBuilder 触发 notifier.append(msg)
列表: ListView.builder(reverse: true) + ScrollController 自动滚底
发送: notifier.sendMessage(text) → optimistic add → WS send → 确认后更新 id
重连: StreamBuilder error → ElevatedButton("重新连接", onPressed: notifier.reconnect)
特征: reverse ListView 实现聊天气泡自然布局，StreamBuilder 驱动实时更新
```
