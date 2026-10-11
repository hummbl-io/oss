# PyPI download snapshots

`pypi-downloads.csv` contains per-package snapshots collected by
[`pypi_download_tracker.py`](../scripts/pypi_download_tracker.py). Current
daily snapshots are stored on the repository's
[`data/pypi-downloads` branch](https://github.com/hummbl-io/oss/blob/data/pypi-downloads/tools/data/pypi-downloads.csv).

| Column | Meaning |
| --- | --- |
| `date` | Collection date |
| `package` | PyPI distribution name |
| `downloads_7day` | Recent endpoint's last-week download count |
| `downloads_30day` | Recent endpoint's last-month download count |
| `downloads_total` | Sum of the overall endpoint's available daily history, with known mirrors excluded; at most 180 days |

`-1` means a count is unknown because collection failed. The
`downloads_total` column retains its historical name for existing readers;
it is a rolling API-window sum, not an all-time package download total.
Newer packages or incomplete responses can cover less than 180 days. The
collector does not record the exact returned date bounds, so this column
does not certify a complete 180-day series. Do not sum window totals across
collection dates: successive snapshots overlap.

The [PyPI Stats API documentation](https://pypistats.org/api/) describes the
retention limit and the `recent` and `overall` endpoints. The collector uses
`overall?mirrors=false`. Download counts include CI and repeated downloads;
they do not establish unique users, production adoption or paying customers.
See the [PyPI Stats FAQ](https://pypistats.org/faqs) for traffic limitations.
