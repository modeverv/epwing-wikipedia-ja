#!/usr/bin/env perl
use strict;
use warnings;

die "usage: generate_gaiji.pl HALF_XBM FULL_XBM\n" if @ARGV != 2;
my ($half_path, $full_path) = @ARGV;

sub write_xbm {
    my ($path, $name, $width, $bytes) = @_;
    my $height = 16;
    my $expected_length = ($width / 8) * $height;
    die "invalid bitmap byte count for $name\n" if @{$bytes} != $expected_length;

    my @values = map { sprintf '0x%02x', $_ } @{$bytes};
    my $source = sprintf(
        "#define %s_width %d\n#define %s_height %d\n"
            . "static unsigned char %s_bits[] = {\n  %s\n};\n",
        $name,
        $width,
        $name,
        $height,
        $name,
        join(', ', @values),
    );
    open my $output, '>:raw', $path or die "cannot write $path: $!\n";
    print {$output} $source or die "cannot write $path: $!\n";
    close $output or die "cannot close $path: $!\n";
}

write_xbm(
    $half_path,
    'half',
    8,
    [0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81,
     0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81],
);
write_xbm(
    $full_path,
    'full',
    16,
    [0xff, 0xff, 0x01, 0x80, 0x01, 0x80, 0x01, 0x80,
     0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0x01, 0x80,
     0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0x01, 0x80,
     0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0xff, 0xff],
);
