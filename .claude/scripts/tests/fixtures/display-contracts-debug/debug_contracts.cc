void debug_display_contracts()
{
#if 0
    simple_god_message("Dead if-zero message.");
#else
    simple_god_message("Live if-zero else message.");
#endif

#ifdef DEBUG_XOM
    simple_god_message("Dead debug message.");
#else
    simple_god_message("Live debug else message.");
#endif

#ifndef DEBUG_XOM
    simple_god_message("Live ifndef-debug message.");
#else
    simple_god_message("Dead ifndef-debug else message.");
#endif

#if 0
    simple_god_message("Dead elif prelude message.");
#elif 1
    simple_god_message("Live elif-one message.");
#else
    simple_god_message("Dead elif else message.");
#endif

#if UNKNOWN_BUILD_FLAG
    simple_god_message("Fail-open unknown branch message.");
#else
    simple_god_message("Fail-open unknown else message.");
#endif

#if 0
# if 1
    simple_god_message("Dead nested inner message.");
# else
    simple_god_message("Dead nested inner else message.");
# endif
#else
# if 0
    simple_god_message("Dead nested live-parent message.");
# else
    simple_god_message("Live nested else message.");
# endif
#endif
}
