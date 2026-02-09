# src/ui/components/sidebar.py
"""Sidebar UI components - ChatGPT-like style."""

import asyncio
from datetime import datetime

from nicegui import ui


class ConversationList:
    """Sidebar component for listing conversations - ChatGPT style."""

    def __init__(
        self,
        conversations: list,
        on_select: callable,
        on_new: callable,
        on_delete: callable,
        on_rename: callable = None,
        is_dark: bool = True,
        show_owner: bool = False,
    ):
        self.conversations = conversations
        self.on_select = on_select
        self.on_new = on_new
        self.on_delete = on_delete
        self.on_rename = on_rename
        self.is_dark = is_dark
        self.show_owner = show_owner
        self.selected_id = None
        self.list_container = None
        self._render()

    def _render(self):
        # WhatsApp-like sidebar
        bg_class = "bg-[#111b21]" if self.is_dark else "bg-white"
        header_bg = "bg-[#202c33]" if self.is_dark else "bg-[#f0f2f5]"
        text_class = "text-white" if self.is_dark else "text-gray-800"

        with ui.column().classes(f"w-72 {bg_class} h-full rounded-3xl overflow-hidden"):
            # Header with title
            with ui.row().classes(f"w-full {header_bg} px-4 py-3 items-center"):
                ui.label("Chat").classes(f"text-xl font-semibold {text_class} flex-grow")
                # New chat button - circular
                ui.button(
                    icon="add_comment",
                    on_click=self._handle_new,
                ).props("round flat").classes("text-gray-400 hover:text-white")

            # Search bar (decorative)
            with ui.row().classes("w-full px-3 py-2"):
                with ui.element("div").classes("w-full bg-[#202c33] rounded-2xl px-4 py-2 flex items-center gap-2"):
                    ui.icon("search").classes("text-gray-400 text-sm")
                    ui.label("Cerca o inizia una nuova chat").classes("text-gray-400 text-sm")

            # Conversations list
            self.list_container = ui.column().classes("w-full overflow-y-auto flex-grow")
            self._render_list()

    def _render_list(self):
        self.list_container.clear()
        with self.list_container:
            for conv in self.conversations:
                self._render_conversation_item(conv)

    def _render_conversation_item(self, conv):
        is_selected = self.selected_id == conv.id
        text_class = "text-white" if self.is_dark else "text-gray-800"
        secondary_text = "text-gray-400" if self.is_dark else "text-gray-500"

        # WhatsApp-like selection style
        bg_selected = "bg-[#2a3942]" if is_selected else ""
        bg_hover = "hover:bg-[#202c33]" if not is_selected else ""

        # Generate display title from conversation
        display_title = self._get_display_title(conv)

        with ui.row().classes(
            f"w-full items-center px-3 py-3 cursor-pointer {bg_selected} {bg_hover} rounded-xl mx-1 my-0.5 group"
        ):
            # Avatar circle
            with ui.element("div").classes(
                "w-12 h-12 rounded-full bg-gradient-to-br from-teal-500 to-green-600 "
                "flex items-center justify-center flex-shrink-0 mr-3"
            ):
                ui.icon("chat").classes("text-white text-lg")

            # Title and preview
            with ui.column().classes("flex-grow min-w-0 gap-0").on("click", lambda c=conv: self._select(c)):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(display_title).classes(f"truncate {text_class} text-base font-medium")
                    # Time label
                    if hasattr(conv, "updated_at") and conv.updated_at:
                        time_str = conv.updated_at.strftime("%H:%M")
                        ui.label(time_str).classes(f"{secondary_text} text-xs")

                # Preview text
                if self.show_owner and hasattr(conv, "user") and conv.user:
                    ui.label(f"👤 {conv.user.username}").classes("truncate text-teal-400 text-xs")
                else:
                    ui.label("Clicca per aprire...").classes(f"truncate {secondary_text} text-sm")

            # Action buttons (visible on hover)
            with ui.column().classes("opacity-0 group-hover:opacity-100 gap-1"):
                # Edit button
                if self.on_rename:
                    ui.button(
                        icon="edit",
                        on_click=lambda c=conv: self._show_rename_dialog(c),
                    ).props("flat round size=xs").classes("text-gray-400 hover:text-blue-400")
                # Delete button
                ui.button(
                    icon="delete",
                    on_click=lambda c=conv: self._handle_delete(c.id),
                ).props("flat round size=xs").classes("text-gray-400 hover:text-red-400")

    def _show_rename_dialog(self, conv):
        """Show dialog to rename conversation."""
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("Rinomina conversazione").classes("text-lg font-bold mb-4")

            new_title = ui.input(
                "Nuovo titolo",
                value=conv.title if conv.title else "",
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Annulla", on_click=dialog.close).props("flat")
                ui.button(
                    "Salva",
                    on_click=lambda: self._handle_rename(conv.id, new_title.value, dialog),
                ).props("color=primary")

        dialog.open()

    async def _handle_rename(self, conv_id: int, new_title: str, dialog):
        """Handle rename conversation."""
        if self.on_rename and new_title.strip():
            await self.on_rename(conv_id, new_title.strip())
            dialog.close()

    def _get_display_title(self, conv) -> str:
        """Generate display title - date or first message summary."""
        # If title is "Nuova conversazione" or empty, show formatted date
        if conv.title in ("Nuova conversazione", "") or not conv.title:
            if hasattr(conv, "created_at") and conv.created_at:
                # Format: "5 Feb 2026" or "Oggi" if same day
                today = datetime.now().date()
                conv_date = conv.created_at.date()
                if conv_date == today:
                    return f"Chat {conv.created_at.strftime('%H:%M')}"
                else:
                    return conv.created_at.strftime("%d %b %Y")
            return f"Chat #{conv.id}"
        else:
            # Truncate long titles
            title = conv.title
            return title[:25] + "..." if len(title) > 25 else title

    def _select(self, conv):
        """Handle conversation selection - use asyncio.create_task for async callback."""
        self.selected_id = conv.id
        # Schedule the async callback properly
        asyncio.create_task(self.on_select(conv.id))
        self._render_list()

    async def _handle_new(self):
        """Handle new conversation click."""
        await self.on_new()

    async def _handle_delete(self, conv_id: int):
        """Handle delete conversation."""
        await self.on_delete(conv_id)

    def update(self, conversations: list, selected_id: int | None = None):
        self.conversations = conversations
        if selected_id is not None:
            self.selected_id = selected_id
        self._render_list()
