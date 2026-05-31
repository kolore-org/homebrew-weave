# Homebrew formula for weave-viewer-cli (macOS arm64, binary release).
#
# OWNED BY THIS REPO. The upstream monorepo only builds the binary and attaches
# `weave-viewer-cli-macos-arm64.tar.gz` (+ `.sha256`, `feature-support.md`) to a
# `weave-v*` GitHub Release here — it no longer pushes the formula (2026-05-27
# decouple decision). `version` + `sha256` are bumped on each release by this
# repo's `.github/workflows/bump-formula.yml` (or manually via
# `scripts/update-formula.sh`), reading the published `.sha256` asset.
#
# Named `weave-viewer` (not `weave`) to avoid colliding with homebrew-core's
# unrelated `weave`. Install with: brew install kolore-org/weave/weave-viewer
class WeaveViewer < Formula
  desc "Preview and render weave (HTML/CSS) templates to PNG and MP4"
  homepage "https://github.com/kolore-org/homebrew-weave"
  # Version is hardcoded in the URL (not #{version}): Homebrew style requires
  # `url` before `version`, so interpolation would resolve empty. The bump
  # workflow/script rewrite the `weave-v<ver>` path segment in lockstep.
  url "https://github.com/kolore-org/homebrew-weave/releases/download/weave-v0.1.7/weave-viewer-cli-macos-arm64.tar.gz"
  version "0.1.7"
  sha256 "a7a5ad5867f03def039bea744d83f0134f9539b42e50e57ba444e7efdff2a68c"
  license :cannot_represent # closed binary; examples/docs licensed separately

  depends_on arch: :arm64 # v1 is Apple Silicon only
  depends_on "ffmpeg" # required by `--record` (MP4 output)
  depends_on :macos

  def install
    # The tarball is a self-contained bundle: the binary plus its runtime
    # assets (shaders/, data/fonts/) and bundled dylibs (lib/) MUST stay
    # adjacent to the binary — it resolves them relative to its own path.
    libexec.install Dir["*"]

    # Wrapper execs the real binary by its libexec path, so SDL_GetBasePath
    # resolves to libexec/ (where shaders/, data/fonts/, lib/ live). A bare
    # symlink in bin/ could leave the base path pointing at bin/ and break
    # asset + dylib lookup, so we use an exec wrapper instead.
    (bin/"weave-viewer-cli").write <<~SH
      #!/bin/bash
      exec "#{libexec}/weave-viewer-cli" "$@"
    SH
  end

  test do
    (testpath/"proj").mkpath
    (testpath/"proj/template.weave").write(
      "<!DOCTYPE html><html><body><div>weave ok</div></body></html>",
    )
    # `--validate` is GPU-free (parses the template + checks override paths).
    # Running it also proves the bundled dylibs resolve at process start and
    # the wrapper points at the right binary.
    system bin/"weave-viewer-cli", testpath/"proj", "--validate"
  end
end
