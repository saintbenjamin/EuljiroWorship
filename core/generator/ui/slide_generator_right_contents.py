# -*- coding: utf-8 -*-
"""
File: EuljiroWorship/core/generator/ui/slide_generator_right_contents.py

Dynamic right-hand content panel for the slide generator UI.

This module defines `SlideGeneratorRightContents`, a QWidget responsible for
hosting the style-specific input panes used to edit slide content. The widget
acts as a dispatcher that selects and embeds the appropriate sub-pane based on
the slide style (e.g., lyrics, verse, anthem).

Each sub-pane encapsulates its own UI logic and data extraction method, allowing
the generator to remain modular and extensible as new slide styles are added.

:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from core.generator.ui.contents.anthem_content import AnthemContent
from core.generator.ui.contents.corner_content import CornerContent
from core.generator.ui.contents.greet_content import GreetContent
from core.generator.ui.contents.hymn_content import HymnContent
from core.generator.ui.contents.image_content import ImageContent
from core.generator.ui.contents.lyrics_content import LyricsContent
from core.generator.ui.contents.prayer_content import PrayerContent
from core.generator.ui.contents.respo_content import RespoContent
from core.generator.ui.contents.verse_content import VerseContent

class SlideGeneratorRightContents(QWidget):
    """
    Right-hand dynamic content panel for editing slide data.

    This widget selects and embeds a style-specific editor pane based on the
    given slide style. Each supported style maps to a dedicated sub-widget
    (e.g., `LyricsContent`, `VerseContent`) that defines its own input fields
    and data extraction logic.

    Supported slide styles
    ----------------------
    - "anthem": Choir name, title, and lyrics
    - "corner": Short caption displayed at the corner
    - "greet": Freeform greeting or announcement text
    - "hymn": Hymn lyrics editor (exported as lyrics)
    - "lyrics": General lyrics editor with line splitting
    - "prayer": Representative name or prayer leader
    - "respo": Responsive reading editor
    - "verse": Bible verse reference and preview editor
    - "image": Image-based slide with caption/headline
    - "blank": Empty slide with no editable content

    Attributes
    ----------
    style : str
        Internal slide style key that determines which sub-pane is created.
    subpane : QWidget
        The embedded style-specific content widget.
    generator_window : QWidget
        Reference to the parent generator window, used by sub-panes for
        callbacks or shared context.
    """

    def __init__(self, style: str, generator_window, caption: str = "", headline: str = "", parent=None):
        """
        Initialize the right-hand content panel for a specific slide style.

        This constructor selects the appropriate style-specific sub-pane and
        embeds it into the panel layout. Initial caption and headline values
        are passed through to the sub-pane to pre-fill the editor when editing
        an existing slide.

        Args:
            style (str):
                Internal slide style key (e.g., "lyrics", "verse", "anthem").
            generator_window:
                Reference to the main slide generator window. This is passed to
                sub-panes so they can access shared state or utilities.
            caption (str):
                Initial caption value for the slide.
            headline (str):
                Initial headline or main content value for the slide.
            parent (QWidget | None):
                Optional parent widget.

        Returns:
            None
        """
        super().__init__(parent)
        self.style = style
        self.generator_window = generator_window
        self.setLayout(QVBoxLayout())

        # Dynamically choose the correct content pane based on the slide style
        if self.style == "anthem":
            self.subpane = AnthemContent(self, self.generator_window, caption, headline)
        elif self.style in ("corner", "intro"):
            self.subpane = CornerContent(self, self.generator_window, caption, headline)
        elif self.style == "greet":
            self.subpane = GreetContent(self, self.generator_window, caption, headline)
        elif self.style == "hymn":
            self.subpane = HymnContent(self, self.generator_window, caption, headline)
        elif self.style == "image":
            self.subpane = ImageContent(self, self.generator_window, caption, headline)
        elif self.style == "lyrics":
            self.subpane = LyricsContent(self, self.generator_window, caption, headline)
        elif self.style == "prayer":
            self.subpane = PrayerContent(self, self.generator_window, caption, headline)
        elif self.style == "respo":
            self.subpane = RespoContent(self, self.generator_window, caption, headline)
        elif self.style == "verse":
            self.subpane = VerseContent(self, self.generator_window, caption, headline)
        elif self.style == "blank":
            self.subpane = QWidget()
        else:
            self.subpane = QWidget()
        # Add the selected sub-pane to the layout of the right-side panel
        self.layout().addWidget(self.subpane)

    def get_slide_data(self) -> dict:
        """
        Retrieve the slide data from the active content sub-pane.

        This method delegates to the embedded sub-pane's `get_slide_data()` method
        if it exists. If the current sub-pane does not implement data extraction
        (e.g., blank slides), an empty dictionary is returned.

        Args:
            None

        Returns:
            dict:
                Dictionary representing the current slide's content, suitable for
                inclusion in the generator's internal slide session data.
        """
        if hasattr(self, "subpane") and hasattr(self.subpane, "get_slide_data"):
            return self.subpane.get_slide_data()
        
        return {}