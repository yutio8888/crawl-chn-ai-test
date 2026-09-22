package org.develz.crawl;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.RootMatchers.isDialog;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import android.content.Context;
import android.content.Intent;
import android.system.Os;
import android.widget.EditText;

import androidx.lifecycle.Lifecycle;
import androidx.lifecycle.LifecycleEventObserver;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class DCSSTextEditorUiTest {
    private static final String ORIGINAL = "# 中文\nlanguage = zh\n";
    private static final String DRAFT = ORIGINAL + "# unsaved edit\n";
    private File directory;
    private File file;

    @Before
    public void createFile() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        directory = File.createTempFile("editor-test-", "", context.getCacheDir());
        assertTrue(directory.delete());
        assertTrue(directory.mkdir());
        file = new File(directory, "init.txt");
        writeOriginal(ORIGINAL);
    }

    @After
    public void removeFile() throws Exception {
        if (directory != null && directory.exists()) {
            Os.chmod(directory.getAbsolutePath(), 0700);
            File[] children = directory.listFiles();
            if (children != null) {
                for (File child : children) {
                    assertTrue(child.delete());
                }
            }
            assertTrue(directory.delete());
        }
    }

    @Test
    public void editorSavesEmptyAsciiUnicodeAndLongFilesByteForByte() throws Exception {
        StringBuilder longText = new StringBuilder();
        for (int i = 0; i < 5000; ++i) {
            longText.append("# 中文 ").append(i).append("\nlanguage = zh\n");
        }
        for (String text : new String[] {"", "language = en\r\n", ORIGINAL,
                "# 中文 😀\r\nlanguage = zh", longText.toString()}) {
            writeOriginal(text);
            try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
                CountDownLatch destroyed = observeDestruction(scenario);
                scenario.onActivity(activity -> {
                    EditText editor = activity.findViewById(R.id.textEditor);
                    assertEquals(text, editor.getText().toString());
                    activity.findViewById(R.id.saveButton).performClick();
                });
                awaitDestruction(destroyed);
            }
            assertArrayEquals(text.getBytes(StandardCharsets.UTF_8), readBytes(file));
            assertEquals(1, directory.list().length);
        }
    }

    @Test
    public void unchangedCancelAndSystemBackCloseDirectly() throws Exception {
        for (boolean systemBack : new boolean[] {false, true}) {
            try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
                CountDownLatch destroyed = observeDestruction(scenario);
                scenario.onActivity(activity -> {
                    if (systemBack) {
                        activity.getOnBackPressedDispatcher().onBackPressed();
                    } else {
                        activity.findViewById(R.id.cancelButton).performClick();
                    }
                });
                awaitDestruction(destroyed);
            }
        }
    }

    @Test
    public void cancelKeepsDraftAndSystemBackRequiresExplicitDiscard() throws Exception {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            CountDownLatch destroyed = observeDestruction(scenario);
            scenario.onActivity(activity -> {
                ((EditText) activity.findViewById(R.id.textEditor)).setText(DRAFT);
                activity.findViewById(R.id.cancelButton).performClick();
            });
            onView(withText(R.string.discard_changes_title)).inRoot(isDialog())
                    .check(matches(isDisplayed()));
            onView(withText(R.string.keep_editing)).inRoot(isDialog()).perform(click());
            scenario.onActivity(activity -> {
                assertFalse(activity.isFinishing());
                assertEquals(DRAFT, ((EditText) activity.findViewById(R.id.textEditor))
                        .getText().toString());
                activity.getOnBackPressedDispatcher().onBackPressed();
            });
            onView(withText(R.string.discard_changes_message)).inRoot(isDialog())
                    .check(matches(isDisplayed()));
            onView(withText(R.string.discard_changes)).inRoot(isDialog()).perform(click());
            awaitDestruction(destroyed);
        }
        assertArrayEquals(ORIGINAL.getBytes(StandardCharsets.UTF_8), readBytes(file));
    }

    @Test
    public void restoringOriginalTextClearsDirtyState() throws Exception {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            CountDownLatch destroyed = observeDestruction(scenario);
            scenario.onActivity(activity -> {
                EditText editor = activity.findViewById(R.id.textEditor);
                editor.setText(DRAFT);
                editor.setText(ORIGINAL);
                activity.findViewById(R.id.cancelButton).performClick();
            });
            awaitDestruction(destroyed);
        }
    }

    @Test
    public void recreationPreservesDraftAndUnsavedBaseline() {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            scenario.onActivity(activity -> ((EditText) activity.findViewById(R.id.textEditor))
                    .setText(DRAFT));
            scenario.recreate();
            scenario.onActivity(activity -> {
                assertEquals(DRAFT, ((EditText) activity.findViewById(R.id.textEditor))
                        .getText().toString());
                activity.getOnBackPressedDispatcher().onBackPressed();
            });
            onView(withText(R.string.discard_changes_title)).inRoot(isDialog())
                    .check(matches(isDisplayed()));
            onView(withText(R.string.keep_editing)).inRoot(isDialog()).perform(click());
        }
    }

    @Test
    public void failedSavePreservesOriginalAndDraftForRetry() throws Exception {
        try (ActivityScenario<DCSSTextEditor> scenario = launch()) {
            CountDownLatch destroyed = observeDestruction(scenario);
            Os.chmod(directory.getAbsolutePath(), 0500);
            try {
                scenario.onActivity(activity -> {
                    ((EditText) activity.findViewById(R.id.textEditor)).setText(DRAFT);
                    activity.findViewById(R.id.saveButton).performClick();
                    assertFalse(activity.isFinishing());
                    assertEquals(DRAFT, ((EditText) activity.findViewById(R.id.textEditor))
                            .getText().toString());
                });
                onView(withId(R.id.status)).check(matches(withText(R.string.save_error)));
                assertArrayEquals(ORIGINAL.getBytes(StandardCharsets.UTF_8), readBytes(file));
            } finally {
                Os.chmod(directory.getAbsolutePath(), 0700);
            }
            scenario.onActivity(activity -> activity.findViewById(R.id.saveButton).performClick());
            awaitDestruction(destroyed);
        }
        assertArrayEquals(DRAFT.getBytes(StandardCharsets.UTF_8), readBytes(file));
        assertEquals(1, directory.list().length);
    }

    @Test
    public void failedReplacementDoesNotReportSuccessOrLeaveTemporaryFiles() throws Exception {
        // A destination that has become a directory must reject the commit.
        File blockedDestination = new File(directory, "blocked");
        assertTrue(blockedDestination.mkdir());
        try {
            DCSSTextFile.save(blockedDestination, DRAFT);
            fail("Replacing a directory with a file must fail");
        } catch (IOException expected) {
            assertTrue(blockedDestination.isDirectory());
            assertArrayEquals(ORIGINAL.getBytes(StandardCharsets.UTF_8), readBytes(file));
            assertEquals(2, directory.list().length);
        } finally {
            assertTrue(blockedDestination.delete());
        }
    }

    private ActivityScenario<DCSSTextEditor> launch() {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        Intent intent = new Intent(context, DCSSTextEditor.class);
        intent.putExtra("file", file);
        return ActivityScenario.launch(intent);
    }

    private static CountDownLatch observeDestruction(ActivityScenario<DCSSTextEditor> scenario) {
        CountDownLatch destroyed = new CountDownLatch(1);
        scenario.onActivity(activity -> activity.getLifecycle().addObserver(
                (LifecycleEventObserver) (source, event) -> {
                    if (event == Lifecycle.Event.ON_DESTROY) {
                        destroyed.countDown();
                    }
                }));
        return destroyed;
    }

    private static void awaitDestruction(CountDownLatch destroyed) throws InterruptedException {
        // An idle main queue does not mean the window's exit animation and the
        // asynchronous Activity destruction have completed. Observe that event
        // without calling scenario.close(), which would itself force a finish.
        assertTrue("The editor did not finish", destroyed.await(5, TimeUnit.SECONDS));
    }

    private void writeOriginal(String text) throws IOException {
        try (FileOutputStream output = new FileOutputStream(file)) {
            output.write(text.getBytes(StandardCharsets.UTF_8));
        }
    }

    private static byte[] readBytes(File source) throws IOException {
        try (FileInputStream input = new FileInputStream(source)) {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
