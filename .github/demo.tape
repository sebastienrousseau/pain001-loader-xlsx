# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered with `make demo` (VHS, https://github.com/charmbracelet/vhs)
# from a virtual environment where the package is installed. Runs the
# repository's own examples against the workbooks they write; no network.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "python examples/01_load_xlsx.py"
Enter
Sleep 4s

Type "python examples/02_iban_safety_guard.py | fold -s -w 110"
Enter
Sleep 6s
