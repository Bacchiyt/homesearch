"""Tests for the Alembic migration foundation."""

from __future__ import annotations

from collections.abc import Callable
from io import StringIO
from pathlib import Path
from shutil import copyfile
from textwrap import dedent
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import SecretStr

from homesearch.adapters.database import resolve_database_url
from homesearch.config import LoadedConfiguration, OperationalSettings, load_configuration

DEFAULTS = Path("config/defaults.toml")
ALEMBIC_CONFIG = Path("alembic.ini")
CONFIGURATION_ATTRIBUTE = "homesearch_configuration"


def _load_with_database_url(
    tmp_path: Path,
    database_url: str,
) -> LoadedConfiguration:
    profile = tmp_path / "migration-profile.toml"
    profile.write_text(
        dedent(
            """
            schema_version = 4
            config_id = "migration-profile"
            config_version = 1
            effective_from = 2026-07-30T00:00:00Z

            [[secret_references]]
            secret_id = "migration-store"
            setting = "database_url"
            required = true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return load_configuration(
        OperationalSettings(
            config_path=DEFAULTS,
            profile_path=profile,
            database_url=SecretStr(database_url),
        )
    )


def _alembic_config(
    configuration: LoadedConfiguration,
    *,
    output_buffer: StringIO | None = None,
    script_location: Path = Path("migrations"),
) -> Config:
    config = Config(str(ALEMBIC_CONFIG), output_buffer=output_buffer)
    config.attributes[CONFIGURATION_ATTRIBUTE] = configuration
    config.set_main_option("script_location", str(script_location))
    return config


def _temporary_migration_environment(tmp_path: Path) -> Path:
    migration_root = tmp_path / "migrations"
    versions = migration_root / "versions"
    versions.mkdir(parents=True)
    copyfile("migrations/env.py", migration_root / "env.py")
    copyfile("migrations/script.py.mako", migration_root / "script.py.mako")
    (versions / "0001_synthetic.py").write_text(
        dedent(
            '''
            """Synthetic migration used only to exercise the Alembic foundation."""

            from collections.abc import Sequence

            revision: str = "0001_synthetic"
            down_revision: str | Sequence[str] | None = None
            branch_labels: str | Sequence[str] | None = None
            depends_on: str | Sequence[str] | None = None


            def upgrade() -> None:
                pass


            def downgrade() -> None:
                pass
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    return migration_root


def test_alembic_configuration_has_no_tracked_database_url_and_one_initial_head() -> None:
    config = Config(str(ALEMBIC_CONFIG))
    scripts = ScriptDirectory.from_config(config)
    script_location = config.get_main_option("script_location")

    assert config.get_main_option("sqlalchemy.url") is None
    assert script_location is not None
    assert Path(script_location).resolve() == Path("migrations").resolve()
    assert scripts.get_heads() == ["20260731_0001"]
    assert [revision.revision for revision in scripts.walk_revisions()] == ["20260731_0001"]


def test_initial_revision_offline_sql_is_deterministic_and_secret_safe(
    tmp_path: Path,
) -> None:
    password = "initial-revision-offline-password"
    configuration = _load_with_database_url(
        tmp_path,
        f"postgresql+psycopg://homesearch:{password}@localhost:5432/homesearch",
    )

    def render_upgrade() -> str:
        output = StringIO()
        command.upgrade(
            _alembic_config(configuration, output_buffer=output),
            "head",
            sql=True,
        )
        return output.getvalue()

    first_render = render_upgrade()
    second_render = render_upgrade()

    assert first_render == second_render
    assert "CREATE TABLE configuration_snapshots" in first_render
    assert "CREATE TABLE polling_runs" in first_render
    assert password not in first_render


def _upgrade_offline(config: Config) -> None:
    command.upgrade(config, "head", sql=True)


def _downgrade_offline(config: Config) -> None:
    command.downgrade(config, "0001_synthetic:base", sql=True)


@pytest.mark.parametrize(
    "migration_command",
    [_upgrade_offline, _downgrade_offline],
    ids=["upgrade", "downgrade"],
)
def test_offline_upgrade_and_downgrade_are_deterministic_secret_safe_and_never_connect(
    tmp_path: Path,
    migration_command: Callable[[Config], None],
) -> None:
    password = "synthetic-migration-password"
    configuration = _load_with_database_url(
        tmp_path,
        f"postgresql+psycopg://homesearch:{password}@localhost:5432/homesearch",
    )
    script_location = _temporary_migration_environment(tmp_path)

    def render_migration() -> str:
        output = StringIO()
        config = _alembic_config(
            configuration,
            output_buffer=output,
            script_location=script_location,
        )
        with (
            patch(
                "homesearch.adapters.database.create_database_engine",
                side_effect=AssertionError("offline migration attempted to connect"),
            ) as engine_factory,
            patch(
                "homesearch.adapters.database.resolve_database_url",
                wraps=resolve_database_url,
            ) as url_resolver,
        ):
            migration_command(config)

        engine_factory.assert_not_called()
        url_resolver.assert_called_once_with(configuration)
        return output.getvalue()

    first_render = render_migration()
    second_render = render_migration()

    assert first_render == second_render
    assert first_render
    assert password not in first_render


def _upgrade_to_head(config: Config) -> None:
    command.upgrade(config, "head")


def _downgrade_to_base(config: Config) -> None:
    command.downgrade(config, "base")


@pytest.mark.parametrize(
    "migration_command",
    [_upgrade_to_head, _downgrade_to_base],
    ids=["upgrade", "downgrade"],
)
def test_online_upgrade_and_downgrade_delegate_to_the_existing_engine_boundary(
    tmp_path: Path,
    migration_command: Callable[[Config], None],
) -> None:
    password = "synthetic-online-password"
    configuration = _load_with_database_url(
        tmp_path,
        f"postgresql+psycopg://homesearch:{password}@localhost:5432/homesearch",
    )
    config = _alembic_config(
        configuration,
        script_location=_temporary_migration_environment(tmp_path),
    )

    class EngineBoundaryReached(RuntimeError):
        pass

    with (
        patch(
            "homesearch.adapters.database.create_database_engine",
            side_effect=EngineBoundaryReached("engine boundary reached"),
        ) as engine_factory,
        pytest.raises(EngineBoundaryReached) as error,
    ):
        migration_command(config)

    engine_factory.assert_called_once_with(configuration)
    assert password not in str(error.value)


def test_invalid_injected_configuration_fails_without_inspecting_credentials(
    tmp_path: Path,
) -> None:
    config = Config(str(ALEMBIC_CONFIG), output_buffer=StringIO())
    config.set_main_option(
        "script_location",
        str(_temporary_migration_environment(tmp_path)),
    )
    config.attributes[CONFIGURATION_ATTRIBUTE] = object()

    with pytest.raises(RuntimeError, match="Injected migration configuration is invalid"):
        command.upgrade(config, "head", sql=True)
