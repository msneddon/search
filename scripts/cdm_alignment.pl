use strict;
use warnings;
use Data::Dumper;
use Bio::KBase::CDMI::CDMIClient;
use JSON;

sub process_tree {
  our $csO;
  our $csEO;
  our $first;
  my $treeids = shift;

  my $toAlignments = $csEO->get_relationship_IsBuiltFromAlignment($treeids, ['id', 'status', 'data_type', 'source_id'],[],['id','n_rows','n_cols','status','sequence_type','source_id']);
  my %tid2info = map{$$_[0]->{id} => $$_[0] } @$toAlignments;
  my %aid2info = map{$$_[2]->{id} => $$_[2] } @$toAlignments;
  my %aid2tid  = map{$$_[2]->{id} => $$_[0]->{id}} @$toAlignments; 
  my %tid2aid = map{$$_[0]->{id}, $$_[2]->{id}} @$toAlignments; 
  my $toARH = $csEO->get_relationship_IncludesAlignmentRow([keys %aid2tid], ['id'],[],['id','row_number','row_id']);
  my %arid2aid = map{$$_[2]->{id} => $$_[0]->{id}} @$toARH;
  my %aid2arid = ();
  my %aid2arid_str = ();
  my %aid2arid_md5 = ();
  map{push@{$aid2arid{$$_[0]->{id}}}, $$_[2]->{id}} @$toARH; 
  map{push@{$aid2arid_str{$$_[0]->{id}}}, "id : ".$$_[2]->{id}." row_number : ".$$_[2]->{row_number}." row_id : ".$$_[2]->{row_id}} @$toARH; 
  map{push@{$aid2arid_md5{$$_[0]->{id}}}, $$_[2]->{row_id}} @$toARH; 
  my $toPS = $csEO->get_relationship_ContainsAlignedProtein([keys %arid2aid], ['id'],[],['id']);
  my %pid2arid = map{$$_[2]->{id} => $$_[0]->{id}} @$toPS;
  my %arid2pid = ();
  map{push@{$arid2pid{$$_[0]->{id}}}, $$_[2]->{id}} @$toPS; 
  my $toF = $csEO->get_relationship_IsProteinFor([keys %pid2arid], ['id'],[],['id', 'source_id', 'function', 'alias']);
  my %fid2pid = map{$$_[2]->{id} => $$_[0]->{id}} @$toF;
  my %pid2fid = ();
  map{push@{$pid2fid{$$_[0]->{id}}}, $$_[2]->{id}} @$toF; 
  my $toGenome   = $csEO->get_relationship_IsOwnedBy([keys %fid2pid],['id'],[],['id','scientific_name', 'md5']);
  my %fid2gid = map{$$_[0]->{id} => $$_[2]->{id}} @$toGenome;
  my %gid2info_str = map{$$_[2]->{id} => $$_[2]->{id}." ".$$_[2]->{scientific_name}." ".$$_[2]->{md5}} @$toGenome;

  foreach my $tid (@$treeids) {
    my %nd = ();
    $nd{'tree_id'} = $tid;
    $nd{'tree_status'} = $tid2info{$tid}->{'status'};
    $nd{'tree_data_type'} = $tid2info{$tid}->{'data_type'};
    $nd{'tree_source_id'} = $tid2info{$tid}->{'source_id'};
    $nd{'aln_id'} = $aid2info{$tid2aid{$tid}}->{'id'};
    $nd{'aln_n_rows'} = $aid2info{$nd{'aln_id'}}->{'n_rows'};
    $nd{'aln_n_cols'} = $aid2info{$nd{'aln_id'}}->{'n_cols'};
    $nd{'aln_status'} = $aid2info{$nd{'aln_id'}}->{'status'};
    $nd{'aln_sequence_type'} = $aid2info{$nd{'aln_id'}}->{'sequence_type'};
    $nd{'aln_source_id'} = $aid2info{$tid}->{'source_id'} if defined $aid2info{$tid}->{'source_id'};
    $nd{'aln_rows_ids'} = [@{$aid2arid{$nd{'aln_id'}}}];
    $nd{'aln_rows_row_ids'} = [@{$aid2arid_md5{$nd{'aln_id'}}}];
    $nd{'aln_rows'} = [@{$aid2arid_str{$nd{'aln_id'}}}];
    $nd{'protein_ids'} = [map{@{$arid2pid{$_}}} @{$nd{'aln_rows_ids'}}]; # pid is equal to aln_rows_row_ids
    $nd{'fids'} = [ map{ (defined $pid2fid{$_}) ? @{$pid2fid{$_}} : ()} @{$nd{'protein_ids'}}];
    my %gids = map{$fid2gid{$_} => $gid2info_str{$fid2gid{$_}}}@{$nd{'fids'}};
    $nd{'genome_ids'} = [ keys %gids];
    $nd{'genome'} = [ values %gids];
    if($first) {
      $first = 0;
    } else {
      print ",\n";
    }
    print to_json(\%nd);
  }
}


our $csO  = Bio::KBase::CDMI::CDMIClient->new_for_script();
our $csEO = Bio::KBase::CDMI::CDMIClient->new_get_entity_for_script();
our $CHUNK_SIZE = 100;
our $first = 1;
my $line = "";
my @treeids = ();
print "[";
while($line = <STDIN>) {
  chomp $line;
  next if $line =~ m/\s+/;
  push @treeids, $line;
  
  if(scalar @treeids >= $CHUNK_SIZE) {
    process_tree(\@treeids);
    @treeids = ();
  }
}

# process left over
process_tree(\@treeids);
print "]\n";
