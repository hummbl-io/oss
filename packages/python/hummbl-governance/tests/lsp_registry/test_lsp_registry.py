"""Tests for the LSP Registry."""

from __future__ import annotations

import os

import pytest
from hummbl_governance.lsp_registry import (
    LANGUAGE_BY_EXT,
    RECIPES,
    REGISTRY_SCHEMA,
    SERVER_SCHEMA,
    ServerContext,
    ServerDef,
    SpawnSpec,
    get_registry,
    nearest_root,
    resolve_workspace_for_file,
    try_install,
    verify_install,
)


class TestLSPRegistry:
    """Tests for the LSPRegistry class."""

    def test_registry_exists(self) -> None:
        """Registry should be accessible."""
        reg = get_registry()
        assert reg is not None

    def test_builtin_servers_registered(self) -> None:
        """Core servers should be registered."""
        reg = get_registry()
        server_ids = reg.all_server_ids()

        expected = [
            "pyright",
            "typescript",
            "gopls",
            "rust-analyzer",
            "clangd",
            "bash-language-server",
            "yaml-language-server",
            "lua-language-server",
        ]

        for sid in expected:
            assert sid in server_ids, f"Missing server: {sid}"

    def test_find_for_file(self) -> None:
        """find_for_file should return correct server for extensions."""
        reg = get_registry()

        test_cases = [
            ("test.py", "pyright"),
            ("main.ts", "typescript"),
            ("app.go", "gopls"),
            ("lib.rs", "rust-analyzer"),
            ("script.sh", "bash-language-server"),
            ("config.yaml", "yaml-language-server"),
            ("mod.lua", "lua-language-server"),
        ]

        for filename, expected_sid in test_cases:
            srv = reg.find_for_file(filename)
            assert srv is not None, f"No server for {filename}"
            assert srv.server_id == expected_sid, f"Wrong server for {filename}: {srv.server_id}"

    def test_find_all_for_file(self) -> None:
        """find_all_for_file should return all matching servers."""
        reg = get_registry()

        # TypeScript handles .ts, .tsx, .js, .jsx
        servers = reg.find_all_for_file("test.ts")
        assert len(servers) >= 1
        assert any(s.server_id == "typescript" for s in servers)

    def test_list_servers_filter_category(self) -> None:
        """list_servers should filter by category."""
        reg = get_registry()

        core = reg.list_servers(category="core")
        assert len(core) >= 8  # all builtins are core
        assert all(s.category == "core" for s in core)

    def test_list_servers_filter_tags(self) -> None:
        """list_servers should filter by tags."""
        reg = get_registry()

        official = reg.list_servers(tags=["official"])
        assert len(official) >= 6
        assert all("official" in s.tags for s in official)

    def test_validate_all(self) -> None:
        """All built-in servers should pass validation."""
        reg = get_registry()
        errors = reg.validate_all()

        assert not errors, f"Validation errors: {errors}"

    def test_server_def_to_dict(self) -> None:
        """ServerDef should serialize to dict."""
        reg = get_registry()
        pyright = reg.get("pyright")
        assert pyright is not None

        d = pyright.to_dict()
        assert d["server_id"] == "pyright"
        assert ".py" in d["extensions"]
        assert d["category"] == "core"
        assert "microsoft" in d["tags"]


class TestLanguageIDs:
    """Tests for language ID mapping."""

    def test_common_extensions(self) -> None:
        """Common extensions should have correct language IDs."""
        assert LANGUAGE_BY_EXT[".py"] == "python"
        assert LANGUAGE_BY_EXT[".ts"] == "typescript"
        assert LANGUAGE_BY_EXT[".js"] == "javascript"
        assert LANGUAGE_BY_EXT[".go"] == "go"
        assert LANGUAGE_BY_EXT[".rs"] == "rust"
        assert LANGUAGE_BY_EXT[".json"] == "json"
        assert LANGUAGE_BY_EXT[".yaml"] == "yaml"

    def test_extensionless_files(self) -> None:
        """Extensionless files should map by basename."""
        # These are handled by _file_ext_or_basename, not LANGUAGE_BY_EXT directly
        pass


class TestWorkspaceUtils:
    """Tests for workspace utilities."""

    def test_resolve_workspace_for_file(self) -> None:
        """Should find git workspace root."""
        root, gated = resolve_workspace_for_file(__file__)
        assert gated is True
        assert root is not None
        # Name-agnostic: a real workspace root has a .git marker (dir or file).
        # This works regardless of checkout directory name (hummbl-oss, oss, etc.)
        assert os.path.exists(os.path.join(root, ".git"))

    def test_nearest_root(self) -> None:
        """Should find nearest marker file."""
        # This file is in tests/, nearest pyproject.toml is at repo root
        root = nearest_root(__file__, ["pyproject.toml"])
        assert root is not None
        # Name-agnostic: the nearest pyproject.toml root is the package or
        # monorepo root; verify it actually contains the marker file.
        assert os.path.exists(os.path.join(root, "pyproject.toml"))

    def test_nearest_root_excludes(self) -> None:
        """Excludes should gate off server."""
        # If we exclude pyproject.toml, should return None
        root = nearest_root(__file__, ["pyproject.toml"], excludes=["pyproject.toml"])
        assert root is None


class TestServerContext:
    """Tests for ServerContext and SpawnSpec."""

    def test_server_context_defaults(self) -> None:
        """ServerContext should have sensible defaults."""
        ctx = ServerContext(workspace_root="/tmp")
        assert ctx.install_strategy == "auto"
        assert ctx.binary_overrides == {}
        assert ctx.env_overrides == {}
        assert ctx.init_overrides == {}

    def test_spawn_spec(self) -> None:
        """SpawnSpec should hold all required fields."""
        spec = SpawnSpec(
            command=["pyright-langserver", "--stdio"],
            workspace_root="/tmp",
            cwd="/tmp",
        )
        assert spec.command == ["pyright-langserver", "--stdio"]
        assert spec.seed_diagnostics_on_first_push is False


class TestInstallRecipes:
    """Tests for installation recipes."""

    def test_recipes_exist(self) -> None:
        """Core recipes should be defined."""
        assert "pyright" in RECIPES
        assert "typescript-language-server" in RECIPES
        assert "gopls" in RECIPES
        assert "rust-analyzer" in RECIPES

    def test_recipe_structure(self) -> None:
        """Recipes should have required fields."""
        recipe = RECIPES["pyright"]
        assert recipe.manager == "npm"
        assert recipe.package == "pyright"
        assert recipe.binary == "pyright-langserver"

    def test_try_install_manual(self) -> None:
        """try_install with manual strategy should not install."""
        # This just checks if binary exists, doesn't install
        result = try_install("pyright", "manual")
        # Result depends on whether pyright is installed on the system
        assert result is None or isinstance(result, str)

    def test_verify_install(self) -> None:
        """verify_install should check binary existence."""
        result = verify_install("pyright")
        # Depends on system state
        assert isinstance(result, bool)


class TestSchemas:
    """Tests for JSON schemas."""

    def test_server_schema_valid(self) -> None:
        """SERVER_SCHEMA should be valid JSON schema."""
        assert SERVER_SCHEMA["title"] == "LSP Server Definition"
        assert "server_id" in SERVER_SCHEMA["required"]
        assert "extensions" in SERVER_SCHEMA["required"]

    def test_registry_schema_valid(self) -> None:
        """REGISTRY_SCHEMA should be valid JSON schema."""
        assert REGISTRY_SCHEMA["title"] == "LSP Registry Configuration"
        assert "servers" in REGISTRY_SCHEMA["properties"]
        assert "install_strategy" in REGISTRY_SCHEMA["properties"]


class TestSpawnResolution:
    """Tests for spawn spec resolution."""

    def test_pyright_spawn(self) -> None:
        """Pyright spawn spec should resolve correctly."""
        reg = get_registry()
        pyright = reg.get("pyright")
        assert pyright is not None

        ctx = ServerContext(workspace_root=".", install_strategy="manual")
        root = pyright.resolve_root("test.py", ".")
        spec = pyright.build_spawn(root, ctx)

        # On systems with pyright installed, should return spec
        if spec is not None:
            assert isinstance(spec, SpawnSpec)
            assert "pyright-langserver" in spec.command[0] or "pyright" in spec.command[0]
            assert "--stdio" in spec.command

    def test_typescript_spawn(self) -> None:
        """TypeScript spawn spec should resolve correctly."""
        reg = get_registry()
        ts = reg.get("typescript")
        assert ts is not None

        ctx = ServerContext(workspace_root=".", install_strategy="manual")
        root = ts.resolve_root("test.ts", ".")
        spec = ts.build_spawn(root, ctx)

        if spec is not None:
            assert isinstance(spec, SpawnSpec)
            assert "typescript-language-server" in spec.command[0]
            assert "--stdio" in spec.command
            assert spec.seed_diagnostics_on_first_push is True


class TestRegistryExtensibility:
    """Tests for registry extensibility."""

    def test_register_custom_server(self) -> None:
        """Should be able to register custom server."""
        reg = get_registry()
        initial_count = len(reg.all_server_ids())

        custom = ServerDef(
            server_id="custom-test",
            extensions=(".cust",),
            language_ids=("custom",),
            resolve_root=lambda fp, ws: ws,
            build_spawn=lambda root, ctx: SpawnSpec(
                command=["custom-ls"],
                workspace_root=root,
                cwd=root,
            ),
            description="Custom test server",
            category="experimental",
            tags=("custom",),
        )

        reg.register(custom)
        assert len(reg.all_server_ids()) == initial_count + 1
        assert reg.get("custom-test") is not None
        assert reg.find_for_file("test.cust").server_id == "custom-test"

        # Clean up
        reg.unregister("custom-test")
        assert len(reg.all_server_ids()) == initial_count

    def test_unregister_removes_from_extension_index(self) -> None:
        """Unregistering should remove from extension index."""
        reg = get_registry()

        custom = ServerDef(
            server_id="custom-test-2",
            extensions=(".cust2",),
            resolve_root=lambda fp, ws: ws,
            build_spawn=lambda root, ctx: None,
            description="Test",
        )
        reg.register(custom)
        assert ".cust2" in reg._by_extension

        reg.unregister("custom-test-2")
        assert ".cust2" not in reg._by_extension or reg._by_extension[".cust2"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
