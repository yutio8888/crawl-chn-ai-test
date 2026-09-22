package org.libsdl.app;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertTrue;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Build;
import android.text.InputType;
import android.text.Selection;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.develz.crawl.DCSSKeyboard;
import org.develz.crawl.DCSSLauncher;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Real Android Editable/InputConnection behavior, recording only the JNI boundary. */
@RunWith(AndroidJUnit4.class)
public class SDLInputConnectionTest {
    @Test
    public void commitBoundaryUsesStandardUtf8WithoutTruncatingLongText() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                List<byte[]> commits = new ArrayList<>();
                SDLInputConnection connection = new SDLInputConnection(new View(activity), true) {
                    @Override
                    protected void nativeCommitUtf8(byte[] text) { commits.add(text); }
                };
                assertTrue(connection.commitText("中\uD83D\uDE00", 1));
                assertArrayEquals(new byte[] {(byte) 0xE4, (byte) 0xB8, (byte) 0xAD,
                        (byte) 0xF0, (byte) 0x9F, (byte) 0x98, (byte) 0x80}, commits.get(0));
                String text = "abcdefghijklmnopqrstuvwxyz0123456789中文\uD83D\uDE00";
                assertTrue(connection.commitText(text, 1));
                assertTrue(commits.get(1).length > 31);
                assertEquals(text, new String(commits.get(1),
                        java.nio.charset.StandardCharsets.UTF_8));
            });
        }
    }

    private static class RecordingConnection extends SDLInputConnection {
        final List<String> commits = new ArrayList<>();
        final List<String> compositions = new ArrayList<>();
        final List<Integer> keys = new ArrayList<>();
        // Suffix-edit oracle at the JNI boundary, independent of Editable:
        // native insertion appends, and one Backspace removes one BMP glyph.
        // Assertions below use standalone Chinese/ASCII glyphs.
        final StringBuilder nativeText = new StringBuilder();

        RecordingConnection(View view) { super(view, true); }

        @Override
        public void nativeCommitText(String text, int position) {
            commits.add(text);
            nativeText.append(text);
        }

        @Override
        public void nativeSetComposingText(String text, int position) { compositions.add(text); }

        @Override
        protected void sendNativeKeyEvent(KeyEvent event) {
            if (event.getAction() == KeyEvent.ACTION_DOWN) {
                keys.add(event.getKeyCode());
                if (event.getKeyCode() == KeyEvent.KEYCODE_DEL && nativeText.length() > 0) {
                    int end = nativeText.length();
                    nativeText.delete(end - Character.charCount(
                            Character.codePointBefore(nativeText, end)), end);
                }
            }
        }
    }

    private static class RecordingEditor extends DummyEdit {
        RecordingEditor(Context context, int keyboardMode) { super(context, keyboardMode); }

        @Override
        protected SDLInputConnection createInputConnection() { return new RecordingConnection(this); }

        RecordingConnection connection(EditorInfo info) {
            return (RecordingConnection) onCreateInputConnection(info);
        }
    }

    private static RecordingEditor attach(DCSSLauncher activity, int mode) {
        RecordingEditor editor = new RecordingEditor(activity, mode);
        ViewGroup content = activity.findViewById(android.R.id.content);
        content.addView(editor, new ViewGroup.LayoutParams(1, 1));
        return editor;
    }

    @Test
    public void chineseCompositionCommitsOnceAndDoneFinishesComposition() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                RecordingEditor editor = attach(activity, 4);
                editor.configureIme(true, DCSSKeyboard.CONTEXT_TEXT);
                RecordingConnection connection = editor.connection(new EditorInfo());
                assertTrue(connection.setComposingText("zhong", 1));
                assertTrue(connection.setComposingText("中文", 1));
                assertTrue(connection.commits.isEmpty());
                assertEquals("中文", connection.getEditable().toString());
                assertTrue(connection.commitText("中文", 1));
                assertTrue(connection.finishComposingText());
                assertEquals(Arrays.asList("中文"), connection.commits);
                assertEquals("中文", connection.getEditable().toString());
                assertEquals(Arrays.asList("zhong", "中文", ""), connection.compositions);

                assertTrue(connection.setComposingText("输入", 1));
                assertTrue(connection.performEditorAction(EditorInfo.IME_ACTION_DONE));
                assertEquals(Arrays.asList("中文", "输入"), connection.commits);
                assertEquals("中文输入", connection.getEditable().toString());
                assertEquals(Arrays.asList(KeyEvent.KEYCODE_ENTER), connection.keys);
                assertFalse(connection.performEditorAction(EditorInfo.IME_ACTION_NONE));

                RecordingConnection finished = new RecordingConnection(editor);
                finished.setComposingText("zhong", 1);
                finished.setComposingText("中文", 1);
                assertTrue(finished.finishComposingText());
                assertTrue(finished.finishComposingText());
                assertEquals(Arrays.asList("中文"), finished.commits);
            });
        }
    }

    @Test
    public void committedReconversionIsRejectedWithoutNativeMutation() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                RecordingEditor editor = attach(activity, 4);
                // The prefix belongs to the native prompt, not the hidden
                // editor. A wrong deletion count would corrupt that prefill.
                RecordingConnection retagged = new RecordingConnection(editor);
                retagged.nativeText.append("前缀");
                retagged.commitText("中文", 1);
                assertFalse(retagged.setComposingRegion(0, 2));
                assertTrue(retagged.finishComposingText());
                assertEquals(Arrays.asList("中文"), retagged.commits);
                assertTrue(retagged.keys.isEmpty());
                assertEquals("前缀中文", retagged.nativeText.toString());

                // After a rejected region, further input is a new insertion;
                // it must never infer native backspaces from local history.
                retagged.commitText("汉字", 1);
                assertEquals("前缀中文汉字", retagged.nativeText.toString());
                assertTrue(retagged.keys.isEmpty());

                for (int key : new int[] {KeyEvent.KEYCODE_DEL, KeyEvent.KEYCODE_DPAD_LEFT,
                        KeyEvent.KEYCODE_MOVE_HOME, KeyEvent.KEYCODE_MOVE_END}) {
                    RecordingConnection raw = new RecordingConnection(editor);
                    raw.nativeText.append("前缀");
                    raw.commitText("中文", 1);
                    raw.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, key));
                    raw.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, key));
                    assertEquals("中文", raw.getEditable().toString());
                    assertFalse(raw.setComposingRegion(0, 2));
                    assertTrue(raw.finishComposingText());
                    assertEquals(Arrays.asList("中文"), raw.commits);
                    assertEquals(Arrays.asList(key), raw.keys);
                    if (key == KeyEvent.KEYCODE_DEL) {
                        raw.commitText("汉字", 1);
                        assertEquals("前缀中汉字", raw.nativeText.toString());
                        assertEquals(Arrays.asList(key), raw.keys);
                    }
                }

                // Native seed fields can reject non-digits without any Java
                // acknowledgement. This fixture records that boundary result;
                // local text is deliberately different from native text.
                RecordingConnection filtered = new RecordingConnection(editor) {
                    @Override
                    public void nativeCommitText(String text, int position) {
                        commits.add(text);
                        if (text.matches("[0-9]+")) nativeText.append(text);
                    }
                };
                filtered.nativeText.append("123");
                filtered.commitText("abc", 1);
                assertEquals("abc", filtered.getEditable().toString());
                assertFalse(filtered.setComposingRegion(0, 3));
                filtered.finishComposingText();
                filtered.commitText("4", 1);
                assertEquals("1234", filtered.nativeText.toString());
                assertTrue(filtered.keys.isEmpty());

                RecordingConnection candidate = new RecordingConnection(editor);
                candidate.commitText("中文", 1);
                candidate.setComposingText("输入", 1);
                assertFalse(candidate.setComposingRegion(0, 2));
                assertFalse(candidate.setComposingRegion(0, 4));
                assertTrue(candidate.setComposingRegion(2, 4));
                assertTrue(candidate.finishComposingText());
                assertTrue(candidate.finishComposingText());
                assertEquals(Arrays.asList("中文", "输入"), candidate.commits);
                assertEquals("中文输入", candidate.nativeText.toString());
                assertTrue(candidate.keys.isEmpty());

                candidate.setComposingText("", 1);
                candidate.finishComposingText();
                assertEquals("中文输入", candidate.nativeText.toString());

                RecordingConnection canceled = new RecordingConnection(editor);
                canceled.commitText("中文", 1);
                assertFalse(canceled.setComposingRegion(0, 2));
                canceled.setComposingText("汉字", 1);
                canceled.deactivate();
                assertFalse(canceled.finishComposingText());
                assertFalse(canceled.commitText("汉字", 1));
                assertFalse(canceled.setComposingRegion(0, 2));
                assertEquals("中文", canceled.nativeText.toString());

                for (String unsupported : new String[] {"abc", "e\u0301", "\uD83D\uDE00"}) {
                    RecordingConnection rejected = new RecordingConnection(editor);
                    rejected.commitText(unsupported, 1);
                    int end = unsupported.equals("abc") ? 2 : unsupported.length();
                    assertFalse(rejected.setComposingRegion(0, end));
                    assertTrue(rejected.finishComposingText());
                    assertEquals(Arrays.asList(unsupported), rejected.commits);
                    assertTrue(rejected.keys.isEmpty());
                }
            });
        }
    }

    @Test
    public void pasteAndUnicodeDeletionUseExistingNativeInputBoundary() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                RecordingEditor editor = attach(activity, 4);
                editor.configureIme(true, DCSSKeyboard.CONTEXT_TEXT);
                assertTrue(editor.requestFocus());
                RecordingConnection connection = editor.connection(new EditorInfo());
                ClipboardManager clipboard = (ClipboardManager) activity.getSystemService(
                        Context.CLIPBOARD_SERVICE);
                ClipData previous = clipboard.getPrimaryClip();
                try {
                    clipboard.setPrimaryClip(ClipData.newPlainText("test", "中文A"));
                    assertTrue(connection.performContextMenuAction(android.R.id.paste));
                    assertEquals(Arrays.asList("中文A"), connection.commits);
                    assertEquals("中文A", connection.getEditable().toString());
                    assertTrue(connection.deleteSurroundingText(1, 0));
                    assertEquals("中文", connection.getEditable().toString());
                    assertEquals(Arrays.asList(KeyEvent.KEYCODE_DEL), connection.keys);
                    assertFalse(connection.setComposingRegion(0, 2));
                    assertTrue(connection.finishComposingText());
                    assertEquals(Arrays.asList("中文A"), connection.commits);
                    assertEquals("中文", connection.nativeText.toString());
                    assertTrue(connection.setComposingText("输入", 1));
                    assertTrue(connection.finishComposingText());
                    assertEquals("中文输入", connection.nativeText.toString());

                    connection.getEditable().clear();
                    connection.keys.clear();
                    connection.commitText("中\uD83D\uDE00", 1);
                    assertTrue(connection.deleteSurroundingText(2, 0));
                    assertEquals("中", connection.getEditable().toString());
                    assertEquals(Arrays.asList(KeyEvent.KEYCODE_DEL), connection.keys);
                    if (Build.VERSION.SDK_INT >= 24) {
                        connection.commitText("\uD83D\uDE00", 1);
                        assertTrue(connection.deleteSurroundingTextInCodePoints(1, 0));
                        assertEquals("中", connection.getEditable().toString());
                        assertEquals(2, connection.keys.size());
                    }

                    connection.getEditable().clear();
                    connection.keys.clear();
                    // Native prompts can have prefilled text absent from the
                    // hidden editor. Backspace must still reach that prompt.
                    assertTrue(connection.deleteSurroundingText(1, 0));
                    assertEquals(Arrays.asList(KeyEvent.KEYCODE_DEL), connection.keys);
                    connection.commitText("中文", 1);
                    Selection.setSelection(connection.getEditable(), 0);
                    assertTrue(connection.deleteSurroundingText(0, 1));
                    assertEquals("文", connection.getEditable().toString());
                    assertEquals(KeyEvent.KEYCODE_FORWARD_DEL,
                            (int) connection.keys.get(connection.keys.size() - 1));
                } finally {
                    if (previous != null) clipboard.setPrimaryClip(previous);
                    else if (Build.VERSION.SDK_INT >= 28) clipboard.clearPrimaryClip();
                    else clipboard.setPrimaryClip(ClipData.newPlainText("", ""));
                }
            });
        }
    }

    @Test
    public void textAndNumericExitReleaseFocusAndRejectStaleImeEvents() {
        try (ActivityScenario<DCSSLauncher> scenario = ActivityScenario.launch(DCSSLauncher.class)) {
            scenario.onActivity(activity -> {
                for (int mode : new int[] {1, 2, 4}) {
                    RecordingEditor editor = attach(activity, mode);
                    assertFalse(editor.isFocusable());
                    for (int context : new int[] {DCSSKeyboard.CONTEXT_TEXT,
                            DCSSKeyboard.CONTEXT_NUMBER}) {
                        editor.configureIme(true, context);
                        assertTrue(editor.isFocusableInTouchMode());
                        assertTrue(editor.requestFocus());
                        assertTrue(editor.hasFocus());
                        EditorInfo info = new EditorInfo();
                        RecordingConnection old = editor.connection(info);
                        assertEquals(context == DCSSKeyboard.CONTEXT_NUMBER
                                        ? InputType.TYPE_CLASS_NUMBER : InputType.TYPE_CLASS_TEXT,
                                info.inputType & InputType.TYPE_MASK_CLASS);
                        if (context == DCSSKeyboard.CONTEXT_TEXT) {
                            assertEquals(0, info.inputType & InputType.TYPE_MASK_VARIATION);
                        }
                        assertTrue((info.imeOptions & EditorInfo.IME_FLAG_NO_EXTRACT_UI) != 0);
                        old.setComposingText("未提交", 1);
                        editor.configureIme(false, DCSSKeyboard.CONTEXT_GAME);
                        assertFalse(editor.hasFocus());
                        assertFalse(editor.isFocusable());
                        assertEquals("", old.getEditable().toString());
                        assertNotSame(old, editor.connection(new EditorInfo()));
                        assertFalse(old.commitText("过期", 1));
                        assertFalse(old.setComposingText("过期", 1));
                        assertFalse(old.finishComposingText());
                        assertFalse(old.deleteSurroundingText(1, 0));
                        assertFalse(old.performContextMenuAction(android.R.id.paste));
                        assertFalse(old.performEditorAction(EditorInfo.IME_ACTION_DONE));
                        assertFalse(old.sendKeyEvent(new KeyEvent(
                                KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ESCAPE)));
                        assertTrue(old.commits.isEmpty());
                        assertTrue(old.keys.isEmpty());
                    }
                    ((ViewGroup) editor.getParent()).removeView(editor);
                }
                // The existing global system-keyboard preference retains its
                // focusable command editor and hardware-key event route.
                RecordingEditor global = attach(activity, 3);
                assertTrue(global.isFocusable());
                global.configureIme(true, DCSSKeyboard.CONTEXT_GAME);
                EditorInfo info = new EditorInfo();
                RecordingConnection connection = global.connection(info);
                assertEquals(InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD,
                        info.inputType & InputType.TYPE_MASK_VARIATION);
                connection.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ESCAPE));
                assertEquals(Arrays.asList(KeyEvent.KEYCODE_ESCAPE), connection.keys);
            });
        }
    }
}
