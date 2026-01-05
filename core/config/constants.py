# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/core/config/constants.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

Defines global constants used across the EuljiroWorship and EuljiroBible systems.

This module centralizes non-path, non-style configuration constants that are
shared across components. It is intended for values that would otherwise be
hard-coded in multiple places, such as parsing limits, default thresholds,
or formatting constraints.

By keeping these constants in a dedicated module, the codebase remains
consistent and easier to maintain as defaults evolve or become user-configurable.
"""

# ───── Global constants ─────
MAX_CHARS = 60