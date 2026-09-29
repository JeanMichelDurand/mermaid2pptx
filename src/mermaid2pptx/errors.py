"""The one error a diagram's text can raise."""


class MermaidError(ValueError):
    """The text is not Mermaid, or uses syntax this converter does not cover."""
