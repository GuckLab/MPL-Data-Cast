try:
    import pyi_splash
except (ImportError, KeyError):
    pyi_splash = None


def splash_close():
    """Close the splash screen"""
    if pyi_splash is not None:
        if pyi_splash.is_alive():
            pyi_splash.close()
