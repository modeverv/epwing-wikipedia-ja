#!/usr/bin/env perl
use strict;
use warnings;

die "usage: generate_bitmap.pl OUTPUT\n" if @ARGV != 1;
my ($output_path) = @ARGV;

my $pixel_data = pack(
    'C*',
    255, 0,   0,   255, 255, 255, 0, 0,
    0,   0,   255, 0,   255, 0,   0, 0,
);
my $bitmap = pack(
    'a2 V v v V V V V v v V V V V V V',
    'BM',
    54 + length($pixel_data),
    0,
    0,
    54,
    40,
    2,
    2,
    1,
    24,
    0,
    length($pixel_data),
    2835,
    2835,
    0,
    0,
) . $pixel_data;

open my $output, '>:raw', $output_path or die "cannot write $output_path: $!\n";
print {$output} $bitmap or die "cannot write $output_path: $!\n";
close $output or die "cannot close $output_path: $!\n";
