/**
 * @file
 * @brief Wrappers for sys/libc calls, mostly for charset purposes.
**/

#include "AppHdr.h"

#include "syscalls.h"
#include <cmath>

#ifdef TARGET_OS_WINDOWS
# ifdef TARGET_COMPILER_VC
#  include <direct.h>
# endif
# define WIN32_LEAN_AND_MEAN
# include <windows.h>
# include <wincrypt.h>
# include <io.h>
#else
# include <dirent.h>
# include <langinfo.h>
# include <unistd.h>
# include <fcntl.h>
# include <sys/types.h>
# include <sys/stat.h>
#endif

#include "files.h"
#include "random.h"
#include "unicode.h"

#if defined(UNIX) && !defined(__ANDROID__)
bool ensure_utf8_ctype()
{
    const char *const current_locale = setlocale(LC_CTYPE, nullptr);
    if (!current_locale)
        return false;
    if (strcmp(current_locale, "C") && strcmp(current_locale, "POSIX"))
        return true;

    static const char *const utf8_locales[] =
    {
        "C.UTF-8", "UTF-8", "en_US.UTF-8"
    };
    for (const char *locale : utf8_locales)
    {
        if (setlocale(LC_CTYPE, locale)
            && !strcasecmp(nl_langinfo(CODESET), "UTF-8"))
        {
            return true;
        }
    }
    return false;
}
#endif

#ifdef __ANDROID__
#include <atomic>
#include "player.h"
#include "state.h"
#include "ui.h"
#include <errno.h>
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <jni.h>
#include <SDL.h>

extern "C"
{
    extern JNIEnv *Android_JNI_GetEnv(); // sigh
}

AAssetManager *_android_asset_manager = nullptr; // XXX

extern "C" JNIEXPORT void JNICALL
Java_org_libsdl_app_SDLActivity_nativeTouchScroll(
    JNIEnv*, jclass, jfloat x, jfloat y, jfloat previous_y, jfloat current_y)
{
    // SDL's Android_OnMouse hardcodes mouse ID 0, so onNativeMouse cannot
    // distinguish a finger swipe from a real wheel. Reuse SDL's touch mouse
    // source marker. This internal wheel carries previous/current surface Y
    // in x/y, consumed only by Scroller. Scale the absolute positions before
    // subtracting so slow drags do not lose a pixel on every event.
    SDL_Event events[2] = {};
    events[0].type = SDL_MOUSEMOTION;
    events[0].motion.which = SDL_TOUCH_MOUSEID;
    events[0].motion.x = static_cast<int>(x);
    events[0].motion.y = static_cast<int>(y);
    events[1].type = SDL_MOUSEWHEEL;
    events[1].wheel.which = SDL_TOUCH_MOUSEID;
    events[1].wheel.x = static_cast<int>(previous_y);
    events[1].wheel.y = static_cast<int>(current_y);
    // Add together so another producer cannot separate the origin and delta.
    SDL_PeepEvents(events, 2, SDL_ADDEVENT, SDL_FIRSTEVENT, SDL_LASTEVENT);
}

time_t jni_package_last_update_time()
{
    static time_t cached_update_time = 0;
    if (cached_update_time)
        return cached_update_time;

    JNIEnv *env = Android_JNI_GetEnv();
    jclass sdl_class = env->FindClass("org/libsdl/app/SDLActivity");
    if (!sdl_class)
        return 1;

    jmethodID get_context = env->GetStaticMethodID(
        sdl_class, "getContext", "()Landroid/content/Context;");
    jobject context = get_context
        ? env->CallStaticObjectMethod(sdl_class, get_context) : nullptr;
    if (!context || env->ExceptionCheck())
    {
        env->ExceptionClear();
        return 1;
    }

    jclass context_class = env->GetObjectClass(context);
    jmethodID get_package_manager = env->GetMethodID(
        context_class, "getPackageManager",
        "()Landroid/content/pm/PackageManager;");
    jmethodID get_package_name = env->GetMethodID(
        context_class, "getPackageName", "()Ljava/lang/String;");
    jobject package_manager = get_package_manager
        ? env->CallObjectMethod(context, get_package_manager) : nullptr;
    jstring package_name = get_package_name
        ? static_cast<jstring>(env->CallObjectMethod(context, get_package_name))
        : nullptr;

    jclass manager_class = package_manager
        ? env->GetObjectClass(package_manager) : nullptr;
    jmethodID get_package_info = manager_class
        ? env->GetMethodID(manager_class, "getPackageInfo",
                           "(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;")
        : nullptr;
    jobject package_info = get_package_info && package_name
        ? env->CallObjectMethod(package_manager, get_package_info,
                                package_name, 0)
        : nullptr;

    jclass info_class = package_info ? env->GetObjectClass(package_info)
                                     : nullptr;
    jfieldID last_update_field = info_class
        ? env->GetFieldID(info_class, "lastUpdateTime", "J") : nullptr;
    const jlong last_update_time = last_update_field
        ? env->GetLongField(package_info, last_update_field) : 0;

    if (env->ExceptionCheck())
        env->ExceptionClear();
    if (info_class)
        env->DeleteLocalRef(info_class);
    if (package_info)
        env->DeleteLocalRef(package_info);
    if (manager_class)
        env->DeleteLocalRef(manager_class);
    if (package_name)
        env->DeleteLocalRef(package_name);
    if (package_manager)
        env->DeleteLocalRef(package_manager);
    env->DeleteLocalRef(context_class);
    env->DeleteLocalRef(context);
    env->DeleteLocalRef(sdl_class);

    // PackageInfo.lastUpdateTime is milliseconds since epoch. Keeping the
    // millisecond value makes consecutive development installs distinct.
    cached_update_time = last_update_time > 0
        ? static_cast<time_t>(last_update_time) : 1;
    return cached_update_time;
}

// Deferred save for SDLActivity.onPause.
//
// save_game() walks the player, the current level, the Lua persist table and
// the save package, all of which the SDL game thread owns; running it on the
// activity's UI thread races that thread and can interleave two writers into
// one package. onPause() therefore only parks a request here, and the game
// thread performs the save itself from android_run_pending_save().
//
// The UI thread waits for the result with a bound, so a game thread that is
// busy (or already gone) delays the pause instead of hanging it.
static const Uint32 SAVE_REQUEST_TIMEOUT_MS = 2000;

// Constructed on first use, which C++11 makes thread-safe; SDL mutexes and
// condition variables do not need SDL_Init().
static SDL_mutex *_save_request_mutex()
{
    static SDL_mutex *mutex = SDL_CreateMutex();
    return mutex;
}

static SDL_cond *_save_request_cond()
{
    static SDL_cond *cond = SDL_CreateCond();
    return cond;
}

static bool save_requested = false;
static bool save_running = false;

// Everything save_game() needs in order not to trip over a half-finished
// level transition, level build, save or shutdown.
static bool _pause_save_is_safe()
{
    return you.save
        && crawl_state.need_save
        && crawl_state.game_started
        && !crawl_state.saving_game
        && !crawl_state.generating_level
        && !crawl_state.updating_scores
        && !crawl_state.game_crashed
        && !crawl_state.seen_hups
        && you.on_current_level
        && !you.entering_level;
}

// Releases onPause() even if save_game() leaves through an exception; the
// exception itself keeps propagating on the game thread as usual.
namespace
{
    struct save_run_guard
    {
        ~save_run_guard()
        {
            SDL_mutex * const mutex = _save_request_mutex();
            SDL_LockMutex(mutex);
            save_running = false;
            SDL_CondBroadcast(_save_request_cond());
            SDL_UnlockMutex(mutex);
        }
    };
}

// Called by the game thread at points where no turn is in progress.
void android_run_pending_save()
{
    SDL_mutex * const mutex = _save_request_mutex();

    SDL_LockMutex(mutex);
    if (!save_requested)
    {
        SDL_UnlockMutex(mutex);
        return;
    }
    save_requested = false;
    if (!_pause_save_is_safe())
    {
        // Skipping is safe: the package still holds everything up to the last
        // commit, so a kill after this loses progress but not the save.
        __android_log_print(ANDROID_LOG_INFO, "Crawl",
                            "pause save skipped: save=%d need_save=%d "
                            "started=%d saving=%d genlevel=%d scores=%d "
                            "crashed=%d hups=%d on_level=%d entering=%d",
                            you.save ? 1 : 0, crawl_state.need_save,
                            crawl_state.game_started, crawl_state.saving_game,
                            crawl_state.generating_level,
                            crawl_state.updating_scores,
                            crawl_state.game_crashed, crawl_state.seen_hups,
                            you.on_current_level, you.entering_level);
        SDL_CondBroadcast(_save_request_cond());
        SDL_UnlockMutex(mutex);
        return;
    }
    save_running = true;
    SDL_UnlockMutex(mutex);

    save_run_guard guard;
    save_game(false);
}

extern "C" JNIEXPORT void JNICALL
Java_org_libsdl_app_SDLActivity_nativeSaveGame(
    JNIEnv* env, jclass thiz)
{
    SDL_mutex * const mutex = _save_request_mutex();
    SDL_cond * const cond = _save_request_cond();

    SDL_LockMutex(mutex);
    save_requested = true;
    SDL_CondBroadcast(cond);

    const Uint32 deadline = SDL_GetTicks() + SAVE_REQUEST_TIMEOUT_MS;
    while (save_requested || save_running)
    {
        const Sint32 left = (Sint32)(deadline - SDL_GetTicks());
        if (left <= 0)
            break;
        SDL_CondWaitTimeout(cond, mutex, (Uint32)left);
    }
    // A request the game thread never reached would otherwise fire at some
    // arbitrary point after the activity resumed; drop it instead.
    if (save_requested || save_running)
    {
        __android_log_print(ANDROID_LOG_WARN, "Crawl",
                            "pause save timed out after %u ms (reached=%d "
                            "still_running=%d); request dropped",
                            SAVE_REQUEST_TIMEOUT_MS, save_requested ? 0 : 1,
                            save_running ? 1 : 0);
    }
    save_requested = false;
    SDL_UnlockMutex(mutex);
}

int jni_ref_display_size()
{
    JNIEnv *env = Android_JNI_GetEnv();
    jclass sdlClass = env->FindClass("org/libsdl/app/SDLActivity");

    if (!sdlClass)
        return 0;

    jmethodID mid =
        env->GetStaticMethodID(sdlClass, "jniRefDisplaySize", "()I");
    jint size = env->CallStaticIntMethod(sdlClass, mid);

    return size;
}

bool jni_keyboard_control(int action)
{
    JNIEnv *env = Android_JNI_GetEnv();
    jclass sdlClass = env->FindClass("org/libsdl/app/SDLActivity");

    if (!sdlClass)
        return false;

    jmethodID mid =
        env->GetStaticMethodID(sdlClass, "jniKeyboardControl", "(I)Z");
    jboolean shown = env->CallStaticBooleanMethod(sdlClass, mid, action);

    return shown;
}

static std::atomic<bool> input_context_refresh(false);

extern "C" JNIEXPORT void JNICALL
Java_org_libsdl_app_SDLActivity_nativeResetInputContext(JNIEnv*, jclass)
{
    // Only the event thread owns the cached descriptor. Keep a reset arriving
    // during publication pending for its next wait, rather than losing it.
    input_context_refresh.store(true);
    SDL_Event event = {};
    event.type = SDL_WINDOWEVENT;
    event.window.event = SDL_WINDOWEVENT_EXPOSED;
    SDL_PushEvent(&event); // Wake an existing wait; first startup may have none.
}

void jni_input_context(const ui::InputDescriptor& descriptor)
{
    static ui::InputDescriptor last;
    static bool sent = false;
    if (input_context_refresh.exchange(false))
        sent = false;
    if (sent && last == descriptor)
        return;
    JNIEnv *env = Android_JNI_GetEnv();
    if (!env)
        return;
    jclass sdl_class = env->FindClass("org/libsdl/app/SDLActivity");
    if (sdl_class)
    {
        jmethodID method = env->GetStaticMethodID(sdl_class, "jniInputContext",
            "(II[Ljava/lang/String;[I)V");
        if (method)
        {
            jclass string_class = env->FindClass("java/lang/String");
            jobjectArray labels = string_class
                ? env->NewObjectArray(6, string_class, nullptr) : nullptr;
            jintArray keys = labels ? env->NewIntArray(6) : nullptr;
            if (keys)
            {
                jint values[6];
                for (int i = 0; i < 6 && !env->ExceptionCheck(); ++i)
                {
                    values[i] = descriptor.actions[i].key;
                    // BMP UTF-8 without NUL agrees with JNI Modified UTF-8.
                    // InputAction labels must stay within that subset.
                    jstring label = env->NewStringUTF(descriptor.actions[i].label.c_str());
                    if (label)
                    {
                        env->SetObjectArrayElement(labels, i, label);
                        env->DeleteLocalRef(label);
                    }
                }
                if (!env->ExceptionCheck())
                {
                    env->SetIntArrayRegion(keys, 0, 6, values);
                    env->CallStaticVoidMethod(sdl_class, method,
                        static_cast<int>(descriptor.context),
                        static_cast<int>(descriptor.screen), labels, keys);
                    if (!env->ExceptionCheck())
                    {
                        last = descriptor;
                        sent = true;
                    }
                }
            }
            if (keys)
                env->DeleteLocalRef(keys);
            if (labels)
                env->DeleteLocalRef(labels);
            if (string_class)
                env->DeleteLocalRef(string_class);
        }
        env->DeleteLocalRef(sdl_class);
    }
    // An unavailable presentation bridge must not poison later JNI calls.
    if (env->ExceptionCheck())
        env->ExceptionClear();
}

// Only keys without an InputConnection character representation use this
// bridge. Queue normal SDL events; never touch the game from the UI thread.
extern "C" JNIEXPORT void JNICALL
Java_org_libsdl_app_SDLActivity_nativeKeyboardKey(JNIEnv*, jclass, jint key)
{
    SDL_Keycode sym;
    switch (key)
    {
    case CK_LEFT:  sym = SDLK_LEFT; break;
    case CK_RIGHT: sym = SDLK_RIGHT; break;
    default:
        __android_log_print(ANDROID_LOG_WARN, "AndroidKeyboard",
                            "Unsupported keyboard key: %d", static_cast<int>(key));
        return;
    }
    SDL_Event event = {};
    event.type = SDL_KEYDOWN;
    event.key.state = SDL_PRESSED;
    event.key.keysym.sym = sym;
    event.key.keysym.scancode = SDL_GetScancodeFromKey(sym);
    SDL_PushEvent(&event);
    event.type = SDL_KEYUP;
    event.key.state = SDL_RELEASED;
    SDL_PushEvent(&event);
}

float jni_get_display_density()
{
    JNIEnv *env = Android_JNI_GetEnv();
    if (!env)
        return 1.0f;
    jclass sdl_class = env->FindClass("org/libsdl/app/SDLActivity");
    float density = 1.0f;
    if (sdl_class)
    {
        jmethodID method = env->GetStaticMethodID(sdl_class, "jniDisplayDensity", "()F");
        if (method)
            density = env->CallStaticFloatMethod(sdl_class, method);
        env->DeleteLocalRef(sdl_class);
    }
    if (env->ExceptionCheck())
    {
        env->ExceptionClear();
        return 1.0f;
    }
    return std::isfinite(density) && density > 0 ? density : 1.0f;
}
#endif

bool lock_file(int fd, bool write, bool wait)
{
#ifdef TARGET_OS_WINDOWS
    OVERLAPPED pos;
    pos.hEvent     = 0;
    pos.Offset     = 0;
    pos.OffsetHigh = 0;
    return !!LockFileEx((HANDLE)_get_osfhandle(fd),
                        (write ? LOCKFILE_EXCLUSIVE_LOCK : 0) |
                        (wait ? 0 : LOCKFILE_FAIL_IMMEDIATELY),
                        0, -1, -1, &pos);
#else
    struct flock fl;
    fl.l_type = write ? F_WRLCK : F_RDLCK;
    fl.l_whence = SEEK_SET;
    fl.l_start = 0;
    fl.l_len = 0;

    return !fcntl(fd, wait ? F_SETLKW : F_SETLK, &fl);
#endif
}

bool unlock_file(int fd)
{
#ifdef TARGET_OS_WINDOWS
    return !!UnlockFile((HANDLE)_get_osfhandle(fd), 0, 0, -1, -1);
#else
    struct flock fl;
    fl.l_type = F_UNLCK;
    fl.l_whence = SEEK_SET;
    fl.l_start = 0;
    fl.l_len = 0;

    return !fcntl(fd, F_SETLK, &fl);
#endif
}

bool read_urandom(char *buf, int len)
{
#ifdef TARGET_OS_WINDOWS
    HCRYPTPROV hProvider = 0;

    if (!CryptAcquireContextW(&hProvider, 0, 0, PROV_RSA_FULL,
                              CRYPT_VERIFYCONTEXT | CRYPT_SILENT))
    {
        return false;
    }

    if (!CryptGenRandom(hProvider, len, (BYTE*)buf))
    {
        CryptReleaseContext(hProvider, 0);
        return false;
    }

    CryptReleaseContext(hProvider, 0);
    return true;
#else
    /* Try opening from various system provided (hopefully) CSPRNGs */
    FILE* seed_f = fopen("/dev/urandom", "rb");
    if (!seed_f)
        seed_f = fopen("/dev/random", "rb");
    if (!seed_f)
        seed_f = fopen("/dev/srandom", "rb");
    if (!seed_f)
        seed_f = fopen("/dev/arandom", "rb");
    if (seed_f)
    {
        int res = fread(buf, 1, len, seed_f);
        fclose(seed_f);
        return res == len;
    }

    return false;
#endif
}

#ifdef TARGET_OS_WINDOWS
# ifndef UNIX
// should check the presence of alarm() instead
static void CALLBACK _abortion(PVOID /*dummy*/, BOOLEAN /*timedout*/)
{
    TerminateProcess(GetCurrentProcess(), 0);
}

void alarm(unsigned int seconds)
{
    HANDLE dummy;
    CreateTimerQueueTimer(&dummy, 0, _abortion, 0, seconds * 1000, 0, 0);
}
# endif

# ifndef CRAWL_HAVE_FDATASYNC
// implementation by Richard W.M. Jones
// He claims this is the equivalent to fsync(), reading the MSDN doesn't seem
// to show that vital metadata is indeed flushed, others report that at least
// non-vital isn't.
int fdatasync(int fd)
{
    HANDLE h = (HANDLE)_get_osfhandle(fd);

    if (h == INVALID_HANDLE_VALUE)
    {
        errno = EBADF;
        return -1;
    }

    if (!FlushFileBuffers(h))
    {
        /* Translate some Windows errors into rough approximations of Unix
         * errors. MSDN is useless as usual - in this case it doesn't
         * document the full range of errors.
         */
        switch (GetLastError())
        {
        /* eg. Trying to fsync a tty. */
        case ERROR_INVALID_HANDLE:
            errno = EINVAL;
            break;

        default:
            errno = EIO;
        }
        return -1;
    }

    return 0;
}
# endif

# ifndef CRAWL_HAVE_MKSTEMP
int mkstemp(char *dummy)
{
    HANDLE fh;

    for (int tries = 0; tries < 100; tries++)
    {
        wchar_t filename[MAX_PATH];
        int len = GetTempPathW(MAX_PATH - 8, filename);
        ASSERT(len);
        for (int i = 0; i < 6; i++)
            filename[len + i] = 'a' + random2(26);
        filename[len + 6] = 0;
        fh = CreateFileW(filename, GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                         CREATE_NEW,
                         FILE_FLAG_DELETE_ON_CLOSE | FILE_ATTRIBUTE_TEMPORARY,
                         nullptr);
        if (fh != INVALID_HANDLE_VALUE)
            return _open_osfhandle((intptr_t)fh, 0);
    }

    die("can't create temporary file in %%TMPDIR%%");
}
# endif

#else
// non-Windows
# ifndef CRAWL_HAVE_FDATASYNC
// At least MacOS X 10.6 has it (as required by Posix) but present only
// as a symbol in the libraries without a proper header.
int fdatasync(int fd)
{
#  ifdef F_FULLFSYNC
    // On MacOS X, fsync() doesn't even try to actually do what it was asked.
    // Sane systems might have this problem only on disks that do write caching
    // but ignore flush requests. fsync() should never return before the disk
    // claims the flush completed, but this is not the case on OS X.
    //
    // Except, this is the case for internal drives only. For "external" ones,
    // F_FULLFSYNC is said to fail (at least on some versions of OS X), while
    // fsync() actually works. Thus, we need to try both.
    return fcntl(fd, F_FULLFSYNC, 0) && fsync(fd);
#  else
    return fsync(fd);
#  endif
}
# endif
#endif

// The old school way of doing short delays via low level I/O sync.
// Good for systems like old versions of Solaris that don't have usleep.
#ifndef CRAWL_HAVE_USLEEP

# ifdef TARGET_OS_WINDOWS
void usleep(unsigned long time)
{
    ASSERT(time > 0);
    ASSERT(!(time % 1000));
    Sleep(time/1000);
}
# else

#include <sys/time.h>
#include <sys/types.h>
#include <sys/unistd.h>

void usleep(unsigned long time)
{
    struct timeval timer;

    timer.tv_sec  = (time / 1000000L);
    timer.tv_usec = (time % 1000000L);

    select(0, nullptr, nullptr, nullptr, &timer);
}
# endif
#endif

#ifdef __ANDROID__
AAssetManager *_android_get_asset_manager()
{
    JNIEnv *env = Android_JNI_GetEnv();
    jclass sdlClass = env->FindClass("org/libsdl/app/SDLActivity");

    if (!sdlClass)
        return nullptr;

    jmethodID mid =
        env->GetStaticMethodID(sdlClass, "getContext",
                               "()Landroid/content/Context;");
    jobject context = env->CallStaticObjectMethod(sdlClass, mid);

    if (!context)
        return nullptr;

    mid = env->GetMethodID(env->GetObjectClass(context), "getAssets",
                           "()Landroid/content/res/AssetManager;");
    jobject assets = env->CallObjectMethod(context, mid);

    if (!assets)
        return nullptr;

    return AAssetManager_fromJava(env, assets);
}
#endif

bool file_exists(const string &name)
{
#ifdef TARGET_OS_WINDOWS
    DWORD lAttr = GetFileAttributesW(OUTW(name));
    return lAttr != INVALID_FILE_ATTRIBUTES
           && !(lAttr & FILE_ATTRIBUTE_DIRECTORY);
#else
#ifdef __ANDROID__
    if (name.find(ANDROID_ASSETS) == 0)
    {
        if (!_android_asset_manager)
            _android_asset_manager = _android_get_asset_manager();

        ASSERT(_android_asset_manager);

        AAsset* asset = AAssetManager_open(_android_asset_manager,
                                           name.substr(strlen(ANDROID_ASSETS)
                                                       + 1)
                                               .c_str(),
                                           AASSET_MODE_UNKNOWN);
        if (asset)
        {
            AAsset_close(asset);
            return true;
        }
        return false;
    }
#endif
    struct stat st;
    const int err = ::stat(OUTS(name), &st);
    return !err && S_ISREG(st.st_mode);
#endif
}

#ifdef __ANDROID__
/**
 * Remove an ANDROID_ASSETS prefix and strip any trailing slashes
 * from a directory name.
 */
static string _android_strip_dir_slash(const string &in)
{
    string out = in.substr(strlen(ANDROID_ASSETS) + 1);
    if (out.back() == '/')
        out = out.substr(0, out.length() - 1);

    return out;
}
#endif

// Low-tech existence check.
bool dir_exists(const string &dir)
{
#ifdef TARGET_OS_WINDOWS
    DWORD lAttr = GetFileAttributesW(OUTW(dir));
    return lAttr != INVALID_FILE_ATTRIBUTES
           && (lAttr & FILE_ATTRIBUTE_DIRECTORY);
#else
#ifdef __ANDROID__
    if (dir.find(ANDROID_ASSETS) == 0)
    {
        if (!_android_asset_manager)
            _android_asset_manager = _android_get_asset_manager();

        ASSERT(_android_asset_manager);

        AAssetDir* adir = AAssetManager_openDir(_android_asset_manager,
                                                _android_strip_dir_slash(dir)
                                                    .c_str());
        if (adir)
        {
            AAssetDir_close(adir);
            return true;
        }
        return false;
    }
#endif
    struct stat st;
    const int err = ::stat(OUTS(dir), &st);
    return !err && S_ISDIR(st.st_mode);
#endif
}

static inline bool _is_good_filename(const string &s)
{
    return s != "." && s != "..";
}

// Returns the names of all files in the given directory. Note that the
// filenames returned are relative to the directory.
vector<string> get_dir_files(const string &dirname)
{
    vector<string> files;

#ifdef TARGET_OS_WINDOWS
    WIN32_FIND_DATAW lData;
    string dir = dirname;
    if (!dir.empty() && dir[dir.length() - 1] != FILE_SEPARATOR)
        dir += FILE_SEPARATOR;
    dir += "*";
    HANDLE hFind = FindFirstFileW(OUTW(dir), &lData);
    if (hFind != INVALID_HANDLE_VALUE)
    {
        do
        {
            if (_is_good_filename(utf16_to_8(lData.cFileName)))
                files.push_back(utf16_to_8(lData.cFileName));
        } while (FindNextFileW(hFind, &lData));
        FindClose(hFind);
    }
#else
#ifdef __ANDROID__
    if (dirname.find(ANDROID_ASSETS) == 0)
    {
        if (!_android_asset_manager)
            _android_asset_manager = _android_get_asset_manager();

        ASSERT(_android_asset_manager);

        AAssetDir* adir =
            AAssetManager_openDir(_android_asset_manager,
                                  _android_strip_dir_slash(dirname).c_str());

        if (!adir)
            return files;

        const char *file;
        while ((file = AAssetDir_getNextFileName(adir)) != nullptr)
            files.emplace_back(file);

        AAssetDir_close(adir);
        return files;
    }
#endif
    DIR *dir = opendir(OUTS(dirname));
    if (!dir)
        return files;

    while (dirent *entry = readdir(dir))
    {
        string name = mb_to_utf8(entry->d_name);
        if (_is_good_filename(name))
            files.push_back(name);
    }
    closedir(dir);
#endif

    return files;
}

int rename_u(const char *oldpath, const char *newpath)
{
#ifdef TARGET_OS_WINDOWS
    return !MoveFileExW(OUTW(oldpath), OUTW(newpath),
                        MOVEFILE_REPLACE_EXISTING);
#else
    return rename(OUTS(oldpath), OUTS(newpath));
#endif
}

int unlink_u(const char *pathname)
{
#ifdef TARGET_OS_WINDOWS
    return _wunlink(OUTW(pathname));
#else
    return unlink(OUTS(pathname));
#endif
}

#ifdef __ANDROID__
/**
 * This implementation of handling Android fopens to Android assets
 * appears to originate from here:
 * http://www.50ply.com/blog/2013/01/19/
 *   loading-compressed-android-assets-with-file-pointer/
 */

static int _android_read(void* cookie, char* buf, int size)
{
    return AAsset_read((AAsset*)cookie, buf, size);
}

static int _android_write(void* cookie, const char* buf, int size)
{
    return EACCES; // can't provide write access to the apk
}

static fpos_t _android_seek(void* cookie, fpos_t offset, int whence)
{
    return AAsset_seek((AAsset*)cookie, offset, whence);
}

static int _android_close(void* cookie)
{
    AAsset_close((AAsset*)cookie);
    return 0;
}
#endif

FILE *fopen_u(const char *path, const char *mode)
{
#ifdef TARGET_OS_WINDOWS
    // Why it wants the mode string as double-byte is beyond me.
    return _wfopen(OUTW(path), OUTW(mode));
#else
#ifdef __ANDROID__
    if (strstr(path, ANDROID_ASSETS) == path)
    {
        if (!mode || mode[0] == 'w')
            return nullptr;

        if (!_android_asset_manager)
            _android_asset_manager = _android_get_asset_manager();

        ASSERT(_android_asset_manager);

        AAsset* asset = AAssetManager_open(_android_asset_manager,
                                           path + strlen(ANDROID_ASSETS) + 1,
                                           AASSET_MODE_RANDOM);
        if (!asset)
            return nullptr;

        return funopen(asset, _android_read, _android_write, _android_seek,
                       _android_close);
    }
#endif
    return fopen(OUTS(path), mode);
#endif
}

int mkdir_u(const char *pathname, mode_t mode)
{
#ifdef TARGET_OS_WINDOWS
    UNUSED(mode);
    return _wmkdir(OUTW(pathname));
#else
    return mkdir(OUTS(pathname), mode);
#endif
}

int open_u(const char *pathname, int flags, mode_t mode)
{
#ifdef TARGET_OS_WINDOWS
    return _wopen(OUTW(pathname), flags, mode);
#else
    return open(OUTS(pathname), flags, mode);
#endif
}
