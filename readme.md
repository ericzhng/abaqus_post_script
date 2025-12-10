
source /home/ZhangHui/software/venv/env_common/bin/activate
python main_abaqus_post.py -i "[142872, 142879:142894]" -o "." -t "Braking"


./post_runner.sh "142872,142879:142894"
./post_runner.sh "142874,142895:142910"
./post_runner.sh "142876,142911:142926"
./post_runner.sh "142878,142927:142942"
