#!/usr/bin/perl

$feature_file  = "Feature.txt";
$genome_file   = "Genome.txt";
$taxonomy_file = "GenomeTaxonomies.txt";






# Process the taxonomy file to link genome ID with taxonomy hierarchy

open (TAXONOMY, $taxonomy_file);

%taxonomy = ();

while (<TAXONOMY>) {
  $entry = $_;
  $entry =~ s/\s*$//;   # Remove trailing whitespace

  $entry =~ /^(\S*)\t(.*)$/;
  $genome_id = $1;
  $hierarchy = $2;

  $taxonomy{$genome_id} = $hierarchy;
}

close(TAXONOMY);







# Process the genome file to extract the fields of interest

open (GENOME, $genome_file);

%genome_fields = ();

while (<GENOME>) {
  $entry = $_;
  $entry =~ s/\s*$//;   # Remove trailing whitespace

  $entry =~ /^([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)$/;
  $gid             =  $1;
  $pegs            =  $2;
  $rnas            =  $3;
  $scientific_name =  $4;
  $complete        =  $5;
  $prokaryotic     =  $6;
  $dna_size        =  $7;
  $contigs         =  $8;
  $domain          =  $9;
  $genetic_code    = $10;
  $gc_content      = $11;
  $phenotype       = $12;
  $md5             = $13;
  $source_id       = $14;

  # Concatenate fields of interest
  $fields = $gid             . "\t" .
            $pegs            . "\t" .
            $rnas            . "\t" .
            $scientific_name . "\t" .
            $complete        . "\t" .
            $prokaryotic     . "\t" .
            $dna_size        . "\t" .
            $contigs         . "\t" .
            $domain          . "\t" .
            $genetic_code    . "\t" .
            $gc_content      . "\t" .
            $source_id              ;

  # Add taxonomy hierarchy
  $fields .= ( "\t" . $taxonomy{$gid} );

  $genome_fields{$gid} = $fields;
           
}

close (GENOME);







# Process the feature file to link feature information to corresponding genome (and taxonomy) information

open (FEATURE, $feature_file);

while (<FEATURE>) {
  $entry = $_;
  $entry =~ s/\s*$//;   # Remove trailing whitespace

  # Fields (and tab delimiters) at the end of a record may be missing
  @columns = ();
  @columns = split(/\t/,$entry);
  if ( $columns[0] ) { $fid             = $columns[0]; } else { $fid             = ""; } 
  if ( $columns[1] ) { $feature_type    = $columns[1]; } else { $feature_type    = ""; } 
  if ( $columns[2] ) { $source_id       = $columns[2]; } else { $source_id       = ""; } 
  if ( $columns[3] ) { $sequence_length = $columns[3]; } else { $sequence_length = ""; } 
  if ( $columns[4] ) { $function        = $columns[4]; } else { $function        = ""; } 
  if ( $columns[5] ) { $alias           = $columns[5]; } else { $alias           = ""; } 

  # Concatenate fields of interest
  $fields = $fid             . "\t" .
            $feature_type    . "\t" .
            $source_id       . "\t" .
            $sequence_length . "\t" .
            $function        . "\t" .
            $alias                  ;

  # Determine genome ID from feature ID
  $fid =~ /^(kb\|g\.\d+)\./;
  $gid = $1;

  print $fields . "\t" . $genome_fields{$gid} . "\n";
}


close (FEATURE);
