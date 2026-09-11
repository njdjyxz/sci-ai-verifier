# Proposed scientific catalog seeds

These entries are provisional design material. They are never loaded by the default desktop extension, and building a release from them does not make them reviewed or executable.

See the [chemical mass pilot](../../reviews/CHEMICAL-MASS-PILOT.md) for scope, primary references, examples and the remaining approval/execution requirements. The selected first family is chemical formula and mass calculations. The runtime must keep composition, monoisotopic mass and average mass distinct.

For a local review package:

```powershell
python scripts/catalog_release.py build --source examples/catalog --output dist/catalog-candidate --version proposal-1 --provenance "Provisional chemical mass candidate; review pending"
```

The reviewed `registry/` and initial distributable `catalog/` remain empty. Automated tests construct separate synthetic approval metadata only inside temporary test directories. No test promotes these proposals or publishes a release.
