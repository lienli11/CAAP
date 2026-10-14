"""
CAAP Attack Module
"""
from importlib import import_module

_EXPORT_MODULES = {
    'CAAP_Attack': 'attack',
    'ASIT': 'modules',
    'MS_DIFE': 'modules',
    'PatchSynthesizer': 'synthesizer',
    'focal_loss': 'losses',
    'cw_like_loss': 'losses',
    'identity_loss': 'losses',
    'feature_diversity_loss': 'losses',
    'create_shape_mask': 'utils',
    'ssim_loss': 'utils',
    '_normalize_for_model': 'utils',
    'ASIT_PRESETS': 'utils',
}


def __getattr__(name):
    if name not in _EXPORT_MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f"caap.attack.{_EXPORT_MODULES[name]}"), name)
    globals()[name] = value
    return value

__all__ = [
    'CAAP_Attack',
    'ASIT',
    'MS_DIFE',
    'PatchSynthesizer',
    'focal_loss',
    'cw_like_loss',
    'identity_loss',
    'feature_diversity_loss',
    'create_shape_mask',
    'ssim_loss',
    '_normalize_for_model',
    'ASIT_PRESETS',
]
