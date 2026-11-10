#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "artefact.h"
#include "art-enum.h"
#include "items.h"
#include "item-prop.h"
#include "item-prop-enum.h"
#include "item-status-flag-type.h"
#include "invent.h"
#include "env.h"
#include "transform.h"
#include "unwind.h"
#include "player-equip.h"
#include "potion-type.h"
#include "player.h"

#include "test_player_fixture.h"

TEST_CASE( "Create item def", "[single-file]" ) {
    item_def foo;
}

TEST_CASE( "Create a specific item def", "[single-file]" ) {
    item_def scroll_of_fear;

    get_item_by_exact_name(scroll_of_fear, "scroll of fear");

    REQUIRE(scroll_of_fear.base_type == OBJ_SCROLLS);
    REQUIRE(scroll_of_fear.sub_type == SCR_FEAR);
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Check mock player has no items", "[single-file]" ) {
    for (int i=0; i < ENDOFPACK; i++)
        REQUIRE(you.inv[i].base_type == OBJ_UNASSIGNED);

    REQUIRE(!any_items_of_type(OSEL_ANY));

}

static item_def simple_create_item(object_class_type base_type,
                                   int sub_type, int plus = 0,
                                   special_armour_type ego = SPARM_NORMAL);

static item_def simple_create_item(object_class_type base_type,
                                   int sub_type, int plus,
                                   special_armour_type ego){
    item_def item;

    item.clear();

    item.base_type = base_type;
    item.sub_type = sub_type;
    item.quantity = 1;
    item.plus = plus;
    item.brand = ego;

    return item;
}

static int find_inv_index_with_exact_item(object_class_type base_type, int sub_type){

    for (int i=0; i < ENDOFPACK; i++)
    {
        item_def item = you.inv[i];
        if (item.base_type == base_type
               && item.sub_type == sub_type)
        {
            return i;
        }
    }

    return -1;
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Give mock player item", "[single-file]" ) {
    item_def scroll_of_fear;

    get_item_by_exact_name(scroll_of_fear, "scroll of fear");

    move_item_to_inv(scroll_of_fear);

    REQUIRE(any_items_of_type(OSEL_ANY));

    int num_fear_stacks_in_invent = 0;

    for (int i=0; i < ENDOFPACK; i++)
    {
        item_def item = you.inv[i];
        if (item.base_type == OBJ_SCROLLS
               && item.sub_type == SCR_FEAR)
        {
            num_fear_stacks_in_invent++;
        }
    }

    REQUIRE(num_fear_stacks_in_invent == 1);
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Mock player armour skill", "[single-file]" ) {
    REQUIRE(you.skill(SK_ARMOUR,20) == 0);
    REQUIRE(you.strength() == 11);
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Give mock armour", "[single-file]" ) {

    item_def armour = simple_create_item(OBJ_ARMOUR, ARM_SCALE_MAIL);

    move_item_to_inv(armour);

    REQUIRE(you.base_ac_from(armour, 100) == 600);

    REQUIRE(any_items_of_type(OSEL_ANY));

    int num_armours = 0;

    for (int i=0; i < ENDOFPACK; i++)
    {
        item_def item = you.inv[i];
        if (item.base_type == OBJ_ARMOUR
               && item.sub_type == ARM_SCALE_MAIL)
        {
            num_armours++;
        }
    }

    REQUIRE(num_armours == 1);

    REQUIRE(you.base_ac(100) == 0);
}

static void make_and_equip_item(object_class_type base_type, int sub_type,
                                int plus = 0,
                                special_armour_type ego = SPARM_NORMAL);

static void find_and_equip_exact_item(item_def item){
    move_item_to_inv(item);

    int index =
        find_inv_index_with_exact_item(item.base_type, item.sub_type);

    REQUIRE(index != -1);

    equip_item(get_all_item_slots(item)[0], index);
}

static void make_and_equip_item(object_class_type base_type, int sub_type,
                                int plus, special_armour_type ego){

    item_def item = simple_create_item(base_type, sub_type, plus,
                                       ego);
    find_and_equip_exact_item(item);

}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Give mock armour and check after after putting it on",
                  "[single-file]" ) {

    make_and_equip_item(OBJ_ARMOUR, ARM_SCALE_MAIL);

    REQUIRE(you.base_ac(100) == 600);
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Give mock robe and check after after putting it on",
                  "[single-file]" ) {

    make_and_equip_item(OBJ_ARMOUR, ARM_ROBE);

    REQUIRE(you.base_ac(100) == 200);
}

TEST_CASE_METHOD( MockPlayerYouTestsFixture,
                  "Give multiple mock items and check after putting it on",
                  "[single-file]" ) {

    make_and_equip_item(OBJ_ARMOUR, ARM_FIRE_DRAGON_ARMOUR);
    make_and_equip_item(OBJ_ARMOUR, ARM_HELMET);
    make_and_equip_item(OBJ_ARMOUR, ARM_BOOTS);
    make_and_equip_item(OBJ_ARMOUR, ARM_GLOVES);
    make_and_equip_item(OBJ_ARMOUR, ARM_CLOAK);

    REQUIRE(you.base_ac(100) == 1200);
}

TEST_CASE("armour_prop_test", "[single-file]"){
    REQUIRE(armour_prop(ARM_SCALE_MAIL, PARM_AC) == 6);
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Sanguine talisman flight returns after bat swarm",
                 "[single-file][transform][upstream-5499]")
{
    unwind_var<dungeon_feature_type> floor(env.grid(you.pos()), DNGN_FLOOR);
    const bool grants_flight = GENERATE(false, true);
    item_def talisman = simple_create_item(OBJ_TALISMANS, TALISMAN_VAMPIRE);
    // Use a deterministic randart, with flight as its only possible property.
    talisman.flags |= ISFLAG_RANDART | ISFLAG_IDENTIFIED;
    CrawlVector &props = talisman.props[ARTEFACT_PROPS_KEY].new_vector(SV_SHORT);
    props.resize(ART_PROPERTIES);
    props.set_max_size(ART_PROPERTIES);
    for (vec_size i = 0; i < ART_PROPERTIES; ++i)
        props[i].get_short() = 0;
    artefact_set_property(talisman, ARTP_FLY, grants_flight);
    move_item_to_inv(talisman);
    const int index = find_inv_index_with_exact_item(OBJ_TALISMANS, TALISMAN_VAMPIRE);
    REQUIRE(index != -1);
    you.cur_talisman = index;
    you.default_form = transformation::vampire;
    REQUIRE(transform(0, you.default_form, true, true));
    REQUIRE(you.airborne() == grants_flight);

    for (int cycle = 0; cycle < 2; ++cycle)
    {
        REQUIRE(transform(15, transformation::bat_swarm, true));
        REQUIRE(you.airborne());
        CHECK(you.equip_flight() == 0);

        return_to_default_form();
        CHECK(you.form == transformation::vampire);
        CHECK(you.equip_flight() == int(grants_flight));
        CHECK(you.attribute[ATTR_PERM_FLIGHT] == int(grants_flight));
        CHECK(you.airborne() == grants_flight);
        CHECK(artefact_property(you.inv[index], ARTP_FLY) == int(grants_flight));
    }
}

TEST_CASE("Test all_item_subtypes() does not include removed items",
          "[single-file]") {
    const auto items = all_item_subtypes(OBJ_POTIONS);

    const auto has_removed_item = find(items.begin(), items.end(), POT_POISON) != items.end();

    REQUIRE(has_removed_item == false);

#if TAG_MAJOR_VERSION == 34
    const auto armour = all_item_subtypes(OBJ_ARMOUR);
    const int removed_hides[] = {
        ARM_TROLL_HIDE,
        ARM_FIRE_DRAGON_HIDE,
        ARM_ICE_DRAGON_HIDE,
        ARM_STEAM_DRAGON_HIDE,
        ARM_ACID_DRAGON_HIDE,
        ARM_STORM_DRAGON_HIDE,
        ARM_GOLDEN_DRAGON_HIDE,
        ARM_SWAMP_DRAGON_HIDE,
        ARM_PEARL_DRAGON_HIDE,
        ARM_SHADOW_DRAGON_HIDE,
        ARM_QUICKSILVER_DRAGON_HIDE,
    };
    for (const int hide : removed_hides)
    {
        INFO("removed armour subtype: " << hide);
        CHECK(item_type_removed(OBJ_ARMOUR, hide));
        CHECK(find(armour.begin(), armour.end(), hide) == armour.end());
    }
#endif
}

TEST_CASE("Test all_item_subtypes() does include items for each category",
          "[single-file]") {
    // Note: CORPSES and RODS do not have any sub-items, so are excluded.
    REQUIRE(all_item_subtypes(OBJ_WEAPONS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_MISSILES).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_ARMOUR).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_WANDS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_SCROLLS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_JEWELLERY).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_POTIONS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_BOOKS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_STAVES).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_ORBS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_MISCELLANY).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_GOLD).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_RUNES).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_TALISMANS).size() > 0);
    REQUIRE(all_item_subtypes(OBJ_GEMS).size() > 0);
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Fortress safety checks preserve bound two-handed weapons",
                 "[single-file][transform][upstream-5530]")
{
    unwind_var<dungeon_feature_type> floor(env.grid(you.pos()), DNGN_FLOOR);
    auto equip = [](object_class_type base, int subtype)
    {
        item_def item = simple_create_item(base, subtype);
        move_item_to_inv(item);
        const int index = find_inv_index_with_exact_item(base, subtype);
        REQUIRE(index != -1);
        autoequip_item(you.inv[index]);
    };
    equip(OBJ_WEAPONS, WPN_GREAT_SWORD);
    item_def* weapon = you.weapon();
    REQUIRE(weapon);
    weapon->flags |= ISFLAG_CURSED;

    // Entering fortress form must not mistake the melded offhand overflow
    // for removal of the weapon.
    CHECK_FALSE(transforming_is_unsafe(transformation::fortress_crab));
    CHECK(you.form == transformation::none);
    CHECK(you.equipment.get_slot_entries(SLOT_OFFHAND).size() == 1);

    // Model the equipment layout produced by entering fortress form.
    you.form = you.default_form = transformation::fortress_crab;
    you.equipment.shift_twohander_to_slot(SLOT_TWOHANDER_ONLY);
    you.equipment.update();
    REQUIRE(you.equipment.get_slot_entries(SLOT_TWOHANDER_ONLY).size() == 1);

    SECTION("Removing the talisman keeps the bound weapon")
    {
        CHECK_FALSE(transforming_is_unsafe(transformation::none));
    }
    SECTION("Changing to another weapon-using form keeps the bound weapon")
    {
        CHECK_FALSE(transforming_is_unsafe(transformation::statue));
    }
    SECTION("A bound shield still prevents losing the extra hand")
    {
        equip(OBJ_ARMOUR, ARM_KITE_SHIELD);
        item_def* shield = you.shield();
        REQUIRE(shield);
        shield->flags |= ISFLAG_CURSED;
        CHECK(transforming_is_unsafe(transformation::none));
        CHECK(you.shield() == shield);
        // Fixture teardown must not destroy an artificially cursed item.
        shield->flags &= ~ISFLAG_CURSED;
    }

    // The safety simulation must leave the real equipment/form untouched.
    CHECK(you.form == transformation::fortress_crab);
    CHECK(you.default_form == transformation::fortress_crab);
    CHECK(you.equipment.get_slot_entries(SLOT_TWOHANDER_ONLY).size() == 1);
    CHECK(you.weapon() == weapon);
    CHECK(weapon->cursed());
    weapon->flags &= ~ISFLAG_CURSED;
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Fisticloak needs two distinct haunted aux slots",
                 "[single-file][equipment][upstream-5378]")
{
    const int occupied = GENERATE(4, 5, 6);
    const int removable = GENERATE(0, 1, 2, 6);
    CAPTURE(occupied, removable);

    // Model a poltergeist's six interchangeable aux slots. Keep this layout
    // local: slot planning must neither equip nor remove any real items.
    player_equip_set equipment;
    equipment.num_slots.init(0);
    equipment.num_slots[SLOT_HAUNTED_AUX] = 6;
    for (int i = 0; i < occupied; ++i)
    {
        item_def& item = you.inv[i];
        item = simple_create_item(OBJ_ARMOUR, ARM_CLOAK);
        item.link = i;
        item.pos = ITEM_IN_INVENTORY;
        if (i >= removable)
            item.flags |= ISFLAG_CURSED;
        equipment.add(item, SLOT_HAUNTED_AUX);
    }

    item_def cloak;
    REQUIRE(make_item_unrandart(cloak, UNRAND_FISTICLOAK));
    const bool can_fit = 6 - occupied + min(occupied, removable) >= 2;
    bool requires_replace = false;
    const equipment_slot slot =
        equipment.find_slot_to_equip_item(cloak, requires_replace);
    CHECK((slot != SLOT_UNUSED || requires_replace) == can_fit);
    CHECK(requires_replace == (can_fit && occupied > 4));
    if (occupied <= 4)
        CHECK(slot == SLOT_HAUNTED_AUX);
    else if (!can_fit)
        CHECK(slot == SLOT_UNUSED);

    // Equipment preview may ignore curses, but must still reserve two slots.
    equipment.find_slot_to_equip_item(cloak, requires_replace, true);
    CHECK(requires_replace == (occupied > 4));
    CHECK(equipment.items.size() == static_cast<size_t>(occupied));
    CHECK(equipment.num_slots[SLOT_HAUNTED_AUX] == 6);
}
