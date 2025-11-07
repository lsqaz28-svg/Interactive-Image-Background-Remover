# processing.py
# Універсальна функція для обробки одного зображення.
# Підтримує застосування режиму (mode_module), вибір фону і формат збереження.
from PIL import Image, ImageOps
import os

def ensure_rgb(im, background_color=(255,255,255)):
    """Повертає RGB-версію зображення; якщо є альфа — композит поверх background_color."""
    if im.mode in ('RGBA','LA') or (im.mode == 'P' and 'transparency' in im.info):
        bg = Image.new("RGBA", im.size, background_color + (255,))
        bg.paste(im, mask=im.convert("RGBA").split()[-1])
        return bg.convert("RGB")
    return im.convert("RGB")

def process_image(input_path, output_path, mode_module=None, params=None,
                  bg_option=None, save_format='PNG', jpeg_quality=90):
    """
    input_path: шлях до вхідного файлу
    output_path: куди записати результат (повний шлях з розширенням)
    mode_module: модуль з функцією apply_mode(image, params) або None
    params: dict параметрів для режиму
    bg_option: None або dict { 'type': 'color'/'image', 'value': (r,g,b) or path_to_image }
    save_format: 'PNG'|'JPEG'|'WEBP'
    jpeg_quality: int 1-100
    """
    im = Image.open(input_path).convert("RGBA")

    # Підготовка зображення для режиму: RGB клона (щоб режим не отримував альфу випадково)
    rgb_for_mode = im.convert("RGB")
    if mode_module is not None:
        try:
            rgb_for_mode = mode_module.apply_mode(rgb_for_mode, params or {})
        except Exception as e:
            print(f"Mode apply error on {input_path}: {e}")
            rgb_for_mode = im.convert("RGB")

    # Якщо в оригіналі є альфа — використаємо її як маску для насадження на фон
    if im.mode == "RGBA":
        alpha = im.split()[-1]  # маска з оригіналу
        if bg_option:
            if bg_option.get('type') == 'color':
                bg_col = tuple(bg_option.get('value', (255,255,255)))
                background = Image.new('RGB', im.size, bg_col)
            elif bg_option.get('type') == 'image':
                try:
                    bg_img = Image.open(bg_option.get('value')).convert('RGB')
                    background = ImageOps.fit(bg_img, im.size)
                except Exception:
                    background = Image.new('RGB', im.size, (255,255,255))
            else:
                background = Image.new('RGB', im.size, (255,255,255))
            composite = background.copy()
            composite.paste(rgb_for_mode, (0,0), mask=alpha)
            final = composite
        else:
            # Якщо фон не вказано — зберігаємо з прозорістю, коли формат підтримує її
            if save_format.upper() in ('PNG', 'WEBP'):
                # зберігаємо RGBA
                # Якщо режим повернув rgb_for_mode без альфи, зберігаємо оригінальну альфу
                if rgb_for_mode.mode != "RGBA":
                    rgba = Image.new("RGBA", im.size)
                    rgba.paste(rgb_for_mode)
                    rgba.putalpha(alpha)
                    final = rgba
                else:
                    final = rgb_for_mode
            else:
                # JPEG не підтримує альфу — композит поверх білого
                final = ensure_rgb(im, background_color=(255,255,255))
    else:
        final = rgb_for_mode

    # Параметри збереження
    fmt = save_format.upper()
    save_kwargs = {}
    if fmt == 'JPEG':
        save_kwargs['format'] = 'JPEG'
        save_kwargs['quality'] = jpeg_quality
        if final.mode in ('RGBA','LA'):
            final = final.convert('RGB')
    elif fmt == 'PNG':
        save_kwargs['format'] = 'PNG'
        save_kwargs['optimize'] = True
    elif fmt == 'WEBP':
        save_kwargs['format'] = 'WEBP'
        save_kwargs['quality'] = jpeg_quality
    else:
        save_kwargs['format'] = fmt

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    final.save(output_path, **save_kwargs)
    return output_path
