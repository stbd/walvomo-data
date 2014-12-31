
path="../walvomo-server/src/db/"
if [ $# -ne 1 ]
then
    echo "Using default path to proto files"
else 
    path=$1
fi

for f in $path*.proto
do
    b=`basename $f`
    echo "$f $b"
    
    `protoc -I=$path --python_out=src/ $f`
done