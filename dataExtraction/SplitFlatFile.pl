#!/usr/bin/perl

$flat_file   = $ARGV[0];
$max_entries = $ARGV[1];


open (FLAT, $flat_file);


$file_number = 0;
$line_count  = 0;

# Assuming we'll have 100 or fewer files after splitting

$file_padded_num = sprintf("%02d", $file_number);
$out_file = ">" . "IndexFile_" . $file_padded_num . ".txt"; 

open (OUT, $out_file);

while(<FLAT>) {
  if ( $line_count == $max_entries) {
    close (OUT);
    $file_number++;
    $file_padded_num = sprintf("%02d", $file_number);
    $out_file = ">" . "IndexFile_" . $file_padded_num . ".txt"; 
    open (OUT, $out_file);
    $line_count = 0;
  }

  print OUT;

  $line_count++;
}
