#!/usr/bin/perl -w
use strict;

use Data::Dumper;
use Test::More qw(no_plan);
use JSON;

my $num_tests = 0;

my $root_url;
open CFG, "../test.cfg" or die "Can't open test config file!";
while (<CFG>) {
	chomp;
	my @pair = split("=");
	if ($pair[0] =~ /^CORE_URL/) {
		$root_url = $pair[1];
	}
}
close CFG;


my $test_commands = {
	'literature' => { 
		'keyword' => ['coli', 'subtilis'],
		'start' => [0, 10],
		'count' => [0, 1, 10],
		'format' => 'json'
	}
};

foreach my $command (keys %{ $test_commands }) {
	run_test($command, $test_commands->{$command});
}

done_testing($num_tests);


sub run_test {
	my ($command, $param_set) = @_;

	# 1. run just the command alone without extra parameters.
	my $url = $root_url . $command;

	print "Testing: " . $url . "\n";

	my $curl = `curl -k -s $url`;


	# 2. include a 'start' parameter

	# 3. include a 'count' parameter

	# 4. include a 'start' and 'count' parameter

	# 5. include a 'format' parameter

	# 6. include a 'start', 'count', and 'format' parameter
}