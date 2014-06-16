# very quick notes on getting CS objects into workspace

# configure my.cnf file in cwd, example in csToFlatFiles/my.cnf
# (keep on local storage, not ~ NFS, or nfs will croak and your run will die)
# this gets full dump
bash csToFlatFiles/dumpFeatureTables
# for debugging, can do
# limit=' LIMIT 5000 ' bash csToFlatFiles/dumpFeatureTables


# need to remind myself what switches there are
# in theory we want switches to ignore or replace existing objects
# and a switch to specify which ws instance to use
# and a switch to specify which workspace to use
python csFlatFiles_to_ws.py
