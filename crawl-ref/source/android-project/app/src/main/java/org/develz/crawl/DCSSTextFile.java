package org.develz.crawl;

import android.system.ErrnoException;
import android.system.Os;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.Reader;
import java.nio.charset.StandardCharsets;

final class DCSSTextFile {
    private DCSSTextFile() {}

    // The caller owns the stream. A byte count is not a character count, and
    // neither read() nor available() promises to return the entire file.
    static String readUtf8(InputStream input) throws IOException {
        Reader reader = new InputStreamReader(input, StandardCharsets.UTF_8);
        StringBuilder text = new StringBuilder();
        char[] buffer = new char[4096];
        int count;
        while ((count = reader.read(buffer)) != -1) {
            text.append(buffer, 0, count);
        }
        return text.toString();
    }

    static void writeUtf8(OutputStream output, CharSequence text) throws IOException {
        output.write(text.toString().getBytes(StandardCharsets.UTF_8));
        output.flush();
    }

    static void save(File file, CharSequence text) throws IOException {
        File destination = file.getAbsoluteFile();
        File temporary = File.createTempFile("dcss-", ".tmp", destination.getParentFile());
        try {
            try (FileOutputStream output = new FileOutputStream(temporary)) {
                writeUtf8(output, text);
                output.getFD().sync();
            }
            // Same-directory rename commits only after writing, syncing and
            // closing succeeded. Unlike AtomicFile.finishWrite(), Os.rename()
            // reports a failed replacement so the editor can show save_error.
            try {
                Os.rename(temporary.getAbsolutePath(), destination.getAbsolutePath());
            } catch (ErrnoException e) {
                throw new IOException("Can't replace file", e);
            }
        } finally {
            // After a successful rename the temporary path no longer exists.
            temporary.delete();
        }
    }
}
