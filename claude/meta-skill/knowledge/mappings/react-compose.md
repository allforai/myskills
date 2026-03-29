# React -> Jetpack Compose Mapping

> Equivalence tables for translating React (web) patterns to Jetpack Compose (Android).
> Three categories: direct equivalence (auto-map), multi-option (user decision), architectural difference (needs explanation).

---

## Component Mapping

| React | Compose | Type | Notes |
|-------|---------|------|-------|
| `<div>` flex row | `Row` | Direct | |
| `<div>` flex column | `Column` | Direct | |
| `<div>` stacked/absolute | `Box` | Direct | |
| `<span>` / `<p>` | `Text` | Direct | |
| `<img>` (static, resource) | `Image(painterResource(...))` | Direct | |
| `<img>` (remote URL) | `AsyncImage` via Coil | Direct | `coil-compose` dependency required |
| `<input type="text">` | `TextField` / `OutlinedTextField` | Multi-option | A: filled / B: outlined — depends on design |
| `<input type="password">` | `TextField(visualTransformation = PasswordVisualTransformation())` | Direct | |
| `<button>` | `Button` | Direct | |
| `<button>` icon-only | `IconButton` | Direct | |
| `<button>` text+icon | `TextButton` / `ElevatedButton` | Multi-option | Material 3 variants |
| `<select>` | `ExposedDropdownMenuBox` + `DropdownMenuItem` | Direct | |
| `<textarea>` | `TextField(maxLines = ...)` | Direct | |
| `<ul>` / `<li>` (long list) | `LazyColumn` | Direct | Virtualized |
| `<ul>` / `<li>` (short list) | `Column` + `items.forEach` | Direct | No virtualization |
| Horizontal list | `LazyRow` | Direct | |
| `<a>` / `<Link>` | Navigation composable call | Direct | |
| `<ScrollView>` | `Column` inside `verticalScroll(rememberScrollState())` | Direct | |
| `<Modal>` / dialog | `AlertDialog` / `Dialog` | Multi-option | A: AlertDialog (simple) / B: custom Dialog |
| Bottom sheet | `ModalBottomSheet` | Direct | Material 3 |
| `<Tabs>` | `TabRow` + content swap | Direct | |
| Loading spinner | `CircularProgressIndicator` | Direct | |
| Loading bar | `LinearProgressIndicator` | Direct | |
| `{condition && <X/>}` | `if (condition) { X() }` | Direct | Kotlin idiomatic |
| `{items.map(i => <X/>)}` | `items.forEach { X(it) }` | Direct | Inside LazyColumn: `items(list) { }` |
| Error boundary | `try/catch` in ViewModel + state | Arch diff | Compose has no error boundary; handle in ViewModel |

---

## State Management

| React | Compose | Type | Notes |
|-------|---------|------|-------|
| `useState` | `remember { mutableStateOf() }` | Direct | Local to composable |
| `useState` (hoisted) | `rememberSaveable { mutableStateOf() }` | Direct | Survives recomposition + process death |
| `useReducer` | `remember { mutableStateOf() }` + sealed class action | Direct | Or ViewModel with sealed Action class |
| `useContext` | `CompositionLocalProvider` + `LocalX.current` | Direct | |
| Global state | ViewModel + `StateFlow` / `MutableStateFlow` | Direct | |
| Redux store | ViewModel + `StateFlow` | Direct | |
| Redux `useSelector` | `viewModel.uiState.collectAsState()` | Direct | |
| Redux `dispatch` | `viewModel.onEvent(action)` method call | Direct | |
| `useMemo` | `remember(key) { computation }` | Direct | Re-computes when key changes |
| `useRef` (mutable) | `remember { mutableStateOf() }` or `by rememberUpdatedState` | Direct | |
| Zustand store | ViewModel + `StateFlow` | Direct | Hilt for injection |
| React Query | `LaunchedEffect` + ViewModel | Direct | No built-in cache; use Room or custom |
| React Query (cache) | Room database as cache layer | Multi-option | A: Room / B: in-memory map in ViewModel |
| `useImperativeHandle` | `SideEffect` / interop with View system | Arch diff | Compose is declarative; imperative handle is rare |

---

## Lifecycle

| React | Compose | Type | Notes |
|-------|---------|------|-------|
| `useEffect(fn, [])` (mount) | `LaunchedEffect(Unit) { }` | Direct | Runs once on first composition |
| `useEffect(fn, [dep])` | `LaunchedEffect(dep) { }` | Direct | Re-launches when `dep` changes |
| `useEffect` cleanup | `DisposableEffect { onDispose { } }` | Direct | Cleanup runs on leaving composition |
| `componentDidMount` | `LaunchedEffect(Unit) { }` | Direct | |
| `componentWillUnmount` | `DisposableEffect { onDispose { } }` | Direct | |
| Side effect (non-suspend) | `SideEffect { }` | Direct | Runs on every recomposition |
| ViewModel init | `init { }` block in ViewModel | Direct | Android lifecycle-aware |
| Activity `onResume` | `LifecycleEventEffect(Lifecycle.Event.ON_RESUME)` | Direct | `lifecycle-compose` artifact |
| Activity `onPause` | `LifecycleEventEffect(Lifecycle.Event.ON_PAUSE)` | Direct | |
| `React.StrictMode` | — | Arch diff | Compose may recompose multiple times; use stable types |

---

## Navigation

| React | Compose | Type | Notes |
|-------|---------|------|-------|
| React Router | Jetpack Navigation Compose (`androidx.navigation.compose`) | Direct | |
| `<Routes>` / `<Switch>` | `NavHost` | Direct | |
| `<Route path="screen">` | `composable("screen") { }` inside NavHost | Direct | |
| `useNavigate()` push | `navController.navigate("screen")` | Direct | |
| `useNavigate(-1)` back | `navController.popBackStack()` | Direct | |
| `<Link to="screen">` | `navController.navigate("screen")` on click | Direct | |
| URL params | `navArgument("id") { type = NavType.StringType }` | Direct | |
| Query string | `navController.navigate("screen?id={id}")` | Direct | |
| Nested routes | Nested `NavHost` | Direct | |
| Tab navigation | `BottomNavigation` + `NavHost` | Direct | |
| Deep linking | `deepLink { uriPattern = "app://..." }` in `composable` | Direct | |
| Route guards | `LaunchedEffect` check + navigate away | Direct | No built-in guards; check in effect |

## Build Commands (Target: Jetpack Compose/Android)

| Action | Command |
|--------|---------|
| Build | `./gradlew assembleDebug` |
| Test | `./gradlew testDebugUnitTest` |
| Clean | `./gradlew clean` |
| Run | `./gradlew installDebug && adb shell am start -n <package>/.MainActivity` |
| Lint | `./gradlew lintDebug` |

Note: `<package>` replaced by bootstrap with actual Android package name.
