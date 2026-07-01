#include "positional_format.h"
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <string>

namespace
{
    enum arg_class
    {
        AC_NONE = 0,
        AC_INT, AC_UINT, AC_LONG, AC_ULONG, AC_LLONG, AC_ULLONG,
        AC_DOUBLE, AC_STR, AC_PTR,
    };

    struct arg_value
    {
        arg_class cls = AC_NONE;
        union {
            int i; unsigned int u; long l; unsigned long ul;
            long long ll; unsigned long long ull;
            double d; const char *s; const void *p;
        } v;
    };

    struct conv_spec
    {
        int position = 0;
        arg_class cls = AC_NONE;
        std::string clean;
    };

    bool classify(const char *&p, arg_class &cls, std::string &clean)
    {
        int longs = 0;
        while (*p == 'l' || *p == 'h' || *p == 'L' || *p == 'j' || *p == 'z' || *p == 't')
        {
            if (*p == 'l') longs++;
            clean += *p;
            p++;
        }
        const char type = *p;
        if (type == '\0') return false;
        clean += type;
        p++;
        switch (type)
        {
        case 'd': case 'i':
            cls = (longs >= 2) ? AC_LLONG : (longs == 1) ? AC_LONG : AC_INT; break;
        case 'u': case 'x': case 'X': case 'o':
            cls = (longs >= 2) ? AC_ULLONG : (longs == 1) ? AC_ULONG : AC_UINT; break;
        case 'f': case 'F': case 'e': case 'E': case 'g': case 'G': case 'a': case 'A':
            cls = AC_DOUBLE; break;
        case 'c': cls = AC_INT; break;
        case 's': cls = AC_STR; break;
        case 'p': cls = AC_PTR; break;
        default: return false;
        }
        return true;
    }

    bool parse_positional(const char *&p, conv_spec &spec)
    {
        const char *q = p;
        if (*q != '%') return false;
        q++;
        if (*q < '1' || *q > '9') return false;
        int pos = 0;
        while (*q >= '0' && *q <= '9') pos = pos * 10 + (*q++ - '0');
        if (*q != '$') return false;
        q++;
        std::string clean = "%";
        while (*q == '-' || *q == '+' || *q == ' ' || *q == '#' || *q == '0')
            clean += *q++;
        if (*q == '*') return false;
        while (*q >= '0' && *q <= '9') clean += *q++;
        if (*q == '.')
        {
            clean += *q++;
            if (*q == '*') return false;
            while (*q >= '0' && *q <= '9') clean += *q++;
        }
        arg_class cls;
        if (!classify(q, cls, clean)) return false;
        spec.position = pos;
        spec.cls = cls;
        spec.clean = clean;
        p = q;
        return true;
    }

    std::string format_one(const conv_spec &spec, const arg_value &av)
    {
        char stackbuf[256];
        const char *fmt = spec.clean.c_str();
        int n = 0;
        switch (av.cls)
        {
        case AC_INT:    n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.i); break;
        case AC_UINT:   n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.u); break;
        case AC_LONG:   n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.l); break;
        case AC_ULONG:  n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.ul); break;
        case AC_LLONG:  n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.ll); break;
        case AC_ULLONG: n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.ull); break;
        case AC_DOUBLE: n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.d); break;
        case AC_STR:    n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.s ? av.v.s : "(null)"); break;
        case AC_PTR:    n = snprintf(stackbuf, sizeof stackbuf, fmt, av.v.p); break;
        default: return std::string();
        }
        if (n < 0) return std::string();
        if (n < (int)sizeof stackbuf) return std::string(stackbuf, n);
        std::vector<char> heap(n + 1);
        switch (av.cls)
        {
        case AC_INT:    snprintf(heap.data(), n + 1, fmt, av.v.i); break;
        case AC_UINT:   snprintf(heap.data(), n + 1, fmt, av.v.u); break;
        case AC_LONG:   snprintf(heap.data(), n + 1, fmt, av.v.l); break;
        case AC_ULONG:  snprintf(heap.data(), n + 1, fmt, av.v.ul); break;
        case AC_LLONG:  snprintf(heap.data(), n + 1, fmt, av.v.ll); break;
        case AC_ULLONG: snprintf(heap.data(), n + 1, fmt, av.v.ull); break;
        case AC_DOUBLE: snprintf(heap.data(), n + 1, fmt, av.v.d); break;
        case AC_STR:    snprintf(heap.data(), n + 1, fmt, av.v.s ? av.v.s : "(null)"); break;
        case AC_PTR:    snprintf(heap.data(), n + 1, fmt, av.v.p); break;
        default: break;
        }
        return std::string(heap.data(), n);
    }

}

std::string vmake_stringf_p(const char *fmt, va_list args)
{
    if (!fmt) return std::string();

    // First pass: scan for positional format specs. If any non-positional
    // % spec is mixed in (e.g. "%1$s %s"), flag as malformed and fall
    // back to standard vsnprintf. Mixed positional/non-positional is
    // undefined by POSIX and cannot be safely handled manually.
    std::vector<conv_spec> specs;
    std::vector<arg_class> pos_type;
    int max_pos = 0;
    bool malformed = false;

    for (const char *p = fmt; *p; )
    {
        if (*p != '%') { p++; continue; }
        if (p[1] == '%') { p += 2; continue; }
        conv_spec spec;
        const char *save = p;
        if (!parse_positional(p, spec))
        {
            malformed = true;
            p = save + 1;
            continue;
        }
        if (spec.position > (int)pos_type.size())
            pos_type.resize(spec.position, AC_NONE);
        arg_class &slot = pos_type[spec.position - 1];
        if (slot == AC_NONE) slot = spec.cls;
        else if (slot != spec.cls) malformed = true;
        if (spec.position > max_pos) max_pos = spec.position;
        specs.push_back(spec);
    }

    // Fall back to standard vsnprintf if no positional specs found
    // or if the format string is malformed (mixed positional + non-positional).
    if (specs.empty() || malformed)
    {
        va_list copy;
        va_copy(copy, args);
        int n = vsnprintf(nullptr, 0, fmt, copy);
        va_end(copy);
        if (n < 0) return std::string();
        std::vector<char> buf(n + 1);
        vsnprintf(buf.data(), n + 1, fmt, args);
        return std::string(buf.data(), n);
    }

    // Read ALL args from va_list first, even for AC_NONE (dropped) positions.
    // This is required because glibc vsnprintf aborts on sparse %N$s like
    // %2$s without %1$s — common in CN Mode 2b translations. For dropped
    // positions we consume via uintptr_t (pointer-sized, safe for all arg
    // types passed to mprf_p in DCSS: const char* and int).
    std::vector<arg_value> values(max_pos);
    for (int i = 0; i < max_pos; i++)
    {
        arg_value &av = values[i];
        av.cls = pos_type[i];
        switch (av.cls)
        {
        case AC_INT:    av.v.i = va_arg(args, int); break;
        case AC_UINT:   av.v.u = va_arg(args, unsigned int); break;
        case AC_LONG:   av.v.l = va_arg(args, long); break;
        case AC_ULONG:  av.v.ul = va_arg(args, unsigned long); break;
        case AC_LLONG:  av.v.ll = va_arg(args, long long); break;
        case AC_ULLONG: av.v.ull = va_arg(args, unsigned long long); break;
        case AC_DOUBLE: av.v.d = va_arg(args, double); break;
        case AC_STR:    av.v.s = va_arg(args, const char *); break;
        case AC_PTR:    av.v.p = va_arg(args, const void *); break;
        default:
            va_arg(args, uintptr_t);
            break;
        }
    }

    // Manual formatting — args already consumed above.
    std::string out;
    size_t spec_idx = 0;
    for (const char *p = fmt; *p; )
    {
        if (*p != '%') { out += *p++; continue; }
        if (p[1] == '%') { out += '%'; p += 2; continue; }
        const conv_spec &spec = specs[spec_idx++];
        if (spec.position > 0 && spec.position <= max_pos
            && values[spec.position - 1].cls != AC_NONE)
        {
            out += format_one(spec, values[spec.position - 1]);
        }
        conv_spec skip;
        parse_positional(p, skip);
    }
    return out;
}

std::string make_stringf_p(const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    std::string s = vmake_stringf_p(fmt, args);
    va_end(args);
    return s;
}
