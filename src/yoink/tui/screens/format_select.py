from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Label

from yoink.core.models import FormatOption


class FormatSelectScreen(ModalScreen[FormatOption | None]):
    """Modal screen for selecting a download format."""

    DEFAULT_CSS = """
    FormatSelectScreen {
        align: center middle;
    }
    FormatSelectScreen > Vertical {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    FormatSelectScreen .modal-title {
        text-style: bold;
        margin-bottom: 1;
        text-align: center;
    }
    FormatSelectScreen DataTable {
        height: auto;
        max-height: 20;
        margin: 1 0;
    }
    FormatSelectScreen .modal-buttons {
        margin-top: 1;
        text-align: center;
    }
    """

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, formats: list[FormatOption]) -> None:
        super().__init__()
        self._formats = formats

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select Download Format", classes="modal-title")
            yield DataTable(id="modal-format-table", cursor_type="row")
            yield Button("Download", variant="success", id="modal-download-btn")

    def on_mount(self) -> None:
        table = self.query_one("#modal-format-table", DataTable)
        table.add_columns("Format", "Resolution", "Ext", "Size", "Type")
        for fmt in self._formats:
            ftype = []
            if fmt.has_video:
                ftype.append("Video")
            if fmt.has_audio:
                ftype.append("Audio")
            size = FormatOption._human_size(fmt.filesize) if fmt.filesize else "?"
            table.add_row(
                fmt.format_note or fmt.format_id,
                fmt.resolution or "-",
                fmt.ext,
                size,
                "+".join(ftype),
                key=fmt.format_id,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal-download-btn":
            self._select_current()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._select_current()

    def _select_current(self) -> None:
        table = self.query_one("#modal-format-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._formats):
            self.dismiss(self._formats[table.cursor_row])

    def action_cancel(self) -> None:
        self.dismiss(None)
