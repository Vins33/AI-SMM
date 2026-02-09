# src/ui/pages/chat_page.py
"""Chat page with LangGraph agent integration - ChatGPT-like style."""

from nicegui import app, ui

from src.core.agent_graph import get_agent_graph_response
from src.services.database import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversations,
    get_db_session,
    get_messages,
    update_conversation_title,
)
from src.ui.components.chat import ChatContainer, ChatInput
from src.ui.components.sidebar import ConversationList


class ChatPage:
    """Main chat page with conversation management - ChatGPT style."""

    def __init__(self, is_dark: bool = True, user_id: int | None = None, role: str = "user"):
        self.is_dark = is_dark
        self.user_id = user_id
        self.role = role
        self.selected_conv_id: int | None = None
        self.sidebar: ConversationList | None = None
        self.chat_container: ChatContainer | None = None
        self.chat_input: ChatInput | None = None
        self.loading_spinner = None
        self.header_label = None

    async def render(self):
        """Render the chat page."""
        # Enable dark mode
        if self.is_dark:
            ui.dark_mode(True)

        conversations = await self._load_conversations()

        # Main container
        with ui.row().classes("w-full h-screen"):
            # Sidebar
            self.sidebar = ConversationList(
                conversations=conversations,
                on_select=self._on_conversation_select,
                on_new=self._on_new_conversation,
                on_delete=self._on_delete_conversation,
                on_rename=self._on_rename_conversation,
                is_dark=self.is_dark,
                show_owner=self.role == "sysadmin",
            )

            # Main chat area - WhatsApp style
            header_bg = "bg-[#202c33]" if self.is_dark else "bg-[#008069]"
            text_class = "text-white"

            with ui.column().classes("flex-grow h-full bg-[#0b141a] rounded-3xl overflow-hidden ml-2"):
                # Header - WhatsApp style with gradient
                with ui.row().classes(f"w-full px-4 py-3 {header_bg} items-center gap-3 shadow-md"):
                    # Avatar
                    with ui.element("div").classes(
                        "w-10 h-10 rounded-full bg-gradient-to-br from-green-400 to-teal-600 "
                        "flex items-center justify-center"
                    ):
                        ui.icon("smart_toy").classes("text-white")

                    # Title and status
                    with ui.column().classes("flex-grow gap-0"):
                        self.header_label = ui.label("Agente Finanziario").classes(
                            f"text-lg font-semibold {text_class}"
                        )
                        ui.label("online").classes("text-xs text-green-300")

                    # Loading spinner
                    self.loading_spinner = ui.spinner("dots", size="md", color="white").classes("ml-4")
                    self.loading_spinner.visible = False

                    # Profile button
                    ui.button(icon="person", on_click=lambda: ui.navigate.to("/profile")).props("flat round").classes(
                        "text-white"
                    ).tooltip("Il Mio Profilo")

                    # Admin button (only for sysadmin)
                    role = app.storage.user.get("role", "")
                    if role == "sysadmin":
                        ui.button(icon="admin_panel_settings", on_click=lambda: ui.navigate.to("/admin")).props(
                            "flat round"
                        ).classes("text-white").tooltip("Admin Panel")

                    # Logout button
                    ui.button(icon="logout", on_click=lambda: ui.navigate.to("/logout")).props("flat round").classes(
                        "text-white"
                    ).tooltip("Logout")

                # Chat messages
                self.chat_container = ChatContainer(is_dark=self.is_dark)

                # Chat input area - WhatsApp style
                self.chat_input = ChatInput(on_send=self._on_send_message, is_dark=self.is_dark)

        # Auto-select first conversation if exists
        if conversations:
            await self._on_conversation_select(conversations[0].id)

    async def _load_conversations(self) -> list:
        """Load conversations for the current user (or all for sysadmin)."""
        async with get_db_session() as session:
            if self.role == "sysadmin":
                return await get_conversations(session)  # tutte le conversazioni
            return await get_conversations(session, user_id=self.user_id)

    async def _load_messages(self, conv_id: int) -> list:
        """Load messages for a conversation."""
        async with get_db_session() as session:
            return await get_messages(session, conv_id)

    async def _on_conversation_select(self, conv_id: int):
        """Handle conversation selection."""
        self.selected_conv_id = conv_id
        self.chat_container.clear()

        messages = await self._load_messages(conv_id)
        for msg in messages:
            self.chat_container.add_message(msg.role, msg.content)

        self.chat_container.scroll_to_bottom()

    async def _on_new_conversation(self):
        """Create a new conversation."""
        async with get_db_session() as session:
            conv = await create_conversation(session, user_id=self.user_id)
            self.selected_conv_id = conv.id

        conversations = await self._load_conversations()
        self.sidebar.update(conversations, self.selected_conv_id)
        self.chat_container.clear()

    async def _on_delete_conversation(self, conv_id: int):
        """Delete a conversation."""
        async with get_db_session() as session:
            # Sysadmin può eliminare qualsiasi conversazione
            uid = None if self.role == "sysadmin" else self.user_id
            await delete_conversation(session, conv_id, user_id=uid)

        if self.selected_conv_id == conv_id:
            self.selected_conv_id = None
            self.chat_container.clear()

        conversations = await self._load_conversations()
        self.sidebar.update(conversations)

        if conversations and self.selected_conv_id is None:
            await self._on_conversation_select(conversations[0].id)

    async def _on_rename_conversation(self, conv_id: int, new_title: str):
        """Rename a conversation."""
        async with get_db_session() as session:
            uid = None if self.role == "sysadmin" else self.user_id
            await update_conversation_title(session, conv_id, new_title, user_id=uid)

        conversations = await self._load_conversations()
        self.sidebar.update(conversations, self.selected_conv_id)
        ui.notify(f"Conversazione rinominata: {new_title}", type="positive")

    async def _on_send_message(self, message: str):
        """Handle sending a message."""
        if not self.selected_conv_id:
            ui.notify("Seleziona o crea una conversazione", type="warning")
            return

        # Add user message to DB and display
        async with get_db_session() as session:
            await add_message(session, self.selected_conv_id, "user", message)
        self.chat_container.add_message("user", message)
        self.chat_container.scroll_to_bottom()

        # Update conversation title with first message topic
        await self._update_conversation_title_if_needed(message)

        # Show loading
        self.loading_spinner.visible = True

        try:
            # Get message history for context
            async with get_db_session() as session:
                messages = await get_messages(session, self.selected_conv_id)

            history = [{"role": m.role, "content": m.content} for m in messages[:-1]]
            # Pass thread_id for LangGraph checkpointing
            thread_id = f"conv_{self.selected_conv_id}"
            response = await get_agent_graph_response(message, history, thread_id)
            response_text = response.content

            # Save and display response
            async with get_db_session() as session:
                await add_message(session, self.selected_conv_id, "assistant", response_text)
            self.chat_container.add_message("assistant", response_text)

        except Exception as e:
            error_msg = f"Errore: {str(e)}"
            self.chat_container.add_message("assistant", error_msg)
            ui.notify(error_msg, type="negative")

        finally:
            self.loading_spinner.visible = False
            self.chat_container.scroll_to_bottom()

    async def _update_conversation_title_if_needed(self, first_message: str):
        """Update conversation title based on first message."""
        async with get_db_session() as session:
            messages = await get_messages(session, self.selected_conv_id)

        # Only update if this is the first message
        if len(messages) == 1:
            # Extract topic from message (first 30 chars or until punctuation)
            topic = first_message[:40]
            if len(first_message) > 40:
                topic = topic.rsplit(" ", 1)[0] + "..."

            async with get_db_session() as session:
                await update_conversation_title(session, self.selected_conv_id, topic)

            # Refresh sidebar
            conversations = await self._load_conversations()
            self.sidebar.update(conversations, self.selected_conv_id)
