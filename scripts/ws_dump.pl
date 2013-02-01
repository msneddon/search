#!/usr/bin/env perl
use strict;
use warnings;
use Bio::KBase::workspaceService::Helpers qw(get_ws_client workspace workspaceURL parseObjectMeta parseWorkspaceMeta);
use Data::Dumper;
use JSON;

sub print_json  {
    my $ra_data = shift;
    my $ra_key = shift;
    my $size = shift;
    die "The key size is not matching to data size\n" if $#$ra_data != $#$ra_key;

    print "{";
    my $first = 1;
    for(my $i = 0; $i < $size; $i += 1) {
        if($first) {
            $first = 0;
        } else {
            print ",\n";
        }
        print '"'.$$ra_key[$i].'" : "'.$$ra_data[$i].'"';
    }
    print "}";
}

my $serv = get_ws_client();
my $output = $serv->list_workspaces({});
my @ws_key = ("id", "owner", "moddate", 'object_count', "user_perm", "defaultPermissions");
my @ws_lobj_key = ("_id", "object", "object_id", "type", "moddate", 'version', 'command', "lastmodifier", 'owner', 'workspace_id', 'workspace_ref', 'chsum', 'mapping');

my $json = JSON->new;
print "[";
my $first = 1;
foreach my $wsra (@$output) {
    # print object meta data in each workspace
    my $lo_output = $serv->list_workspace_objects({'workspace' => $$wsra[0]});
    foreach my $wsomra (@$lo_output) {
        if($first) { 
            $first = 0;
        } else {
            print ",\n";
        }

        my $object = $serv->get_object({'workspace' => $$wsra[0], 'id' => $$wsomra[0], 'type' => $$wsomra[1]});
        my $ostr = to_json($object);
        
        $ostr =~ s/\\/\\\\/g;
        $ostr =~ s/\//\\\//g;
        $ostr =~ s/\n/\\n/g;
        $ostr =~ s/"/\\"/g;
        unshift @$wsomra, $ostr;
        unshift (@$wsomra, $$wsra[0]."_".$$wsomra[1]);
        print_json($wsomra, \@ws_lobj_key, 10);
    } 
}
print "]\n";
