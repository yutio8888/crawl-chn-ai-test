# Android 暂停存档并发安全调查

调查分支：`codex/android-save-safety`，基线 `chn-0.34.1-base` @ `6b82440c54`。
本文只描述 `__ANDROID__` 路径。行号引用调查时的仓库状态。

## 1. 调用链与执行线程

### 1.1 UI 线程一侧

| 步骤 | 位置 | 线程 |
|---|---|---|
| `SDLActivity.onPause()` | `crawl-ref/source/android-project/app/src/main/java/org/libsdl/app/SDLActivity.java:372` | Android 主线程（UI 线程） |
| `SDLActivity.nativeSaveGame()` | 同上 `:376`（声明在 `:769`） | UI 线程 |
| `Java_org_libsdl_app_SDLActivity_nativeSaveGame` | `crawl-ref/source/syscalls.cc:169-175` | UI 线程（JNI 直接调用，无线程切换） |
| `save_game(false)` | `crawl-ref/source/files.cc:2651` | UI 线程 |

`onPause()` 的语句顺序很关键：

```java
372  protected void onPause() {
375      // CRAWL HACK: Save game
376      SDLActivity.nativeSaveGame();      // ← 整个存档在这里同步完成
378      super.onPause();
386      SDLActivity.handleNativeState();   // ← 之后才走到 nativePause()
```

也就是说存档发生在 SDL 收到任何暂停通知**之前**。

### 1.2 游戏线程一侧

游戏逻辑跑在 `SDLActivity.java:579-581` 启动的 `SDLThread` 上（`SDLMain` → `nativeRunMain`
→ crawl `main()`）。该线程独立于 UI 线程，两者之间除本次 JNI 调用外没有任何同步。

`save_game(false)` 在 Android 下访问的对象（`files.cc:2651-2695`）：

- `crawl_state.saving_game`（`unwind_bool`，全局，进出各写一次）
- `ASSERT(you.on_current_level || Options.no_save)`
- `_save_game_base()`（`files.cc:2587`）：`StashTrack`、`clua`、`you.kills`、
  `travel_cache`、notes、messages、dlua errors、tiles doll，以及
  `_write_tagged_chunk("you"/"chr")`
- Android 专属分支 `files.cc:2681-2688`：`clua.save_persist()`、`macro_save()`、
  `save_level(level_id::current())`
- `save_level()`（`files.cc:2561`）：`travel_cache.get_level_info(...).update()`、
  `fix_item_coordinates()`（**写** `env.item` 坐标）、写整层 `TAG_LEVEL`
- `you.save->commit()`（`files.cc:2691` → `package.cc:235`）

这些全部是游戏线程独占的状态。

### 1.3 存档请求发生时 SDLThread 可能处于的位置

`nativeSaveGame()` 返回之前 SDL 完全不知道要暂停，因此游戏线程处于它当时正在做的
任何事情上，包括：

- 阻塞在 `SDLWrapper::wait_event()`（`windowmanager-sdl.cc:967`）→
  `SDL_WaitEventTimeout(..., INT_MAX)`（等待命令、菜单、弹窗、文本输入）
- 自动探索 / travel：`kbhit()`（`libgui.cc:232`）只调用
  `wm->next_event_is(WME_KEYDOWN)`，即 `SDL_PeepEvents`，**不阻塞**，游戏线程
  在满速跑回合循环
- `world_reacts()` 中的回合结算，包括它自己的存档检查点
  （`main.cc:2765-2774`：`save_level(); save_game(false);`）
- 跨层：`stairs.cc:1105` `save_game_state()` → `save_game(false)`
- 层生成：`crawl_state.generating_level`，正在写 `you.save`
- 深渊传送检查点：`player-reacts.cc:1344`；额外生命检查点：`ouch.cc:1615`

## 2. SDL 暂停事件顺序，以及 crawl 是否已经在 SDL 线程处理

SDL 版本：`crawl-ref/source/contrib/sdl2` @ `a6d964d0`（`SDL_version.h` 为 2.0.x 系）。

`Java_org_libsdl_app_SDLActivity_nativePause`（`src/core/android/SDL_android.c:701-715`）
在 UI 线程上依次投递
`SDL_WINDOWEVENT_FOCUS_LOST` → `SDL_WINDOWEVENT_MINIMIZED` →
`SDL_APP_WILLENTERBACKGROUND` → `SDL_APP_DIDENTERBACKGROUND`，然后 post
`Android_PauseSem`。

`Android_PumpEvents`（`src/video/android/SDL_androidevents.c`，`SDL_ANDROID_BLOCK_ON_PAUSE`
默认开启）在**游戏线程**上观察 `Android_PauseSem`；只有当上述事件已经被应用取走
（`SDL_HasEvent(...)` 全部为假）之后才置 `isPaused`，再下一次 pump 才
`SDL_SemWait(Android_ResumeSem)` 阻塞游戏线程。

crawl 侧的结论：

- 全仓库（排除 `contrib/`）**没有任何** `SDL_APP_WILLENTERBACKGROUND` /
  `SDL_APP_DIDENTERBACKGROUND` / `SDL_APP_TERMINATING` / `SDL_APP_WILLENTERFOREGROUND`
  的引用。
- `SDLWrapper::wait_event()` 的 `switch` 对这些事件类型落到
  `default: return 0;`（`windowmanager-sdl.cc:1070-1071`），即静默丢弃。

**所以 crawl 目前没有在 SDL 线程上响应任何后台事件做保存**，UI 线程的
`nativeSaveGame()` 是唯一的暂停存档路径，不存在"删除重复保存"这个选项。

由此还得到一个必须处理的约束：游戏线程如果正阻塞在
`SDL_WaitEventTimeout(..., INT_MAX)`，只有 UI 线程后续调用 `nativePause()`
投递事件才会把它唤醒；而 `nativePause()` 在 `nativeSaveGame()` 返回之后才发生。
任何"让 UI 线程等游戏线程执行保存"的修复，都必须自己解决唤醒问题，不能依赖
SDL 的暂停事件（否则必然死锁到超时）。

## 3. 风险场景判定

`package` 的读写状态全部是进程内可变结构：`directory`、`free_blocks`、
`block_map`、`new_chunks`、`dirty`，加上一个共享的文件描述符，`package::seek()`
用 `lseek` + `write` 定位（`package.cc:273-281`）。两个线程同时写同一个
`package` 不只是"丢更新"，而是把数据写到彼此的偏移上，并让最终 commit 写出的
目录指向已被覆盖的块。

| # | 场景 | 是否并发 | 后果 | 证据 |
|---|---|---|---|---|
| 1 | 游戏线程阻塞在 `wait_event`（等命令 / 菜单 / 弹窗 / 文本输入）时按 Home | **否**（游戏状态静止） | 实际安全；这是目前多数情况 | `windowmanager-sdl.cc:967`，`tilesdl.cc:690`，`ui.cc:3279` |
| 2 | 自动探索 / travel / 休息中按 Home | **是** | UI 线程与游戏线程同时改 `you`、`env`、`travel_cache`，并同时写 `you.save`；`fix_item_coordinates()` 在游戏线程移动物品的同时改物品坐标 | `libgui.cc:232`（`kbhit` 非阻塞）、`main.cc:1214-1234`、`files.cc:2567` |
| 3 | 跨层（`stairs.cc:1105` `save_game_state()`）时按 Home | **是** | 两个 `save_game(false)` 并发写同一个 `package`：`fd` 偏移竞争 + `directory`/`free_blocks` 竞争 → 提交出的存档指向被覆盖的块，属于真正的坏档 | `stairs.cc:1105`、`files.cc:2691`、`package.cc:235-270` |
| 4 | 回合检查点（`main.cc:2765-2774`）与 Home 重合 | **是** | 同 #3 | `main.cc:2769-2773` |
| 5 | 层生成中（`crawl_state.generating_level`）按 Home | **是** | UI 线程在半生成的关卡上跑 `save_level()`；`ASSERT(you.on_current_level)` 也可能在 UI 线程上触发 crawl 的 `die()` | `files.cc:2229-2231` |
| 6 | 玩家正在退出 / 死亡（`_save_game_exit()` 执行 `delete you.save; you.save = 0;`）时按 Home | **是** | `syscalls.cc:173` 的 `if (you.save)` 与 `save_game(false)` 之间存在 TOCTOU，可能对已释放的 `package` 解引用 | `files.cc:2647-2648`、`syscalls.cc:173-174` |
| 7 | 深渊传送检查点（`player-reacts.cc:1344`）、额外生命检查点（`ouch.cc:1615`）与 Home 重合 | **是** | 同 #3 | 对应行 |
| 8 | 主菜单 / 新游戏界面按 Home | 否 | `you.save == nullptr`，JNI 直接返回 | `syscalls.cc:173` |
| 9 | 存档中再次 onPause | 不适用 | 同一线程不可重入；但当前实现没有任何限流，第二次 onPause 会串行地再存一次 | `SDLActivity.java:376` |
| 10 | SDLThread 已退出（native 线程结束但 Activity 还在） | 否 | `you.save` 已为空 → 空操作 | `files.cc:2648` |

补充：`crawl_state.saving_game` 由 `unwind_bool` 管理（`files.cc:2653`）。UI 线程
进入 `save_game` 会把它置真、退出时恢复为**进入时读到的值**；若游戏线程在这中间
也进出 `save_game`，恢复出来的值可能是错的，`saving_game` 会永久卡在 true 或
提前变 false。

另外 `save_game(false)` 在 Android 下会调 `clua.save_persist()`（`files.cc:2683`）。
Lua 状态机不是线程安全的；游戏线程执行任意 Lua（用户脚本、`dlua`、地图代码）
时 UI 线程进入同一个 `lua_State`，属于未定义行为。

**判定**：场景 1、8、10 安全；场景 2、3、4、5、6、7 存在真实并发访问，其中
3、4、7 可直接产出结构性坏档，6 可产生释放后使用。风险确实存在，不是理论问题。

## 4. 进程被杀后的恢复路径

- 存档容器 `package`（`package.cc:6-19` 的注释即为其契约）保证：任意时刻崩溃，
  存档回到最后一次 `commit()` 的状态。
- `commit()`（`package.cc:235-270`）先写新目录，`fdatasync` 屏障，再原子写 header
  的 `start` 指针，再 `fdatasync`。`DO_FSYNC` 在 `package.h:21` 无条件定义，因此
  屏障在 Android 上是生效的。
- **没有** `.bak`、影子文件或临时副本机制；一致性完全依赖上述"最后写 header"的
  顺序。这对 `adb shell am kill`（SIGKILL）这种进程级别的杀是足够的。
- 存档用 `lock_file(fd, true)`（`package.cc:102`、`:119`）加锁；SIGKILL 时内核释放
  fd，锁随之消失，重启不会误报 "Another game is already in progress using this save!"。
- 加载失败的表现：`package::load()` 的各种 `corrupted(...)`（`package.cc:170-592`）
  和 `_restore_tagged_chunk` 的 "Level file is invalid."（`files.cc:2237`）都会走
  crawl 的致命错误路径，玩家看到的是启动即崩/存档损坏，而不是回退到上一个检查点。

关键点：**崩溃一致性保护的是"写到一半被杀"，保护不了"两个线程交错写"**。第 3 节
场景 3/4/7 破坏的是 commit 之后的已提交状态，`package` 的保证在这里不适用，
也没有备份可回退。

## 5. 复现结果

**未在真机/模拟器上复现，仅静态分析。**

环境中存在 `emulator-5554`（x86_64）与一台物理设备，但：

- 该模拟器上已安装 `org.develz.crawl`、`org.develz.crawl.uiux105`、
  `org.develz.crawl.landscape113`、`org.develz.crawl.portrait`，调查时
  `org.develz.crawl.portrait/.DungeonCrawlStoneSoup` 处于 `topResumedActivity`，
  即有并行代理正在使用该设备；
- 仓库的 Android 构建助手 `crawl-ref/source/util/build-android.sh` 固定把
  `.worktrees/android-tiles` 同步到**主检出的 HEAD** 后再构建，本任务的分支边界
  禁止改动其他 worktree。

因此本调查没有执行 "自动探索中 / 跨层中 / 弹窗中按 Home + `adb shell am kill`"
的对照实验。需要注意，即使执行了，场景 2/3/4 是窄窗口竞态，阴性结果不能证伪；
本报告的结论建立在调用链和线程归属的静态证据上。

## 6. 推荐修复与范围评估

### 6.1 方案选择

| 方案 | 评估 |
|---|---|
| 删除 UI 线程的重复保存 | **不可行**：第 2 节确认 crawl 没有任何 SDL 线程侧的后台事件保存，删掉就等于取消暂停存档 |
| 复用 `crawl_state.seen_hups` | **不可行**：`seen_hups` 语义是"尽快存盘并退出"（`main.cc:1120`、`:1304`），按 Home 会直接结束游戏 |
| 复用 `crawl_state.save_after_turn` | **不充分**：`main.cc:2769` 的检查点被 `!you_are_delayed()` 挡住，且玩家在提示符前按 Home 时根本不会再走到回合结束 |
| 把保存请求投递给游戏线程，在安全点执行，UI 线程有界等待 | **采纳** |

### 6.2 采纳方案

1. `nativeSaveGame()`（`syscalls.cc`）不再自己存档，改为置一个"待保存"请求，
   唤醒并有界等待（2 秒上限）游戏线程完成，然后无论成败都返回。UI 线程绝不
   触碰 `you` / `env` / `clua` / `you.save`。
2. 游戏线程在两个已有的安全点消费该请求：
   - `SDLWrapper::wait_event()`（`windowmanager-sdl.cc`）的入口——游戏线程在等
     输入，回合已结算完毕；覆盖场景 1/6/8/9；
   - `world_reacts()` 尾部现有检查点旁（`main.cc:2765-2774`）——覆盖自动探索 /
     travel / 休息（场景 2/4/7）。
3. 唤醒问题（第 2 节末尾）：不向 SDL 队列推自定义事件（`SDL_USEREVENT` 会被
   `ui.cc:2868` 当成函数指针回调，推空指针会崩），改为在 Android 上把
   `SDL_WaitEventTimeout` 的长等待切成固定片。SDL 的 `SDL_WaitEventTimeout`
   本身就是每 10 ms `SDL_PumpEvents` 一次的轮询循环，切片不增加唤醒次数。
4. 安全性判据（游戏线程侧）：`you.save && crawl_state.need_save &&
   crawl_state.game_started && !crawl_state.saving_game &&
   !crawl_state.generating_level && !crawl_state.updating_scores &&
   !crawl_state.game_crashed && !crawl_state.seen_hups && you.on_current_level &&
   !you.entering_level`。不满足时直接丢弃请求并唤醒 UI 线程——覆盖场景 5，并让
   场景 3（跨层）退化为"这次不存"而不是"存坏"。
5. 三个必须覆盖的情况：
   - **保存进行中再次 onPause**：请求标志 + "正在保存"标志，第二次 onPause 会等
     前一次结束，不会叠加两次并发保存。
   - **保存失败**：用 RAII 守卫清理"正在保存"标志并广播，`save_game()` 抛出的
     异常照常沿游戏线程传播给 crawl 既有的错误处理，不被吞掉。
   - **SDLThread 已退出**：Java 侧只在 `mSDLThread != null` 时才发请求；万一线程
     在窗口期内消失，2 秒上界兜底，不会 ANR。

### 6.3 范围评估

- 不新建生命周期框架，不新增模块或目录，不新增持久状态。同步原语用 SDL 自带的
  `SDL_mutex` / `SDL_cond`（SDL 自己的暂停握手也用同一套原语），不引入
  `<thread>` / `<mutex>` 这类 crawl 目前未使用的依赖。
- 改动文件 4 个，全部在 `#ifdef __ANDROID__` 下：`syscalls.cc`、`syscalls.h`、
  `windowmanager-sdl.cc`、`main.cc`，加 `SDLActivity.java` 的一处空判。
- 已知的行为取舍：若游戏线程 2 秒内没有到达任何安全点（例如卡在层生成里），
  这次暂停就不存档。相对当前实现，这是用"可能少一次检查点"换掉"可能写坏存档"，
  而且崩溃后仍可回到上一次 commit（第 4 节）。
