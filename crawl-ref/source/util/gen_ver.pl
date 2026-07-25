#!/usr/bin/env perl

use strict;
use warnings;

use File::Basename;

my $scriptpath = dirname($0);
my $outfile = $ARGV[0];
my $mergebase = $ARGV[1];
my $nullfile = @ARGV >= 3 ? $ARGV[2] : "/dev/null";

$mergebase or $mergebase = "";

mkdir dirname($outfile);

# to build without git or with a shallow clone, you will need to generate
# the file `release_ver` somehow with version information. This file is just
# intended to contain the output of `git describe`, and anything that
# conforms to the regex below is fine. For example, "0.28-a" would be safe.
#
# Source tarbells distributed as part of a release include this file already
# generated with the release version.
$_ = `git describe $mergebase 2> $nullfile`
    || (open(IN, "<", "$scriptpath/release_ver") ? <IN>
        : die "Error: Can't get version information: `git describe` failed (no git, no repository, or shallow clone), and $scriptpath/release_ver doesn't exist.\n")
    or die "Error: couldn't get the version information\n";

chomp;

/v?(?<tag>(?<major>[0-9]+\.[0-9]+)(?:\.[0-9]+)?(?:-(?<pretyp>[a-zA-Z]+[0-9]+(?:-[0-9]+-[0-9]{3})?))?)(?:-[0-9]+-g[a-fA-F0-9]+)?/
    or die "Version string '$_' is malformed.\n";

my ($major, $tag, $pretyp) = @+{qw(major tag pretyp)};

my $rel = !defined($pretyp)
    || $pretyp =~ /^zh[1-9][0-9]*$/
    || $pretyp =~ /^zh[1-9][0-9]*-[1-9][0-9]*-(?:00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})$/
    ? "FINAL"
    : $pretyp le "b" ? "ALPHA" : "BETA";

my $prefix = "CRAWL";

open OUT, ">", "$outfile" or die $!;
print OUT <<__eof__;
#define ${prefix}_VERSION_MAJOR "$major"
#define ${prefix}_VERSION_RELEASE VER_$rel
#define ${prefix}_VERSION_SHORT "$tag"
#define ${prefix}_VERSION_LONG "$_"
__eof__
close OUT or die $!;
