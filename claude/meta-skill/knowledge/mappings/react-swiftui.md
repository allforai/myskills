# React -> SwiftUI Mapping

> Equivalence tables for translating React (web) patterns to SwiftUI (iOS/macOS).
> Three categories: direct equivalence (auto-map), multi-option (user decision), architectural difference (needs explanation).

---

## Component Mapping

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| `<div>` flex column | `VStack` | Direct | Default axis |
| `<div>` flex row | `HStack` | Direct | |
| `<div>` stacked/absolute | `ZStack` | Direct | |
| `<span>` / `<p>` | `Text` | Direct | |
| `<img>` (static) | `Image` | Direct | |
| `<img>` (remote URL) | `AsyncImage` | Direct | Built-in async loading |
| `<input type="text">` | `TextField` | Direct | |
| `<input type="password">` | `SecureField` | Direct | |
| `<button>` | `Button` | Direct | |
| `<select>` | `Picker` | Direct | Multiple styles (wheel, segmented, menu) |
| `<textarea>` | `TextEditor` | Direct | |
| `<ul>` / `<li>` | `List` / `ForEach` | Direct | |
| `<a>` / `<Link>` | `NavigationLink` | Direct | |
| `<ScrollView>` | `ScrollView` | Direct | |
| `<Modal>` / dialog | `.sheet()` / `.fullScreenCover()` | Multi-option | A: sheet (partial) / B: fullScreenCover (full) |
| `<Tabs>` | `TabView` | Direct | |
| Loading spinner | `ProgressView` | Direct | Determinate or indeterminate |
| `{condition && <X/>}` | `if condition { X() }` | Direct | |
| `{items.map(i => <X/>)}` | `ForEach(items) { X() }` | Direct | Requires `Identifiable` or `\.self` keyPath |
| Error boundary | `do/catch` + `@State var error` | Arch diff | SwiftUI has no error boundary concept |

---

## State Management

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| `useState` | `@State` | Direct | Local ephemeral state |
| `useReducer` | `@State` + enum action pattern | Direct | No dedicated reducer; use methods |
| `useContext` (read) | `@Environment` | Direct | System environment values |
| `useContext` (custom) | `@EnvironmentObject` | Direct | Injected via `.environmentObject()` |
| `useRef` (DOM ref) | `@FocusState` / `.focused()` | Multi-option | Focus management |
| `useRef` (mutable) | Local variable (not in body) | Direct | |
| `useMemo` | Computed property | Direct | Re-computes only on state change |
| `useCallback` | Method on View / ViewModel | Direct | |
| `useImperativeHandle` | — | Arch diff | SwiftUI is declarative; no imperative handle |
| Redux store | `@Observable` class (iOS 17+) | Direct | |
| Redux store (pre-iOS 17) | `@ObservableObject` + `@Published` | Direct | Legacy pattern |
| Redux `useSelector` | Property access on `@Observable` | Direct | |
| Redux `dispatch` | Method call on `@Observable` | Direct | |
| Zustand store | `@Observable` singleton | Direct | |
| React Query | Async method on ViewModel | Direct | No cache layer equivalent; roll your own |
| React Query (cache) | — | Arch diff | Must implement caching manually or use URLCache |

---

## Lifecycle

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| `useEffect(fn, [])` (mount) | `.task { }` | Direct | Async-safe; auto-cancelled on disappear |
| `useEffect(fn, [])` (mount, sync) | `.onAppear { }` | Direct | Synchronous; no async support |
| `useEffect(fn, [dep])` | `.onChange(of: dep) { }` | Direct | iOS 17+: `onChange(of:) { old, new in }` |
| `useEffect(fn, [dep])` (async) | `.task(id: dep) { }` | Direct | Re-launches task when dep changes |
| `useEffect` cleanup | `.onDisappear { }` / Task cancellation | Direct | Structured concurrency cancels `.task` |
| `componentWillUnmount` | `.onDisappear { }` | Direct | |
| `React.StrictMode` double-invoke | — | Arch diff | SwiftUI previews re-render but no strict double-invoke |

---

## Navigation

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| React Router `<Routes>` | `NavigationStack` | Direct | iOS 16+ data-driven navigation |
| `<Route path="/">` | `.navigationDestination(for:)` | Direct | Type-driven destination registration |
| `useNavigate()` | `NavigationPath` + `@State` | Direct | Push path values to navigate |
| `useNavigate()` back | `@Environment(\.dismiss)` | Direct | |
| `<Link to="/">` | `NavigationLink(value:)` | Direct | |
| Nested routes | Nested `NavigationStack` / `TabView` | Multi-option | A: nested stacks / B: tab-based split |
| Query string params | Associated values on navigation type | Direct | |
| Browser back button | Swipe-back gesture (built-in) | Direct | |
| Deep linking (URL) | `.onOpenURL` + universal links | Direct | |

---

## Async Patterns

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| `async/await` in useEffect | `.task { await fetch() }` | Direct | |
| `Promise.all` | `async let x = …; async let y = …` | Direct | |
| `Promise.all` (dynamic) | `TaskGroup` / `withTaskGroup` | Direct | |
| Loading state pattern | `@State var isLoading` + `ProgressView` | Direct | |
| Error state pattern | `@State var error: Error?` + alert | Direct | |
| Cancellable fetch | `Task { }` stored + `.cancel()` | Direct | Or use `.task { }` for auto-cancel |
| Debounce | `Task.sleep` + re-issue | Multi-option | A: manual sleep / B: Combine `debounce` |
| Polling | `while !Task.isCancelled { await sleep; fetch }` | Direct | |

---

## Styling

| React | SwiftUI | Type | Notes |
|-------|---------|------|-------|
| CSS `className` | View modifiers chain | Direct | Modifiers are order-sensitive |
| `styled-components` | `ViewModifier` + custom extension | Direct | |
| Tailwind `flex` col/row | `VStack` / `HStack` | Direct | |
| Tailwind `padding` | `.padding()` / `.padding(.horizontal, 16)` | Direct | |
| Tailwind `margin` | Spacer or padding on parent | Direct | SwiftUI has no margin; use Spacer or padding |
| Tailwind `gap` | `spacing:` param on VStack/HStack | Direct | |
| CSS `display: none` | `.hidden()` / `if show { View() }` | Multi-option | A: `.hidden()` keeps layout space / B: `if` removes view |
| CSS custom properties | `@Environment` values or extension constants | Direct | |
| CSS media query (screen width) | `@Environment(\.horizontalSizeClass)` | Direct | compact vs regular |
| Dark mode | `@Environment(\.colorScheme)` | Direct | |
| Responsive font size | `.font(.title)` semantic sizes | Direct | |
| CSS animation | `.animation()` + `withAnimation { }` | Direct | |
| CSS transition | `.transition()` | Direct | |
| z-index | ZStack layer order | Arch diff | Order in ZStack determines stacking; no z-index number |

## Build Commands (Target: SwiftUI/iOS)

| Action | Command |
|--------|---------|
| Build | `xcodebuild -scheme <AppName> -destination 'platform=iOS Simulator,name=iPhone 16' build` |
| Test | `xcodebuild -scheme <AppName> -destination 'platform=iOS Simulator,name=iPhone 16' test` |
| Clean | `xcodebuild -scheme <AppName> clean` |
| Run | `open -a Simulator && xcodebuild -scheme <AppName> -destination 'platform=iOS Simulator,name=iPhone 16' build` |

Note: `<AppName>` replaced by bootstrap with actual Xcode scheme name.
