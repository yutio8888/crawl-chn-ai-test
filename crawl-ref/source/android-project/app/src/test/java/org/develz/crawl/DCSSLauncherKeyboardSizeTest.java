package org.develz.crawl;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class DCSSLauncherKeyboardSizeTest {
    @Test
    public void validCommittedSizeIsPreserved() {
        assertEquals(56, DCSSLauncher.normalizeKeyboardSizeDp("56", 4, 40, 60));
        assertEquals(52, DCSSLauncher.normalizeKeyboardSizeDp("52", 1, 40, 60));
    }

    @Test
    public void invalidCommittedInputUsesModeAppropriateDefault() {
        for (String input : new String[] {"", "not a number", "999999999999999999"}) {
            assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp(input, 1, 40, 60));
            assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp(input, 4, 40, 60));
        }
    }

    @Test
    public void committedInputIsLimitedByDisplaySize() {
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("999", 1, 40, 60));
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("999", 4, 40, 60));
        assertEquals(60, DCSSLauncher.normalizeKeyboardSizeDp("60", 4, 40, 60));
        // Preserve the existing default-size floor for very small displays.
        assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp("999", 1, 40, 30));
        assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp("999", 4, 40, 30));
    }

    @Test
    public void customModesMatchTheirRenderedMinimumIncludingOldPreferences() {
        for (int mode : new int[] {1, 2, 4}) {
            for (String input : new String[] {"-1", "0", "1", "40", "47", "48"}) {
                assertEquals(48, DCSSLauncher.normalizeKeyboardSizeDp(input, mode, 40, 60));
            }
            assertEquals(49, DCSSLauncher.normalizeKeyboardSizeDp("49", mode, 40, 60));
        }
    }

    @Test
    public void otherModesRetainZeroAndSmallSizes() {
        for (int mode : new int[] {0, 3}) {
            assertEquals(0, DCSSLauncher.normalizeKeyboardSizeDp("0", mode, 40, 60));
            assertEquals(0, DCSSLauncher.normalizeKeyboardSizeDp("-1", mode, 40, 60));
            assertEquals(1, DCSSLauncher.normalizeKeyboardSizeDp("1", mode, 40, 60));
        }
    }
    @Test
    public void readingScaleAcceptsOnlyTheAvailablePresets() {
        for (int scale : new int[] {80, 100, 120, 150}) {
            assertEquals(scale, DCSSLauncher.normalizeReadingScale(scale));
        }
        for (int scale : new int[] {-1, 0, 79, 81, 101, 149, 151, Integer.MAX_VALUE}) {
            assertEquals(100, DCSSLauncher.normalizeReadingScale(scale));
        }
    }
}
