"""
Unified Entry Point for UNIX MLFQ Scheduler Simulator.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import sys
import os

def main():
    if len(sys.argv) > 1:
        flag = sys.argv[1].lower()
        if flag in ("--gui", "-g"):
            import gui
            gui.launch_gui()
            return
        elif flag in ("--web", "-w"):
            import web_dashboard
            web_dashboard.generate_and_open()
            return
        elif flag in ("--test", "-t"):
            import unittest
            suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
            runner = unittest.TextTestRunner()
            runner.run(suite)
            return

    # Default to CLI
    import cli
    cli.main()


if __name__ == "__main__":
    main()
