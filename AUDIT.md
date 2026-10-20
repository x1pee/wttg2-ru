# Installer audit — 0.3.1 RC

This patch release fixes failed installation and language restoration. The translation, all 15 binary patch payloads and their expected original/translated hashes are unchanged from 0.3.0 RC.

The previous installer could delete a matching helper that existed before a failed install, miss the destination of a partial failing copy, and leave changed files after final verification failed. Installation now tracks attempted writes before copying, includes verification in rollback, and preserves pre-existing helpers.

Restoration previously stopped halfway if a later destination could not be written. It now snapshots each changing file's exact prior bytes/existence before changing anything, including a partially restored installation. A failure restores that prior state and continues rollback if one file fails. Successful restoration or complete rollback cleans only its unique temporary snapshot directory. An incomplete rollback retains snapshots and reports both the original error and individual rollback errors. The ordinary English backup remains intact.

Run `tests/run-installer.ps1` on Windows with the .NET Framework C# compiler. **68 assertions passed** using real temporary files and valid miniature patches, with injected partial writes, corruption and blocked rollback. The production command-line installer also passed the regression where a matching pre-existing helper survives a read-only destination failure. All 15 unchanged game patches were reconstructed in memory from hash-checked local English backups and matched the manifest's translated SHA-256 values.

Tests never execute the fake fixture's `WTTG2.exe` marker. No game saves, original game binaries or user configurations are part of the test suite or release. These results do not establish full gameplay behavior or compatibility with every retail Steam build. The installer still requires exact supported source hashes and has .NET Framework path-length limits.

**Before restoring English, roll back the separate radio-subtitle addon first.** Its modified subtitle table is intentionally protected by the existing external-modification guard. The base installer must not overwrite independent addon changes. If OS permissions also prevent rollback, release the lock and recover using the retained backup/snapshot paths reported by the installer.
