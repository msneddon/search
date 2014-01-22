#!/usr/bin/perl
#
use strict;
use warnings;

use File::Slurp;
use JSON;

my @files=@ARGV;
my $json=JSON->new;

foreach my $file (@files)
{
	# two different modes: the example is pretty-printed
	# the dump files are not, and have an extraneous first line
	my @jsonText=read_file($file);
	my $jsonMedia;
	my ($mediaId,$mediaWorkspace);
	if (scalar @jsonText > 2)
	{
		# will this work?
		$jsonMedia=$json->decode(join '',@jsonText);
	} else {
                # hack to get the workspace name
                # turns out it's not a hack, it's actually where
                # the actual id is stored
                # not sure what the relationship is between this id
                # and the id in the JSON
                ($mediaWorkspace)=$jsonText[0]=~/Media\/(.*?)\//;
                $mediaId=$jsonText[0];
                chomp $mediaId;

		$jsonMedia->[0]=$json->decode($jsonText[1]);
	}

	foreach my $media (@$jsonMedia)
	{
		next unless (keys %$media);
		my @emptyCompoundColumns=('','','','','');
		print join "\t",
			$mediaId,
			'Media',
			$media->{id},
			$mediaWorkspace,
			$media->{pH},
			$media->{temperature},
			$media->{name},
			@emptyCompoundColumns,
			;
		print "\n";

# loop over compounds
		foreach my $compound (@{$media->{media_compounds}})
		{
			print join "\t",
				$mediaId.'.'.$compound->{compound},
				'MediaCompound',
				$media->{id},
				$mediaWorkspace,
				$media->{pH},
				$media->{temperature},
				$media->{name},
				$compound->{compound},
				$compound->{name},
				$compound->{concentration},
				$compound->{min_flux},
				$compound->{max_flux},
				;
			print "\n";
		}
	}
}
