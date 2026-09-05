package org.develz.crawl;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class DCSSLauncherKeyboardSizeTest {
    @Test
    public void validCommittedSizeIsPreserved() {
        assertEquals(56, DCSSLauncher.normalizeKeyboardSizeDp("56", 4, 40, 60));
        assertEquals(32, DCSSLauncher.normalizeKeyboardSizeDp("32", 1, 40, 60));
    }

    @Test
    public void invalidCommittedInputUsesModeAppropriateDefault() {
        for (String input : new String[] {"", "not a number", "999999999999999999"}) {
            assertEquals(40, DCSSLauncher.normalizeKeyboardSizeDp(input, 1, 40, 60));
            assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp(input, 4, 40, 60));
        }
    }

    @Test
    public void committedInputIsLimitedByDisplaySize() {
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("999", 1, 40, 60));
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("999", 4, 40, 60));
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("60", 4, 40, 60));
        // Preserve the existing default-size floor for very small displays.
        assertEquals(40, DCSSLauncher.normalizeKeyboardSizeDp("999", 1, 40, 30));
        assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp("999", 4, 40, 30));
    }

    @Test
    public void compactModeMatchesItsRenderedMinimumIncludingOldPreferences() {
        for (String input : new String[] {"-1", "0", "1", "40", "47", "48"}) {
            assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp(input, 4, 40, 60));
        }
        assertEquals(49, DCSSLauncher.normalizeKeyboardSizeDp("49", 4, 40, 60));
    }

    @Test
    public void otherModesRetainZeroAndSmallSizes() {
        for (int mode : new int[] {0, 1, 2, 3}) {
            assertEquals(0, DCSSLauncher.normalizeKeyboardSizeDp("0", mode, 40, 60));
            assertEquals(0, DCSSLauncher.normalizeKeyboardSizeDp("-1", mode, 40, 60));
            assertEquals(1, DCSSLauncher.normalizeKeyboardSizeDp("1", mode, 40, 60));
        }
    }
}
