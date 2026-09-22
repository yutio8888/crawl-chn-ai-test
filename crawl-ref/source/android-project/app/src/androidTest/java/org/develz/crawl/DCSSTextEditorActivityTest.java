package org.develz.crawl;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.RootMatchers.isDialog;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.content.Intent;
import android.widget.EditText;
import android.widget.TextView;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class DCSSTextEditorActivityTest {
    private File file;
    private static final String ORIGINAL = "# Original 中文\nlanguage = zh\n";
    private static final String EDITED = "# Edited 中文\nlanguage = en\n";

    @Before
    public void createFile() throws IOException {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        file = File.createTempFile("editor-test-", ".txt", context.getCacheDir());
        writeBytes(ORIGINAL.getBytes(StandardCharsets.UTF_8));
    }

    @After
    public void deleteFile() {
        file.delete();
    }

    private void writeBytes(byte[] bytes) throws IOException {
        try (FileOutputStream output = new FileOutputStream(file)) {
            output.write(bytes);
        }
    }

    private ActivityScenario<DCSSTextEditor> launch() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent intent = new Intent(context, DCSSTextEditor.class);
        intent.putExtra("file", file);
        return ActivityScenario.launch(intent);
    }

    private String readFile() throws IOException {
        return DCSSTextBase.readUtf8(new FileInputStream(file));
    }

    private byte[] readBytes() throws IOException {
        try (FileInputStream input = new FileInputStream(file);
                ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }

    @Test
    public void unchangedTextAndUndoneEditsCloseWithoutConfirmation() {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                activity.getOnBackPressedDispatcher().onBackPressed();
                assertTrue(activity.isFinishing());
            });
        }
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.textEditor);
                editor.setText(EDITED);
                editor.setText(ORIGINAL);
                activity.findViewById(R.id.cancelButton).performClick();
                assertTrue(activity.isFinishing());
            });
        }
    }

    @Test
    public void backAndCancelProtectEditsUntilExplicitDiscard() throws IOException {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                ((EditText) activity.findViewById(R.id.textEditor)).setText(EDITED);
                activity.getOnBackPressedDispatcher().onBackPressed();
                assertFalse(activity.isFinishing());
            });
            // Dialog focus arrives asynchronously after onActivity returns.
            // Select its window explicitly instead of retaining the Activity
            // root while the dialog takes focus.
            onView(withText(R.string.discard_changes_title)).inRoot(isDialog())
                    .check(matches(isDisplayed()));
            onView(withText(R.string.keep_editing)).inRoot(isDialog()).perform(click());
            scenario.onActivity(activity -> {
                assertEquals(EDITED, ((EditText) activity.findViewById(R.id.textEditor))
                        .getText().toString());
                activity.findViewById(R.id.cancelButton).performClick();
                assertFalse(activity.isFinishing());
            });
            onView(withText(R.string.discard_changes)).inRoot(isDialog()).perform(click());
            assertEquals(ORIGINAL, readFile());
        }
    }

    @Test
    public void recreationRetainsEditsSelectionAndOriginalBaseline() throws IOException {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.textEditor);
                editor.setText(EDITED);
                editor.setSelection(3, 8);
            });
            scenario.recreate();
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.textEditor);
                assertEquals(EDITED, editor.getText().toString());
                assertEquals(3, editor.getSelectionStart());
                assertEquals(8, editor.getSelectionEnd());
                activity.getOnBackPressedDispatcher().onBackPressed();
                assertFalse(activity.isFinishing());
            });
            onView(withText(R.string.keep_editing)).inRoot(isDialog()).perform(click());
            scenario.onActivity(activity -> {
                ((EditText) activity.findViewById(R.id.textEditor)).setText(ORIGINAL);
                activity.getOnBackPressedDispatcher().onBackPressed();
                assertTrue(activity.isFinishing());
            });
            assertEquals(ORIGINAL, readFile());
        }
    }

    @Test
    public void saveFailureRetainsFileTextAndDirtyStateThenAllowsRetry() throws IOException {
        // Leave an unmatched surrogate at EOF to force a real encoder failure,
        // after the temporary output has already received valid data.
        String unsavable = EDITED + '\uD800';
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.textEditor);
                editor.setText(unsavable);
                activity.findViewById(R.id.saveButton).performClick();
                assertFalse(activity.isFinishing());
                assertEquals(unsavable, editor.getText().toString());
                assertEquals(activity.getString(R.string.save_error),
                        ((TextView) activity.findViewById(R.id.status)).getText().toString());
            });
            assertEquals(ORIGINAL, readFile());
            scenario.recreate();
            scenario.onActivity(activity -> {
                assertEquals(unsavable, ((EditText) activity.findViewById(R.id.textEditor))
                        .getText().toString());
                assertEquals(activity.getString(R.string.save_error),
                        ((TextView) activity.findViewById(R.id.status)).getText().toString());
                activity.findViewById(R.id.cancelButton).performClick();
            });
            onView(withText(R.string.keep_editing)).inRoot(isDialog()).perform(click());
            scenario.onActivity(activity -> {
                ((EditText) activity.findViewById(R.id.textEditor)).setText(EDITED);
                activity.findViewById(R.id.saveButton).performClick();
                assertTrue(activity.isFinishing());
            });
            assertEquals(EDITED, readFile());
        }
    }

    @Test
    public void actualEditorRoundTripsUtf8WithoutAddingNuls() throws IOException {
        StringBuilder longText = new StringBuilder();
        for (int i = 0; i < 10000; ++i) {
            longText.append("# Long 中文\n");
        }
        for (String content : new String[] {"", "language = en", "# 中文\nlanguage = zh\n",
                "# 中文 😀\r\nlanguage = zh\r\n\r\nlast line", longText.toString()}) {
            byte[] original = content.getBytes(StandardCharsets.UTF_8);
            writeBytes(original);
            try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
                scenario.onActivity(activity -> {
                    assertEquals(content, ((EditText) activity.findViewById(R.id.textEditor))
                            .getText().toString());
                    activity.findViewById(R.id.saveButton).performClick();
                    assertTrue(activity.isFinishing());
                });
                assertArrayEquals(original, readBytes());
                assertEquals(original.length, file.length());
            }
        }
    }

    @Test
    public void unreadableUtf8CannotBeOverwrittenByAnEmptyEditor() throws IOException {
        byte[] invalid = {(byte) 0xc3, 0x28};
        writeBytes(invalid);
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> {
                assertFalse(activity.findViewById(R.id.saveButton).isEnabled());
                assertEquals(activity.getString(R.string.open_error),
                        ((TextView) activity.findViewById(R.id.status)).getText().toString());
            });
            assertEquals(invalid.length, file.length());
            try (FileInputStream input = new FileInputStream(file)) {
                assertEquals(0xc3, input.read());
                assertEquals(0x28, input.read());
                assertEquals(-1, input.read());
            }
        }
    }
}
