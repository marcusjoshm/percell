from pathlib import Path
import pandas as pd
from percell.adapters.outbound.pandas_metadata_adapter import PandasMetadataAdapter


def test_read_write_roundtrip(tmp_path: Path):
    adapter = PandasMetadataAdapter()
    df = pd.DataFrame({"id": [1, 2], "v": ["a", "b"]})
    path = tmp_path / 'a.csv'
    adapter.write_csv(path, df, index=False)
    df2 = adapter.read_csv(path)
    pd.testing.assert_frame_equal(df2, df)


def test_merge_csv(tmp_path: Path):
    adapter = PandasMetadataAdapter()
    left = pd.DataFrame({"id": [1, 2], "x": [10, 20]})
    right = pd.DataFrame({"id": [2, 3], "y": [200, 300]})
    left_path = tmp_path / 'left.csv'
    right_path = tmp_path / 'right.csv'
    out_path = tmp_path / 'merged.csv'
    left.to_csv(left_path, index=False)
    right.to_csv(right_path, index=False)

    merged = adapter.merge_csv(left_path, right_path, on='id', how='outer', output_path=out_path)
    assert out_path.exists()
    # expected merge result contains rows for ids 1,2,3
    assert set(merged['id'].tolist()) == {1, 2, 3}
