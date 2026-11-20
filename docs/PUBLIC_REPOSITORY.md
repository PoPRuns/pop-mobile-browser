# Publication process for PoP Mobile

A separate, **history-clean repository snapshot** is prepared for the eventual
public `PoPRuns/pop-mobile-browser` repository. Follow
[`CLEAN_PUBLIC_HISTORY.md`](CLEAN_PUBLIC_HISTORY.md) for the exact, reversible
steps. Do not expose or force-push the original private development history:
it includes the previous MIDI binary.

The clean snapshot ships the new FM-based MIDI WebAssembly build. Use
`python3 tools/verify_public_snapshot.py` to check its binary fingerprints and
initial Git history before pushing to a new repository.

**This is not permission to enable public distribution yet.** The corresponding
source archive must be published with a working direct link, appropriate
third-party notices must accompany it, and MIDI playback should be tested in
Firefox. See [`SOURCE_COMPLIANCE.md`](SOURCE_COMPLIANCE.md). Keep the GitHub
Pages publication gate disabled until those remaining checks are complete.
