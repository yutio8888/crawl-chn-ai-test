package org.develz.crawl;

import static org.junit.Assert.assertEquals;

import java.util.Locale;

import org.junit.Test;

public class DCSSTextEditorTest {
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
