# Contributing

Please open an issue or pull request with the affected citation key, dataset file, run identifier or figure, and a primary-source link where applicable.

For literature additions, distinguish corrections to the manuscript snapshot from work published after its September 2026 scope cutoff. Do not change method categories merely to match another survey. For data corrections, preserve the original artifact and document the transformation and record counts.

For code changes, run `python -m unittest discover -s tests -v` and `python -m analysis.insight rebuild --output-dir outputs/review`. Keep new outputs outside released data/results/assets. GPU extraction is optional and should be reported separately from CPU archive reconstruction.

Please do not add model weights, access tokens, private local paths or third-party paper PDFs. Detector training/evaluation implementations belong to their upstream projects; this companion repository documents their reported use.
