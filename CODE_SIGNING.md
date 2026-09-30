# Code signing policy

The Windows executable attached to each [release](https://github.com/JeanMichelDurand/mermaid2pptx/releases)
is meant to be signed through [SignPath.io](https://about.signpath.io/), with a certificate issued to
the [SignPath Foundation](https://signpath.org/) for open-source projects. Until that is in place, the
executable is unsigned: Windows SmartScreen asks for confirmation, and Smart App Control blocks it.
The [browser version](https://jeanmicheldurand.github.io/mermaid2pptx/) needs no executable at all.

## What gets signed

Only `mermaid2pptx-windows-x86_64.exe`, built by the `release` workflow on GitHub Actions from the
tagged commit of this repository (`.github/workflows/release.yml`), and nothing built elsewhere.
Every signing request is tied to that workflow run, so a signed file can always be traced back to
its source.

## Team roles

| Role | Members |
|---|---|
| Committers and reviewers | [@JeanMichelDurand](https://github.com/JeanMichelDurand) |
| Approvers (each signing request) | [@JeanMichelDurand](https://github.com/JeanMichelDurand) |

Changes from other contributors reach `main` only through a reviewed pull request that passes CI.

## Privacy

This program does not transfer any information to other networked systems. It reads the Mermaid file
you give it and writes one `.pptx` file next to it. The browser version downloads Python and the
converter into your browser, then works offline: your diagram never leaves your computer.
