+++
title = "Landovskis Forge"
description = "Web software in Rust and WebAssembly, designed, built and tested end to end."
template = "index.html"

[extra]
hero_kicker = "Rust · WebAssembly · Open data"
hero_pitch = "Web software in Rust and WebAssembly, designed, built and tested end to end."
about_title = "About the forge"
about_text = "Landovskis Forge is the portfolio of Alex Landovskis. The work here is held to a short list of standards: it is tested, it is accessible, it speaks English and French, and it says plainly what is finished and what is not."
other_title = "Other work"

[[extra.other]]
name = "ansible"
url = "https://github.com/alandovskis/ansible"
text = "Provisions my development machines on macOS and Debian/Ubuntu. CI runs the whole playbook on Ubuntu 26.04, checks that every expected tool is on the PATH, and runs it a second time to prove it is idempotent."
tags = ["Ansible", "macOS", "Debian/Ubuntu", "GitHub Actions"]

[[extra.other]]
name = "ai-plugins"
url = "https://github.com/alandovskis/ai-plugins"
text = "A Claude Code plugin of agent skills for requirements documents, planning, code review and pull requests, built around my own workflow. CI validates the plugin manifests and every skill's layout. Each skill ships with evals; they are run locally, not in CI, and the known failures are listed in the repository."
tags = ["Claude Code", "Agent skills", "Evals", "GitHub Actions"]
+++
