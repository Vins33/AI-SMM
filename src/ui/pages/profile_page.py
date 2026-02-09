# src/ui/pages/profile_page.py
"""User profile and insights page."""

from nicegui import app, ui


class ProfilePage:
    """User profile page with stats, insights and profile editing."""

    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.username_input = None
        self.email_input = None
        self.current_password_input = None
        self.new_password_input = None
        self.confirm_password_input = None
        self.error_label = None
        self.success_label = None
        self.delete_password_input = None
        self.delete_confirm_input = None

    def _get_auth_headers(self):
        """Get authorization headers."""
        token = app.storage.user.get("access_token", "")
        return {"Authorization": f"Bearer {token}"}

    async def render(self):
        """Render the profile page."""
        if self.is_dark:
            ui.dark_mode(True)

        ui.add_head_html(
            """
            <style>
                body { margin: 0; padding: 0; background-color: #0b141a; }
                .nicegui-content { min-height: 100vh; }
            </style>
            """
        )

        # Check authentication
        token = app.storage.user.get("access_token", "")
        if not token:
            with ui.column().classes("w-full h-screen items-center justify-center"):
                ui.icon("login").classes("text-6xl text-teal-500 mb-4")
                ui.label("Sessione scaduta").classes("text-2xl text-white font-bold")
                ui.button("Vai al Login", on_click=lambda: ui.navigate.to("/login")).classes("mt-4 bg-teal-600")
            return

        # Header
        with ui.row().classes("w-full px-6 py-4 bg-[#202c33] items-center"):
            with ui.element("div").classes(
                "w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center"
            ):
                ui.icon("person").classes("text-white")

            ui.label("Il Mio Profilo").classes("text-xl font-bold text-white ml-3")

            ui.element("div").classes("flex-grow")

            username = app.storage.user.get("username", "Utente")
            role = app.storage.user.get("role", "user")
            role_badge_color = {
                "sysadmin": "bg-red-600",
                "admin": "bg-orange-600",
                "user": "bg-blue-600",
            }.get(role, "bg-gray-600")

            ui.label(f"👤 {username}").classes("text-gray-300 mr-2")
            ui.badge(role.upper()).classes(f"{role_badge_color} text-white mr-4")

            # Navigation buttons
            ui.button("Chat", on_click=lambda: ui.navigate.to("/")).classes("bg-teal-600 hover:bg-teal-700")
            if role == "sysadmin":
                ui.button("Admin", on_click=lambda: ui.navigate.to("/admin")).classes(
                    "bg-orange-600 hover:bg-orange-700 ml-2"
                )
            ui.button("Logout", on_click=lambda: ui.navigate.to("/logout")).classes("bg-red-600 hover:bg-red-700 ml-2")

        # Main content
        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            # Stats section
            await self._render_stats_section()

            # Two-column layout
            with ui.row().classes("w-full gap-6 flex-wrap"):
                # Profile info (left)
                with ui.column().classes("flex-1 min-w-[350px]"):
                    await self._render_profile_section()

                # Activity insights (right)
                with ui.column().classes("flex-1 min-w-[350px]"):
                    await self._render_insights_section()

            # Danger zone - delete account (only for non-sysadmin)
            role = app.storage.user.get("role", "user")
            if role != "sysadmin":
                await self._render_delete_account_section()

    async def _render_stats_section(self):
        """Render statistics cards."""
        import httpx

        ui.label("📊 Le Tue Statistiche").classes("text-2xl font-bold text-white mb-4")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/auth/me/stats",
                    headers=self._get_auth_headers(),
                )

                if response.status_code == 200:
                    stats = response.json()

                    with ui.row().classes("w-full gap-4 flex-wrap"):
                        self._stat_card(
                            "Conversazioni",
                            stats["total_conversations"],
                            "chat_bubble",
                            "from-blue-500 to-blue-700",
                        )
                        self._stat_card(
                            "Messaggi Totali",
                            stats["total_messages"],
                            "message",
                            "from-purple-500 to-purple-700",
                        )
                        self._stat_card(
                            "Messaggi Inviati",
                            stats["messages_sent"],
                            "send",
                            "from-green-500 to-green-700",
                        )
                        self._stat_card(
                            "Risposte Ricevute",
                            stats["messages_received"],
                            "smart_toy",
                            "from-orange-500 to-orange-700",
                        )
                        self._stat_card(
                            "Media Msg/Conv",
                            stats["avg_messages_per_conversation"],
                            "analytics",
                            "from-teal-500 to-teal-700",
                        )
                        self._stat_card(
                            "Giorni Account",
                            stats["account_age_days"],
                            "calendar_today",
                            "from-pink-500 to-pink-700",
                        )
                else:
                    ui.label("Impossibile caricare le statistiche").classes("text-red-400")
        except Exception as e:
            ui.label(f"Errore: {e}").classes("text-red-400")

    def _stat_card(self, title: str, value, icon: str, gradient: str):
        """Create a statistics card."""
        with ui.card().classes(f"bg-gradient-to-br {gradient} p-5 rounded-xl shadow-lg min-w-[150px] flex-1"):
            with ui.row().classes("items-center gap-3"):
                ui.icon(icon).classes("text-white/80 text-3xl")
                with ui.column().classes("gap-0"):
                    ui.label(str(value)).classes("text-3xl font-bold text-white")
                    ui.label(title).classes("text-white/70 text-sm")

    async def _render_profile_section(self):
        """Render profile editing section."""
        import httpx

        with ui.card().classes("w-full bg-[#202c33] p-6 rounded-xl"):
            ui.label("✏️ Modifica Profilo").classes("text-xl font-bold text-white mb-4")

            # Load current user data
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "http://localhost:8000/api/v1/auth/me",
                        headers=self._get_auth_headers(),
                    )
                    if response.status_code == 200:
                        user_data = response.json()
                    else:
                        user_data = {
                            "username": app.storage.user.get("username", ""),
                            "email": "",
                        }
            except Exception:
                user_data = {
                    "username": app.storage.user.get("username", ""),
                    "email": "",
                }

            # Form fields
            self.username_input = (
                ui.input("Username", value=user_data.get("username", ""))
                .classes("w-full mb-3")
                .props("dark outlined color=teal")
            )

            self.email_input = (
                ui.input("Email", value=user_data.get("email", ""))
                .classes("w-full mb-3")
                .props("dark outlined color=teal")
            )

            ui.separator().classes("my-4")
            ui.label("Cambia Password").classes("text-white font-semibold mb-2")

            self.current_password_input = (
                ui.input("Password Attuale", password=True).classes("w-full mb-3").props("dark outlined color=teal")
            )

            self.new_password_input = (
                ui.input("Nuova Password", password=True).classes("w-full mb-3").props("dark outlined color=teal")
            )

            self.confirm_password_input = (
                ui.input("Conferma Nuova Password", password=True)
                .classes("w-full mb-4")
                .props("dark outlined color=teal")
            )

            # Messages
            self.error_label = ui.label("").classes("text-red-400 text-sm mb-2")
            self.error_label.visible = False

            self.success_label = ui.label("").classes("text-green-400 text-sm mb-2")
            self.success_label.visible = False

            # Save button
            ui.button("💾 Salva Modifiche", on_click=self._save_profile).classes(
                "w-full bg-gradient-to-r from-teal-500 to-green-600 text-white py-3 "
                "rounded-lg font-semibold hover:from-teal-600 hover:to-green-700"
            )

    async def _save_profile(self):
        """Save profile changes."""
        import httpx

        self.error_label.visible = False
        self.success_label.visible = False

        # Validate password confirmation
        new_password = self.new_password_input.value
        confirm_password = self.confirm_password_input.value

        if new_password and new_password != confirm_password:
            self.error_label.text = "Le password non corrispondono"
            self.error_label.visible = True
            return

        if new_password and not self.current_password_input.value:
            self.error_label.text = "Inserisci la password attuale per cambiarla"
            self.error_label.visible = True
            return

        # Build update payload
        payload = {}
        if self.username_input.value:
            payload["username"] = self.username_input.value
        if self.email_input.value:
            payload["email"] = self.email_input.value
        if new_password:
            payload["current_password"] = self.current_password_input.value
            payload["new_password"] = new_password

        if not payload:
            self.error_label.text = "Nessuna modifica da salvare"
            self.error_label.visible = True
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    "http://localhost:8000/api/v1/auth/me",
                    headers=self._get_auth_headers(),
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Update storage
                    app.storage.user["username"] = data["username"]
                    self.success_label.text = "Profilo aggiornato con successo! ✅"
                    self.success_label.visible = True
                    # Clear password fields
                    self.current_password_input.value = ""
                    self.new_password_input.value = ""
                    self.confirm_password_input.value = ""
                    ui.notify("Profilo aggiornato!", type="positive")
                else:
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            error = error_data.get("detail", str(error_data))
                            if isinstance(error, dict):
                                error = error.get("message", str(error))
                        else:
                            error = str(error_data)
                    except Exception:
                        error = f"Errore {response.status_code}"
                    self.error_label.text = str(error)
                    self.error_label.visible = True

        except Exception as e:
            self.error_label.text = f"Errore di connessione: {e}"
            self.error_label.visible = True

    async def _render_insights_section(self):
        """Render activity insights section."""
        import httpx

        with ui.card().classes("w-full bg-[#202c33] p-6 rounded-xl"):
            ui.label("💡 Insights & Attività").classes("text-xl font-bold text-white mb-4")

            try:
                async with httpx.AsyncClient() as client:
                    # Get user info
                    me_response = await client.get(
                        "http://localhost:8000/api/v1/auth/me",
                        headers=self._get_auth_headers(),
                    )
                    stats_response = await client.get(
                        "http://localhost:8000/api/v1/auth/me/stats",
                        headers=self._get_auth_headers(),
                    )

                if me_response.status_code == 200 and stats_response.status_code == 200:
                    user = me_response.json()
                    stats = stats_response.json()

                    # Account info card
                    with ui.card().classes("w-full bg-[#1a2730] p-4 rounded-lg mb-4"):
                        ui.label("📋 Informazioni Account").classes("text-white font-semibold mb-3")

                        info_items = [
                            ("👤 Username", user.get("username", "-")),
                            ("📧 Email", user.get("email", "-")),
                            ("🛡️ Ruolo", user.get("role", "-").upper()),
                            ("✅ Stato", "Attivo" if user.get("is_active") else "Inattivo"),
                        ]

                        # Account creation date
                        created = user.get("created_at")
                        if created:
                            created_str = created[:10] if isinstance(created, str) else str(created)[:10]
                            info_items.append(("📅 Registrato il", created_str))

                        # Last login
                        last_login = user.get("last_login")
                        if last_login:
                            login_str = (
                                last_login[:16].replace("T", " ")
                                if isinstance(last_login, str)
                                else str(last_login)[:16]
                            )
                            info_items.append(("🕐 Ultimo accesso", login_str))

                        for label, value in info_items:
                            with ui.row().classes("w-full justify-between py-1"):
                                ui.label(label).classes("text-gray-400 text-sm")
                                ui.label(str(value)).classes("text-white text-sm font-medium")

                    # Activity summary
                    with ui.card().classes("w-full bg-[#1a2730] p-4 rounded-lg mb-4"):
                        ui.label("📈 Riepilogo Attività").classes("text-white font-semibold mb-3")

                        total_msgs = stats.get("total_messages", 0)
                        sent = stats.get("messages_sent", 0)
                        received = stats.get("messages_received", 0)
                        convs = stats.get("total_conversations", 0)
                        avg = stats.get("avg_messages_per_conversation", 0)
                        days = stats.get("account_age_days", 1)

                        # Messages per day
                        msgs_per_day = round(total_msgs / max(days, 1), 1)

                        # Conversations per week
                        convs_per_week = round(convs / max(days / 7, 1), 1)

                        activity_items = [
                            ("📨 Messaggi al giorno", f"{msgs_per_day}"),
                            ("💬 Conversazioni a settimana", f"{convs_per_week}"),
                            ("📊 Media messaggi per conversazione", f"{avg}"),
                            ("📤 Rapporto invio/ricezione", f"{sent}/{received}"),
                        ]

                        for label, value in activity_items:
                            with ui.row().classes("w-full justify-between py-1"):
                                ui.label(label).classes("text-gray-400 text-sm")
                                ui.label(value).classes("text-white text-sm font-medium")

                    # Usage level
                    with ui.card().classes("w-full bg-[#1a2730] p-4 rounded-lg"):
                        ui.label("🏆 Livello di Utilizzo").classes("text-white font-semibold mb-3")

                        # Determine usage level
                        if total_msgs >= 500:
                            level = "🥇 Esperto"
                            level_color = "text-yellow-400"
                            progress = 1.0
                        elif total_msgs >= 200:
                            level = "🥈 Avanzato"
                            level_color = "text-gray-300"
                            progress = total_msgs / 500
                        elif total_msgs >= 50:
                            level = "🥉 Intermedio"
                            level_color = "text-orange-400"
                            progress = total_msgs / 200
                        elif total_msgs >= 10:
                            level = "🌱 Principiante"
                            level_color = "text-green-400"
                            progress = total_msgs / 50
                        else:
                            level = "🆕 Nuovo"
                            level_color = "text-blue-400"
                            progress = total_msgs / 10

                        ui.label(level).classes(f"text-2xl font-bold {level_color} mb-2")
                        ui.linear_progress(value=min(progress, 1.0)).classes("mb-2").props("color=teal rounded")

                        # Next level info
                        if total_msgs < 10:
                            next_msg = f"Ancora {10 - total_msgs} messaggi per il livello Principiante"
                        elif total_msgs < 50:
                            next_msg = f"Ancora {50 - total_msgs} messaggi per il livello Intermedio"
                        elif total_msgs < 200:
                            next_msg = f"Ancora {200 - total_msgs} messaggi per il livello Avanzato"
                        elif total_msgs < 500:
                            next_msg = f"Ancora {500 - total_msgs} messaggi per il livello Esperto"
                        else:
                            next_msg = "Hai raggiunto il livello massimo! 🎉"

                        ui.label(next_msg).classes("text-gray-400 text-xs")

                else:
                    ui.label("Impossibile caricare i dati").classes("text-red-400")

            except Exception as e:
                ui.label(f"Errore: {e}").classes("text-red-400")

    async def _render_delete_account_section(self):
        """Render the danger zone with account deletion."""
        with ui.card().classes("w-full bg-[#2a1a1a] border border-red-900 p-6 rounded-xl"):
            ui.label("⚠️ Zona Pericolosa").classes("text-xl font-bold text-red-400 mb-2")
            ui.label(
                "L'eliminazione dell'account è permanente. "
                "Tutte le conversazioni e i dati verranno eliminati."
            ).classes("text-gray-400 text-sm mb-4")

            with ui.expansion("Elimina il mio account").classes("w-full text-red-400"):
                self.delete_password_input = (
                    ui.input("Password di conferma", password=True)
                    .classes("w-full mb-3")
                    .props("dark outlined color=red")
                )

                self.delete_confirm_input = (
                    ui.input("Digita DELETE per confermare", placeholder="DELETE")
                    .classes("w-full mb-4")
                    .props("dark outlined color=red")
                )

                self.delete_error_label = ui.label("").classes("text-red-400 text-sm mb-2")
                self.delete_error_label.visible = False

                ui.button(
                    "🗑️ Elimina Account Definitivamente",
                    on_click=self._delete_account,
                ).classes(
                    "w-full bg-red-700 hover:bg-red-800 text-white py-3 rounded-lg font-semibold"
                )

    async def _delete_account(self):
        """Handle account self-deletion."""
        import httpx

        self.delete_error_label.visible = False

        password = self.delete_password_input.value
        confirmation = self.delete_confirm_input.value

        if not password:
            self.delete_error_label.text = "Inserisci la password"
            self.delete_error_label.visible = True
            return

        if confirmation != "DELETE":
            self.delete_error_label.text = "Digita 'DELETE' per confermare"
            self.delete_error_label.visible = True
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "DELETE",
                    "http://localhost:8000/api/v1/auth/me",
                    headers=self._get_auth_headers(),
                    json={"password": password, "confirmation": confirmation},
                )

                if response.status_code == 200:
                    app.storage.user.clear()
                    ui.notify("Account eliminato con successo", type="positive")
                    ui.navigate.to("/login")
                else:
                    try:
                        error = response.json().get("detail", "Errore")
                    except Exception:
                        error = f"Errore {response.status_code}"
                    self.delete_error_label.text = str(error)
                    self.delete_error_label.visible = True

        except Exception as e:
            self.delete_error_label.text = f"Errore: {e}"
            self.delete_error_label.visible = True
