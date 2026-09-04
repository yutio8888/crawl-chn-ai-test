package org.develz.crawl;

import android.content.res.Configuration;
import android.os.Bundle;

import org.libsdl.app.SDLActivity;

import java.util.Locale;

/*
 * SDLActivity for Dungeon Crawl Stone Soup
 */
public class DungeonCrawlStoneSoup extends SDLActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Configuration configuration = new Configuration(
                getResources().getConfiguration());
        configuration.setLocale(Locale.SIMPLIFIED_CHINESE);
        getResources().updateConfiguration(
                configuration, getResources().getDisplayMetrics());
        super.onCreate(savedInstanceState);
    }

    @Override
    protected String[] getLibraries() {
        return new String[] {
                "c++_shared",
                "SDL2",
                "SDL2_image",
                "mikmod",
                "smpeg2",
                "SDL2_mixer",
                "sqlite",
                "lua",
                "zlib",
                "main"
        };
    }

}
