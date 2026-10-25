"""Scene pictures made by LOCAL AI (text-to-image diffusion on the CPU). No stock footage, no API, no key.
If the image model cannot run, the same calls fall back to generated abstract art, so the video is always finished.
Interface is unchanged (Media.photo / Media.video), so editor.py needs no edit."""
import hashlib, os, random, threading, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import config

PALETTES = [((20, 33, 61), (252, 163, 17), (229, 229, 229)), ((43, 45, 66), (237, 242, 244), (239, 35, 60)),
            ((13, 59, 102), (250, 240, 202), (244, 211, 94)), ((38, 70, 83), (42, 157, 143), (233, 196, 106)),
            ((52, 43, 65), (224, 159, 122), (244, 226, 198)), ((27, 38, 44), (79, 172, 254), (255, 255, 255)),
            ((69, 20, 38), (255, 107, 107), (255, 230, 109)), ((24, 54, 44), (140, 200, 120), (245, 240, 220))]


def procedural_art(w, h, seed):
    """Soft abstract artwork drawn with code (used when the diffusion model is unavailable or the budget is used up)."""
    r = random.Random(seed)
    bg, c1, c2 = r.choice(PALETTES)
    img = Image.new("RGB", (w, h), bg)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = min(w, h)
    for _ in range(r.randint(5, 9)):
        rad = r.randint(s // 6, s // 2)
        x, y = r.randint(-rad // 2, w + rad // 2), r.randint(-rad // 2, h + rad // 2)
        col = r.choice([c1, c2, tuple(min(255, v + 45) for v in bg)])
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(*col, r.randint(70, 160)))
    for _ in range(3):
        ax, ay, rad = r.randint(0, w), r.randint(0, h), r.randint(s // 3, s)
        d.arc([ax - rad, ay - rad, ax + rad, ay + rad], r.randint(0, 360), r.randint(0, 360), fill=(*c2, 130), width=max(2, w // 220))
    layer = layer.filter(ImageFilter.GaussianBlur(s // 14))
    img.paste(layer, (0, 0), layer)
    img = Image.blend(img, Image.effect_noise((w, h), 18).convert("RGB"), 0.04)
    return ImageEnhance.Contrast(img).enhance(1.08)


class Media:
    def __init__(self, cache: Path):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.pipe, self.failed = None, False
        self.made, self.spent = 0, 0.0
        self.pool = {True: [], False: []}      # generated pictures per orientation (portrait?)
        self.rnd = random.Random(7)

    # ---- model -----------------------------------------------------------
    def _load(self):
        if self.pipe is not None or self.failed:
            return
        try:
            import torch
            from diffusers import DiffusionPipeline
            torch.set_num_threads(os.cpu_count() or 4)
            t0 = time.time()
            self.pipe = DiffusionPipeline.from_pretrained(config.IMAGE_MODEL, torch_dtype=torch.float32,
                                                          safety_checker=None, requires_safety_checker=False)
            self.pipe.set_progress_bar_config(disable=True)
            print(f"[image] local model ready: {config.IMAGE_MODEL} ({time.time() - t0:.0f}s)", flush=True)
        except Exception as e:
            self.failed = True
            print("[image] local image model unavailable, using generated abstract art:", str(e)[:150], flush=True)

    def _diffuse(self, prompt, portrait, seed):
        import torch
        w, h = (config.IMAGE_H, config.IMAGE_W) if portrait else (config.IMAGE_W, config.IMAGE_H)
        out = self.pipe(prompt=prompt, num_inference_steps=config.IMAGE_STEPS, guidance_scale=config.IMAGE_GUIDANCE,
                        width=w, height=h, generator=torch.Generator("cpu").manual_seed(seed))
        img = out.images[0].convert("RGB")
        img = img.resize((w * 2, h * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=3))
        return ImageEnhance.Color(img).enhance(1.08)

    # ---- public API (same as before) ---------------------------------------
    def photo(self, queries, portrait=False):
        subject = next((q for q in queries if q), "abstract shapes")
        with self.lock:                       # one picture at a time: the model uses all CPU cores
            seed = self.rnd.randint(1, 10_000_000)
            key = hashlib.md5(f"{subject}|{portrait}|{seed}".encode()).hexdigest()[:12]
            path = self.cache / f"gen_{key}.jpg"
            over_budget = self.spent > config.IMAGE_BUDGET_MIN * 60 or self.made >= config.IMAGE_MAX
            if over_budget and self.pool[portrait]:
                return self.rnd.choice(self.pool[portrait])      # re-use an earlier picture (new motion in the editor)
            w, h = (config.IMAGE_H, config.IMAGE_W) if portrait else (config.IMAGE_W, config.IMAGE_H)
            t0 = time.time()
            img = None
            if not over_budget:
                self._load()
                if self.pipe is not None:
                    try:
                        img = self._diffuse(f"{subject}, {config.IMAGE_STYLE}", portrait, seed)
                    except Exception as e:
                        print("[image] generation failed, abstract art instead:", str(e)[:120], flush=True)
            if img is None:
                img = procedural_art(w * 2, h * 2, seed)
            img.save(path, quality=93)
            self.made += 1
            self.spent += time.time() - t0
            self.pool[portrait].append(path)
            if self.made % 10 == 0:
                print(f"[image] {self.made} pictures made, {self.spent / 60:.1f} min used", flush=True)
            return path

    def video(self, queries, portrait=False):
        """No stock video: the editor turns a generated picture into a moving shot (zoom / pan) instead."""
        return None
