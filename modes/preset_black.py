# Пресет: зменшення яскравості (preset black)
from PIL import ImageEnhance

LABEL = "Пресет: Чорний"

def apply_mode(image, params=None):
    """
    image: PIL.Image (RGB)
    params: dict (може містити 'brightness' — множник яскравості)
    Повертає: PIL.Image
    """
    if params is None:
        params = {}
    brightness = float(params.get('brightness', 0.7))
    try:
        enhancer = ImageEnhance.Brightness(image)
        out = enhancer.enhance(brightness)
        return out
    except Exception as e:
        # Якщо щось пішло не так — повертаємо оригінал
        print(f"preset_black.apply_mode error: {e}")
        return image
