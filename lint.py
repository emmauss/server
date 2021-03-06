import os
import sys
import argparse
from subprocess import run

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--format', action='store_true', help="Autoformat before running flake8")
    args = parser.parse_args()

    if not os.path.isdir("happypanda"):
        print("This file needs to be run in the same directory as the 'happypanda/' directory")
        sys.exit()

    if args.format:
        for root, dirs, files in os.walk("happypanda"):

            for f in files:
                if f.endswith('.py'):
                    f_path = os.path.join(root, f)
                    print("Auto formatting", f_path)
                    run(["autopep8", "--in-place", "-a", "--max-line-length=120", f_path])

    print("Running flake8...\n")
    return run(["flake8", "--config", "./setup.cfg", "happypanda"]).returncode

if __name__ == '__main__':
    sys.exit(main())