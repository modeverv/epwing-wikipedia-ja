#!/usr/bin/env perl
use strict;
use warnings;

use FreePWING::FPWUtils::FPWParser;

my @entries = (
    ["Emacs", "An extensible text editor.", "Linux"],
    ["Linux", "A Unix-like operating system kernel.", "Wikipedia"],
    ["Wikipedia", "A free encyclopedia.", "Emacs"],
);

initialize_fpwparser(
    'text' => \my $text,
    'heading' => \my $heading,
    'word2' => \my $word2,
);

for my $entry (@entries) {
    my ($title, $body, $target) = @{$entry};
    $text->new_entry() or die $text->error_message(), "\n";
    $heading->new_entry() or die $heading->error_message(), "\n";
    $heading->add_text($title) or die $heading->error_message(), "\n";
    $text->add_tag($title) or die $text->error_message(), "\n";
    $text->add_keyword_start() or die $text->error_message(), "\n";
    $text->add_text($title) or die $text->error_message(), "\n";
    $text->add_keyword_end() or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";
    $text->add_text($body) or die $text->error_message(), "\n";
    $text->add_reference_start() or die $text->error_message(), "\n";
    $text->add_text($target) or die $text->error_message(), "\n";
    $text->add_reference_end($target) or die $text->error_message(), "\n";
    $text->add_newline() or die $text->error_message(), "\n";
    $word2->add_entry($title, $heading->entry_position(), $text->entry_position())
        or die $word2->error_message(), "\n";
}

finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2);
