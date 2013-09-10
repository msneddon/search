#!/usr/bin/perl


# Config
#
$merge_str = ': ';
$join_str = ' !KK! ';

$merge_cols = +[ 
    +[ 2 ], 
    +[ 10 ], 
    +[ 2, 10 ],
    +[ 11 ],
    +[ 12 ],
    +[ 11, 12],
    ];

$enum_prefix = +{
    '2' => +{
	'PF' => +['PF', 'PFAM'],
	'TIGR' => +['TIGR', 'TF', 'TIGRFAM'],
	'PIRSF' => +['PIRSF', 'PIR'],
	'SM' => +['SM', 'SMART'],
	'PTHR' => +['PTHR', 'PANTHER'],
	'SSF' => +['SSF', 'SF', 'SUPERFAMILY', 'SUPERFAM'],
	'G3DSA:' => +['G3DSA:', 'GENE3D:', 'G3DSA', 'GENE3D'],
    }
};


# Main
#
$last_id = undef;
$id = undef;
@row_fields = ();
@row = ();

open (FILE, $ARGV[0]);
while (<FILE>) {
    chomp;
    next if (/^\s*$/);
    next if (/^fid/);
    s/\s+$//;

    @dat = split (/ *\t */, $_);

    $id = $dat[0];

    if (! defined $last_id || $id ne $last_id) {
	if (@row_fields) {
	    for ($i=0; $i <= $#{$merge_cols}; ++$i) {
		$row[$i] = join ($join_str, @{$row_fields[$i]});
	    }
	    print join ("\t", $last_id, @row)."\n"  if (@row);
	    @row_fields = ();
	    @row = ();
	}
	$last_id = $id;
    }

    # get busy
    #
    for ($i=0; $i <= $#{$merge_cols}; ++$i) {
	$col_set = $merge_cols->[$i];
	if ($#{$col_set} == 0) {
	    $col = $col_set->[0];
	    if (defined $enum_prefix->{$col}) {
		$orig_db_id = $dat[$col];
		if ($orig_db_id =~ /^(G3DSA:)(\d+)(\S*?)$/) {
		    $db_name = $1;
		    $db_num = $2;
		    $db_id_tail = $3;
		}
		elsif ($orig_db_id =~ /^(\D+)(\d+)(\S*?)$/) {
		    $db_name = $1;
		    $db_num = $2;
		    $db_id_tail = $3;
		} else {
		    print STDERR "Badly formatted record $dat[$col]\n";
		    exit -1;
		}
		@enum_nums = ($db_num);
		$short_num = $db_num;
		if ($short_num =~ s/^0+//) {
		    push (@enum_nums, $short_num);
		}
		foreach $num (@enum_nums) {
		    if (! defined $enum_prefix->{$col}->{$db_name}) {
			$new_db_id = $db_name.$num.$db_id_tail;
			push (@{$row_fields[$i]}, $new_db_id);
		    }
		    else {
			foreach $alt_prefix (@{$enum_prefix->{$col}->{$db_name}}) {
			    $new_db_id = $alt_prefix.$num.$db_id_tail;
			    push (@{$row_fields[$i]}, $new_db_id);
			}
		    }
		}
	    } 
	    else {
		push (@{$row_fields[$i]}, $dat[$col]) if ($dat[$col] && 
							  $dat[$col] !~ /^NULL$/i && 
							  $dat[$col] !~ /^FAMILY NOT NAMED$/i &&
							  $dat[$col] !~ /^SUBFAMILY NOT NAMED$/i
		    );
	    }
	}
	else {
	    @fields_dat = ();
	    foreach $col (@$col_set) {
		push (@fields_dat, $dat[$col])  if ($dat[$col] && 
						    $dat[$col] !~ /^NULL$/i && 
						    $dat[$col] !~ /^FAMILY NOT NAMED$/i &&
						    $dat[$col] !~ /^SUBFAMILY NOT NAMED$/i
		    );
	    }
	    $fields_dat[0]='' unless ($fields_dat[0]);
	    $fields_dat[1]='' unless ($fields_dat[1]);
	    $fields_dat[2]='' unless ($fields_dat[2]);

	    push (@{$row_fields[$i]}, join ($merge_str, @fields_dat))  if (@fields_dat);
	}
    }
}
close (FILE);

# don't forget last record
#
if (@row_fields) {
    for ($i=0; $i <= $#{$merge_cols}; ++$i) {
	$row[$i] = join ($join_str, @{$row_fields[$i]});
    }
    print join ("\t", $last_id, @row)."\n"  if (@row);
    @row_fields = ();
    @row = ();
}



