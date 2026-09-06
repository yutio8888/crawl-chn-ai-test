package org.develz.crawl;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class DCSSKeyboardAutofightRepeatTest {
    @Test
    public void heldKeyKeepsRepeatingUpToTheCap() {
        for (int sent = 0; sent < DCSSKeyboard.AUTOFIGHT_MAX_REPEATS; ++sent) {
            assertEquals(DCSSKeyboard.AUTOFIGHT_REPEAT_INTERVAL_MS,
                    DCSSKeyboard.autofightRepeatDelayMs(sent));
        }
    }

    @Test
    public void repeatStopsAtTheCap() {
        assertEquals(-1, DCSSKeyboard.autofightRepeatDelayMs(
                DCSSKeyboard.AUTOFIGHT_MAX_REPEATS));
        assertEquals(-1, DCSSKeyboard.autofightRepeatDelayMs(
                DCSSKeyboard.AUTOFIGHT_MAX_REPEATS + 1));
    }

    @Test
    public void holdStaysWithinAReasonableBound() {
        long total = DCSSKeyboard.AUTOFIGHT_MAX_REPEATS
                * DCSSKeyboard.AUTOFIGHT_REPEAT_INTERVAL_MS;
        assertTrue("a single hold should not drive the game for minutes",
                total <= 30000);
    }
}
