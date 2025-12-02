from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .config import get_config


class I18nManager:
    """
    Internationalization manager for variable and value labels.
    
    Supports multiple languages and provides fallback mechanisms.
    """

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation files from cache directory."""
        cfg = get_config()
        translations_dir = cfg.cache_dir / "translations"
        
        if not translations_dir.exists():
            return
        
        # Load JSON translation files
        for lang_file in translations_dir.glob("*.json"):
            lang = lang_file.stem
            try:
                with lang_file.open(encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
            except Exception:
                # Silently fail if translation file is invalid
                pass

    def translate_label(
        self,
        label: str,
        language: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> str:
        """
        Translate a label to the specified language.
        
        Args:
            label: Original label text
            language: Target language code (e.g., 'de', 'fr', 'en')
            dataset_id: Optional dataset ID for dataset-specific translations
        
        Returns:
            Translated label or original if translation not found
        """
        if not label:
            return label
        
        lang = language or self.default_language
        
        # If already in default language, return as-is
        if lang == self.default_language:
            return label
        
        # Try dataset-specific translation first
        if dataset_id and dataset_id in self.translations.get(lang, {}):
            dataset_translations = self.translations[lang][dataset_id]
            if label in dataset_translations:
                return dataset_translations[label]
        
        # Try global translation
        if "global" in self.translations.get(lang, {}):
            global_translations = self.translations[lang]["global"]
            if label in global_translations:
                return global_translations[label]
        
        # Fallback to original label
        return label

    def translate_variable_labels(
        self,
        variable_labels: Dict[str, str],
        language: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Translate a dictionary of variable labels.
        
        Args:
            variable_labels: Dictionary mapping variable names to labels
            language: Target language code
            dataset_id: Optional dataset ID
        
        Returns:
            Dictionary with translated labels
        """
        lang = language or self.default_language
        
        if lang == self.default_language:
            return variable_labels
        
        translated = {}
        for var_name, label in variable_labels.items():
            translated[var_name] = self.translate_label(label, language, dataset_id)
        
        return translated

    def translate_value_labels(
        self,
        value_labels: Dict[str, Dict[str, str]],
        language: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Translate a dictionary of value labels.
        
        Args:
            value_labels: Dictionary mapping variable names to value label dictionaries
            language: Target language code
            dataset_id: Optional dataset ID
        
        Returns:
            Dictionary with translated value labels
        """
        lang = language or self.default_language
        
        if lang == self.default_language:
            return value_labels
        
        translated = {}
        for var_name, value_dict in value_labels.items():
            translated[var_name] = {
                value: self.translate_label(label, language, dataset_id)
                for value, label in value_dict.items()
            }
        
        return translated

    def save_translation(
        self,
        language: str,
        translations: Dict[str, str],
        dataset_id: Optional[str] = None,
    ) -> None:
        """
        Save translations to a file.
        
        Args:
            language: Language code
            translations: Dictionary of label -> translation mappings
            dataset_id: Optional dataset ID for dataset-specific translations
        """
        cfg = get_config()
        translations_dir = cfg.cache_dir / "translations"
        translations_dir.mkdir(parents=True, exist_ok=True)
        
        lang_file = translations_dir / f"{language}.json"
        
        # Load existing translations
        if lang_file.exists():
            try:
                with lang_file.open(encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        else:
            existing = {}
        
        # Update with new translations
        target_key = dataset_id or "global"
        if target_key not in existing:
            existing[target_key] = {}
        
        existing[target_key].update(translations)
        
        # Save back
        with lang_file.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        # Reload translations
        self._load_translations()

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        cfg = get_config()
        translations_dir = cfg.cache_dir / "translations"
        
        if not translations_dir.exists():
            return [self.default_language]
        
        languages = [self.default_language]
        for lang_file in translations_dir.glob("*.json"):
            lang = lang_file.stem
            if lang != self.default_language:
                languages.append(lang)
        
        return sorted(languages)


# Global i18n manager instance
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager(default_language: str = "en") -> I18nManager:
    """Get or create the global i18n manager instance."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager(default_language=default_language)
    return _i18n_manager
