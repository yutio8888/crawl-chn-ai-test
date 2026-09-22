package org.develz.crawl;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.content.ComponentName;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.text.Layout;
import android.util.TypedValue;
import android.view.ContextThemeWrapper;
import android.view.View;
import android.view.ViewGroup;
import android.view.KeyEvent;
import android.view.inputmethod.BaseInputConnection;
import android.widget.Button;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.Locale;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

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
    public void fontChangesRefitRowsAndPreserveManualLayoutsAndContextLabels() {
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
                    measureKeyboard(keyboard, 320);
                    assertTextSp(keyboard.findViewById(R.id.key_q), 12);
                    assertTextSp(keyboard.findViewById(R.id.key_mobile_expand), 18);
                    assertTextSp(keyboard.findViewById(R.id.key_context_0), 12);
                    assertTextSp(extra.findViewById(R.id.key_extra_7), 12);
                    assertVisibleLabelsFit(keyboard);
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

    @Test
    public void narrowAndLargeFontLayoutsFitWithoutShrinkingOrContextResize() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
            for (int densityDpi : new int[] {420, 540}) {
                for (String language : new String[] {"en", "zh-CN"}) {
                    for (int width : new int[] {320, 360, 411}) {
                        for (float scale : new float[] {1.0f, 1.3f, 2.0f}) {
                            Configuration config = new Configuration(
                                    target.getResources().getConfiguration());
                            config.fontScale = scale;
                            config.densityDpi = densityDpi;
                            config.screenWidthDp = width;
                            config.screenHeightDp = 640;
                            config.setLocale(Locale.forLanguageTag(language));
                            Context context = new ContextThemeWrapper(
                                    target.createConfigurationContext(config), R.style.CrawlTheme);
                            DCSSKeyboard keyboard = new DCSSKeyboard(context);
                            keyboard.initKeyboard(4, 0);
                            int height = 0;
                            int[] screens = {18, 1, 4, 7, 10, 6};
                            int[][] keys = {{'5', 'q', 'r', 'f', 'z', 'a'},
                                    {13, 27, -253, -254, 0, '!'},
                                    {13, 27, '-', '+', '.', -274},
                                    {13, 27, '<', '>', '\\', '^'},
                                    {13, 27, '/', '=', '-', -274},
                                    {' ', 27, 0, 0, 0, 0}};
                            for (int i = 0; i < screens.length; ++i) {
                                String[] labels = new String[6];
                                if (screens[i] == 6) {
                                    labels[0] = "Continue";
                                    labels[1] = context.getString(R.string.keyboard_skip_messages);
                                }
                                keyboard.setInputContext(i == 0 ? DCSSKeyboard.CONTEXT_GAME
                                                : DCSSKeyboard.CONTEXT_NAVIGATION,
                                        screens[i], labels, keys[i]);
                                measureKeyboard(keyboard, width);
                                if (i == 0) height = keyboard.getHeight();
                                assertEquals("context must not resize SDL", height, keyboard.getHeight());
                                assertVisibleLabelsFit(keyboard);
                                assertTextSp(keyboard.findViewById(R.id.key_q), 12);
                                assertTextSp(keyboard.findViewById(R.id.key_mobile_autofight), 12);
                                assertTextSp(keyboard.findViewById(R.id.key_context_0), 12);
                                for (int id : new int[] {R.id.key_mobile_1, R.id.key_mobile_2,
                                        R.id.key_mobile_3, R.id.key_mobile_4, R.id.key_mobile_5,
                                        R.id.key_mobile_6, R.id.key_mobile_7, R.id.key_mobile_8,
                                        R.id.key_mobile_9, R.id.key_mobile_back,
                                        R.id.key_mobile_explore, R.id.key_mobile_expand,
                                        R.id.key_context_0, R.id.key_context_1}) {
                                    assertTouchTarget(keyboard.findViewById(id));
                                }
                            }
                            keyboard.setInputContext(DCSSKeyboard.CONTEXT_TEXT, 0,
                                    new String[6], new int[6]);
                            measureKeyboard(keyboard, width);
                            assertEquals(height, keyboard.getHeight());
                            assertEquals(View.VISIBLE,
                                    keyboard.findViewById(R.id.keyboard_lower).getVisibility());
                            assertVisibleLabelsFit(keyboard);
                            assertTouchTarget(keyboard.findViewById(R.id.key_enter));
                            assertTouchTarget(keyboard.findViewById(R.id.key_compact_lower));
                            assertTouchTarget(keyboard.findViewById(R.id.key_system_keyboard));
                            for (int key : new int[] {R.id.key_shift_lower, R.id.key_ctrl_upper,
                                    R.id.key_123_ctrl, R.id.key_abc, R.id.key_compact_lower}) {
                                keyboard.updateLayout(keyboard.findViewById(key));
                                measureKeyboard(keyboard, width);
                                assertEquals(height, keyboard.getHeight());
                                assertVisibleLabelsFit(keyboard);
                            }
                            keyboard.setInputContext(DCSSKeyboard.CONTEXT_NUMBER, 0,
                                    new String[6], new int[6]);
                            measureKeyboard(keyboard, width);
                            assertEquals(height, keyboard.getHeight());
                            assertVisibleLabelsFit(keyboard);
                            assertTouchTarget(keyboard.findViewById(R.id.key_context_2));
                            // Leave a usable native view even on a shorter portrait
                            // display; fitting text must not put controls off-screen.
                            float density = context.getResources().getDisplayMetrics().density;
                            assertTrue(language + "/" + width + "/" + scale + " keyboard height "
                                    + height / density, height <= Math.round(440 * density));
                        }
                    }
                }
            }
        });
    }

    @Test
    public void textImeActionsAndExitPreserveEachPreviousManualLayout() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
            Context context = new ContextThemeWrapper(target, R.style.CrawlTheme);
            for (int mode : new int[] {1, 2, 4}) {
                for (int layout : new int[] {R.id.keyboard_mobile, R.id.keyboard_lower,
                        R.id.keyboard_upper, R.id.keyboard_ctrl, R.id.keyboard_numeric}) {
                    DCSSKeyboard keyboard = new DCSSKeyboard(context);
                    keyboard.initKeyboard(mode, 0);
                    keyboard.setInputContext(DCSSKeyboard.CONTEXT_GAME, 0,
                            new String[6], new int[6]);
                    keyboard.updateLayout(keyboard.findViewById(R.id.key_mobile_expand));
                    int switchKey = layout == R.id.keyboard_mobile ? R.id.key_compact_lower
                            : layout == R.id.keyboard_upper ? R.id.key_shift_lower
                            : layout == R.id.keyboard_ctrl ? R.id.key_ctrl_lower
                            : layout == R.id.keyboard_numeric ? R.id.key_123_lower
                            : R.id.key_mobile_expand;
                    keyboard.updateLayout(keyboard.findViewById(switchKey));
                    int[] requests = {0};
                    keyboard.setSystemKeyboardAction(() -> ++requests[0]);
                    List<Integer> sentKeys = new ArrayList<>();
                    keyboard.setInputConnection(new BaseInputConnection(keyboard, true) {
                        @Override
                        public boolean sendKeyEvent(KeyEvent event) {
                            if (event.getAction() == KeyEvent.ACTION_DOWN) {
                                sentKeys.add(event.getKeyCode());
                            }
                            return true;
                        }
                    });
                    for (int textContext : new int[] {DCSSKeyboard.CONTEXT_TEXT,
                            DCSSKeyboard.CONTEXT_NUMBER}) {
                        keyboard.setInputContext(textContext, 0, new String[6], new int[6]);
                        assertEquals(View.VISIBLE,
                                keyboard.findViewById(R.id.keyboard_lower).getVisibility());
                        for (int key : new int[] {R.id.key_mobile_expand, R.id.key_shift_lower,
                                R.id.key_ctrl_upper, R.id.key_123_ctrl}) {
                            keyboard.updateLayout(keyboard.findViewById(key));
                            assertEquals(View.VISIBLE,
                                    keyboard.findViewById(R.id.key_system_keyboard).getVisibility());
                            keyboard.findViewById(R.id.key_system_keyboard).performClick();
                        }
                        keyboard.updateLayout(keyboard.findViewById(R.id.key_abc));
                        keyboard.findViewById(R.id.key_compact_lower).performClick();
                        assertEquals(View.VISIBLE,
                                keyboard.findViewById(R.id.keyboard_mobile).getVisibility());
                        keyboard.findViewById(R.id.key_context_2).performClick();
                        keyboard.findViewById(R.id.key_context_0).performClick();
                        keyboard.findViewById(R.id.key_context_1).performClick();
                        assertEquals(Arrays.asList(KeyEvent.KEYCODE_ENTER, KeyEvent.KEYCODE_ESCAPE),
                                sentKeys);
                        sentKeys.clear();
                        keyboard.setInputContext(DCSSKeyboard.CONTEXT_GAME, 0,
                                new String[6], new int[6]);
                        assertEquals(View.VISIBLE, keyboard.findViewById(layout).getVisibility());
                        assertEquals(View.INVISIBLE,
                                keyboard.findViewById(R.id.key_system_keyboard).getVisibility());
                    }
                    assertEquals(10, requests[0]);
                }
            }
        });
    }

    private static void measureKeyboard(DCSSKeyboard keyboard, int widthDp) {
        int width = Math.round(widthDp * keyboard.getResources().getDisplayMetrics().density);
        keyboard.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        keyboard.layout(0, 0, width, keyboard.getMeasuredHeight());
    }

    private static void assertTouchTarget(Button button) {
        int minimum = Math.round(48 * button.getResources().getDisplayMetrics().density);
        assertEquals(View.VISIBLE, button.getVisibility());
        assertTrue(button.getWidth() + 1 >= minimum);
        assertTrue(button.getHeight() >= minimum);
    }

    private static void assertVisibleLabelsFit(View view) {
        if (view.getVisibility() != View.VISIBLE) return;
        if (view instanceof Button) {
            Button button = (Button) view;
            Layout text = button.getLayout();
            String label = button.getText().toString();
            assertTrue(label + " has a text layout", text != null);
            int width = button.getWidth() - button.getCompoundPaddingLeft()
                    - button.getCompoundPaddingRight();
            int height = button.getHeight() - button.getCompoundPaddingTop()
                    - button.getCompoundPaddingBottom();
            assertTrue(label + " text height " + text.getHeight() + " exceeds " + height,
                    text.getHeight() <= height);
            assertEquals(label.length(), text.getLineEnd(text.getLineCount() - 1));
            Rect ink = new Rect();
            for (int line = 0; line < text.getLineCount(); ++line) {
                assertEquals(label + " must not ellipsize", 0, text.getEllipsisCount(line));
                // Android can keep a trailing wrap-space beyond the line's
                // width. It has no ink; getLineMax excludes that whitespace.
                assertTrue(label + " text width " + text.getLineMax(line) + " exceeds " + width,
                        text.getLineMax(line) <= width + 1);
                button.getPaint().getTextBounds(label, text.getLineStart(line),
                        text.getLineEnd(line), ink);
                assertTrue(label + " ink outside content width",
                        text.getLineLeft(line) + ink.left >= -1
                        && text.getLineLeft(line) + ink.right <= width + 1);
                assertTrue(label + " ink outside content height",
                        text.getLineBaseline(line) + ink.top >= 0
                        && text.getLineBaseline(line) + ink.bottom <= text.getHeight());
            }
            assertContentInsidePaintedKey(button);
        } else if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); ++i) {
                View child = group.getChildAt(i);
                if (child.getVisibility() == View.VISIBLE) {
                    assertTrue("child below keyboard", child.getBottom() <= group.getHeight());
                    assertTrue("child outside keyboard", child.getRight() <= group.getWidth());
                    assertTrue(child.getTop() >= 0 && child.getLeft() >= 0);
                }
                assertVisibleLabelsFit(child);
            }
        }
    }

    // Layout-versus-View checks alone missed text drawn into the transparent
    // AppCompat background insets. Rasterize the real background independently
    // of production sizing and keep the text content inside its coloured face.
    private static void assertContentInsidePaintedKey(Button button) {
        int width = button.getWidth();
        int height = button.getHeight();
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Drawable background = button.getBackground();
        Rect previous = new Rect(background.getBounds());
        try {
            background.setBounds(0, 0, width, height);
            background.draw(new Canvas(bitmap));
            int left = 0;
            while (left < width && Color.alpha(bitmap.getPixel(left, height / 2)) == 0) ++left;
            int right = width;
            while (right > left && Color.alpha(bitmap.getPixel(right - 1, height / 2)) == 0) --right;
            int top = 0;
            while (top < height && Color.alpha(bitmap.getPixel(width / 2, top)) == 0) ++top;
            int bottom = height;
            while (bottom > top && Color.alpha(bitmap.getPixel(width / 2, bottom - 1)) == 0) --bottom;
            assertTrue("key background is painted", left < right && top < bottom);
            assertTrue(button.getText() + " content outside painted key",
                    button.getCompoundPaddingLeft() >= left
                    && width - button.getCompoundPaddingRight() <= right
                    && button.getCompoundPaddingTop() >= top
                    && height - button.getCompoundPaddingBottom() <= bottom);
        } finally {
            background.setBounds(previous);
            bitmap.recycle();
        }
    }

    private static void assertTextSp(Button button, float sp) {
        // XML inflation rounds the initial text dimension to whole pixels;
        // converting that back to sp can retain a subpixel rounding difference.
        assertEquals(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, sp,
                button.getResources().getDisplayMetrics()), button.getTextSize(), 1.0f);
    }
}
