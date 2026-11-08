import tempfile
import unittest
from pathlib import Path

from PIL import Image

from img_batch.core import collect, flatten, fit, process, square_pad, trim_border


def make_product(path: Path, size=(900, 600), box=(250, 150, 650, 450), background=(255, 255, 255)):
    """White canvas with a dark rectangle in the middle."""
    img = Image.new("RGB", size, background)
    for x in range(box[0], box[2]):
        for y in range(box[1], box[3]):
            img.putpixel((x, y), (20, 60, 120))
    img.save(path)
    return path


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.photo = make_product(self.dir / "FOA-110.png")

    def tearDown(self):
        self.tmp.cleanup()

    def test_trim_removes_white_border(self):
        with Image.open(self.photo) as img:
            trimmed = trim_border(img.convert("RGB"))
        self.assertEqual(trimmed.size, (400, 300))

    def test_square_pad_is_square(self):
        with Image.open(self.photo) as img:
            padded = square_pad(trim_border(img.convert("RGB")))
        self.assertEqual(padded.size[0], padded.size[1])
        self.assertGreater(padded.size[0], 400)

    def test_fit_does_not_upscale(self):
        small = Image.new("RGB", (200, 200), "white")
        img, upscaled = fit(small, 1600)
        self.assertEqual(img.size, (200, 200))
        self.assertTrue(upscaled)

    def test_fit_downscales_large(self):
        big = Image.new("RGB", (3000, 3000), "white")
        img, upscaled = fit(big, 1600)
        self.assertEqual(img.size, (1600, 1600))
        self.assertFalse(upscaled)

    def test_flatten_transparent_png_to_white(self):
        png = self.dir / "a.png"
        Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(png)
        with Image.open(png) as img:
            flat = flatten(img)
        self.assertEqual(flat.mode, "RGB")
        self.assertEqual(flat.getpixel((50, 50)), (255, 255, 255))

    def test_process_writes_jpeg_without_exif(self):
        target = self.dir / "out" / "x.jpg"
        result = process(self.photo, target, size=1200)
        self.assertTrue(target.exists())
        self.assertEqual(result.width, 1200)
        self.assertEqual(result.height, 1200)
        with Image.open(target) as out:
            self.assertEqual(out.format, "JPEG")
            self.assertEqual(len(out.getexif()), 0)

    def test_collect_filters_extensions(self):
        (self.dir / "note.txt").write_text("x")
        files = collect(self.dir)
        self.assertEqual([f.name for f in files], ["FOA-110.png"])


if __name__ == "__main__":
    unittest.main()
