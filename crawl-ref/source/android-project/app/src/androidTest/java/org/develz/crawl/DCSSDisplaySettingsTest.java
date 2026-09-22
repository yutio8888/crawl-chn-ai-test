package org.develz.crawl;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.util.TypedValue;
import android.view.ContextThemeWrapper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.inputmethod.EditorInfo;
import android.widget.CheckedTextView;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;

import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.File;
import java.io.IOException;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicReference;

@RunWith(AndroidJUnit4.class)
public class DCSSDisplaySettingsTest {
    private final Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();

    @Test
    public void launcherCommitsFocusDonePresetsAndStartAndPersistsReadingSize() {
        AtomicReference<SharedPreferences> preferences = new AtomicReference<>();
        String[] keys = {"keyboard", "keyboard_size", "reading_scale"};
        int[] originals = new int[keys.length];
        boolean[] present = new boolean[keys.length];
        AtomicReference<Intent> started = new AtomicReference<>();
        Instrumentation.ActivityMonitor monitor = new Instrumentation.ActivityMonitor() {
            @Override
            public Instrumentation.ActivityResult onStartActivity(Intent intent) {
                if (intent.getComponent() != null && intent.getComponent().getClassName()
                        .equals(DungeonCrawlStoneSoup.class.getName())) {
                    started.set(intent);
                    return new Instrumentation.ActivityResult(Activity.RESULT_CANCELED, null);
                }
                return null;
            }
        };
        instrumentation.addMonitor(monitor);
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                SharedPreferences prefs = activity.getPreferences(Context.MODE_PRIVATE);
                preferences.set(prefs);
                for (int i = 0; i < keys.length; ++i) {
                    present[i] = prefs.contains(keys[i]);
                    originals[i] = prefs.getInt(keys[i], 0);
                }
                activity.findViewById(R.id.inputDisplayButton).performClick();
                ((Spinner) activity.findViewById(R.id.keyboardSpinner)).setSelection(4);
            });
            instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.keyboardSize);
                editor.requestFocus();
                editor.setText("1");
                activity.findViewById(R.id.launcherRoot).requestFocus();
                assertEquals(48, preferences.get().getInt("keyboard_size", -1));
                editor.setText("invalid");
                editor.onEditorAction(EditorInfo.IME_ACTION_DONE);
                assertEquals("48", editor.getText().toString());
                activity.findViewById(R.id.keyboardLarge).performClick();
                int size = preferences.get().getInt("keyboard_size", -1);
                assertEquals(Integer.toString(size), editor.getText().toString());
                assertEquals(activity.getString(R.string.keyboard_height_applied, size),
                        ((TextView) activity.findViewById(R.id.keyboardSizeApplied))
                                .getText().toString());
                assertTrue(size >= 48 && size <= 64);
                ((Spinner) activity.findViewById(R.id.readingSize)).setSelection(3);
            });
            instrumentation.waitForIdleSync();
            assertEquals(150, preferences.get().getInt("reading_scale", -1));
            scenario.recreate();
            scenario.onActivity(activity -> {
                assertEquals(3, ((Spinner) activity.findViewById(R.id.readingSize))
                        .getSelectedItemPosition());
                assertEquals(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, 14,
                        activity.getResources().getDisplayMetrics()) * 1.5f,
                        ((TextView) activity.findViewById(R.id.readingSizePreview))
                                .getTextSize(), 0.01f);
                // Start must commit a still-focused edit without requiring Done.
                activity.findViewById(R.id.inputDisplayButton).performClick();
                EditText editor = activity.findViewById(R.id.keyboardSize);
                editor.requestFocus();
                editor.setText("999");
                activity.findViewById(R.id.startButton).performClick();
                assertNotNull(started.get());
                float density = activity.getResources().getDisplayMetrics().density;
                assertEquals(Math.round(preferences.get().getInt("keyboard_size", -1) * density),
                        started.get().getIntExtra("keyboard_size", -1));
                assertEquals(150, started.get().getIntExtra("reading_scale", -1));
            });
        } finally {
            instrumentation.removeMonitor(monitor);
            if (preferences.get() != null) {
                SharedPreferences.Editor editor = preferences.get().edit();
                for (int i = 0; i < keys.length; ++i) {
                    if (present[i]) editor.putInt(keys[i], originals[i]);
                    else editor.remove(keys[i]);
                }
                editor.commit();
            }
        }
    }

    @Test
    public void previewMeasuresTheProductionKeyboardAtGameWidthAndNeverDispatchesInput() {
        instrumentation.runOnMainSync(() -> {
            for (String language : new String[] {"en", "zh-CN"}) {
                for (float fontScale : new float[] {1, 2}) {
                    Context context = configuredContext(language, fontScale);
                    float density = context.getResources().getDisplayMetrics().density;
                    int width = Math.round(320 * density);
                    for (int mode : new int[] {1, 2, 4}) {
                        FrameLayout root = new FrameLayout(context);
                        measureAndLayout(root, width, Math.round(640 * density));
                        DCSSLauncher.KeyboardPreview preview = new DCSSLauncher.KeyboardPreview(context);
                        preview.setKeyboard(mode, Math.round(48 * density));
                        root.addView(preview, new FrameLayout.LayoutParams(width - 40,
                                FrameLayout.LayoutParams.WRAP_CONTENT));
                        measureAndLayout(root, width, Math.round(640 * density));
                        DCSSKeyboard actual = new DCSSKeyboard(context);
                        actual.initKeyboard(mode, Math.round(48 * density));
                        actual.setInputContext(DCSSKeyboard.CONTEXT_GAME, 18,
                                new String[6], new int[] {'5', 'q', 'r', 'f', 'z', 'a'});
                        actual.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                                View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
                        assertEquals(actual.getMeasuredHeight(), preview.keyboard.getMeasuredHeight());
                        assertEquals(width, preview.keyboard.getMeasuredWidth());
                        assertEquals(Math.round((float) actual.getMeasuredHeight()
                                * preview.getWidth() / width), preview.getHeight());
                        assertNull(preview.keyboard.getParent());
                        assertFalse(preview.isClickable());
                        assertFalse(preview.performClick());
                    }
                }
            }
        });
    }

    @Test
    public void expandedSettingsRemainScrollableAtNarrowWidthAndDoubleFont() {
        instrumentation.runOnMainSync(() -> {
            for (String language : new String[] {"en", "zh-CN"}) {
                Context context = configuredContext(language, 2);
                float density = context.getResources().getDisplayMetrics().density;
                View root = LayoutInflater.from(context).inflate(R.layout.launcher, null);
                root.findViewById(R.id.inputDisplayGroup).setVisibility(View.VISIBLE);
                measureAndLayout(root, Math.round(320 * density), Math.round(640 * density));
                ScrollView scroll = root.findViewById(R.id.launcherScroll);
                assertTrue(scroll.getChildAt(0).getHeight() > scroll.getHeight());
                // This detached layout has no Choreographer frames to finish
                // smoothScrollBy. Exercise the same full-scroll path with
                // animation disabled, then inspect its final viewport.
                scroll.setSmoothScrollingEnabled(false);
                scroll.fullScroll(View.FOCUS_DOWN);
                assertTrue(scroll.getScrollY() > 0);
                View fullscreen = root.findViewById(R.id.fullScreen);
                android.graphics.Rect bounds = new android.graphics.Rect();
                fullscreen.getDrawingRect(bounds);
                scroll.offsetDescendantRectToMyCoords(fullscreen, bounds);
                String viewport = language + " fullscreen=" + bounds
                        + " scrollY=" + scroll.getScrollY() + " height=" + scroll.getHeight();
                assertTrue(viewport, bounds.bottom <= scroll.getScrollY() + scroll.getHeight());
                assertTrue(viewport, bounds.top >= scroll.getScrollY());
                for (int id : new int[] {R.id.keyboardSmall, R.id.keyboardStandard, R.id.keyboardLarge}) {
                    TextView button = root.findViewById(id);
                    assertTrue(button.getHeight() >= Math.round(48 * density));
                    assertEquals(button.getText().length(), button.getLayout().getLineEnd(
                            button.getLayout().getLineCount() - 1));
                    assertTrue(button.getLayout().getHeight() <= button.getHeight()
                            - button.getCompoundPaddingTop() - button.getCompoundPaddingBottom());
                }
            }
        });
    }

    @Test
    public void fileRowsExposeSelectionAndPreserveSelectedModAcrossReload() throws IOException {
        Context target = instrumentation.getTargetContext();
        File directory = new File(target.getCacheDir(), "display-file-rows-" + System.nanoTime());
        assertTrue(directory.mkdir());
        File first = new File(directory, "z-long-file-name-with-a-description.txt");
        File added = new File(directory, "a-new-file.txt");
        assertTrue(first.createNewFile());
        try {
            instrumentation.runOnMainSync(() -> {
                Context context = configuredContext("en", 2);
                int width = Math.round(320 * context.getResources().getDisplayMetrics().density);
                RecyclerView parent = new RecyclerView(context);
                // Row inflation asks its RecyclerView parent for LayoutParams,
                // just as the production file-list Activities do.
                parent.setLayoutManager(new LinearLayoutManager(context));
                DCSSModsAdapter mods = new DCSSModsAdapter(directory, position -> { });
                mods.sortModsFiles();
                DCSSModsAdapter.ViewHolder holder = mods.onCreateViewHolder(parent, 0);
                mods.setSelectedPosition(0);
                mods.onBindViewHolder(holder, 0);
                measureAndLayout(holder.itemView, width, 0);
                assertTrue(holder.itemView.getHeight() >= Math.round(48
                        * context.getResources().getDisplayMetrics().density));
                assertTrue(holder.itemView.isSelected());
                assertTrue(((CheckedTextView) holder.itemView.findViewById(R.id.fileName)).isChecked());
                AccessibilityNodeInfo info = holder.itemView.createAccessibilityNodeInfo();
                assertTrue(info.isCheckable());
                assertTrue(info.isChecked());
                info.recycle();
                try {
                    assertTrue(added.createNewFile());
                } catch (IOException e) {
                    throw new AssertionError(e);
                }
                mods.reloadModsFiles();
                assertEquals(first, mods.getSelectedFile());
                assertEquals(1, mods.getSelected());
                mods.onBindViewHolder(holder, 0);
                assertFalse(holder.itemView.isSelected());
                assertFalse(((CheckedTextView) holder.itemView.findViewById(R.id.fileName)).isChecked());
                DCSSMorgueAdapter morgue = new DCSSMorgueAdapter(directory, position -> { });
                morgue.sortMorgueFiles(0);
                DCSSMorgueAdapter.ViewHolder row = morgue.onCreateViewHolder(parent, 0);
                morgue.setSelectedPosition(1);
                morgue.onBindViewHolder(row, 1);
                measureAndLayout(row.itemView, width, 0);
                assertTrue(row.itemView.isSelected());
                assertTrue(row.itemView.getHeight() >= Math.round(48
                        * context.getResources().getDisplayMetrics().density));
                morgue.sortMorgueFiles(1);
                morgue.onBindViewHolder(row, 0);
                assertTrue(row.itemView.isSelected());
            });
        } finally {
            first.delete();
            added.delete();
            directory.delete();
        }
    }

    @Test
    public void previewSummaryLaysOutItsCompleteTextAfterPreviewMeasurement() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                activity.findViewById(R.id.inputDisplayButton).performClick();
                ((Spinner) activity.findViewById(R.id.keyboardSpinner)).setSelection(4);
            });
            instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> {
                TextView summary = activity.findViewById(R.id.keyboardPreviewSummary);
                android.text.Layout layout = summary.getLayout();
                assertNotNull(layout);
                assertTrue(summary.getText().length() > 0);
                int last = layout.getLineCount() - 1;
                assertEquals(summary.getText().length(), layout.getLineEnd(last));
                int width = summary.getWidth() - summary.getCompoundPaddingLeft()
                        - summary.getCompoundPaddingRight();
                for (int line = 0; line <= last; ++line) {
                    assertEquals(0, layout.getEllipsisCount(line));
                    assertTrue(layout.getLineWidth(line) <= width + 1);
                }
                assertTrue(layout.getHeight() <= summary.getHeight()
                        - summary.getCompoundPaddingTop() - summary.getCompoundPaddingBottom());
            });
        }
    }

    private Context configuredContext(String language, float fontScale) {
        Context target = instrumentation.getTargetContext();
        Configuration config = new Configuration(target.getResources().getConfiguration());
        config.fontScale = fontScale;
        config.densityDpi = 540;
        config.screenWidthDp = 320;
        config.screenHeightDp = 640;
        config.setLocale(Locale.forLanguageTag(language));
        return new ContextThemeWrapper(target.createConfigurationContext(config), R.style.CrawlTheme);
    }

    private static void measureAndLayout(View view, int width, int height) {
        view.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(height, height == 0
                        ? View.MeasureSpec.UNSPECIFIED : View.MeasureSpec.EXACTLY));
        view.layout(0, 0, width, view.getMeasuredHeight());
    }
}
