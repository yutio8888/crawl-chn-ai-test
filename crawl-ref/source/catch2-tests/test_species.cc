#include "catch_amalgamated.hpp"

#include "AppHdr.h"
#include "initfile.h"
#include "jobs.h"
#include "newgame-def.h"
#include "species.h"
#include "test_zh_fixture.h"

static string _serialize_prefs(const newgame_def& prefs)
{
    FILE* file = tmpfile();
    REQUIRE(file);
    prefs.write_prefs(file);
    REQUIRE(fflush(file) == 0);
    rewind(file);

    string result;
    char buffer[1024];
    while (const size_t count = fread(buffer, 1, sizeof(buffer), file))
        result.append(buffer, count);
    REQUIRE(ferror(file) == 0);
    fclose(file);
    return result;
}

static void _check_prefs_protocol_names()
{
    for (int i = 0; i < NUM_SPECIES; ++i)
    {
        const auto sp = static_cast<species_type>(i);
        if (!species::is_starting_species(sp))
            continue;

        newgame_def prefs;
        prefs.species = sp;
        const string output = _serialize_prefs(prefs);
        INFO("species " << species::name(sp, species::SPNAME_PLAIN, true));
        REQUIRE(output.find("species = "
                    + species::name(sp, species::SPNAME_PLAIN, true) + "\n")
                != string::npos);
    }

    for (int i = 0; i < NUM_JOBS; ++i)
    {
        const auto job = static_cast<job_type>(i);
        if (!is_starting_job(job))
            continue;

        newgame_def prefs;
        prefs.job = job;
        const string output = _serialize_prefs(prefs);
        INFO("job " << get_job_name_en(job));
        REQUIRE(output.find(string("background = ") + get_job_name_en(job) + "\n")
                != string::npos);
    }
}

TEST_CASE( "Random draconian species are not removed", "[single-file]" ) {
    for (int i = 0; i < 100; ++i)
    {
        auto species = species::random_draconian_colour();
        REQUIRE( !species::is_removed(species) );
    }
}

TEST_CASE( "Random draconian species are derived draconians", "[single-file]" ) {
    for (int i = 0; i < 100; ++i)
    {
        auto species = species::random_draconian_colour();
        REQUIRE( species::is_draconian(species) );
        REQUIRE( species != SP_BASE_DRACONIAN );
    }
}

TEST_CASE("Legacy Chinese species aliases do not require i18n",
          "[species][prefs]")
{
    // Catch2 starts in English and does not initialise the Chinese TextDB.
    REQUIRE(species::from_str("豺狼人") == SP_GNOLL);

    const pair<const char*, species_type> migration_aliases[] = {
        { "高等精灵", SP_HIGH_ELF }, { "污泥精灵", SP_SLUDGE_ELF },
        { "半身人", SP_HALFLING }, { "深矮人", SP_DEEP_DWARF },
        { "熔岩兽人", SP_LAVA_ORC },
        { "鱼人", SP_MERFOLK }, { "人鱼", SP_MERFOLK },
        { "猫人", SP_FELID }, { "猫", SP_FELID },
        { "章鱼人", SP_OCTOPODE }, { "章鱼", SP_OCTOPODE },
        { "强风半人马", SP_MAYFLYTAUR }, { "蜉蝣半人马", SP_MAYFLYTAUR },
    };
    for (const auto& alias : migration_aliases)
    {
        INFO(alias.first);
        REQUIRE(species::from_str(alias.first) == alias.second);
    }
}

TEST_CASE("Startup preference protocol accepts stable choices",
          "[species][prefs]")
{
    REQUIRE(str_to_species("Gnoll") == SP_GNOLL);
    REQUIRE(str_to_species("豺狼人") == SP_GNOLL);
    REQUIRE(str_to_job("Fighter") == JOB_FIGHTER);
    REQUIRE(str_to_job("战士") == JOB_FIGHTER);
    REQUIRE(str_to_species("random") == SP_RANDOM);
    REQUIRE(str_to_species("viable") == SP_VIABLE);
    REQUIRE(str_to_job("random") == JOB_RANDOM);
    REQUIRE(str_to_job("viable") == JOB_VIABLE);
}

TEST_CASE("Startup preference writer uses English protocol names",
          "[species][prefs]")
{
    _check_prefs_protocol_names();

    newgame_def prefs;
    prefs.species = SP_RANDOM;
    prefs.job = JOB_VIABLE;
    const string output = _serialize_prefs(prefs);
    REQUIRE(output.find("species = random\n") != string::npos);
    REQUIRE(output.find("background = viable\n") != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Startup preference writer uses English names in Chinese mode",
                 "[species][prefs][zh]")
{
    REQUIRE(species::name(SP_GNOLL) == "豺狼人");
    REQUIRE(string(get_job_name(JOB_FIGHTER)) == "战士");
    _check_prefs_protocol_names();
}
