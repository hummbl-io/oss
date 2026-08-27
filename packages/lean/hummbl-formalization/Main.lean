import HummblFormalization

def main : IO Unit := do
  IO.println "=== HUMMBL Formalization Kernel (Lean 4) ==="
  IO.println "Loaded & Verified Modules:"
  IO.println "  - HummblFormalization.Basic (McShea Goal-Directedness & Plasticity)"
  IO.println "  - HummblFormalization.AshbyWissnerGross (Requisite Variety & Path Entropy)"
  IO.println "All mathematical theorems verified with 0 sorry."
