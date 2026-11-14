"""Create an isolated run directory, preserving submitted evidence and holdout freeze."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.output.resolve()
    if destination.exists():
        raise ValueError('Choose a new output directory; existing runs are never overwritten')
    destination.mkdir(parents=True)
    for folder in ('src', 'configs', 'benchmark', 'scripts'):
        shutil.copytree(root / folder, destination / folder, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(root / 'data/day6', destination / 'data/day6')
    # Start from dev only. New traces require a fresh audit, selection, then test.
    subprocess.run([sys.executable, '-m', 'src.run', '--split', 'dev'], cwd=destination, check=True)
    print(f'New dev traces: {destination}/results/dev')
    print('Audit each configuration into reviews.json, run scripts/freeze.py --split dev, then src.run --split test.')


if __name__ == '__main__':
    main()
