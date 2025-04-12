#!/bin/bash
#CHeck requirments,txt if any is not needed
#create list of import used in all of our py code,
#1 list all py files 
# grep for import on ly
#go thru req and check if not found anywhere we can assum its not needed!

#BUGS:
# its getting some packages that are not needed to be imported like os or time
# does not seem to have entire list of used 

#maybe would be easier to just find out all packages we need 

FI="requirements-used.txt"
echo "" > $FI 
LISTF=$(tree  --gitignore -I '*pyc' -I __pycache__ -I include -I backups -f -i |grep '.py' )
LF=""

#Go thru all py and get all import to a txt file
for I in $LISTF; do
 #echo $I 
 #grep '^import' $I |awk '{ print $2 }' |tee -a $FI
 grep  -w import $I |grep -v '\.'|awk '{ print $2 }' >> $FI
done
#cat $FI 

#Clean up 
cat $FI |sort |uniq > $FI.clean
mv -fv $FI.clean $FI 

wc -l $FI
wc -l requirements.txt 
#cat $FI 

T=0
for i in $(cat requirements.txt|awk -F'=' '{ print $1}'); do
 CHECK=$(grep -i -c $i $FI) 
#echo "CHECKING $i"
  if [ $CHECK -eq 0 ]; then
   T=$(echo "1 + $T"|bc)
   echo "$i is not needed"
  fi  
done

echo "Total not needed $T"