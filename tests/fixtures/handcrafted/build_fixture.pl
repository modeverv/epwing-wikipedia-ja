#!/usr/bin/env perl
use strict;
use warnings;

use FreePWING::FPWUtils::FPWParser;

my @entries;
my %tags;
my %headwords;

open my $input, '<:raw', 'entries.tsv' or die "cannot open entries.tsv: $!\n";
while (my $line = <$input>) {
    die "fixture line exceeds 4096 bytes\n" if length($line) > 4096;
    $line =~ s/\r?\n\z//;
    my @fields = split /\t/, $line, -1;
    die "fixture row must have exactly five fields\n" if @fields != 5;
    my ($tag, $title, $alias_text, $body, $target) = @fields;
    die "invalid tag: $tag\n" if $tag !~ /\A[a-z][a-z0-9_-]{0,31}\z/;
    die "duplicate tag: $tag\n" if $tags{$tag}++;
    die "empty title or body\n" if $title eq '' || $body eq '';

    my @aliases = split /\|/, $alias_text, -1;
    die "each entry must have exactly two aliases\n" if @aliases != 2;
    for my $headword ($title, @aliases) {
        die "empty headword\n" if $headword eq '';
        die "headword exceeds 128 bytes\n" if length($headword) > 128;
        die "duplicate headword: $headword\n" if $headwords{$headword}++;
    }
    push @entries, {
        tag => $tag,
        title => $title,
        aliases => \@aliases,
        body => $body,
        target => $target,
    };
}
close $input or die "cannot close entries.tsv: $!\n";

die "fixture must contain exactly three entries\n" if @entries != 3;
for my $entry (@entries) {
    die "unknown link target: $entry->{target}\n" if !$tags{$entry->{target}};
}

initialize_fpwparser(
    'text' => \my $text,
    'heading' => \my $heading,
    'word2' => \my $word2,
);

for my $entry (@entries) {
    $text->new_entry() or die $text->error_message(), "\n";
    $heading->new_entry() or die $heading->error_message(), "\n";
    $heading->add_text($entry->{title}) or die $heading->error_message(), "\n";

    $text->add_tag($entry->{tag}) or die $text->error_message(), "\n";
    $text->add_text($entry->{title}) or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";
    $text->add_text($entry->{body}) or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";
    if ($entry->{tag} eq "wikipedia") {
        $text->add_color_graphic_start("wiki-mark") or die $text->error_message(), "\n";
        $text->add_text("[image]") or die $text->error_message(), "\n";
        $text->add_color_graphic_end() or die $text->error_message(), "\n";
        $text->add_newline() or die $text->error_message(), "\n";
    }
    if ($entry->{tag} eq "linux") {
        $text->add_text("gaiji: ") or die $text->error_message(), "\n";
        $text->add_half_user_character("half-mark") or die $text->error_message(), "\n";
        $text->add_text(" ") or die $text->error_message(), "\n";
        $text->add_full_user_character("full-mark") or die $text->error_message(), "\n";
        $text->add_newline() or die $text->error_message(), "\n";
    }
    $text->add_reference_start() or die $text->error_message(), "\n";
    $text->add_text($entry->{target}) or die $text->error_message(), "\n";
    $text->add_reference_end($entry->{target}) or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";

    for my $headword ($entry->{title}, @{$entry->{aliases}}) {
        $word2->add_entry($headword, $heading->entry_position(), $text->entry_position())
            or die $word2->error_message(), "\n";
    }
}

finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2);
