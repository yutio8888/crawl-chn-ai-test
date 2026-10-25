#include "AppHdr.h"
#include "zh-scroll-appearance.h"

#include "describe.h"
#include "i18n.h"
#include "item-prop-enum.h"
#include "options.h"
#include "player.h"
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

// A unique saved label seed does not imply a unique physical description.
// Reserve the original slots first, then place colliding seeds in unused
// slots. The saved registry is complete before play, so the result never
// depends on discovery/identification order, language switches or item order.
static int _scroll_appearance_slot(uint32_t seed)
{
    constexpr int count = NDSC_SCROLL_BINDING * NDSC_SCROLL_SEAL;
    COMPILE_CHECK(NUM_SCROLLS <= count);
    const auto original_slot = [](uint32_t value) {
        return ((value >> 12) % NDSC_SCROLL_SEAL) * NDSC_SCROLL_BINDING
               + (value >> 4) % NDSC_SCROLL_BINDING;
    };
    vector<uint32_t> seeds;
    for (int type = 0; type < NUM_SCROLLS; ++type)
    {
        const uint32_t value = you.item_description[IDESC_SCROLLS][type];
        if (value != 255) // Uninitialized registry entries are not appearances.
            seeds.push_back(value);
    }
    sort(seeds.begin(), seeds.end());
    seeds.erase(unique(seeds.begin(), seeds.end()), seeds.end());
    if (!binary_search(seeds.begin(), seeds.end(), seed))
        return original_slot(seed);

    bool used[count] = {};
    vector<int> slots(seeds.size(), -1);
    for (size_t i = 0; i < seeds.size(); ++i)
    {
        const int slot = original_slot(seeds[i]);
        if (!used[slot])
        {
            slots[i] = slot;
            used[slot] = true;
        }
    }
    for (size_t i = 0; i < seeds.size(); ++i)
    {
        if (slots[i] != -1)
            continue;
        int slot = original_slot(seeds[i]);
        while (used[slot])
            slot = (slot + 1) % count;
        slots[i] = slot;
        used[slot] = true;
    }
    return slots[lower_bound(seeds.begin(), seeds.end(), seed) - seeds.begin()];
}

string translated_scroll_appearance(uint32_t seed)
{
    if (Options.language != lang_t::ZH)
        return "";

    const int slot = _scroll_appearance_slot(seed);
    const int binding = slot % NDSC_SCROLL_BINDING;
    const int seal = slot / NDSC_SCROLL_BINDING;
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
