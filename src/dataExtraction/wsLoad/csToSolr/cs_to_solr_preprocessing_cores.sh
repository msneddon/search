# all this is likely throwaway code while we learn the right
# way to deal with these structures
# is also somewhat incomplete (e.g., doesn't cover Feature, FeatureAlias,
# Location; those are more or less just a direct import into solr)

# first: dump all db tables in tables file
# (may not need all of them, may be some needed not listed there
# need to curate the list better)

# horrible perl one-liner to join Family and FamilyFunction
# need to fix in case fid has multiple families; see pubs
cat Family.tab FamilyFunction.tab | perl -F\\t -ane 'if(eof){map {print join "\t",$families{$_}{family},$families{$_}{release},$families{$_}{type},($families{$_}{function}."\n") } sort keys %families}elsif($F[2]){chomp $F[2];$families{$F[0]}{family}=$F[0];$families{$F[0]}{release}=$F[1];$families{$F[0]}{type}=$F[2]}else{chomp $F[1];$families{$F[0]}{family} = $F[0];$families{$F[0]}{function}=$F[1];};' > Family+Function.tab

# join
join -t $'\t' HasMember.tab Family+Function.tab |perl -p -e 's/"//g' > Families.tab


cat publications.tab Concerns.tab | perl -F\\t -ane 'next if /^pubmed_id/; if($F[7]){chomp $F[7];$pubs{$F[0]}{pubmed_id}=$F[0];$pubs{$F[0]}{pubmed_url}=$F[1];$pubs{$F[0]}{pubdate}=$F[2];$pubs{$F[0]}{journal_title}=$F[3];$pubs{$F[0]}{link}=$F[1];$pubs{$F[0]}{article_title}=$F[4];$pubs{$F[0]}{article_title_sort}=$F[5];$pubs{$F[0]}{authors}=$F[6]} else {chomp $F[1]; print join "\t",$F[1],$F[0],$pubs{$F[0]}{pubdate},$pubs{$F[0]}{link},$pubs{$F[0]}{journal_title},$pubs{$F[0]}{article_title},$pubs{$F[0]}{article_title_sort},($pubs{$F[0]}{authors}."\n")}; ' | perl -p -e "s/'//g" |sort > publications+Concerns.tab

cat publications+Concerns.tab IsProteinFor.tab | perl -F\\t -ane 'if($F[7]){$pubs{$F[0]}=$_;}elsif($pubs{$F[0]}){chomp $F[1];print join "\t",$F[1],$pubs{$F[0]}}' \
|perl -p -e 's/"//g' | cut -f1,3- > Publications.tab

# subsystems
#cat Includes.tab IsRoleOf.tab | perl -F\\t -ane 'if(defined $F[2]){chomp $F[4]; $subsys{$F[1]}{subsystem}=$F[0];$subsys{$F[1]}{role}=$F[1];} else{chomp $F[1]; print join "\t",@F,($subsys{$F[0]}{subsystem}."\n");}' \
# | perl -p -e 's/"//g' | sort > subsystems.tab
saplingv3db -B -N -e 'select * from IsRoleOf r join Includes i ON (r.from_link=i.to_link) limit 1;' |head -1 > IsRoleOf+Includes.tab.headers
cut -f1-3 IsRoleOf+Includes.tab > subsystems.tab

# why dups?  grr
# possibly nothing to worry about, just get rid of dups
# will need all later for subsystem_data
cat Contains.tab subsystems.tab | perl -F\\t -ane 'if(defined $F[2]){chomp $F[2];print join "\t",$ss{$F[1]}{fid},($F[2]."\n")}else{chomp $F[1];$ss{$F[0]}{cell}=$F[0];$ss{$F[0]}{fid}=$F[1];};' \
 | perl -p -e 's/"//g' | sort -u > Subsystems.tab

# subsystem_data is horrible
# just do one crazy query, has everything needed
# takes ~45min
time saplingv3db -B -N -e ' select c.to_link as feature_id,d.from_link as subsystem,v.code as variant,ir.from_link as role from Variant v join IsImplementedBy im ON (v.id=im.from_link) join IsRowOf r on (im.to_link=r.from_link) join Describes d on (v.id=d.to_link) join Includes i on (d.from_link=i.from_link) join Contains c on (c.from_link=r.to_link) join IsRoleOf ir on (ir.to_link = c.from_link and ir.from_link=i.to_link) ' > SubsystemData.tab
perl -pi -e 's/"//g' SubsystemData.tab
 

# atomic regulons
# should be easy but need counts
cat IsFormedOf.tab | perl -F\\t -ane '$count{$F[0]}++;if(eof){print map {$_."\t".$count{$_}."\n"} sort keys %count;}' > arcount.tab
join -t $'\t' IsFormedOf.tab arcount.tab > AtomicRegulons.tab

# cooccurring
LC_COLLATE=C sort IsDeterminedBy.tab > IsDeterminedBy.sorted.tab
join -t $'\t' IsDeterminedBy.sorted.tab PairSet.tab |sort -k2 > cooccurring.tab
LC_COLLATE=C sort -k2 IsInPair.tab > IsInPair.sorted.tab
# this is a cheat
cat cooccurring.tab | perl -F\\t -ane '($fid1,$fid2)=split /:/,$F[1];print join "\t",$fid1,$fid2,$F[3];print join "\t",$fid2,$fid1,$F[3];' \
 > CoOccurringFids.tab

# coexpressed
ln -s IsCoregulatedWith.tab CoExpressedFids.tab

# regulon_data
cat IsRegulatedIn.tab | perl -F\\t -ane 'chomp $F[1];push @{$reg{$F[1]}},$F[0];if(eof){for $key (sort keys %reg){for $fid (@{$reg{$key}}) {print join "\t",$fid,$key,(join ",",@{$reg{$key}});print "\n"; }  } };' \
 > regulondata.tab

cat Controls.tab regulondata.tab | perl -F\\t -ane 'if($F[2]){chomp $F[2];print join "\t",@F,( (join ",",@{$reg{$F[1]}}) . "\n");}else{chomp $F[1];push @{$reg{$F[1]}},$F[0]; }' \
 > RegulonData.tab
