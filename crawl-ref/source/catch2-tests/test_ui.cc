#include <random>

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "ui.h"
#include "ui-scissor.h"
#include "libutil.h"

namespace
{
struct slot_cleanup
{
    ui::Slot<int, bool()>& slot;
    int* target;
    int& destroyed;

    ~slot_cleanup()
    {
        ++destroyed;
        slot.remove_by_target(target);
    }
};
}

TEST_CASE("Slot callback destruction can remove another target", "[ui-slot]")
{
    ui::Slot<int, bool()> slot;
    // Array addresses ensure target 1 is target 0's equal_range end node.
    int targets[3] = {};
    int destroyed = 0;
    int calls = 0;
    auto captured = shared_ptr<slot_cleanup>(
        new slot_cleanup{slot, &targets[1], destroyed});
    SECTION("Destruction removes the following target") {}
    SECTION("Destruction removes the same target again")
    {
        captured->target = &targets[0];
    }
    const int removed_target = captured->target - targets;
    slot.on(&targets[0], [captured]() { return false; });
    slot.on(&targets[0], []() { return false; });
    slot.on(&targets[1], [&calls]() { ++calls; return true; });
    slot.on(&targets[2], [&calls]() { ++calls; return true; });
    captured.reset();

    slot.remove_by_target(&targets[0]);
    CHECK(destroyed == 1);
    CHECK_FALSE(slot.emit(&targets[0]));
    CHECK(slot.emit(&targets[1]) == (removed_target != 1));
    CHECK(slot.emit(&targets[2]));
    CHECK(calls == (removed_target == 1 ? 1 : 2));
    slot.remove_by_target(&targets[0]);
    CHECK(destroyed == 1);
}

// Layout-only tests do not need a GL context. Console push/pop clears a live
// terminal, so exercise these through the existing local-tiles test target.
#ifdef USE_TILE_LOCAL
namespace
{
class test_layout
{
public:
    explicit test_layout(shared_ptr<ui::Widget> widget)
    {
        ui::push_layout(std::move(widget));
    }
    ~test_layout() { ui::pop_layout(); }
};

class text_input_box : public ui::Box
{
public:
    text_input_box() : ui::Box(ui::Widget::VERT) {}
    bool accepts_text_input() const override { return true; }
};

class scroll_test_content : public ui::Widget
{
public:
    void _render() override {}
    ui::SizeReq _get_preferred_size(Direction dim, int) override
    {
        return dim == VERT ? ui::SizeReq{400, 400} : ui::SizeReq{200, 200};
    }
};
}

TEST_CASE("Finger scroll only affects a scroller at its origin", "[ui-touch]")
{
    REQUIRE_FALSE(ui::has_layout());
    CHECK_FALSE(ui::scroll_touch_at(50, 50, -30));
    auto scroller = make_shared<ui::Scroller>();
    scroller->set_child(make_shared<scroll_test_content>());
    {
        test_layout layout(scroller);
        scroller->allocate_region({0, 0, 200, 100});
        CHECK(ui::scroll_touch_at(50, 50, -30));
        CHECK(scroller->get_scroll() == 30);
        CHECK_FALSE(ui::scroll_touch_at(50, 101, -30));
        CHECK(scroller->get_scroll() == 30);
        CHECK(ui::scroll_touch_at(50, 50, 60));
        CHECK(scroller->get_scroll() == 0);
        {
            auto modal = make_shared<ui::Box>(ui::Widget::VERT);
            test_layout nested(modal);
            modal->allocate_region({0, 0, 200, 100});
            CHECK_FALSE(ui::scroll_touch_at(50, 50, -30));
            CHECK(scroller->get_scroll() == 0);
        }
        CHECK(ui::scroll_touch_at(50, 50, -30));
        CHECK(scroller->get_scroll() == 30);
    }
}

TEST_CASE("Input context follows focus and nested layout restoration", "[ui-input]")
{
    REQUIRE_FALSE(ui::has_layout());
    mouse_control command_mode(MOUSE_MODE_COMMAND);
    CHECK(ui::input_context() == ui::InputContext::GAME);
    auto text = make_shared<text_input_box>();
    auto child = make_shared<ui::Box>(ui::Widget::VERT);
    text->add_child(child);
    {
        test_layout outer(text);
        ui::set_focused_widget(child.get());
        CHECK(ui::input_context() == ui::InputContext::TEXT);
        {
            test_layout modal(make_shared<ui::Box>(ui::Widget::VERT));
            CHECK(ui::input_context() == ui::InputContext::NAVIGATION);
        }
        CHECK(ui::get_focused_widget() == child.get());
        CHECK(ui::input_context() == ui::InputContext::TEXT);
    }
    CHECK(ui::input_context() == ui::InputContext::GAME);
    {
        mouse_control target_mode(MOUSE_MODE_TARGET);
        CHECK(ui::input_context() == ui::InputContext::NAVIGATION);
    }
    CHECK(ui::input_context() == ui::InputContext::GAME);
}

TEST_CASE("Legacy text input scope does not leak into a nested menu", "[ui-input]")
{
    REQUIRE_FALSE(ui::has_layout());
    mouse_control command_mode(MOUSE_MODE_COMMAND);
    {
        ui::TextInputScope input;
        CHECK(ui::input_context() == ui::InputContext::TEXT);
        {
            test_layout menu(make_shared<ui::Box>(ui::Widget::VERT));
            CHECK(ui::input_context() == ui::InputContext::NAVIGATION);
            {
                ui::TextInputScope nested_input;
                CHECK(ui::input_context() == ui::InputContext::TEXT);
            }
            CHECK(ui::input_context() == ui::InputContext::NAVIGATION);
        }
        CHECK(ui::input_context() == ui::InputContext::TEXT);
    }
    CHECK(ui::input_context() == ui::InputContext::GAME);
}
#endif

TEST_CASE( "Test region methods", "[single-file]" ) {

    SECTION ("Test constructor parameter order is x, y, w, h") {
        const ui::Region region = {1, 2, 3, 4};

        REQUIRE(region.x == 1);
        REQUIRE(region.y == 2);
        REQUIRE(region.width == 3);
        REQUIRE(region.height == 4);
    }

    SECTION ("Test operator== requires all fields to be identical") {
        REQUIRE(ui::Region(0, 0, 0, 0) != ui::Region(0, 0, 0, 1));
        REQUIRE(ui::Region(0, 0, 0, 0) != ui::Region(0, 0, 1, 0));
        REQUIRE(ui::Region(0, 0, 0, 0) != ui::Region(0, 1, 0, 0));
        REQUIRE(ui::Region(0, 0, 0, 0) != ui::Region(1, 0, 0, 0));
    }

    SECTION ("Test emptiness checking checks width and height") {
        REQUIRE(ui::Region(0, 0, 0, 0).empty() == true);
        REQUIRE(ui::Region(0, 0, 1, 0).empty() == true);
        REQUIRE(ui::Region(0, 0, 0, 1).empty() == true);
        REQUIRE(ui::Region(0, 0, 1, 1).empty() == false);
    }

    SECTION ("Test ex() method returns right side") {
        REQUIRE(ui::Region(5, 0, 7, 0).ex() == 12);
    }

    SECTION ("Test ey() method returns bottom side") {
        REQUIRE(ui::Region(0, 3, 0, 5).ey() == 8);
    }

    SECTION ("Test contains_point ") {
        const ui::Region region = {-10, -10, 20, 20};

        // Excludes points wholly outside
        REQUIRE(region.contains_point(-20, 0) == false);
        REQUIRE(region.contains_point(20, 0) == false);
        REQUIRE(region.contains_point(0, -20) == false);
        REQUIRE(region.contains_point(0, 20) == false);

        // Top-left sides are inclusive, right-bottom sides are not.
        REQUIRE(region.contains_point(-10, 0) == true);
        REQUIRE(region.contains_point(0, -10) == true);
        REQUIRE(region.contains_point(10, 0) == false);
        REQUIRE(region.contains_point(0, 10) == false);

        REQUIRE(region.contains_point(0, 0) == true);
    }

    SECTION ("Test AABB intersection") {
        const ui::Region region1 = {21, 0, 20, 42};
        const ui::Region region2 = {-1, 2, 37, 44};

        REQUIRE(region1.aabb_intersect(region2) == ui::Region(21, 2, 15, 40));
    }

    SECTION ("Test AABB union") {
        const ui::Region region1 = {21, 0, 20, 42};
        const ui::Region region2 = {-1, 2, 37, 44};

        REQUIRE(region1.aabb_union(region2) == ui::Region(-1, 0, 42, 46));
    }
}

TEST_CASE( "Test scissor stack", "[single-file]" ) {

    SECTION ("Test that scissor stack starts out with no scissor") {
        ui::ScissorStack s;

        REQUIRE(s.top() == ui::Region(0, 0, INT_MAX, INT_MAX));
    }

#ifndef USE_TILE_LOCAL
    // Local tiles need a live GL manager; the console build exercises the
    // same stack operations without sending the resulting clip to GL.
    SECTION ("Test that scissor stack top() returns top region.") {
        ui::ScissorStack s;

        s.push(ui::Region(0, 0, 3, 3));
        REQUIRE(s.top() == ui::Region(0, 0, 3, 3));
        s.push(ui::Region(0, 0, 2, 2));
        REQUIRE(s.top() == ui::Region(0, 0, 2, 2));
        s.push(ui::Region(0, 0, 1, 1));
        REQUIRE(s.top() == ui::Region(0, 0, 1, 1));
        s.pop();
        REQUIRE(s.top() == ui::Region(0, 0, 2, 2));
    }

    SECTION ("Disjoint and touching clips stay empty and restore the parent") {
        const ui::Region parent(10, 10, 20, 20);
        const ui::Region children[] = {
            {40, 15, 5, 5}, {0, 15, 5, 5},
            {15, 40, 5, 5}, {15, 0, 5, 5},
            {30, 15, 5, 5}, {15, 30, 5, 5},
        };
        for (const auto &child : children)
        {
            ui::ScissorStack s;
            s.push(parent);
            s.push(child);
            REQUIRE(s.top().width >= 0);
            REQUIRE(s.top().height >= 0);
            REQUIRE((s.top().width == 0 || s.top().height == 0));
            const auto empty = s.top();
            s.push(parent);
            REQUIRE(s.top().width >= 0);
            REQUIRE(s.top().height >= 0);
            REQUIRE((s.top().width == 0 || s.top().height == 0));
            s.pop();
            REQUIRE(s.top() == empty);
            s.pop();
            REQUIRE(s.top() == parent);
            s.pop();
            REQUIRE(s.top() == ui::Region(0, 0, INT_MAX, INT_MAX));
        }
    }
#endif
}
