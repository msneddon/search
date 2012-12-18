use strict;
use Data::Dumper;
use Bio::KBase::CDMI::CDMIClient;

sub process_features {
  our $csO;
  our $csEO;
  my $fids = shift;

  # pulling data from CDM
  my $pfH  = $csO->fids_to_protein_families($fids);
  my $psH  = $csO->fids_to_protein_sequences($fids);
  my $pH   = $csO->fids_to_proteins($fids);
  my $gH   = $csO->fids_to_genomes($fids);
  my $lH   = $csO->fids_to_locations($fids);
  my $rH   = $csO->fids_to_roles($fids);
  my $sH   = $csO->fids_to_subsystem_data($fids);
  my $fdH  = $csO->fids_to_feature_data($fids);
  my $gdH  = $csO->genomes_to_genome_data([values %$gH]);
  my %tH   = map{@$_[1]->{'from_link'} => @$_[2]->{'id'}} @{$csEO->get_relationship_IsInTaxa([values %$gH],[],[],['id'])};
  $fdH = $csEO->get_entity_Feature($fids, ['id','feature-type','alias']);

  print Dumper($fdH);
  # dumping results as view
  foreach my $fid (@$fids) {

    # fields from pathways, which includes dnafeature, figfam ecnumber, taxonomy
    my $genome_name = '';        # from Genome
    my $accession = '';          # from Genome
    my $na_feature_id = '';      # from Feature (same to fid)
    my $gid = '';                # from Genome
    my $ncbi_tax_id = '';        # from Taxonomies
    my $sequence_info_id = '';   # 
    my $locus_tag = '';          # not available in CDM
    my $feature_type = '';       # gene, CDS, etc... need from entity API
    my $annotation = '';         #
    my $gene = '';               # from Feature
    my $product = '';            # from Role
    my $ec_number = '';          # not available in EcNumber table (sometime in roles)
    my $ec_name = '';            # not available in EcNumber table (sometime in roles)
    my $pathway_id = '';         # not available in CDM (use name instead)
    my $pathway_name = '';       # from subsystem
    my $start_max = '';          # from location
    my $end_min = '';            # inferred from location
    my $strand = '';             # from location
    my $na_length = '';          # from location
    my $aa_length = '';          # inferred from protein_seq
    
    # fields from figfam <-- data from Families
    my $figfam_id = '';          # from Family
    my $figfam_product = '';     # from Role

    # fields from taxonomy
    my $taxonomy_rank = '';      # not available in CDM

    # additional fields
    my $protein_seq        = "";

   

    $genome_name = $gdH->{$gH->{$fid}}->{'scientific_name'} if defined $gdH->{$gH->{$fid}}->{'scientific_name'};
    $accession = $gH->{$fid} if defined $gH->{$fid};
    $na_feature_id = $fid;
    $gid = $gH->{$fid} if defined $gH->{$fid};
    $ncbi_tax_id = $tH{$gH->{$fid}} if defined $tH{$gH->{$fid}};
    $feature_type = $fdH->{$fid}->{'feature_type'} if defined $fdH->{$fid}->{'feature_type'};

    if( defined $psH->{$fid}) {
      $protein_seq = $psH->{$fid};
      $aa_length = length($protein_seq);
    }
    
    my @loc_ref = ("DEFAULT_LOCATION");
    if( defined $lH->{$fid}) {
      @loc_ref = @{$lH->{$fid}};
    }
    my @families = ("DEFAULT_FAMILY");
    if( defined $pfH->{$fid}) {
      @families = @{$pfH->{$fid}};
    }
    my @roles = ("DEFAULT_ROLE");
    if( defined $rH->{$fid}) {
      @roles = @{$rH->{$fid}};
    }
    my @sub_ref = ("DEFAULT_SUBSYSTEM");
    if( defined $sH->{$fid}) {
      @sub_ref = @{$sH->{$fid}};
    }

    foreach my $location (@loc_ref) {
      if($#loc_ref == 0  && $location eq "DEFAULT_LOCATION") {
        # set default location values;
        $sequence_info_id = '';
        $locus_tag = '';
        $start_max = '';
        $end_min = '';
        $na_length = '';
        $strand = '';
      } else {
        $sequence_info_id = $$location[0];
        $start_max = $$location[1];
        $na_length = $$location[3];
        $strand = $$location[2];
        $end_min = $start_max + $na_length - 1;
      }
      foreach my $family (@families) {

        if($#loc_ref == 0  && $location eq "DEFAULT_FAMILY") {
          $figfam_id = '';
        } else {
          $figfam_id = $family;
        }
        foreach my $role (@roles) {
          if($#loc_ref == 0  && $role eq "DEFAULT_ROLE") {
            $figfam_product = '';
            $product = '';
          } else {
            $figfam_product = $role;
            $product = $role;
          }

          foreach my $subsystem_ref (@sub_ref){
            if($#loc_ref == 0  && $subsystem_ref eq "DEFAULT_SUBSYSTEM") {
              $pathway_id = '';
              $pathway_name = '';
            } else {
              next if $$subsystem_ref[2] ne $role; # we skip printing because role and subsystem is not matching (need more thorough checking later)
              $pathway_id = $$subsystem_ref[0];
              $pathway_name = $$subsystem_ref[0];
            }
            print "$genome_name\t$accession\t$na_feature_id\t$gid\t$fid\t$ncbi_tax_id\t$sequence_info_id\t$locus_tag\t$feature_type\t$annotation\t$gene\t$product\t$ec_number\t$ec_name\t$pathway_id\t$pathway_name\t$start_max\t$end_min\t$strand\t$na_length\t$aa_length\t$figfam_id\t$figfam_product\t$protein_seq\n";
          }
        }
      }
    }
  }
}


our $csO  = Bio::KBase::CDMI::CDMIClient->new_for_script();
our $csEO = Bio::KBase::CDMI::CDMIClient->new_get_entity_for_script();
our $CHUNK_SIZE = 100;
my $line = "";
my @fids = ();
while($line = <STDIN>) {
  chomp $line;
  next if $line =~ m/\s+/;
  push @fids, $line;
  
  if(scalar @fids >= $CHUNK_SIZE) {
    process_features(\@fids);
    @fids = ();
  }
}

# process left over
process_features(\@fids);
