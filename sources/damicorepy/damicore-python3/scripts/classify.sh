#!/bin/bash

if [ ! -e ../../results/dataset ]; then
  mkdir ../../results/dataset
fi

set -x

SOME_DATASETS=(binaries EuroGOV TCL Wikipedia sms_spam)
DATASETS=(binaries EuroGOV TCL Wikipedia sms-spam lingspam-bare lingspam-lemmstop)

# Split datasets
for dataset in ${SOME_DATASETS[@]}; do
  dataset.py "../../dataset/${dataset}" \
    --membership "../../dataset/${dataset}-membership.csv" \
    --dest-dir ../../results/dataset \
    --split 0.1
done

# lingspam bare and lemmstop ref and test were copied manually

#### N.C.D. ####

if [ ! -e ../../results/ncd ]; then
  mkdir ../../results/ncd
fi

for compressor in zlib bz2 ppmd; do
  for dataset in ${DATASETS[@]}; do
    ref="../../results/dataset/${dataset}-ref"
    tst="../../results/dataset/${dataset}-test"
    self="../../results/ncd/${dataset}_${compressor}_self.csv"
    cross="../../results/ncd/${dataset}_${compressor}_cross.csv"

    if [ ! -e $self ]; then
      ncd2.py $ref \
        --output "${self}" \
        --compressor "${compressor}" \
        --level 9 --model-order 6
    fi
    if [ ! -e  $cross ]; then
      ncd2.py $ref $tst \
        --output "${cross}" \
        --compressor "${compressor}" \
        --level 9 --model-order 6
    fi
  done
done

#### Classification ####

if [ ! -e ../../results/classes ]; then
  mkdir ../../results/classes
fi

for compressor in zlib bz2 ppmd; do
  for dataset in ${DATASETS[@]}; do
    ncd_self="../../results/ncd/${dataset}_${compressor}_self.csv"
    ncd_cross="../../results/ncd/${dataset}_${compressor}_cross.csv"
    membership="../../dataset/${dataset}-membership.csv"
    if [ -e "../../results/classes/${dataset}_${compressor}_k${k}.csv" ]; then
      continue
    fi

    for k in 1 3 5; do
      classification.py $ncd_self $ncd_cross $membership --matrix-mode \
        --output "../../results/classes/${dataset}_${compressor}_k${k}.csv" \
        -k $k
    done
    # Counterproof classifier
#    classification.py $ncd_self $ncd_cross $membership --matrix-mode \
#      --output "../../results/classes/${dataset}_${compressor}_counter.csv" \
#      --use-counterproof
    # Quartet tree classifier
    classification.py $ncd_self $ncd_cross $membership --matrix-mode \
      --output "../../results/classes/${dataset}_${compressor}_quartet.csv"
  done
done

#### Compare partitions ####

if [ ! -e ../../results/validation ]; then
  mkdir ../../results/validation
fi

if [ ! -e ../../results/validation/tables ]; then
  mkdir ../../results/validation/tables
fi

if [ ! -e ../../results/easy_validation ]; then
  mkdir ../../results/easy_validation
fi

if [ ! -e ../../results/easy_validation/tables ]; then
  mkdir ../../results/easy_validation/tables
fi

for compressor in zlib bz2 ppmd; do 
  for dataset in ${DATASETS[@]}; do
    membership="../../dataset/${dataset}-membership.csv"
    output_base="../../results/classes/${dataset}_${compressor}"
    for classifier in k1 k3 k5 quartet; do
      partition.py $membership "${output_base}_${classifier}.csv" all \
        --output-table "../../results/validation/tables/${dataset}_${compressor}_${classifier}.txt" \
        --parse-classification --untrusted-group '*UNTRUSTED*' --trust-threshold 0.5 \
        > "../../results/validation/${dataset}_${compressor}_${classifier}_metrics.csv"

      partition.py $membership "${output_base}_${classifier}.csv" all --trim \
        --output-table "../../results/easy_validation/tables/${dataset}_${compressor}_${classifier}.txt" \
        --parse-classification --untrusted-group '*UNTRUSTED*' --trust-threshold 0.5 \
        > "../../results/easy_validation/${dataset}_${compressor}_${classifier}_metrics.csv"
    done
  done
done

../scripts/organize-validations.py
