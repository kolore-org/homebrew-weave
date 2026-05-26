# Homebrew formula for weave-viewer-cli (macOS arm64, binary release).
#
# STAGING DRAFT — kept in the monorepo's docs/satellite-repo/ next to the
# README. Copy to `Formula/weave.rb` in the kolore-org/homebrew-weave repo when
# bootstrapping that repo.
#
# This is the SOURCE-OF-TRUTH template. The monorepo release workflow
# (.github/workflows/release-weave-viewer-cli.yml) auto-fills `version` +
# `sha256` from each published `weave-v*` release and pushes the result to
# kolore-org/homebrew-weave/Formula/weave.rb — so the placeholders below are
# expected here and are replaced automatically on release. (Manual fill, if ever
# needed: version = tag minus "weave-v"; sha256 = the published
# `weave-viewer-cli-macos-arm64.tar.gz.sha256` asset.)
class Weave < Formula
  desc "Preview and render weave (HTML/CSS) templates to PNG and MP4"
  homepage "https://github.com/kolore-org/homebrew-weave"
  version "0.1.0"
  url "https://github.com/kolore-org/homebrew-weave/releases/download/weave-v#{version}/weave-viewer-cli-macos-arm64.tar.gz"
  sha256 "a7c10702f193e3155143388116f4b912c5fceb63969738099931421a4dfe6905" # TODO: real release tarball sha256
  license :cannot_represent # closed binary; examples/docs licensed separately

  depends_on :macos
  depends_on arch: :arm64       # v1 is Apple Silicon only
  depends_on "ffmpeg"           # required by `--record` (MP4 output)

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
      "<!DOCTYPE html><html><body><div>weave ok</div></body></html>"
    )
    # `--validate` is GPU-free (parses the template + checks override paths).
    # Running it also proves the bundled dylibs resolve at process start and
    # the wrapper points at the right binary.
    system bin/"weave-viewer-cli", testpath/"proj", "--validate"
  end
end
