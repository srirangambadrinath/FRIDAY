from PIL import Image, ImageDraw, ImageFilter


def generate_friday_icon(path: str = "friday.ico") -> None:
	# Base image
	size = 256
	img = Image.new("RGBA", (size, size), (5, 6, 10, 255))  # near-black background
	draw = ImageDraw.Draw(img)

	center = (size // 2, size // 2)
	radii = [96, 72, 48, 24]
	cyan = (34, 211, 238, 255)

	# Neon rings
	for r in radii:
		bbox = [center[0] - r, center[1] - r, center[0] + r, center[1] + r]
		draw.ellipse(bbox, outline=cyan, width=4)

	# Core
	core_r = 18
	core_bbox = [center[0] - core_r, center[1] - core_r, center[0] + core_r, center[1] + core_r]
	draw.ellipse(core_bbox, fill=cyan)

	# Glow overlay
	glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
	gdraw = ImageDraw.Draw(glow)
	for r in [110, 80, 54, 30]:
		alpha = 60 if r == 110 else 50 if r == 80 else 40 if r == 54 else 35
		gdraw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], outline=(34, 211, 238, alpha), width=6)

	glow = glow.filter(ImageFilter.GaussianBlur(8))
	img = Image.alpha_composite(img, glow)

	# Save ICO with multiple sizes
	img.save(path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


if __name__ == "__main__":
	generate_friday_icon()


