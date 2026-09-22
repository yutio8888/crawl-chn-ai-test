package org.develz.crawl;

import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.util.TypedValue;

import org.libsdl.app.SDLActivity;

/*
 * SDLActivity for Dungeon Crawl Stone Soup
 */
public class DungeonCrawlStoneSoup extends SDLActivity {

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Keep SDL and the selected keyboard layouts alive. Refit key rows
        // for the new font metrics before the next view traversal.
        if (mKeyboard != null) {
            mKeyboard.refreshTextSizes();
        }
        if (mKeyboardExtra != null) {
            mKeyboardExtra.refreshTextSizes();
        }
        // Repaint SDL after the Android view traversal has applied the new
        // text metrics, even when the native surface dimensions are unchanged.
        getWindow().getDecorView().post(() -> {
            if (mSingleton == this && !mBrokenLibraries && mIsSurfaceReady) {
                nativeRequestRedraw();
            }
        });
    }

    // Native font sizing reads this at the point of layout; use current
    // resources so Android 14 nonlinear SP scaling and configuration changes
    // are reflected instead of caching scaledDensity or a startup font size.
    public static float jniReadingFontPixels() {
        Resources resources = mSingleton == null ? Resources.getSystem()
                : mSingleton.getResources();
        int percent = mSingleton == null || mSingleton.getIntent() == null ? 100
                : DCSSLauncher.normalizeReadingScale(
                        mSingleton.getIntent().getIntExtra("reading_scale", 100));
        return TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 14,
                resources.getDisplayMetrics()) * percent / 100.0f;
    }

    private static native void nativeRequestRedraw();

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
