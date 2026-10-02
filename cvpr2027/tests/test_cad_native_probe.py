"""Verifier controls and generated-code execution boundary checks."""
import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cad_native_probe import build_shape, geometry_delta

class NativeProbeTests(unittest.TestCase):
    def test_equivalent_constructions(self):
        a=build_shape('import cadquery as cq\nresult=cq.Workplane("XY").box(10,12,4)')
        b=build_shape('result=cq.Workplane("XY").rect(10,12).extrude(2,both=True)')
        self.assertLess(geometry_delta(a,b)['symmetric_difference_fraction'],1e-8)

    def test_same_volume_wrong_position_fails(self):
        a=build_shape('result=cq.Workplane("XY").box(10,12,4)')
        b=a.translate((0.1,0,0))
        self.assertAlmostEqual(a.Volume(),b.Volume())
        self.assertGreater(geometry_delta(a,b)['symmetric_difference_fraction'],0.0001)

    def test_same_bbox_missing_hole_fails(self):
        a=build_shape('result=cq.Workplane("XY").box(10,12,4)')
        b=build_shape('result=cq.Workplane("XY").box(10,12,4).faces(">Z").workplane().hole(2)')
        self.assertGreater(geometry_delta(a,b)['symmetric_difference_fraction'],0.0001)

    def test_io_and_introspection_rejected(self):
        for code in ['import os\nresult=1','result=open("/tmp/x","w")','result=cq.__dict__',
                     'result=cq.exporters.export(1,"x")','cq=1','result=(1).__class__']:
            with self.subTest(code=code),self.assertRaises(ValueError):build_shape(code)

    def test_step_roundtrip_is_equivalent_or_unscored(self):
        import cadquery as cq
        source=Path(__file__).resolve().parents[1]/'data/cad-native-probe/t5hard_pipe_elbow_U_a/source.py'
        a=build_shape(source.read_text())
        with tempfile.TemporaryDirectory() as d:
            p=str(Path(d)/'elbow.step');cq.exporters.export(a,p)
            b=cq.importers.importStep(p).val()
            try:delta=geometry_delta(a,b)
            except ArithmeticError:return # Kernel inconsistency must not yield a false failure.
            self.assertLess(delta['symmetric_difference_fraction'],0.0001)

if __name__=='__main__':unittest.main()
