import logging
import sys

from src.main import Lorekeeper

logging.basicConfig(level=logging.INFO)
lorekeeper = Lorekeeper(sys.argv)
sys.exit(lorekeeper.exec_())
