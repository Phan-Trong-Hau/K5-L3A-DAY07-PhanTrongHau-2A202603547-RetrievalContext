"""Run the full code test suite and record an explicit reproducible result."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import save, utc


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    save('results/nd13/code_tests.json', {'recorded_at': utc(), 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
        'successful': result.wasSuccessful(), 'command': 'python3 scripts/check_tests.py',
        'note': 'Offline behavior tests include mocks; not model-quality benchmark.'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
