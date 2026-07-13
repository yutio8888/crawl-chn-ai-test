import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import net.sf.okapi.common.LocaleId;
import net.sf.okapi.common.pipeline.Pipeline;
import net.sf.okapi.common.resource.RawDocument;
import net.sf.okapi.filters.xliff.XLIFFFilter;
import net.sf.okapi.lib.verification.Parameters;
import net.sf.okapi.lib.verification.PatternItem;
import net.sf.okapi.steps.common.RawDocumentToFilterEventsStep;
import net.sf.okapi.steps.qualitycheck.QualityCheckStep;

/** Headless Okapi Quality Check runner for a bilingual XLIFF document. */
public final class OkapiQaRunner {
    private OkapiQaRunner() {}

    private static void usage() {
        System.err.println("Usage: OkapiQaRunner <input.xlf> <report.xml> [blacklist.tsv]");
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2 || args.length > 3) {
            usage();
            System.exit(2);
        }
        Path input = Paths.get(args[0]).toAbsolutePath();
        Path report = Paths.get(args[1]).toAbsolutePath();
        if (!Files.isRegularFile(input)) {
            throw new IllegalArgumentException("Input does not exist: " + input);
        }
        if (report.getParent() != null) {
            Files.createDirectories(report.getParent());
        }

        LocaleId source = new LocaleId("en");
        LocaleId target = new LocaleId("zh");
        RawDocument raw = new RawDocument(input.toUri(), "UTF-8", source, target);
        raw.setFilterConfigId("okf_xliff");

        Parameters parameters = new Parameters();
        parameters.setOutputPath(report.toString());
        // Okapi 1.48: 0 = HTML, 1 = tab-delimited, 2 = XML.
        parameters.setOutputType(2);
        parameters.setAutoOpen(false);
        parameters.setEmptyTarget(true);
        parameters.setTargetSameAsSource(true);
        parameters.setCodeDifference(true);
        parameters.setLeadingWS(true);
        parameters.setTrailingWS(true);
        // Chinese translations are commonly shorter than English source.
        // Use 20% for short source segments and 25% for longer ones.
        parameters.setCheckMinCharLength(true);
        parameters.setMinCharLengthBreak(20);
        parameters.setMinCharLengthBelow(20);
        parameters.setMinCharLengthAbove(25);
        parameters.setCheckPatterns(true);
        // The project already validates printf parameters independently.
        // Keep Okapi's other pattern checks without duplicating that gate.
        for (PatternItem pattern : parameters.getPatterns()) {
            if ("C-style printf codes".equals(pattern.description)) {
                pattern.enabled = false;
            }
        }
        // Project terminology is checked by check_terms.py. Okapi's SimpleTB
        // checker cannot express multiple legal translations or domain rules.
        parameters.setCheckTerms(false);
        if (args.length == 3) {
            parameters.setCheckBlacklist(true);
            parameters.setblacklistPath(Paths.get(args[2]).toAbsolutePath().toString());
        }

        RawDocumentToFilterEventsStep extract =
            new RawDocumentToFilterEventsStep(new XLIFFFilter());
        QualityCheckStep quality = new QualityCheckStep();
        quality.setParameters(parameters);
        quality.setSourceLocale(source);
        quality.setTargetLocale(target);
        quality.setRootDirectory(input.getParent().toString());

        Pipeline pipeline = new Pipeline();
        pipeline.addStep(extract);
        pipeline.addStep(quality);
        pipeline.startBatch();
        pipeline.process(raw);
        pipeline.endBatch();
        pipeline.destroy();
        System.out.println("Wrote Okapi QA report: " + report);
    }
}
