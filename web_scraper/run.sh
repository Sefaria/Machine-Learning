# /bin/bash
# for i in {1..100}; do echo -e "\n$i\n"; python ./main.py -e -c -u urls.txt -s "`ls -l output | wc -l`"; done
for i in {1..100}; do echo -e "\n$i\n"; python ./main.py -e -c -u urls.txt -s "184000"; done
