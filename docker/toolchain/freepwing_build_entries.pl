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
# string field is re-encoded to EUC-JP right after JSON decode (except body
# text -- see add_text_with_gaiji below).
#
# Perl's Encode module's "euc-jp" happily encodes JIS X 0212 supplementary
# characters too, using the SS3 (\x8f) prefix -- but FPWParser only
# understands plain two-byte JIS X 0208 and rejects any \x8f it sees with
# "invalid character" (TASK-T013). wikiepwing's gaiji pipeline
# (wikiepwing.gaiji.embedding, wired into wikiepwing.render.freepwing_source
# and wikiepwing.render.generate, GAIJI.md) resolves every such character
# before entries.jsonl is even written: title/alias text gets the plain
# `[U+XXXX]` fallback (itself plain ASCII, safe for to_euc_jp as-is), and
# body text gets an `@@GAIJI:<code>@@` placeholder token that
# add_text_with_gaiji below turns into a real gaiji reference. So by the
# time any string reaches to_euc_jp, it must not contain a JIS X
# 0212-only character any more -- encode() is left to raise on \x8f as a
# defensive check (rather than silently substituting a geta mark, this
# script's previous stopgap) in case that invariant is ever violated
# upstream.
sub to_euc_jp {
    my ($value) = @_;
    return $value unless defined $value;
    my $bytes = encode('euc-jp', $value);
    die "invalid character: unresolved JIS X 0212 (SS3) byte in: $value\n"
        if $bytes =~ /\x8f/;
    return $bytes;
}

# GAIJI_TOKEN matches wikiepwing.gaiji.embedding.GAIJI_TOKEN_FORMAT
# ("@@GAIJI:<code>@@") and wikiepwing.gaiji.code_assignment's
# "<narrow|wide>-NNNN" assigned_code format, so the width class needed to
# choose add_half_user_character vs add_full_user_character is read directly
# off the token's own prefix -- no separate lookup table is needed here.
my $GAIJI_TOKEN = qr/\@\@GAIJI:([a-z0-9-]+)\@\@/;

# Splits $value on GAIJI_TOKEN (v1/toolchain/records/build_records.pl's
# proven placeholder-token design) and feeds each piece to $writer: plain
# text through to_euc_jp/add_text, gaiji codes through
# add_half_user_character/add_full_user_character
# (tests/fixtures/handcrafted/build_fixture.pl demonstrates both real API
# calls). A capturing split alternates [text, code, text, code, ..., text],
# so odd indices are always the captured gaiji code.
sub add_text_with_gaiji {
    my ($writer, $value) = @_;
    return unless defined $value && $value ne '';
    my @pieces = split(/$GAIJI_TOKEN/, $value, -1);
    for my $index (0 .. $#pieces) {
        my $piece = $pieces[$index];
        next unless defined $piece && length($piece);
        if ($index % 2 == 1) {
            if ($piece =~ /^narrow-/) {
                $writer->add_half_user_character($piece) or die $writer->error_message(), "\n";
            } elsif ($piece =~ /^wide-/) {
                $writer->add_full_user_character($piece) or die $writer->error_message(), "\n";
            } else {
                die "invalid gaiji code: $piece\n";
            }
        } else {
            $writer->add_text(to_euc_jp($piece)) or die $writer->error_message(), "\n";
        }
    }
}

# This script has no incremental output of its own (unlike wikiepwing's
# Python CLI stages, which all report progress); at full-scale (~1.5M
# entries) both loops below take long enough that silence reads as "did it
# hang?". `$PROGRESS_EVERY` entries, report a line count to stderr -- $| = 1
# so it's never buffered and delayed behind the loop's own work.
$| = 1;
my $PROGRESS_EVERY = 10;

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
        # Not pre-encoded here: body may contain @@GAIJI:...@@ placeholder
        # tokens interleaved with plain text, and only add_text_with_gaiji
        # (called per-entry below) knows how to split those apart before
        # encoding the plain-text pieces.
        body => $record->{body},
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
        add_text_with_gaiji($text, $entry->{body});
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
