package org.develz.crawl;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

import org.junit.Test;

public class DCSSTextFileTest {
    @Test
    public void utf8RoundTripsWithoutPaddingOrNewlineChanges() throws Exception {
        StringBuilder longText = new StringBuilder();
        for (int i = 0; i < 10000; ++i) {
            longText.append("# 中文 comment ").append(i).append("\nlanguage = zh\n");
        }
        for (String text : new String[] {"", "language = en\n", "# 中文\nlanguage = zh\n",
                "# 中文 😀\r\nlanguage = zh\r\n# no final newline", longText.toString()}) {
            byte[] original = text.getBytes(StandardCharsets.UTF_8);
            String decoded = DCSSTextFile.readUtf8(new ByteArrayInputStream(original));
            assertEquals(text, decoded);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            DCSSTextFile.writeUtf8(output, decoded);
            assertArrayEquals(original, output.toByteArray());
        }
    }

    @Test
    public void shortReadsAndZeroAvailableDoNotTruncateMultibyteText() throws Exception {
        String original = "# 中文 😀\nlanguage = zh\n";
        ByteArrayInputStream input = new ByteArrayInputStream(
                original.getBytes(StandardCharsets.UTF_8)) {
            @Override
            public synchronized int read(byte[] bytes, int offset, int length) {
                return super.read(bytes, offset, Math.min(length, 1));
            }

            @Override
            public synchronized int available() {
                return 0;
            }
        };
        assertEquals(original, DCSSTextFile.readUtf8(input));
    }

    @Test
    public void writeErrorsPropagateToTheSaveTransaction() throws Exception {
        OutputStream failing = new OutputStream() {
            private int written;

            @Override
            public void write(int value) throws IOException {
                if (++written == 4) {
                    throw new IOException("Injected full storage");
                }
            }
        };
        try {
            DCSSTextFile.writeUtf8(failing, "# 中文\nlanguage = zh\n");
            fail("A partial write must not look successful");
        } catch (IOException expected) {
            assertEquals("Injected full storage", expected.getMessage());
        }
    }
}
