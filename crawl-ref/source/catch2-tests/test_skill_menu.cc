/**
 * @file
 * @brief Ownership regression for upstream #5413.
**/

#include "AppHdr.h"

#include "catch_amalgamated.hpp"
#include "skill-menu.h"
#include "test_player_fixture.h"

extern SkillMenu skm;

// Local tiles needs an initialized font; console exercises the same bounds
// rejection and ownership path without a window system.
#ifndef USE_TILE_LOCAL
namespace
{
class TrackedSkillText : public TextItem
{
public:
    explicit TrackedSkillText(int& destroyed) : m_destroyed(destroyed) {}
    ~TrackedSkillText() override { ++m_destroyed; }

private:
    int& m_destroyed;
};

struct SkillMenuCleanup
{
    ~SkillMenuCleanup() { skm.clear(); }
};
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Skill menu retains rejected items until cleanup",
                 "[skill-menu]")
{
    int attached_destroyed = 0;
    int rejected_destroyed = 0;
    SkillMenuCleanup cleanup;

    // Reinitializing the menu on layout changes must also release rejected
    // items from the previous allocation.
    for (int pass = 0; pass < 2; ++pass)
    {
        skm.init(0, 24);
        auto attached = new TrackedSkillText(attached_destroyed);
        auto rejected = new TrackedSkillText(rejected_destroyed);
        coord_def inside(2, 2);
        coord_def outside(2, -1);
        skm.add_item(attached, 1, inside);
        skm.add_item(rejected, 1, outside);

        // Callers continue updating even items that cannot be displayed.
        attached->set_text("attached");
        rejected->set_text("rejected");
        CHECK(attached->get_text() == "attached");
        CHECK(rejected->get_text() == "rejected");
        CHECK(attached_destroyed == pass);
        CHECK(rejected_destroyed == pass);

        skm.clear();
        CHECK(attached_destroyed == pass + 1);
        CHECK(rejected_destroyed == pass + 1);
        skm.clear();
        CHECK(attached_destroyed == pass + 1);
        CHECK(rejected_destroyed == pass + 1);
    }
}
#endif
