"""Import smoke tests for the ARCANA compatibility package."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_root_api_client_imports_without_pipeline_cycle():
    import api_client

    assert api_client.APIClient is not None
    assert api_client.AgentGenerationRequest is not None


def test_root_cli_imports_without_pipeline_cycle():
    import cli

    assert callable(cli.main)


def test_pipeline_submodules_import():
    import pipeline.api_client as pipeline_api
    import pipeline.cli as pipeline_cli
    import pipeline.governance as pipeline_governance
    import pipeline.models as pipeline_models
    import pipeline.renderer as pipeline_renderer

    assert pipeline_api.APIClient is not None
    assert callable(pipeline_cli._main)
    assert callable(pipeline_governance.validate_receipt)
    assert pipeline_models.ARCANAArticle is not None
    assert callable(pipeline_renderer.render_article)


def test_pipeline_package_lazy_api_exports():
    from pipeline import APIClient, ARCANAArticle

    assert APIClient is not None
    assert ARCANAArticle is not None


def _run_standalone():
    fns = [(n, f) for n, f in globals().items()
           if n.startswith("test_") and callable(f)]
    fails = 0
    for name, fn in fns:
        try:
            fn()
            print(f"OK    {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - fails}/{len(fns)} passed")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
