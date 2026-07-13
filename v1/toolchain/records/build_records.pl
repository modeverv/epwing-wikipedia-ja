#!/usr/bin/env perl
use strict;
use warnings;
use FreePWING::FPWUtils::FPWParser;

open(my $input, '<', 'records.tsv') or die "records.tsv: $!\n";
initialize_fpwparser('text' => \my $text, 'heading' => \my $heading, 'word2' => \my $word2);
my $empty_headwords = 0;
my $unindexable_headwords = 0;
my $line_number = 0;

sub add_text_with_markup {
    my ($writer, $value) = @_;
    for my $piece (split(/(\@\@(?:GAIJI|CGRAPH):[a-z0-9-]+\@\@)/, $value)) {
        if ($piece =~ /^\@\@GAIJI:([a-z0-9-]+)\@\@$/) {
            $writer->add_full_user_character($1) or die $writer->error_message(), "\n";
        } elsif ($piece =~ /^\@\@CGRAPH:([a-z0-9-]+)\@\@$/) {
            $writer->add_color_graphic_start($1) or die $writer->error_message(), "\n";
            $writer->add_text("[image]") or die $writer->error_message(), "\n";
            $writer->add_color_graphic_end() or die $writer->error_message(), "\n";
        } elsif (length($piece)) {
            $writer->add_text($piece) or die $writer->error_message(), "\n";
        }
    }
}
while (my $line = <$input>) {
    $line_number++;
    chomp($line);
    my ($title, $body) = split(/\t/, $line, 2);
    $body //= '';
    if (!defined($title) || $title !~ /[^\s]/) {
        $empty_headwords++;
        next;
    }
    $body =~ s/\\n/\n/g;
    $text->new_entry() or die $text->error_message(), "\n";
    $heading->new_entry() or die $heading->error_message(), "\n";
    add_text_with_markup($heading, $title);
    $text->add_keyword_start() or die $text->error_message(), "\n";
    add_text_with_markup($text, $title);
    $text->add_keyword_end() or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";
    for my $paragraph (split(/\n/, $body)) {
        add_text_with_markup($text, $paragraph);
        $text->add_newline() or die $text->error_message(), "\n";
    }
    if ($title =~ /[A-Za-z0-9\xA3-\xFE]/) {
        if (!$word2->add_entry(
            $title,
            $heading->entry_position(),
            'head',
            $text->entry_position(),
            'text',
        )) {
            $unindexable_headwords++;
        }
    } else {
        $unindexable_headwords++;
    }
}
finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2);
warn "EMPTY_HEADWORD_SKIPPED=$empty_headwords\n" if $empty_headwords;
warn "UNINDEXABLE_HEADWORD=$unindexable_headwords\n" if $unindexable_headwords;
