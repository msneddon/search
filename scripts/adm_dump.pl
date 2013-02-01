#!/usr/bin/perl -w
use strict;
use JSON;

my $json = new JSON;
my $BASE_URL = "http://kbase.us/services/shock-api";
my $URI = "$BASE_URL/node";

my $chunk_size = 8192;
my $skip= - $chunk_size;
my $first = 1;
print "[";
while(1) {
  $skip += $chunk_size;
  my $res = `curl -s -X GET '$URI/?skip=$skip&limit=$chunk_size'`;
  my $rh =  from_json($res);
  
  last if !defined $rh->{'D'} || scalar @{$rh->{'D'}} == 0;
  foreach my $doc (@{$rh->{'D'}}) {
    my %nd = ();
    $nd{'adm_id'} = $doc->{'id'};
    $nd{'version'} = $doc->{'version'};
    $nd{'meta_data'} = join("\n", map{defined $doc->{'attributes'}->{$_} && $_." : ".$doc->{'attributes'}->{$_}} keys %{$doc->{'attributes'}})."\n" if(defined $doc->{'attributes'});
    if (defined $doc->{'file'}) {
      $nd{'file_format'} = $doc->{'file'}->{'foramt'} if defined $doc->{'file'}->{'foramt'};
      $nd{'file_name'} = $doc->{'file'}->{'name'} if defined  $doc->{'file'}->{'name'} && $doc->{'file'}->{'name'} ne "";
      $nd{'file_size'} = $doc->{'file'}->{'size'} if defined $doc->{'file'}->{'size'} && $doc->{'file'}->{'size'} > 0;
    }
    if($first) {
      $first = 0;
    } else {
      print ",\n";
    }
    print to_json(\%nd);
  }
}
print "]\n";
