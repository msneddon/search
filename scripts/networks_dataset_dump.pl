use strict;
use Carp;
use Data::Dumper;
use JSON;
use Bio::KBase::KBaseNetworksService::Client;

my $oc = Bio::KBase::KBaseNetworksService::Client->new("http://140.221.84.160:7064/KBaseNetworksRPC/networks");
my $results = $oc->allDatasets();
my $first = 1;
print "[";
foreach my $rh (@{$results}) {
  if($first > 0) {
    $first = 0;
  } else {
    print ",\n";
  }
  delete  $rh->{'properties'};
  print to_json($rh);
}
print "]\n";
