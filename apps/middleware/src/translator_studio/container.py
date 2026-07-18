from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_CONFIG_PATH, Settings
from .detector.service import DetectorService
from .glossary.service import GlossaryService
from .logs.logger import TranslationLogger
from .postprocess.service import Postprocessor
from .prompt.builder import PromptBuilder
from .prompt.presets import PresetRepository
from .prompt.templates import TemplateRepository
from .translation.llama_client import LlamaClient
from .translation.service import TranslationService


@dataclass
class Services:
    """Dependency-injection root: every long-lived service, built once."""

    settings: Settings
    llama_client: LlamaClient
    glossary: GlossaryService
    detector: DetectorService
    templates: TemplateRepository
    presets: PresetRepository
    prompt_builder: PromptBuilder
    postprocessor: Postprocessor
    logger: TranslationLogger
    translation: TranslationService
    config_path: Path | None = DEFAULT_CONFIG_PATH


def build_services(
    settings: Settings,
    llama_client: LlamaClient | None = None,
    config_path: Path | None = DEFAULT_CONFIG_PATH,
) -> Services:
    llama = llama_client or LlamaClient(
        base_url=settings.llama_server.base_url,
        api_key=settings.llama_server.api_key,
        timeout=settings.llama_server.request_timeout,
    )
    glossary = GlossaryService.from_dir(settings.paths.glossary_dir)
    detector = DetectorService(
        min_alias_length=settings.detector.min_alias_length,
        longest_match_first=settings.detector.longest_match_first,
    )
    templates = TemplateRepository(settings.paths.prompts_dir)
    presets = PresetRepository(settings.paths.presets_dir)
    prompt_builder = PromptBuilder(templates)
    postprocessor = Postprocessor()
    logger = TranslationLogger(settings.paths.logs_dir)
    translation = TranslationService(
        llama_client=llama,
        glossary=glossary,
        detector=detector,
        prompt_builder=prompt_builder,
        presets=presets,
        postprocessor=postprocessor,
        logger=logger,
        settings=settings,
    )
    return Services(
        settings=settings,
        llama_client=llama,
        glossary=glossary,
        detector=detector,
        templates=templates,
        presets=presets,
        prompt_builder=prompt_builder,
        postprocessor=postprocessor,
        logger=logger,
        translation=translation,
        config_path=config_path,
    )
