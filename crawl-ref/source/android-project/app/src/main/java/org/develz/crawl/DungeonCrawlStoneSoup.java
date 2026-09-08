package org.develz.crawl;

import android.content.pm.ActivityInfo;
import android.content.res.Configuration;

import org.libsdl.app.SDLActivity;

/*
 * SDLActivity for Dungeon Crawl Stone Soup
 */
public class DungeonCrawlStoneSoup extends SDLActivity {

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Keep SDL and the selected keyboard layouts alive. Key heights are
        // launcher-supplied pixels; fontScale changes only the button text.
        if (mKeyboard != null) {
            mKeyboard.refreshTextSizes();
        }
        if (mKeyboardExtra != null) {
            mKeyboardExtra.refreshTextSizes();
        }
    }

    @Override
    public void setOrientationBis(int w, int h, boolean resizable, String hint) {
        // Keep SDL window hints from overriding the app's portrait layout.
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
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
