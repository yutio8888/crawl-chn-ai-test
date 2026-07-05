#include "AppHdr.h"
#include "zh-scroll-appearance.h"

const char* const scroll_binding_zh[] =
{
    "红绸带",    // SBI_RED_SILK
    "蓝绸带",    // SBI_BLUE_SILK
    "麻绳",      // SBI_HEMP_CORD
    "金丝线",    // SBI_GOLD_THREAD
    "银丝线",    // SBI_SILVER_THREAD
    "皮绳",      // SBI_LEATHER_CORD
    "绿绸带",    // SBI_GREEN_SILK
    "紫绸带",    // SBI_PURPLE_SILK
    "黑丝线",    // SBI_BLACK_THREAD
    "白绸带",    // SBI_WHITE_SILK
    "铜链",      // SBI_COPPER_CHAIN
    "素色带",    // SBI_PLAIN_BAND
};
COMPILE_CHECK(ARRAYSZ(scroll_binding_zh) == NDSC_SCROLL_BINDING);

const char* const scroll_seal_zh[] =
{
    "蜡封",      // SSE_WAX
    "金箔封",    // SSE_GOLD_FOIL
    "银箔封",    // SSE_SILVER_FOIL
    "骨扣",      // SSE_BONE_CLASP
    "玉扣",      // SSE_JADE_CLASP
    "铜扣",      // SSE_COPPER_CLASP
    "锡封",      // SSE_TIN
    "火漆印",    // SSE_SEALING_WAX
    "符纸封",    // SSE_TALISMAN
    "",          // SSE_NONE — empty string, omitted during assembly
};
COMPILE_CHECK(ARRAYSZ(scroll_seal_zh) == NDSC_SCROLL_SEAL);
