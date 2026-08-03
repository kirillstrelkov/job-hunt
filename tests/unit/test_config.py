from pathlib import Path

import yaml

from job_hunt.config.config import CONFIG_DIR, ConfigManager, check_config


def test_default_config_composer_and_tailor_paths_exist() -> None:
    cm = ConfigManager(CONFIG_DIR / "config.yaml")
    assert cm.composer.header.is_file()
    assert cm.composer.body.is_file()
    assert cm.composer.footer.is_file()
    assert cm.tailor.prompt.is_file()


def test_check_config_missing_file() -> None:
    assert check_config(CONFIG_DIR / "does_not_exist.yaml") is False


def test_check_config_with_valid_and_missing_paths(tmp_path: Path) -> None:
    existing_file = tmp_path / "existing.md"
    existing_file.write_text("content")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "composer": {
                    "header": str(existing_file),
                    "body": str(existing_file),
                    "footer": str(existing_file),
                },
                "tailor": {"prompt": str(existing_file)},
                "paths": {
                    "root_dir": str(tmp_path),
                    "tmp_output_dir": str(tmp_path / "missing_dir"),
                },
            }
        )
    )

    assert check_config(config_path) is False

    (tmp_path / "missing_dir").mkdir()
    assert check_config(config_path) is True


def test_job_hunt_config_env_var(monkeypatch, tmp_path: Path) -> None:
    from job_hunt.config.config import ConfigManager, get_default_config_path

    custom_config = tmp_path / "custom_config.yaml"
    custom_config.write_text(yaml.safe_dump({"paths": {"root_dir": str(tmp_path)}}))

    monkeypatch.setenv("JOB_HUNT_CONFIG", str(custom_config))
    assert get_default_config_path() == custom_config.resolve()

    cm = ConfigManager()
    assert cm.get_path() == custom_config.resolve()
