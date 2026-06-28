import sys
import os

import pytest

# tools/ is not a package; add it to the path to import the script module.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

from watch_batch import vid_id


class TestVidId:
    def test_reel_url(self):
        assert vid_id("https://www.instagram.com/reel/DZVEN4gMRXV/", 1) == "DZVEN4gMRXV"

    def test_p_post_url(self):
        assert vid_id("https://www.instagram.com/p/DZlQ7GZnJR7/", 1) == "DZlQ7GZnJR7"

    def test_tv_url(self):
        assert vid_id("https://www.instagram.com/tv/ABC123/", 1) == "ABC123"

    def test_strips_query_string(self):
        assert vid_id("https://www.instagram.com/reel/ID42/?utm=1", 1) == "ID42"

    def test_unmatched_url_falls_back_to_index(self):
        assert vid_id("https://example.com/not-a-reel", 7) == "video_7"
