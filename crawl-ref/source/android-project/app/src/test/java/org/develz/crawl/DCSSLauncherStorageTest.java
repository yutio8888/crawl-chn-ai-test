package org.develz.crawl;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;

import org.junit.Test;

public class DCSSLauncherStorageTest {
    @Test
    public void createsFreshInstallDirectoryLayout() throws IOException {
        Path root = Files.createTempDirectory("dcss-launcher-storage");
        try {
            assertTrue(DCSSLauncher.createGameDirectories(root.toFile(), "test-version"));
            assertTrue(new File(root.toFile(), "saves").isDirectory());
            assertTrue(new File(root.toFile(), "morgue").isDirectory());
            assertTrue(new File(root.toFile(), "saves/bones").isDirectory());
            assertTrue(new File(root.toFile(), "saves/sprint/bones").isDirectory());
            assertTrue(new File(root.toFile(), "saves/descent/bones").isDirectory());
            assertTrue(new File(root.toFile(),
                    "saves/cache.test-version/db").isDirectory());
            assertTrue(new File(root.toFile(),
                    "saves/cache.test-version/des").isDirectory());

            // Existing save and cache directories must remain usable on update.
            assertTrue(DCSSLauncher.createGameDirectories(root.toFile(), "test-version"));
        } finally {
            try (var paths = Files.walk(root)) {
                paths.sorted(Comparator.reverseOrder())
                        .map(Path::toFile)
                        .forEach(File::delete);
            }
        }
    }

    @Test
    public void rejectsUnavailableExternalStorage() {
        assertFalse(DCSSLauncher.createGameDirectories(null, "test-version"));
    }
}
