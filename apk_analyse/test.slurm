#!/bin/bash
#SBATCH --job-name=hello_world
#SBATCH --partition=small
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH -n 1
#SBATCH --ntasks-per-node=1

module load miniconda3/4.8.2
source activate mypython3
python test_androguard.py