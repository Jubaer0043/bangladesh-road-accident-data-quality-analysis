"""Execute notebooks with the active project interpreter, without global configuration."""

import json
from pathlib import Path
import sys
import tempfile

from .config import ROOT

NOTEBOOK_NAMES = (
    "00_dataset_and_source_assessment.ipynb",
    "01_source_quality_and_cleaning.ipynb",
    "02_eda_statistics_and_visualization.ipynb",
    "03_statistics_and_identity_sensitivity.ipynb",
    "04_data_suitability.ipynb",
)


def execute():
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager

    runtime = ROOT / "data/interim"
    runtime.mkdir(parents=True, exist_ok=True)
    paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
    if tuple(path.name for path in paths) != NOTEBOOK_NAMES:
        raise ValueError("Notebook files do not match the documented sequence")
    with tempfile.TemporaryDirectory(dir=runtime) as directory:
        spec = Path(directory) / "bd-safety"
        spec.mkdir()
        (spec / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        sys.executable,
                        "-m",
                        "ipykernel_launcher",
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": "Bangladesh road safety project",
                    "language": "python",
                    "env": {
                        "IPYTHONDIR": str(runtime / "ipython"),
                        "MPLCONFIGDIR": str(runtime / "matplotlib"),
                    },
                }
            )
        )
        for path in paths:
            notebook = nbformat.read(path, as_version=4)
            nbformat.validate(notebook)
            km = KernelManager(
                kernel_name="bd-safety",
                kernel_spec_manager=KernelSpecManager(
                    kernel_dirs=[directory], ensure_native_kernel=False
                ),
            )
            try:
                NotebookClient(
                    notebook,
                    km=km,
                    kernel_name="bd-safety",
                    timeout=300,
                    resources={"metadata": {"path": str(ROOT)}},
                ).execute()
            finally:
                if km.has_kernel:
                    km.shutdown_kernel(now=True)
            nbformat.write(notebook, path)
    return [p.name for p in paths]
