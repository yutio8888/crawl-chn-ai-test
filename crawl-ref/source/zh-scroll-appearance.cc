#include "AppHdr.h"
#include "zh-scroll-appearance.h"

#include "i18n.h"
#include "options.h"
#include "stringutil.h"

// These are stable keys indexed by saved appearance seeds, never translated
// pointers. Resolve only after selecting the binding and seal for display.
static const char * const _scroll_binding_keys[] =
{
    NC_("scroll binding", "red silk ribbon"),
    NC_("scroll binding", "blue silk ribbon"),
    NC_("scroll binding", "hemp cord"),
    NC_("scroll binding", "gold thread"),
    NC_("scroll binding", "silver thread"),
    NC_("scroll binding", "leather cord"),
    NC_("scroll binding", "green silk ribbon"),
    NC_("scroll binding", "purple silk ribbon"),
    NC_("scroll binding", "black thread"),
    NC_("scroll binding", "white silk ribbon"),
    NC_("scroll binding", "copper chain"),
    NC_("scroll binding", "plain band")
};
COMPILE_CHECK(ARRAYSZ(_scroll_binding_keys) == NDSC_SCROLL_BINDING);

static const char * const _scroll_seal_keys[] =
{
    NC_("scroll seal", "wax seal"),
    NC_("scroll seal", "gold foil seal"),
    NC_("scroll seal", "silver foil seal"),
    NC_("scroll seal", "bone clasp"),
    NC_("scroll seal", "jade clasp"),
    NC_("scroll seal", "copper clasp"),
    NC_("scroll seal", "tin seal"),
    NC_("scroll seal", "sealing wax stamp"),
    NC_("scroll seal", "talisman seal"),
    "", // SSE_NONE is structural absence, not a translatable descriptor.
};
COMPILE_CHECK(ARRAYSZ(_scroll_seal_keys) == NDSC_SCROLL_SEAL);

string translated_scroll_appearance(uint32_t seed)
{
    if (Options.language != lang_t::ZH)
        return "";

    // Preserve the established mapping from subtype_rnd without consuming RNG.
    const int binding = (seed >> 4) % NDSC_SCROLL_BINDING;
    const int seal = (seed >> 12) % NDSC_SCROLL_SEAL;
    const char *binding_key = _scroll_binding_keys[binding];
    const char *seal_key = _scroll_seal_keys[seal];
    const string binding_name = C_("scroll binding", binding_key);
    const string seal_name = C_("scroll seal", seal_key);
    const string format = C_("scroll appearance", "%s%s scroll");

    // A missing selected component or template must not produce a mixed name.
    // The caller falls back to the ordinary deterministic English scroll label.
    if (binding_name == binding_key
        || seal != SSE_NONE && seal_name == seal_key
        || format == "%s%s scroll")
    {
        return "";
    }
    return make_stringf(format.c_str(), binding_name.c_str(), seal_name.c_str());
}
