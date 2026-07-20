#!/usr/bin/env perl
# Generic FreePWING source builder: reads entries.jsonl (written by
# wikiepwing.render.freepwing_source.write_entries_jsonl_stream) and drives
# FreePWING::FPWUtils::FPWParser to build the fpwmake source tree
# (work/text, work/heading, work/word2). Unlike
# tests/fixtures/handcrafted/build_fixture.pl (a fixed 3-entry/2-alias smoke
# fixture), this accepts any number of entries with any number of aliases
# or internal link targets (including zero).
#
# At full scale (~1.5M entries / ~13GB) the per-entry JSON decode + EUC-JP
# re-encode dominates wall time and is embarrassingly parallel, while the
# FPWParser writes are inherently serial (every entry's honmon position
# depends on all bytes written before it). So the build is split in two:
# forked workers each take a byte range of entries.jsonl and turn it into a
# spool of pre-encoded records (Storable-frozen, length-prefixed), then a
# single serial pass streams the spools in input order into FPWParser.
# Entries are never all held in memory at once -- the resident state is just
# the tag and headword sets needed for cross-entry validation.
use strict;
use warnings;

use Encode qw(encode);
use Fcntl qw(SEEK_SET);
use File::Temp qw(tempdir);
use FreePWING::FPWUtils::FPWParser;
use POSIX qw(_exit);
use Storable qw(freeze thaw);

# JSON::XS (C implementation, in the toolchain image) decodes roughly two
# orders of magnitude faster than pure-Perl JSON::PP; JSON::PP stays as the
# fallback so the script still runs on hosts without the XS module. Both
# expose the same ->new->utf8->decode interface.
my $JSON_CLASS = eval { require JSON::XS; 'JSON::XS' }
    || do { require JSON::PP; 'JSON::PP' };

# FPWParser expects EUC-JP byte strings (matching the encoding
# tests/fixtures/handcrafted's smoke test applies via `iconv` before Perl
# ever sees the data); entries.jsonl is UTF-8 (JSON's own encoding), so every
# string field is re-encoded to EUC-JP right after JSON decode (except body
# text -- see body_to_ops below).
#
# Perl's Encode module's "euc-jp" happily encodes JIS X 0212 supplementary
# characters too, using the SS3 (\x8f) prefix -- but FPWParser only
# understands plain two-byte JIS X 0208 and rejects any \x8f it sees with
# "invalid character" (TASK-T013). wikiepwing's gaiji pipeline
# (wikiepwing.gaiji.embedding, wired into wikiepwing.render.freepwing_source
# and wikiepwing.render.generate, GAIJI.md) resolves every such character
# before entries.jsonl is even written: title/alias text gets the plain
# `[U+XXXX]` fallback (itself plain ASCII, safe for to_euc_jp as-is), and
# body text gets an `@@GAIJI:<code>@@` placeholder token that body_to_ops
# below turns into a real gaiji reference. So by the time any string reaches
# to_euc_jp, it must not contain a JIS X 0212-only character any more --
# encode() is left to raise on \x8f as a defensive check (rather than
# silently substituting a geta mark, this script's previous stopgap) in case
# that invariant is ever violated upstream.
sub to_euc_jp {
    my ($value) = @_;
    return $value unless defined $value;
    my $bytes = encode('euc-jp', $value);
    die "invalid character: unresolved JIS X 0212 (SS3) byte in: $value\n"
        if $bytes =~ /\x8f/;
    return $bytes;
}

# FreePWING::BaseWord removes these ASCII/JIS X 0208 punctuation bytes while
# normalizing search words. Calling add_entry with a word made only of these
# bytes closes one of Word2's output handles, so detect that documented edge
# case before handing the value to the destructive API.
sub is_empty_search_word {
    my ($value) = @_;
    $value =~ s/(?:[ '\-]|\xa1(?:\xa1|\xa6|\xbe|\xc7|\xdd))//g;
    return $value eq '';
}

# GAIJI_TOKEN matches wikiepwing.gaiji.embedding.GAIJI_TOKEN_FORMAT
# ("@@GAIJI:<code>@@") and wikiepwing.gaiji.code_assignment's
# "<narrow|wide>-NNNN" assigned_code format, so the width class needed to
# choose add_half_user_character vs add_full_user_character is read directly
# off the token's own prefix -- no separate lookup table is needed here.
my $GAIJI_TOKEN = qr/\@\@GAIJI:([a-z0-9-]+)\@\@/;
my $REF_TOKEN = qr/\x1eR:([a-z][a-z0-9_-]{0,31})\x1f(.*?)\x1eE\x1f/s;
my $GRAPHIC_TOKEN = qr/\x1eG:([A-Za-z0-9_-]+)\x1f/;
my $BODY_TOKEN = qr/\x1eR:([a-z][a-z0-9_-]{0,31})\x1f(.*?)\x1eE\x1f|\x1eG:([A-Za-z0-9_-]+)\x1f/s;

# Splits $value on GAIJI_TOKEN (v1/toolchain/records/build_records.pl's
# proven placeholder-token design) into a flat op list -- ['t', euc_bytes]
# for plain text, ['h'|'f', code] for narrow/wide gaiji -- so the expensive
# split + EUC-JP encode runs in the parallel workers and the serial feed
# stage only replays writer calls. A capturing split alternates
# [text, code, text, code, ..., text], so odd indices are always the
# captured gaiji code.
sub plain_text_to_ops {
    my ($value) = @_;
    return [] unless defined $value && $value ne '';
    my @ops;
    my @pieces = split(/$GAIJI_TOKEN/, $value, -1);
    for my $index (0 .. $#pieces) {
        my $piece = $pieces[$index];
        next unless defined $piece && length($piece);
        if ($index % 2 == 1) {
            if ($piece =~ /^narrow-/ || $piece =~ /^wide-/) {
                push @ops, [substr($piece, 0, 1) eq 'n' ? 'h' : 'f', $piece];
            } else {
                die "invalid gaiji code: $piece\n";
            }
        } else {
            die "unparsed body marker: " . unpack('H*', $piece) . "\n"
                if $piece =~ /[\x1e\x1f]/;
            push @ops, ['t', to_euc_jp($piece)];
        }
    }
    return \@ops;
}

sub body_to_ops {
    my ($value) = @_;
    return [] unless defined $value && $value ne '';
    my @ops;
    my $position = 0;
    while ($value =~ /$BODY_TOKEN/g) {
        my $plain = substr($value, $position, $-[0] - $position);
        push @ops, @{plain_text_to_ops($plain)};
        if (defined $3) {
            push @ops, ['g', $3];
        } else {
            my ($target, $label) = ($1, $2);
            push @ops, ['s', ''];
            push @ops, @{plain_text_to_ops($label)};
            push @ops, ['r', $target];
        }
        $position = $+[0];
    }
    push @ops, @{plain_text_to_ops(substr($value, $position))};
    return \@ops;
}

# Replays a body_to_ops op list against the text writer:
# add_half_user_character/add_full_user_character for gaiji, add_text for
# already-encoded text (tests/fixtures/handcrafted/build_fixture.pl
# demonstrates both real API calls).
sub add_body_ops {
    my ($writer, $ops) = @_;
    for my $op (@{$ops}) {
        my ($kind, $payload) = @{$op};
        if ($kind eq 'h') {
            $writer->add_half_user_character($payload) or die $writer->error_message(), "\n";
        } elsif ($kind eq 'f') {
            $writer->add_full_user_character($payload) or die $writer->error_message(), "\n";
        } elsif ($kind eq 's') {
            $writer->add_reference_start() or die $writer->error_message(), "\n";
        } elsif ($kind eq 'r') {
            $writer->add_reference_end($payload) or die $writer->error_message(), "\n";
        } elsif ($kind eq 'g') {
            $writer->add_color_graphic_start($payload) or die $writer->error_message(), "\n";
            $writer->add_color_graphic_end() or die $writer->error_message(), "\n";
        } else {
            $writer->add_text($payload) or die $writer->error_message(), "\n";
        }
    }
}

# Progress is time-bounded rather than count-bounded: entry sizes vary by
# orders of magnitude, so "every N entries" is either spam or silence
# depending on the corpus. Every $PROGRESS_CHECK_EVERY entries the clock is
# checked (cheap), and a line is emitted at most every $PROGRESS_SECONDS.
# $| = 1 so it's never buffered and delayed behind the loop's own work.
$| = 1;
my $PROGRESS_SECONDS = 2;
my $PROGRESS_CHECK_EVERY = 1000;

my $input_path = $ARGV[0] // 'entries.jsonl';
my $input_size = -s $input_path;
die "cannot stat $input_path: $!\n" if !defined $input_size;

# Worker count: WIKIEPWING_PARSE_JOBS overrides, else every online CPU.
# Small inputs (the smoke fixtures) stay single-process -- forking 16 workers
# over a 500-byte file costs more than it saves.
my $jobs = 0;
$jobs = int($1)
    if defined $ENV{WIKIEPWING_PARSE_JOBS}
    && $ENV{WIKIEPWING_PARSE_JOBS} =~ /\A(\d+)\z/;
# Debian's POSIX module does not expose _SC_NPROCESSORS_ONLN, so the online
# CPU count comes from nproc(1) (coreutils, present in the toolchain image).
if ($jobs < 1) {
    my $nproc = qx(nproc 2>/dev/null);
    $jobs = defined $nproc && $nproc =~ /(\d+)/ ? int($1) : 1;
    $jobs = 1 if $jobs < 1;
}
my $MIN_CHUNK_BYTES = 4 * 1024 * 1024;
my $max_jobs_by_size = int($input_size / $MIN_CHUNK_BYTES) || 1;
$jobs = $max_jobs_by_size if $jobs > $max_jobs_by_size;

my $spool_directory = tempdir('fpwparse-XXXXXXXX', TMPDIR => 1, CLEANUP => 1);
my @spools = map { "$spool_directory/chunk-$_" } 0 .. $jobs - 1;

# Parses one byte range of entries.jsonl into a spool. A chunk owns every
# line that *starts* inside [$start, $end): seeking to $start - 1 and
# discarding one read positions the handle at the first line start >= $start
# whether $start lands mid-line or exactly on a boundary, and the loop stops
# once the next line would start at or past $end.
sub parse_chunk {
    my ($chunk, $start, $end, $spool_path) = @_;

    open my $input, '<:raw', $input_path or die "cannot open $input_path: $!\n";
    if ($start > 0) {
        seek($input, $start - 1, SEEK_SET) or die "cannot seek $input_path: $!\n";
        my $discard = <$input>;
    }

    open my $spool, '>:raw', $spool_path or die "cannot open $spool_path: $!\n";
    open my $tags_out, '>:raw', "$spool_path.tags"
        or die "cannot open $spool_path.tags: $!\n";
    open my $targets_out, '>:raw', "$spool_path.targets"
        or die "cannot open $spool_path.targets: $!\n";

    my $json = $JSON_CLASS->new->utf8;
    my $count = 0;
    my $last_report = time();
    while (tell($input) < $end) {
        my $line = <$input>;
        last if !defined $line;
        $line =~ s/\r?\n\z//;
        next if $line eq '';
        my $record = $json->decode($line);

        my $tag = to_euc_jp($record->{tag});
        die "invalid tag: " . ($tag // '') . "\n"
            if !defined($tag) || $tag !~ /\A[a-z][a-z0-9_-]{0,31}\z/;
        die "empty title for tag $tag\n"
            if !defined($record->{title}) || $record->{title} eq '';

        my @targets = map { to_euc_jp($_) } @{$record->{targets} // []};
        my %declared_targets = map { $_ => 1 } @targets;
        for my $target (@targets) {
            # Every real tag matches the pattern below, so a target that
            # does not can never resolve; rejecting it here also keeps the
            # newline-delimited .targets side file well-formed.
            die "unknown link target: $target\n"
                if $target !~ /\A[a-z][a-z0-9_-]{0,31}\z/;
        }
        my $body_ops = body_to_ops($record->{body});
        for my $op (@{$body_ops}) {
            next unless $op->[0] eq 'r';
            die "inline reference target not declared: $op->[1]\n"
                if !$declared_targets{$op->[1]};
        }

        my $frozen = freeze({
            tag => $tag,
            title => to_euc_jp($record->{title}),
            aliases => [map { to_euc_jp($_) } @{$record->{aliases} // []}],
            keywords => [map { to_euc_jp($_) } @{$record->{keywords} // []}],
            body_ops => $body_ops,
            targets => \@targets,
        });

        print {$spool} pack('N', length $frozen), $frozen;
        print {$tags_out} $tag, "\n";
        print {$targets_out} map { "$_\n" } @targets;

        $count++;
        if ($count % $PROGRESS_CHECK_EVERY == 0
            && time() - $last_report >= $PROGRESS_SECONDS) {
            print STDERR "parse worker $chunk: $count entries\n";
            $last_report = time();
        }
    }
    close $targets_out or die "cannot close $spool_path.targets: $!\n";
    close $tags_out or die "cannot close $spool_path.tags: $!\n";
    close $spool or die "cannot close $spool_path: $!\n";
    close $input or die "cannot close $input_path: $!\n";
    print STDERR "parse worker $chunk: $count entries (done)\n";
}

my @pids;
for my $chunk (0 .. $jobs - 1) {
    my $start = int($input_size * $chunk / $jobs);
    my $end = $chunk == $jobs - 1 ? $input_size : int($input_size * ($chunk + 1) / $jobs);
    my $pid = fork();
    die "fork failed: $!\n" if !defined $pid;
    if ($pid == 0) {
        my $completed = eval { parse_chunk($chunk, $start, $end, $spools[$chunk]); 1 };
        print STDERR $@ if !$completed;
        # POSIX::_exit skips END blocks so a child never runs File::Temp's
        # CLEANUP handler and deletes the spool directory out from under the
        # other workers and the parent.
        _exit($completed ? 0 : 1);
    }
    push @pids, $pid;
}
for my $pid (@pids) {
    waitpid($pid, 0);
    die "entry preprocessing worker failed\n" if $? != 0;
}

# Cross-entry validation before any FPWParser output is opened, preserving
# the all-or-nothing semantics of the previous in-memory implementation:
# duplicate tags die in input order, and every link target must exist
# somewhere in the corpus. The spools are read in chunk order, which is
# exactly input order.
my %tags;
my $total_entries = 0;
for my $spool_path (@spools) {
    open my $tags_in, '<:raw', "$spool_path.tags"
        or die "cannot open $spool_path.tags: $!\n";
    while (my $tag = <$tags_in>) {
        chomp $tag;
        die "duplicate tag: $tag\n" if $tags{$tag}++;
        $total_entries++;
    }
    close $tags_in or die "cannot close $spool_path.tags: $!\n";
}
die "no entries to build\n" if !$total_entries;
for my $spool_path (@spools) {
    open my $targets_in, '<:raw', "$spool_path.targets"
        or die "cannot open $spool_path.targets: $!\n";
    while (my $target = <$targets_in>) {
        chomp $target;
        die "unknown link target: $target\n" if !$tags{$target};
    }
    close $targets_in or die "cannot close $spool_path.targets: $!\n";
}

initialize_fpwparser(
    'text' => \my $text,
    'heading' => \my $heading,
    'word2' => \my $word2,
    'keyword' => \my $keyword,
);

my %global_headwords;
my $indexed = 0;
my $duplicate_headwords = 0;
my $skipped_empty_headwords = 0;
my $last_report = time();

my $first_heading_pos;
my $first_text_pos;
my $has_keyword = 0;

for my $spool_path (@spools) {
    open my $spool, '<:raw', $spool_path or die "cannot open $spool_path: $!\n";
    my ($header, $frozen);
    while (read($spool, $header, 4) == 4) {
        my $length = unpack('N', $header);
        read($spool, $frozen, $length) == $length
            or die "truncated spool record in $spool_path\n";
        my $entry = thaw($frozen);

        $text->new_entry() or die $text->error_message(), "\n";
        $heading->new_entry() or die $heading->error_message(), "\n";
        $heading->add_text($entry->{title}) or die $heading->error_message(), "\n";

        if (!defined $first_heading_pos) {
            $first_heading_pos = $heading->entry_position();
            $first_text_pos = $text->entry_position();
        }

        $text->add_tag($entry->{tag}) or die $text->error_message(), "\n";
        $text->add_text($entry->{title}) or die $text->error_message(), "\n";
        $text->add_newline() or die $text->error_message(), "\n";

        if (@{$entry->{body_ops}}) {
            add_body_ops($text, $entry->{body_ops});
            $text->add_newline() or die $text->error_message(), "\n";
        }

        my %seen_in_entry;
        for my $headword ($entry->{title}, @{$entry->{aliases}}) {
            next if $seen_in_entry{$headword}++;
            if (is_empty_search_word($headword)) {
                $skipped_empty_headwords++;
                print STDERR "headword skipped tag=$entry->{tag} "
                    . "reason=word-is-empty value=$headword\n";
                next;
            }
            $duplicate_headwords++ if $global_headwords{$headword}++;
            $word2->add_entry($headword, $heading->entry_position(), $text->entry_position())
                or die "headword rejected for tag $entry->{tag}: "
                    . $word2->error_message() . "\n";
        }

        my %seen_keywords;
        for my $kw (@{$entry->{keywords} // []}) {
            next if $seen_keywords{$kw}++;
            if (is_empty_search_word($kw)) {
                next;
            }
            $keyword->add_entry($kw, $heading->entry_position(), $text->entry_position())
                or die "keyword rejected for tag $entry->{tag}: "
                    . $keyword->error_message() . "\n";
            $has_keyword = 1;
        }

        $indexed++;
        if ($indexed % $PROGRESS_CHECK_EVERY == 0
            && time() - $last_report >= $PROGRESS_SECONDS) {
            print STDERR "index $indexed/$total_entries\n";
            $last_report = time();
        }
    }
    close $spool or die "cannot close $spool_path: $!\n";
}
print STDERR "index $indexed/$total_entries\n";
print STDERR "headwords duplicated count=$duplicate_headwords\n";
print STDERR "headwords skipped reason=word-is-empty count=$skipped_empty_headwords\n";

if (!$has_keyword && defined $first_heading_pos) {
    $keyword->add_entry(to_euc_jp("dummy"), $first_heading_pos, $first_text_pos)
        or die "failed to add dummy keyword: " . $keyword->error_message() . "\n";
}

die "spool entry count mismatch: indexed $indexed, expected $total_entries\n"
    if $indexed != $total_entries;

finalize_fpwparser('text' => \$text, 'heading' => \$heading, 'word2' => \$word2, 'keyword' => \$keyword);
