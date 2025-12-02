import json
from pathlib import Path

from socdata.core.i18n import get_i18n_manager


def test_i18n_translate_label(tmp_path, monkeypatch):
    """Test basic label translation."""
    # Set cache dir to tmp_path
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    i18n = get_i18n_manager(default_language="en")
    
    # Without translations, should return original
    assert i18n.translate_label("Unemployment", "de") == "Unemployment"
    
    # Save a translation
    i18n.save_translation("de", {"Unemployment": "Arbeitslosigkeit"}, dataset_id="test")
    
    # Now should translate
    assert i18n.translate_label("Unemployment", "de", dataset_id="test") == "Arbeitslosigkeit"


def test_i18n_translate_variable_labels(tmp_path, monkeypatch):
    """Test variable labels translation."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    i18n = get_i18n_manager(default_language="en")
    
    var_labels = {
        "var1": "Unemployment rate",
        "var2": "GDP",
    }
    
    # Save translations
    i18n.save_translation("de", {
        "Unemployment rate": "Arbeitslosenquote",
        "GDP": "BIP",
    })
    
    translated = i18n.translate_variable_labels(var_labels, "de")
    assert translated["var1"] == "Arbeitslosenquote"
    assert translated["var2"] == "BIP"


def test_i18n_get_available_languages(tmp_path, monkeypatch):
    """Test getting available languages."""
    monkeypatch.setenv("SOCDATA_CACHE_DIR", str(tmp_path))
    
    i18n = get_i18n_manager(default_language="en")
    
    # Initially only default language
    langs = i18n.get_available_languages()
    assert "en" in langs
    
    # Add a translation file
    i18n.save_translation("de", {"test": "test"})
    
    # Now should include German
    langs = i18n.get_available_languages()
    assert "de" in langs
    assert "en" in langs
