#define CATCH_CONFIG_RUNNER

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "fake-main.hpp"

#include <iostream>
#include <unistd.h>

#include "database.h"
#include "feature.h"
#include "files.h"
#include "initfile.h"
#include "mutation.h"
#include "macro.h"
#include "options.h"
#ifdef USE_TILE_LOCAL
#include "dungeon.h"
#include "startup.h"
#include "tilesdl.h"
#endif

namespace
{
bool initialise_catch_environment()
{
    if (!dir_exists("dat") || !dir_exists("dat/descript"))
    {
        std::cerr << "Catch2 must run from crawl-ref/source; required data "
                     "directories are missing." << std::endl;
        return false;
    }

    if (SysEnv.crawl_dir.empty())
    {
        char cwd[4096];
        if (!getcwd(cwd, sizeof(cwd)))
        {
            std::cerr << "Catch2 cannot determine crawl-ref/source: "
                      << strerror(errno) << std::endl;
            return false;
        }
        SysEnv.crawl_dir = cwd;
    }

    // Mirror the production ordering for shared, language-independent lookup
    // tables. Language-specific TextDB state remains fixture-owned.
    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    clua.init_libraries();
    init_keybindings();
    init_show_table();
    init_mut_index();
    i18n_cache_clear();
#ifdef USE_TILE_LOCAL
    // An empty test world has no vault placements. Rendering can inspect cells
    // beyond a fixture's local terrain, so initialise the full lookup mask.
    level_clear_vault_memory();
    // Menu construction and gameplay updates both consume Tiles resources.
    // Use the production bootstrap, including real fonts and layout, instead
    // of leaving each test to discover which UI dependency it needs.
    if (!tiles.initialise())
    {
        std::cerr << "Local-Tiles Catch2 could not initialise UI resources. "
                     "An SDL/OpenGL display is required; use a virtual "
                     "display such as xvfb-run on headless Linux hosts."
                  << std::endl;
        return false;
    }
    // The initial Tiles resize precedes character selection and can leave
    // game-screen geometry unset. Match the normal I/O startup as well.
    cio_init();
#endif
    return true;
}
}

int main(int argc, char* argv[])
{
    Catch::Session session;
    const int cli_result = session.applyCommandLine(argc, argv);
    if (cli_result != 0)
        return cli_result;

    // Catch2 metadata queries do not execute consumers of game resources.
    const auto &config = session.configData();
    if (config.showHelp || config.libIdentify || config.listTests
        || config.listTags || config.listReporters || config.listListeners)
    {
        return session.run();
    }

    if (!initialise_catch_environment())
        return 2;

    const int result = session.run();
#ifdef USE_TILE_LOCAL
    tiles.shutdown();
#endif
    databaseSystemShutdown();
    i18n_cache_clear();
    return result;
}
