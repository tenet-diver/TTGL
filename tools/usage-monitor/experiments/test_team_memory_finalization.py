import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from finalize_team_memory_results import archive_audit,totals
from plot_team_memory_extension import static_svg,plot


class FinalAuditTests(unittest.TestCase):
    def cell(self,complete):
        return dict(native_usage_by_model={'gpt-6.1-sol':dict(input_tokens=100,cached_input_tokens=40,output_tokens=10,total_tokens=110),
            'gpt-6-luna':dict(input_tokens=10,cached_input_tokens=2,output_tokens=1,total_tokens=11)},
            inference_accounting_complete=complete,standard_credit_scenario_lower_bound=2,
            unknown_request_count=0 if complete else 1,observed_local_embedding_inferences=3,summed_recorded_embedding_seconds=.5)

    def test_full_total_includes_maintenance_without_adding_cached_subset(self):
        value=totals([self.cell(True)])
        self.assertEqual(value['actual_total_native_usage']['total_tokens'],121)
        self.assertEqual(value['actual_total_native_usage']['cached_input_tokens'],42)

    def test_one_unknown_request_makes_aggregate_total_unknown(self):
        value=totals([self.cell(True),self.cell(False)])
        self.assertEqual(value['recorded_native_usage_lower_bound']['total_tokens'],242)
        self.assertIsNone(value['actual_total_native_usage'])
        self.assertIsNone(value['standard_scenario_total'])

    def test_archive_member_hash_not_only_compressed_file_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'snapshot.tar.xz';body=b'original proof'
            with tarfile.open(archive,'w:xz') as tar:
                info=tarfile.TarInfo('evidence.txt');info.size=len(body);tar.addfile(info,io.BytesIO(body))
            (root/'recompression-001.json').write_text(json.dumps(dict(exact_raw_tar_roundtrip=True,xz_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))
            expected=dict(verified=True,file_hashes={'evidence.txt':hashlib.sha256(body).hexdigest()},symlinks={})
            (root/'archive.json').write_text(json.dumps(expected));self.assertEqual(archive_audit(root)['verified_files'],1)
            expected['file_hashes']['evidence.txt']='0'*64;(root/'archive.json').write_text(json.dumps(expected))
            with self.assertRaises(ValueError):archive_audit(root)

    def test_svg_is_self_contained_and_browser_inline_compatible(self):
        svg=static_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><script>ignored()</script><text>measured</text></svg>')
        self.assertTrue(svg.startswith('<svg '));self.assertNotIn('script',svg);self.assertIn('measured',svg)
        with self.assertRaises(ValueError):static_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://external.invalid/a"/></svg>')

    def test_final_figure_rejects_incomplete_comparison_before_importing_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):plot(dict(state='running',completed=55,planned=56),Path(directory))


if __name__=='__main__':unittest.main()
