# test_propan_runner.py
# Automated tests for PROPAN Fortran solver runner.

import unittest
from pathlib import Path
from propan_runner import run_propan_custom_j, SOLVER_EXE

class TestPropanRunner(unittest.TestCase):
    def test_solver_exists(self):
        self.assertTrue(SOLVER_EXE.exists(), "PROPAN Fortran solver executable does not exist.")

    def test_run_arbitrary_custom_j_values(self):
        arbitrary_test_j_list = [0.651, 0.712, 0.781, 0.7137]
        for test_j in arbitrary_test_j_list:
            with self.subTest(j=test_j):
                df_res = run_propan_custom_j(test_j)
                self.assertFalse(df_res.empty, "DataFrame should not be empty")
                self.assertEqual(len(df_res), 1)
                self.assertAlmostEqual(df_res["J"].iloc[0], test_j, places=4)
                self.assertGreater(df_res["KTP"].iloc[0], 0.0)
                self.assertGreater(df_res["KQP"].iloc[0], 0.0)
                self.assertGreater(df_res["eta_o"].iloc[0], 0.0)
                # Ensure convergence metadata is preserved
                self.assertIn("ERRK_final", df_res.columns)
                self.assertIn("kutta_iterations", df_res.columns)

if __name__ == "__main__":
    unittest.main()

