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
#include "options.h"

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
    init_show_table();
    init_mut_index();
    i18n_cache_clear();
    return true;
}
}

int main(int argc, char* argv[])
{
    if (!initialise_catch_environment())
        return 2;

    const int result = Catch::Session().run(argc, argv);
    databaseSystemShutdown();
    i18n_cache_clear();
    return result;
}
