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
	warn $file;
	my @jsonText=read_file($file);
	my $jsonModels;
	my ($modelId,$modelWorkspace);

        if (scalar @jsonText > 2)
        {
                # will this work?
                $jsonModels=$json->decode(join '',@jsonText);
        } else {
                # hack to get the workspace name
                # turns out it's not a hack, it's actually where
                # the actual id is stored
                # not sure what the relationship is between this id
                # and the id in the JSON
		# also not sure we need $modelWorkspace, as
		# for Models there is a workspace attribute
		# (but is it accurate?)
                ($modelWorkspace)=$jsonText[0]=~/Model\/(.*?)\//;
                $modelId=$jsonText[0];
                chomp $modelId;

                $jsonModels->[0]=$json->decode($jsonText[1]);
        }

	foreach my $model (@$jsonModels)
	{
		next unless (keys %$model);
		my @emptyReactionColumns=('','','','','','','');
		my @emptyCompoundColumns=('','','');
		my @emptyR_CColumns=('');
# populate biomasses
		my $biomassesString='';
		foreach my $biomass (@{$model->{biomasses}})
		{
			$biomassesString.=$biomass->{name};
			$biomassesString.=' ';
		}
# populate compartments
		my $compartmentsString='';
		foreach my $compartment (@{$model->{compartments}})
		{
			$compartmentsString.=$compartment->{name};
			$compartmentsString.=' ';
		}
		print join "\t",
			$modelId,
			'Model',
			$model->{id},
			$model->{workspace},
			($model->{genome} or 'null'),
			$model->{genome_workspace},
			$model->{name},
			$model->{type},
			($model->{status} or 'null'),
			$biomassesString,
			$compartmentsString,
			@emptyReactionColumns,
			@emptyCompoundColumns,
			@emptyR_CColumns
			;
		print "\n";

# loop over reactions
		foreach my $reaction (@{$model->{reactions}})
		{
			my $featuresString=join ' ',@{$reaction->{features}};
			print join "\t",
				$modelId.'.'.$reaction->{id},
				'Reaction',
				$model->{id},
				$model->{workspace},
				($model->{genome} or 'undefined'),
				$model->{genome_workspace},
				$model->{name},
				$model->{type},
				($model->{status} or 'null'),
				$biomassesString,
				$compartmentsString,
				$reaction->{id},
				$reaction->{reaction},
				$reaction->{name},
				$reaction->{direction},
				$reaction->{equation},
				$reaction->{definition},
				$featuresString,
				@emptyCompoundColumns,
				$reaction->{compartment},
				;
			print "\n";
		}
#
# loop over compounds
		foreach my $compound (@{$model->{compounds}})
		{
			print join "\t",
				$modelId.'.'.$compound->{id},
				'Compound',
				$model->{id},
				$model->{workspace},
				($model->{genome} or 'undefined'),
				$model->{genome_workspace},
				$model->{name},
				$model->{type},
				($model->{status} or 'null'),
				$biomassesString,
				$compartmentsString,
				@emptyReactionColumns,
				$compound->{id},
				$compound->{compound},
				$compound->{name},
				$compound->{compartment},
				;
			print "\n";
		}
	}
}
