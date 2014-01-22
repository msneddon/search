#!/usr/bin/perl
#
use strict;
use warnings;

use File::Slurp;
use JSON;
use Data::Dumper;

my @files=@ARGV;
my $json=JSON->new;

foreach my $file (@files)
{
	# two different modes: the example is pretty-printed
	# the dump files are not, and have an extraneous first line
	# actually, it's not extraneous any more, as it has the
	# name of the workspace embedded in it
	my @jsonText=read_file($file);
	my $jsonPhenotypeSets;
	my $phenotypeSetWorkspace='unspecified workspace';
	my $phenotypeSetId;
	my $phenotypeSetName;
	if (scalar @jsonText > 2)
	{
		# will this work?
		$jsonPhenotypeSets->[0]=$json->decode(join '',@jsonText);
	} else {
		# hack to get the workspace name
		# turns out it's not a hack, it's actually where
		# the actual id is stored
		# not sure what the relationship is between this id
		# and the id in the JSON
		($phenotypeSetWorkspace)=$jsonText[0]=~/PhenotypeSet\/(.*?)\//;
		$phenotypeSetId=$jsonText[0];
		chomp $phenotypeSetId;
		$jsonPhenotypeSets->[0]=$json->decode($jsonText[1]);
	}

	foreach my $phenotypeSet (@$jsonPhenotypeSets)
	{
		my @emptyPhenotypeColumns=('','','','','');
		print join "\t",
			$phenotypeSetId,
			'PhenotypeSet',
			$phenotypeSet->{id},
			$phenotypeSetWorkspace,
			$phenotypeSet->{genome},
			$phenotypeSet->{genome_workspace},
			($phenotypeSet->{name} || 'unnamed PhenotypeSet'),
			($phenotypeSet->{type} || 'type not specified'),
			@emptyPhenotypeColumns,
			;
		print "\n";

# loop over phenotypes; need the array index to be able to create
# a unique identifier
		foreach my $phIndex (0..(scalar @{$phenotypeSet->{phenotypes}})-1)
		{
			my $phenotype=$phenotypeSet->{phenotypes}[$phIndex];
			# need to unroll knockouts and compounds
			# id is not unique here, so we need a different
			# id strategy
			my $knockouts=join ' ',@{$phenotype->[0]};
			my $addlCompounds=join ' ',@{$phenotype->[3]};
			print join "\t",
				$phenotypeSetId.'.'.$phIndex,
				'Phenotype',
				$phenotypeSet->{id},
				$phenotypeSetWorkspace,
				$phenotypeSet->{genome},
				$phenotypeSet->{genome_workspace},
				($phenotypeSet->{name} || 'unnamed PhenotypeSet'),
				($phenotypeSet->{type} || 'type not specified'),
				$phenotype->[1],
				$phenotype->[2],
				$knockouts,
				$addlCompounds,
				$phenotype->[4],

				;
			print "\n";
		}
	}
}
