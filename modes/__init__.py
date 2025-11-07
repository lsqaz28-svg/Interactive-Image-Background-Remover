# Простий лоадер режимів (plugin loader)
# Автоматично імпортує всі .py в папці modes (окрім __init__.py)
import importlib
import os
import pkgutil

MODES = {}

def discover_modes():
    """
    Знаходить модулі у папці modes і реєструє ті, які мають функцію apply_mode.
    Запускається при імпорті пакету.
    """
    global MODES
    MODES = {}
    package_dir = os.path.dirname(__file__)
    for finder, name, ispkg in pkgutil.iter_modules([package_dir]):
        if name.startswith('_'):
            continue
        try:
            module = importlib.import_module(f"modes.{name}")
            label = getattr(module, 'LABEL', getattr(module, 'label', name))
            apply_fn = getattr(module, 'apply_mode', None)
            if callable(apply_fn):
                MODES[name] = {
                    'module': module,
                    'label': label,
                    'apply': apply_fn
                }
        except Exception as e:
            # Якщо модуль упав — ігноруємо, але логимо помилку в консолі
            print(f"Error loading mode {name}: {e}")

# Виклик при імпорті
discover_modes()
