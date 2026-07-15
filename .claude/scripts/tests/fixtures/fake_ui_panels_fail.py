#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--crawl')
parser.add_argument('--mode', required=True)
parser.add_argument('--transcript')
args = parser.parse_args()
raise SystemExit(7 if args.mode == 'panels' else 0)
