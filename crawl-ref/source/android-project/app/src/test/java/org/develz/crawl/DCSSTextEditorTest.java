package org.develz.crawl;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertThrows;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Locale;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

public class DCSSTextEditorTest {
    @Rule
    public TemporaryFolder folder = new TemporaryFolder();

    @Test
    public void unchangedUtf8FilesRoundTripByteForByte() throws IOException {
        String longText = "# 中文配置 😀\r\nlanguage = zh\n".repeat(10000);
        for (String content : new String[] {"", "language = en", "# 中文\nlanguage = zh\n",
                "# Mixed 中文 😀\r\nlanguage = zh\r\n\r\n# no final newline",
                "\uFEFF# UTF-8 BOM\n", longText}) {
            File file = folder.newFile();
            byte[] original = content.getBytes(StandardCharsets.UTF_8);
            Files.write(file.toPath(), original);

            String loaded = DCSSTextBase.readUtf8(new FileInputStream(file));
            assertEquals(content, loaded);
            DCSSTextBase.writeUtf8(file, loaded);

            assertArrayEquals(original, Files.readAllBytes(file.toPath()));
        }
    }

    @Test
    public void readsThroughShortReadsAndClosesInput() throws IOException {
        String content = "# 中文 😀\nlanguage = zh\n".repeat(1000);
        boolean[] closed = {false};
        ByteArrayInputStream input = new ByteArrayInputStream(
                content.getBytes(StandardCharsets.UTF_8)) {
            @Override
            public synchronized int read(byte[] bytes, int offset, int length) {
                return super.read(bytes, offset, Math.min(length, 3));
            }

            @Override
            public synchronized int available() {
                return 0;
            }

            @Override
            public void close() throws IOException {
                closed[0] = true;
                super.close();
            }
        };
        assertEquals(content, DCSSTextBase.readUtf8(input));
        assertTrue(closed[0]);
    }

    @Test
    public void malformedUtf8IsRejectedInsteadOfSilentlyReplaced() {
        assertThrows(IOException.class, () -> DCSSTextBase.readUtf8(
                new ByteArrayInputStream(new byte[] {(byte) 0xc3, 0x28})));
    }

    @Test
    public void failedWritePreservesOriginalAndRemovesTemporaryFile() throws IOException {
        File file = folder.newFile("init.txt");
        byte[] original = "# Original 中文\n".getBytes(StandardCharsets.UTF_8);
        Files.write(file.toPath(), original);
        // An incomplete surrogate fails the UTF-8 encoder after writing a long
        // prefix, exercising failure after the temporary file has received data.
        String invalidText = "language = zh\n".repeat(10000) + '\uD800';

        assertThrows(IOException.class, () -> DCSSTextBase.writeUtf8(file, invalidText));

        assertArrayEquals(original, Files.readAllBytes(file.toPath()));
        assertArrayEquals(new String[] {"init.txt"}, folder.getRoot().list());
    }

    @Test
    public void failedReplacementPreservesDestinationAndRemovesTemporaryFile() throws IOException {
        File target = folder.newFolder("init.txt");
        File original = new File(target, "keep.txt");
        byte[] bytes = "Original data".getBytes(StandardCharsets.UTF_8);
        Files.write(original.toPath(), bytes);

        assertThrows(IOException.class, () -> DCSSTextBase.writeUtf8(target, "new text"));

        assertTrue(target.isDirectory());
        assertArrayEquals(bytes, Files.readAllBytes(original.toPath()));
        assertArrayEquals(new String[] {"init.txt"}, folder.getRoot().list());
    }

    @Test
    public void chineseLocalesSelectLocalizedGuide() {
        assertEquals("docs/zh/options_guide.txt",
                DCSSTextEditor.optionsGuideAsset(Locale.SIMPLIFIED_CHINESE));
        assertEquals("docs/zh/options_guide.txt",
                DCSSTextEditor.optionsGuideAsset(Locale.TRADITIONAL_CHINESE));
    }

    @Test
    public void nonChineseLocalesSelectEnglishGuide() {
        assertEquals("docs/options_guide.txt",
                DCSSTextEditor.optionsGuideAsset(Locale.ENGLISH));
        assertEquals("docs/options_guide.txt",
                DCSSTextEditor.optionsGuideAsset(null));
    }

    @Test
    public void defaultLocaleCanBeSelectedAndRestored() {
        Locale saved = Locale.getDefault();
        try {
            Locale.setDefault(Locale.SIMPLIFIED_CHINESE);
            assertEquals("docs/zh/options_guide.txt",
                    DCSSTextEditor.optionsGuideAsset(Locale.getDefault()));
        } finally {
            Locale.setDefault(saved);
        }
        assertEquals(saved, Locale.getDefault());
    }
}
