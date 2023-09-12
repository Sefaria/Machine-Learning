# /bin/bash
for i in {1..1000}; do echo -e "\n$i\n"; python ./main.py -e -c -u urls.txt -m 1000 --skip-existing --use-selenium; done
# -s "`ls -l output | wc -l`"; done
#python ./main.py -e -c -u urls.txt
