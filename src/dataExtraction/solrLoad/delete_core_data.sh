
core=$1

echo deleting data from core $core

curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=$core"
curl "http://localhost:7077/search/$core/update?stream.body=<delete><query>*:*</query></delete>"

curl -q "http://localhost:7077/search/admin/cores?wt=json&action=RELOAD&core=$core"
