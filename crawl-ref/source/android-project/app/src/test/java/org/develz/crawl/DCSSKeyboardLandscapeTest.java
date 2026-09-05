package org.develz.crawl;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class DCSSKeyboardLandscapeTest {
    @Test
    public void compactLandscapePreservesSquareViewport() {
        assertTrue(DCSSKeyboard.canSplit(700, 320, 48, 320));
        assertTrue(DCSSKeyboard.canSplit(960, 540, 56, 320));
        assertTrue(DCSSKeyboard.canSplit(656, 320, 48, 320));
        assertFalse(DCSSKeyboard.canSplit(655, 320, 48, 320));
    }

    @Test
    public void portraitAndUnmeasuredContentStayAtBottom() {
        assertFalse(DCSSKeyboard.canSplit(320, 640, 48, 320));
        assertFalse(DCSSKeyboard.canSplit(640, 640, 48, 320));
        assertFalse(DCSSKeyboard.canSplit(0, 0, 48, 320));
        assertFalse(DCSSKeyboard.canSplit(640, 320, 0, 320));
    }

    @Test
    public void oversizedPreferenceAndShortWindowFallBack() {
        assertFalse(DCSSKeyboard.canSplit(700, 320, 56, 320));
        assertFalse(DCSSKeyboard.canSplit(700, 143, 48, 320));
        assertTrue(DCSSKeyboard.canSplit(700, 144, 48, 320));
        // Evaluate pixels at the same density, including the central floor.
        assertTrue(DCSSKeyboard.canSplit(1640, 800, 120, 800));
        assertFalse(DCSSKeyboard.canSplit(1639, 800, 120, 800));
    }
}
