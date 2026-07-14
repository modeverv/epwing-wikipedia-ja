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
sub to_euc_jp {
    my ($value) = @_;
    return defined($value) ? encode('euc-jp', $value) : $value;
}

my $input_path = $ARGV[0] // 'entries.jsonl';

open my $input, '<:raw', $input_path or die "cannot open $input_path: $!\n";
my $json = JSON::PP->new->utf8;
my @entries;
my %tags;
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
}
close $input or die "cannot close $input_path: $!\n";

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
}

finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2);
