#!/usr/bin/env python3
"""Final boundary controls: pause/seal separate state, actor/verifier UID drops."""
import argparse
import lhtb_actor_controls as original
from lhtb_actor_runtime_v4 import UnknownActor
original.ROOT=original.BASE/'actor-controls-008'
original.UnknownActor=UnknownActor
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('condition',choices=['boundary','empty','reference']);original.run(parser.parse_args().condition)
