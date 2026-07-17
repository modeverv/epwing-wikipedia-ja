#!/usr/bin/env perl
# Generic FreePWING source builder: reads entries.jsonl (written by
# wikiepwing.render.freepwing_source.write_entries_jsonl) and drives
# FreePWING::FPWUtils::FPWParser to build the fpwmake source tree
# (work/text, work/heading, work/word2). Unlike
# tests/fixtures/handcrafted/build_fixture.pl (a fixed 3-entry/2-alias smoke
# fixture), this accepts any number of entries with any number of aliases
# or internal link targets (including zero).
use strict;
use warnings;

use Encode qw(encode);
use FreePWING::FPWUtils::FPWParser;
use JSON::PP;

# FPWParser expects EUC-JP byte strings (matching the encoding
# tests/fixtures/handcrafted's smoke test applies via `iconv` before Perl
# ever sees the data); entries.jsonl is UTF-8 (JSON's own encoding), so every
# string field is re-encoded to EUC-JP right after JSON decode.
#
# Perl's Encode module's "euc-jp" happily encodes JIS X 0212 supplementary
# characters too, using the SS3 (\x8f) prefix -- but FPWParser only
# understands plain two-byte JIS X 0208 and rejects any \x8f it sees with
# "invalid character". Real Wikipedia body text contains X 0212-only kanji,
# so encode() alone crashes the build on real (not fixture) data. Until
# proper gaiji (external character) substitution exists end-to-end
# (ARCHITECTURE.md 17.2/18.3/18.4's gaiji pipeline is implemented as library
# code but not yet wired into normalize/generate), fall back per-character:
# substitute a geta mark (GETA MARK, U+3013 -- the conventional Japanese
# "character cannot be displayed" placeholder, itself plain JIS X 0208) for
# anything that would otherwise need the SS3 prefix. This is a stopgap that
# loses those specific characters, not a real fix.
#
# This used to loop over the string one Perl-level character at a time,
# calling encode() per character -- at full scale (~1.5M entries, each with
# a title/body/aliases) that's on the order of a billion individual encode()
# calls, and Perl function-call overhead dominates. A JIS X 0212 sequence is
# always exactly SS3 (\x8f) + 2 bytes in 0xA1-0xFE, and \x8f cannot appear as
# a trailing byte of any other valid EUC-JP sequence (plain JIS X 0208's
# second byte and SS2 kana's second byte are both >= 0xA1, all above \x8f),
# so encoding the whole string in one call and then regex-substituting any
# \x8f + 2 bytes run is byte-for-byte equivalent to the old per-character
# loop, just without the per-character Perl call overhead.
my $GETA_MARK_EUC_JP = encode('euc-jp', "\x{3013}");

sub to_euc_jp {
    my ($value) = @_;
    return $value unless defined $value;
    my $bytes = encode('euc-jp', $value);
    $bytes =~ s/\x8f../$GETA_MARK_EUC_JP/gs;
    return $bytes;
}

# This script has no incremental output of its own (unlike wikiepwing's
# Python CLI stages, which all report progress); at full-scale (~1.5M
# entries) both loops below take long enough that silence reads as "did it
# hang?". `$PROGRESS_EVERY` entries, report a line count to stderr -- $| = 1
# so it's never buffered and delayed behind the loop's own work.
$| = 1;
my $PROGRESS_EVERY = 20_000;

my $input_path = $ARGV[0] // 'entries.jsonl';

my $total_lines = 0;
{
    open my $count_input, '<:raw', $input_path or die "cannot open $input_path: $!\n";
    $total_lines++ while <$count_input>;
    close $count_input or die "cannot close $input_path: $!\n";
}

open my $input, '<:raw', $input_path or die "cannot open $input_path: $!\n";
my $json = JSON::PP->new->utf8;
my @entries;
my %tags;
my $parsed = 0;
while (my $line = <$input>) {
    $line =~ s/\r?\n\z//;
    next if $line eq '';
    my $record = $json->decode($line);
    my $tag = to_euc_jp($record->{tag});
    die "invalid tag: " . ($tag // '') . "\n" if !defined($tag) || $tag !~ /\A[a-z][a-z0-9_-]{0,31}\z/;
    die "duplicate tag: $tag\n" if $tags{$tag}++;
    die "empty title for tag $tag\n" if !defined($record->{title}) || $record->{title} eq '';
    push @entries, {
        tag => $tag,
        title => to_euc_jp($record->{title}),
        aliases => [map { to_euc_jp($_) } @{$record->{aliases} // []}],
        body => to_euc_jp($record->{body}),
        targets => [map { to_euc_jp($_) } @{$record->{targets} // []}],
    };
    $parsed++;
    print STDERR "parse $parsed/$total_lines\n" if $parsed % $PROGRESS_EVERY == 0;
}
close $input or die "cannot close $input_path: $!\n";
print STDERR "parse $parsed/$total_lines\n";

die "no entries to build\n" if !@entries;

for my $entry (@entries) {
    for my $target (@{$entry->{targets} // []}) {
        die "unknown link target: $target\n" if !$tags{$target};
    }
}

initialize_fpwparser(
    'text' => \my $text,
    'heading' => \my $heading,
    'word2' => \my $word2,
);

my %global_headwords;
my $indexed = 0;
my $total_entries = scalar @entries;
for my $entry (@entries) {
    $text->new_entry() or die $text->error_message(), "\n";
    $heading->new_entry() or die $heading->error_message(), "\n";
    $heading->add_text($entry->{title}) or die $heading->error_message(), "\n";

    $text->add_tag($entry->{tag}) or die $text->error_message(), "\n";
    $text->add_text($entry->{title}) or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";

    if (defined $entry->{body} && $entry->{body} ne '') {
        $text->add_text($entry->{body}) or die $text->error_message(), "\n";
        $text->add_newline() or die $text->error_message(), "\n";
    }

    for my $target (@{$entry->{targets} // []}) {
        $text->add_reference_start() or die $text->error_message(), "\n";
        $text->add_text($target) or die $text->error_message(), "\n";
        $text->add_reference_end($target) or die $text->error_message(), "\n";
        $text->add_newline() or die $text->error_message(), "\n";
    }

    my %seen_in_entry;
    for my $headword ($entry->{title}, @{$entry->{aliases} // []}) {
        next if $seen_in_entry{$headword}++;
        die "duplicate headword: $headword\n" if $global_headwords{$headword}++;
        $word2->add_entry($headword, $heading->entry_position(), $text->entry_position())
            or die $word2->error_message(), "\n";
    }
    $indexed++;
    print STDERR "index $indexed/$total_entries\n" if $indexed % $PROGRESS_EVERY == 0;
}
print STDERR "index $indexed/$total_entries\n";

finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2);
