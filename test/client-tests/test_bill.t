#!/usr/bin/perl -w

# A bunch of happy path tests for the search service, via REST.
# These all use multiple starts and counts, and (hopefully) appropriate search terms
# that return something testable.
#
# A few categories were mislabeled in the docs, and a little exploration showed
# how they should be used. These are labeled below
# (doc term -> working term)
# rsw -> riboswitch
# pseudo -> pseudogene
# trnspn -> transposon
#
# Bill Riehl
# wjriehl@lbl.gov
# May 17, 2013

use strict;

use Data::Dumper;
use Test::More qw(no_plan);
use JSON;

my $num_tests = 0;

my $root_url;
open CFG, "test.cfg" or die "Can't open test config file!";
while (<CFG>) {
	chomp;
	my @pair = split("=");
	if ($pair[0] =~ /^CORE_URL/) {
		$root_url = $pair[1];
	}
}
close CFG;


my $test_commands = {
	# general
	'literature' => { 
		'keyword' => 'coli',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},

	# genomes
	'genome' => { 
		'keyword' => 'coli',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'viruses' => { 
		'keyword' => 'ebolavirus',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'bacteria' => { 
		'keyword' => 'coli',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'archaea' => { 
		'keyword' => 'maripaludis',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'eukaryota' => { 
		'keyword' => 'saccharomyces',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'virusescount' => { 
		'keyword' => 'ebolavirus',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'bacteriacount' => { 
		'keyword' => 'coli',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'archaeacount' => { 
		'keyword' => 'maripaludis',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'eukaryotacount' => { 
		'keyword' => 'saccharomyces',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},

	# function
	'gene' => { 
		'keyword' => 'dnaa',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'prophage' => { 
		'keyword' => 'yersinia',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'pseudogene' => { 
		'keyword' => 'stevor',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'locus' => { 
		'keyword' => 'antisense',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},

	# regulation
	'operator' => { 
		'keyword' => 'metA',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'promoter' => { 
		'keyword' => 'rot',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'riboswitch' => { 
		'keyword' => 'glycine',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'bindingsite' => { 
		'keyword' => 'coli',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},

	# rna
	'rna' => { 
		'keyword' => '16s',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'transposon' => { 
		'keyword' => 'Tn3',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'srna' => { 
		'keyword' => 'rpoS',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'mrna' => { 
		'keyword' => 'dnaa',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	},
	'pathogenicityisland' => { 
		'keyword' => 'SaPI',
		'start' => [0, 1],
		'count' => [1, 10],
		'format' => ['json']
	}
};

foreach my $command (keys %{ $test_commands }) {
	run_test_set($command, $test_commands->{$command});
}

done_testing($num_tests);


sub run_test_set {
	my ($command, $param_set) = @_;

	# 1. run just the command alone without extra parameters.
	my $command_url = $root_url . $command;

	print "Testing: " . $command_url . "\n";
	my $struct = test_url($command_url);

	# 2. include the 'keyword' parameter
	my $keyword_url = $command_url . "/" . $param_set->{'keyword'};
	$struct = test_url($keyword_url);
	test_data_struct($struct);

	# 3. include a 'start' parameter
	foreach my $start (@{ $param_set->{'start'} }) {
		my $url = $keyword_url . "?start=" . $start;
		$struct = test_url($url);
		test_data_struct($struct);
	}

	# 4. include a 'count' parameter
	foreach my $count (@{ $param_set->{'count'} }) {
		my $url = $keyword_url . "?count=" . $count;
		$struct = test_url($url);
		test_data_struct($struct);
	}

	# 5. include a 'start' and 'count' parameter
	foreach my $start (@{ $param_set->{'start'} }) {
		foreach my $count (@{ $param_set->{'count'} }) {
			my $url = $keyword_url . "?start=" . $start . "&count=" . $count;
			$struct = test_url($url);
			test_data_struct($struct);
		}
	}

	# 6. include a 'format' parameter
	foreach my $format(@{ $param_set->{'format'} }) {
		my $url = $keyword_url . "?format=" . $format;
		$struct = test_url($url);
	}

	# 7. include a 'start' and 'format' parameter
	foreach my $start (@{ $param_set->{'start'} }) {
		foreach my $format (@{ $param_set->{'format'} }) {
			my $url = $keyword_url . "?start=" . $start . "&format=" . $format;
			$struct = test_url($url);
			test_data_struct($struct);
		}
	}

	# 8. include a 'count' and 'format' parameter
	foreach my $count (@{ $param_set->{'count'} }) {
		foreach my $format (@{ $param_set->{'format'} }) {
			my $url = $keyword_url . "?count=" . $count . "&format=" . $format;
			$struct = test_url($url);
			test_data_struct($struct);
		}
	}

	# 9. include a 'start', 'count', and 'format' parameter
	foreach my $start (@{ $param_set->{'start'} }) {
		foreach my $count (@{ $param_set->{'count'} }) {
			foreach my $format(@{ $param_set->{'format'} }) {
				my $url = $keyword_url . "?start=" . $start . "&count=" . $count . "&format=" . $format;
				$struct = test_url($url);
				test_data_struct($struct);			
			}
		}
	}
}

sub test_url {
	my $url = shift;

	print "Testing: " . $url . "\n";
	my $curl = `curl -k -s $url`;
	my $json = decode_json $curl;
	isa_ok($json, 'HASH', "returned a valid JSON hash");
	$num_tests++;

	return $json;
}

sub test_data_struct {
	my $struct = shift;
	ok(exists($struct->{'status'}), "struct contains a 'status' field");
	$num_tests++;

	ok(exists($struct->{'search'}), "struct contains a 'search' field");
	$num_tests++;

	ok(exists($struct->{'query'}), "struct contains a 'query' field");
	$num_tests++;

	ok(exists($struct->{'keyword'}), "struct contains a 'keyword' field");
	$num_tests++;

	ok(exists($struct->{'start'}), "struct contains a 'start' field");
	$num_tests++;

	ok(exists($struct->{'returned'}), "struct contains a 'returned' field");
	$num_tests++;

	ok(exists($struct->{'found'}), "struct contains a 'found' field");
	$num_tests++;

	ok(exists($struct->{'body'}), "struct contains a 'body' field");
	$num_tests++;

	isa_ok($struct->{'body'}, 'ARRAY');
	$num_tests++;

	if(exists($struct->{'keyword'}) && $struct->{'keyword'} !~ /count$/) {
		ok(scalar(@{ $struct->{'body'} }) == $struct->{'returned'}, "'returned' field matches the number of objects returned in the 'body' field");
		$num_tests++;
	}
}
