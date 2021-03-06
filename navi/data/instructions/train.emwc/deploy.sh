#!/bin/bash
python ../../../../pysrc/labeled_to_singlesentence.py -u corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.txt > corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg
python ~/dev/research/tiny.git/tiny/pysrc/singlesentence_preprocess.py corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg
python split_to_folds.py
mv *.ccg ~/dev/research/tiny.git/navi/experiments/noimplicit.segmented.dev.emwc.cross
cd ~/dev/research/tiny.git/navi/experiments/noimplicit.segmented.dev.emwc.cross
mkdir giza
cd giza
python ~/dev/research/tiny.git/tiny/pysrc/create_gize_job.py -o nl2lf -g ~/dev/research/tiny.git/tiny/giza/giza-pp/GIZA++-v2 -s NL -p ~/dev/research/tiny.git/tiny/pysrc/giza_postprocess.py ../corpus1-instructions.xgoal.noimplicit.segmented.train.emwc.ccg 
./nl2lf.giza.sh
mv nl2lf.giza.cooc ..
cd ..
rm -rf giza
