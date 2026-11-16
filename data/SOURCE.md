# Verse data source

`src/wordflash/data/verses.json` is copied byte-for-byte from the original WordFlash application's generated KJV corpus. The copied file's SHA-256 is `7f989fee93fdc321ae5d0c8f51c841267956aea221d80bc04f1473ead5bddcec`. Its source archive and attribution follow.

| Field | Value |
|---|---|
| Edition | King James (Authorized) Version, 1769 text, protocanon, with Strong's numbers (`eng-kjv2006`) |
| Download | https://ebible.org/Scriptures/eng-kjv2006_usfm.zip |
| Source files dated | 2026-09-26 |
| SHA-256 | `5789dcd000d60a554abb4cf9b37ce10a53628bfc686e11ada2d6c981455239c1` |
| Licence | Public domain (per `copr.htm` in the archive). In the United Kingdom, the Crown's letters patent restrict printing; this does not apply elsewhere. |

Words of Jesus come from the archive's `\wj` (red-letter) markers.

## Regenerate

The generator remains in the original C# WordFlash repository at `tools/WordFlash.DataGen`; it is not part of this Python app. To change the corpus, regenerate and review it there, then copy the reviewed JSON here and update the copied-file checksum above and the tests. Do not silently replace the pinned source archive with a newer edition.
