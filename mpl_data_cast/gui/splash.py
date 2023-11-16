import platform

pyi_splash = None
if platform.system() in ["Linux", "Windows"]:
    # Don't even try this on macOS.
    try:
        import pyi_splash
    except (ImportError, KeyError):
        pass


def splash_close():
    """Close the splash screen"""
    if pyi_splash is not None:
        if pyi_splash.is_alive():
            pyi_splash.close()
