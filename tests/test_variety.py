from PIL import Image, ImageDraw, ImageEnhance

from vidlib.variety import dhash, distance, repeats_across, repeats_within


def scene(path, blob_x):
    img = Image.new("RGB", (180, 320))
    d = ImageDraw.Draw(img)
    for y in range(320):
        d.line([(0, y), (180, y)], fill=(y // 2, 80, 200 - y // 2))
    d.ellipse([blob_x, 100, blob_x + 70, 170], fill=(250, 240, 40))
    img.save(path, quality=90)
    return path


def test_same_shot_matches_and_a_different_one_does_not(tmp_path):
    a_path = scene(tmp_path / "a.jpg", 20)
    # The same frame re-encoded a little brighter: what a reused clip looks like.
    ImageEnhance.Brightness(Image.open(a_path)).enhance(1.05).save(tmp_path / "a2.jpg", quality=70)
    a, a2 = dhash(a_path), dhash(tmp_path / "a2.jpg")
    b = dhash(scene(tmp_path / "b.jpg", 100))
    assert distance(a, a2) <= 6 < distance(a, b)
    assert repeats_within({"b01": a, "b02": b, "b03": a2}) == {"b03": "b01"}
    assert repeats_across({"b01": b}, [{"run_id": "old", "frame_hashes": [a]}]) == {}
    assert repeats_across({"b01": a2}, [{"run_id": "old", "frame_hashes": [a]}]) == {"b01": "old"}
