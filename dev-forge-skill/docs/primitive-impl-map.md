# 行为原语实现映射

> **⚠ 本文件为历史参考，非强制映射。**
> 优先通过 context7 文档搜索获取当前技术栈的最新实现方案。
> 此表仅作降级参考，映射关系可能因库版本更新而过时。

> Step 2 识别出项目使用的行为原语后，查此表确定各技术栈的具体实现选项。
> 优先选用技术栈自带能力（零额外依赖），其次选生态标准库。

## Web 技术栈

| 原语 | UmiJS + AntD Pro | Vue 3 + Element Plus | Next.js (React) | Nuxt (Vue SSR) |
|------|-----------------|---------------------|-----------------|----------------|
| `VirtualList` | ProTable 内置虚拟化 | `el-table-v2`（虚拟表格） | `@tanstack/react-virtual` | `@tanstack/vue-virtual` |
| `InfiniteScroll` | `ProList` + `onLoadMore` | `el-infinite-scroll` 指令 / `useInfiniteScroll`（VueUse） | `useInfiniteQuery` + `IntersectionObserver` | `useInfiniteQuery`（@tanstack/vue-query）+ `IntersectionObserver` |
| `PullToRefresh` | 刷新按钮（桌面无下拉） | 刷新按钮（桌面无下拉） | `queryClient.invalidateQueries` | `queryClient.invalidateQueries` |
| `SwipeAction` | 操作列按钮替代（桌面） | 操作列按钮替代（桌面） | 操作列按钮替代（桌面） | 操作列按钮替代（桌面） |
| `HorizontalSwipe` | N/A（桌面不适用） | N/A（桌面不适用） | `react-swipeable` / `framer-motion` | `@vueuse/motion` |
| `VerticalSwipe` | N/A（桌面不适用） | N/A（桌面不适用） | `framer-motion` 手势 | `@vueuse/motion` |
| `DragAndDrop` | `@dnd-kit/core` + `@dnd-kit/sortable` | `vuedraggable` / `@vueuse/integrations/useSortable` | `@dnd-kit/core` | `vuedraggable` |
| `CanvasDrag` | `konva` / `react-flow` | `konva-vue` / `vue-flow` | `konva` / `react-flow` | `konva-vue` / `vue-flow` |
| `StateMachine` | 自定义 `useStateMachine` hook（枚举 + 合法转换 Map） | Pinia store + 枚举 + 合法转换函数 | `XState` / Zustand slice | Pinia + 枚举状态 / `XState` |
| `AppendOnlyStream` | Socket.io-client + `useRef` + `requestAnimationFrame` 滚动底 | Socket.io-client + `ref([])` + `nextTick` 滚底 | Socket.io-client / `EventSource`（SSE） | Socket.io-client + Nuxt SSE |
| `RealtimeSync` | Socket.io-client + 乐观更新 + reconcile | Socket.io-client + Pinia 乐观更新 | Socket.io-client + `useSyncExternalStore` | Socket.io-client + Pinia |
| `FormWithValidation` | `ProForm` + `rules` 数组 | `el-form` + `:rules` + `formRef.validate()` | `react-hook-form` + `zod` | `vee-validate` + `zod` / `yup` |
| `MultiStepWizard` | `StepsForm`（ProForm 内置） | `el-steps` + 分步 `el-form` | 自定义 step state + 条件渲染 | `el-steps` + 分步表单 |
| `TreeNavigation` | `Tree` 组件（AntD） | `el-tree` + `default-expanded-keys` | `react-arborist` / 自定义递归 | `el-tree` |
| `MediaPlayer` | `react-player` / HTML5 `<video>` | `vue-plyr` / HTML5 `<video>` | `react-player` | `vue-plyr` / HTML5 `<video>` |
| `ImageLightbox` | `Image.PreviewGroup`（AntD 内置） | `el-image` + `preview-src-list` | `yet-another-react-lightbox` | `vue-easy-lightbox` |
| `Timeline` | `Timeline`（AntD） | `el-timeline` + `el-timeline-item` | 自定义竖向列表 | `el-timeline` |
| `BatchSelection` | `ProTable` + `rowSelection` + `toolBarRender` | `el-table` + `@selection-change` + 批量操作 `el-button` | 自定义 checkbox state + toolbar | `el-table` + `@selection-change` |
| `FileUpload` | `Upload` + `Dragger` + `beforeUpload` + `onChange` 进度 | `el-upload` + `:before-upload` + `:on-progress` + `el-progress` | `react-dropzone` + `axios onUploadProgress` | `el-upload` + `el-progress` |
| `AsyncProcessing` | `useInterval`（ahooks）+ `Steps` 状态 | `useIntervalFn`（VueUse）+ `el-steps` 状态 | `useQuery(refetchInterval: 2000)` + 状态 badge | `useIntervalFn` + `el-steps` |
| `InlineEdit` | `ProTable editable={{ type: 'single' }}` | `el-table` 可编辑行（条件渲染 `el-input`） | 自定义 `<InlineEdit>` + `onBlur` + `useMutation` | `el-table` 可编辑行 |
| `BatchImport` | `Upload(accept=".csv,.xlsx")` + `xlsx` + `ProTable` 错误高亮 | `el-upload(accept=".csv,.xlsx")` + `xlsx` + `el-table` 错误高亮 | `react-dropzone` + `papaparse` + `Table` 错误高亮 | `el-upload` + `xlsx` + `el-table` 错误高亮 |

## 原生 / 桌面技术栈

| 原语 | iOS Swift/SwiftUI | Android Kotlin/Compose | Flutter | React Native | Windows WPF/Electron |
|------|-------------------|------------------------|---------|--------------|----------------------|
| `VirtualList` | `List` / `LazyVStack`（原生懒渲染） | `LazyColumn`（原生） | `ListView.builder`（原生） | `FlatList`（原生） | `VirtualizingStackPanel`（WPF）/ `react-window`（Electron） |
| `InfiniteScroll` | `List` + `.onAppear` 末尾触发 | `LazyColumn` + `LazyListState` 末尾检测 | `ListView.builder` + `onEndReached` | `FlatList` + `onEndReached` | `ScrollViewer.ScrollChanged`（WPF）/ `IntersectionObserver`（Electron） |
| `PullToRefresh` | `.refreshable { await viewModel.refresh() }` | `SwipeRefresh`（accompanist）/ `PullRefreshIndicator`（M3） | `RefreshIndicator` | `RefreshControl` | N/A（桌面用工具栏刷新按钮） |
| `SwipeAction` | `.swipeActions { Button {...} }` | `SwipeToDismiss`（Compose） | `Dismissible` / `flutter_slidable` | `react-native-swipeable` | N/A（右键上下文菜单替代） |
| `HorizontalSwipe` | `TabView(.page)` / `DragGesture` | `HorizontalPager`（Accompanist） | `PageView` + `GestureDetector` | `PanGestureHandler` | 鼠标横向滚动 / N/A |
| `VerticalSwipe` | `ScrollView` + `DragGesture` | `VerticalPager` | `PageView(scrollDirection: Axis.vertical)` | `FlatList(pagingEnabled)` | 鼠标纵向滚动 / N/A |
| `DragAndDrop` | `.draggable()` + `.dropDestination()`（iOS 16+） | `reorderable`（Compose）库 | `ReorderableListView` | `react-native-draggable-flatlist` | `AllowDrop="True"` + DragOver/Drop（WPF）/ HTML5 DnD（Electron） |
| `CanvasDrag` | `Canvas` + `DragGesture`（SwiftUI） | `Canvas` + `pointerInput detectDragGestures` | `CustomPaint` + `GestureDetector` | `react-native-canvas` | `InkCanvas`（WPF）/ `konva`（Electron） |
| `StateMachine` | Swift `enum State` + `@Published var state` + `switch` | `sealed class State` + `StateFlow` in ViewModel | Riverpod `StateNotifier` | Zustand slice | C# `enum` + `switch expression`（WPF）/ `XState`（Electron） |
| `AppendOnlyStream` | `URLSessionWebSocketTask` + `@MainActor append` | `Flow<Message>` + `LazyColumn(reverseLayout=true)` | `StreamBuilder` + `web_socket_channel` | Socket.io-client + `FlatList inverted` | SignalR client（WPF）/ Socket.io（Electron） |
| `RealtimeSync` | `URLSessionWebSocketTask` + `ObservableObject` | OkHttp WebSocket + `MutableStateFlow` in ViewModel | `web_socket_channel` + Riverpod | Socket.io-client + Zustand | SignalR（WPF）/ Socket.io（Electron） |
| `FormWithValidation` | `Form` + `TextField` + `@State` 验证 + 错误 overlay | `TextField` + `derivedStateOf` 验证 + ViewModel 提交 | `Form` + `TextFormField` + `validator` | `react-hook-form` | `INotifyDataErrorInfo`（WPF）/ `react-hook-form`（Electron） |
| `MultiStepWizard` | `@State step` + `NavigationStack` / `TabView` 分步 | `@State step` + `HorizontalPager` / 条件渲染 | `Stepper` package / 自定义 `PageView` | `react-native-paper` Steps | Wizard（WPF Extended Toolkit）/ 自定义 Steps（Electron） |
| `TreeNavigation` | `OutlineGroup`（SwiftUI） | 递归 `LazyColumn` + `AnimatedVisibility` 展开 | `flutter_treeview` | `react-native-tree-select` | `TreeView`（WPF）/ `react-arborist`（Electron） |
| `MediaPlayer` | `AVPlayer` + `VideoPlayer`（SwiftUI） | `ExoPlayer` + `AndroidView` | `video_player` + `Chewie` | `react-native-video` | `MediaElement`（WPF）/ HTML5 video（Electron） |
| `ImageLightbox` | `AsyncImage` + `fullScreenCover` 全屏 | Coil + `Dialog` + `HorizontalPager` | `photo_view` | `react-native-image-viewing` | 自定义 `Window`（WPF）/ lightbox 库（Electron） |
| `Timeline` | 自定义 `LazyVStack` 时间轴 View | 自定义 `LazyColumn` + `TimelineItem` Composable | `timeline_tile` | 自定义 `FlatList` | 自定义 `ItemsControl` + DataTemplate（WPF）/ 自定义组件（Electron） |
| `BatchSelection` | `List` + `EditButton` + `Set<Selection>` | `LazyColumn` + checkbox + `BottomAppBar` 批量操作 | `ListView` + `Checkbox` + `FloatingActionButton` | `FlatList` + Checkbox + bottom toolbar | `DataGrid SelectionMode="Extended"`（WPF）/ checkbox 列（Electron） |
| `FileUpload` | `fileImporter`（SwiftUI）+ `URLSession` multipart | `ActivityResultContracts.GetContent` + Retrofit multipart | `file_picker` + `dio(onSendProgress)` + `LinearProgressIndicator` | `react-native-document-picker` + `axios onUploadProgress` | `OpenFileDialog` + `HttpClient` multipart（WPF）/ `dialog.showOpenDialog`（Electron） |
| `AsyncProcessing` | `Task { while !done { try await Task.sleep(); await check() } }` | `WorkManager`（后台）/ coroutine polling + `CircularProgressIndicator` | `Timer.periodic` + Riverpod + `LinearProgressIndicator` | `setInterval` 轮询 + Zustand + `ActivityIndicator` | `BackgroundWorker` + `ProgressBar`（WPF）/ IPC + `ProgressBar`（Electron） |
| `InlineEdit` | `@FocusState` + `TextField` + `onSubmit` 保存 | `TextField` + `FocusRequester` + `.onFocusChanged { if !focused { save() } }` | `InkWell` + `TextFormField(autofocus)` + `FocusNode` | `Pressable` → `TextInput(autoFocus)` + `onBlur` | `DataGrid` 内联编辑（WPF）/ 自定义可编辑单元格（Electron） |
| `BatchImport` | `fileImporter(contentTypes: [.commaSeparatedText])` + CSV 解析 + `List` 错误高亮 | `GetContent("text/csv")` + `CsvReader` + `LazyColumn` 错误高亮 | `file_picker` + `csv` package + `DataTable` 错误高亮 | `react-native-document-picker` + `papaparse` + `FlatList` 错误高亮 | `OpenFileDialog` + `CsvHelper`（WPF）/ `papaparse`（Electron）+ DataGrid 错误高亮 |
