use strict;
use Data::Dumper;
use Bio::KBase::CDMI::CDMI;
use Bio::KBase::CDMI::CDMI_EntityAPIImpl;
use Bio::KBase::CDMI::CDMI_APIImpl;

my $cdmi = Bio::KBase::CDMI::CDMI->new(
                                        #loadDirectory  => '~sjyoo/repo/kb_seed/lib/KSaplingDBD.xml',
                                        DBD  => '/home/newyork/sjyoo/repo/kb_seed/lib/KSaplingDBD.xml',
                                        #dbName => $dbName, 
                                        userData => 'cdmro/cdmro',
                                        dbhost => '127.0.0.1',
                                        port => 3306, dbms =>'mysql' );
my $csO = Bio::KBase::CDMI::CDMI_APIImpl->new($cdmi);
my $csEO = Bio::KBase::CDMI::CDMI_EntityAPIImpl->new($cdmi);

my $gH   = $csO->fids_to_genomes(['kb|g.3899.mRNA.10']);

print Dumper($gH);

