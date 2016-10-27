
mkdir out

file=$1

for pyscript in *.py; do
   ipython $pyscript $file
done
	

