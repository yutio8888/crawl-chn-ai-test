package org.develz.crawl;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.util.TypedValue;
import android.view.ContextThemeWrapper;
import android.view.View;
import android.widget.Button;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class DCSSKeyboardConfigurationTest {
    @Test
    public void gameHandlesFontAndNightModeWithoutChangingPortraitLock() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        ActivityInfo info = context.getPackageManager().getActivityInfo(
                new ComponentName(context, DungeonCrawlStoneSoup.class), 0);
        assertTrue((info.configChanges & ActivityInfo.CONFIG_FONT_SCALE) != 0);
        assertTrue((info.configChanges & ActivityInfo.CONFIG_UI_MODE) != 0);
        assertEquals(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT, info.screenOrientation);
    }

    @Test
    public void fontChangesPreserveManualLayoutsContextLabelsAndPixelHeights() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
            // A private resource configuration keeps this fixture from changing
            // the device setting or another Activity's resources.
            Configuration initial = new Configuration(target.getResources().getConfiguration());
            initial.fontScale = 1.3f;
            Context context = new ContextThemeWrapper(
                    target.createConfigurationContext(initial), R.style.CrawlTheme);
            Resources resources = context.getResources();
            DCSSKeyboard keyboard = new DCSSKeyboard(context);
            DCSSKeyboardExtra extra = new DCSSKeyboardExtra(context);
            keyboard.initKeyboard(4, 160);
            extra.initKeyboard(2, 160);
            keyboard.setInputContext(DCSSKeyboard.CONTEXT_GAME, 0,
                    new String[] {"A", "B", "", "", "", ""},
                    new int[] {97, 98, 0, 0, 0, 0});
            int height = keyboard.findViewById(R.id.main_layout).getLayoutParams().height;
            int keyHeight = keyboard.findViewById(R.id.key_q).getLayoutParams().height;
            keyboard.updateLayout(keyboard.findViewById(R.id.key_mobile_expand));
            for (int switchKey : new int[] {R.id.key_shift_lower, R.id.key_ctrl_upper,
                    R.id.key_123_ctrl, R.id.key_abc, R.id.key_compact_lower}) {
                keyboard.updateLayout(keyboard.findViewById(switchKey));
                int[] layouts = {R.id.keyboard_lower, R.id.keyboard_upper,
                        R.id.keyboard_ctrl, R.id.keyboard_numeric, R.id.keyboard_mobile};
                int[] visibility = new int[layouts.length];
                for (int i = 0; i < layouts.length; ++i) {
                    visibility[i] = keyboard.findViewById(layouts[i]).getVisibility();
                }
                for (float scale : new float[] {1.0f, 1.3f, 2.0f, 1.0f}) {
                    Configuration changed = new Configuration(initial);
                    changed.fontScale = scale;
                    changed.uiMode = (changed.uiMode & ~Configuration.UI_MODE_NIGHT_MASK)
                            | (scale == 1.0f ? Configuration.UI_MODE_NIGHT_NO
                                            : Configuration.UI_MODE_NIGHT_YES);
                    // Simulate Android updating existing view resources before
                    // delivering the Activity's configuration callback.
                    resources.updateConfiguration(changed, resources.getDisplayMetrics());
                    keyboard.refreshTextSizes();
                    extra.refreshTextSizes();
                    assertTextSp(keyboard.findViewById(R.id.key_q), 12);
                    assertTextSp(keyboard.findViewById(R.id.key_mobile_expand), 18);
                    assertTextSp(keyboard.findViewById(R.id.key_context_0), 12);
                    assertTextSp(extra.findViewById(R.id.key_extra_7), 12);
                    assertEquals(height, keyboard.findViewById(R.id.main_layout)
                            .getLayoutParams().height);
                    assertEquals(keyHeight, keyboard.findViewById(R.id.key_q)
                            .getLayoutParams().height);
                    assertEquals(160, extra.findViewById(R.id.key_extra_7)
                            .getLayoutParams().height);
                    for (int i = 0; i < layouts.length; ++i) {
                        assertEquals(visibility[i], keyboard.findViewById(layouts[i]).getVisibility());
                    }
                    assertEquals("A", ((Button) keyboard.findViewById(R.id.key_context_0))
                            .getText().toString());
                    assertEquals(View.INVISIBLE, keyboard.findViewById(R.id.key_context_2)
                            .getVisibility());
                }
            }
        });
    }

    private static void assertTextSp(Button button, float sp) {
        // XML inflation rounds the initial text dimension to whole pixels;
        // converting that back to sp can retain a subpixel rounding difference.
        assertEquals(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, sp,
                button.getResources().getDisplayMetrics()), button.getTextSize(), 1.0f);
    }
}
