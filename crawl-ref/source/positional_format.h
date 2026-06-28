#pragma once
#include <string>
#include <cstdarg>
std::string vmake_stringf_p(const char *fmt, va_list args);
std::string make_stringf_p(const char *fmt, ...);
