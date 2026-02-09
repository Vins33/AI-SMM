# src/ui/pages/admin_page.py
"""Admin dashboard page for system administrators."""

from nicegui import app, ui


class AdminDashboard:
    """Admin dashboard component with CRUD operations."""

    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.stats = None
        self.users_table = None
        self.tables_list = None
        self.query_input = None
        self.query_result = None
        self.selected_table = None
        self.search_input = None

    def _get_auth_headers(self):
        """Get authorization headers."""
        token = app.storage.user.get("access_token", "")
        return {"Authorization": f"Bearer {token}"}

    async def render(self):
        """Render the admin dashboard."""
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

        # Check if user is sysadmin
        token = app.storage.user.get("access_token", "")
        role = app.storage.user.get("role", "")

        # If no token, redirect to login
        if not token:
            with ui.column().classes("w-full h-screen items-center justify-center"):
                ui.icon("login").classes("text-6xl text-teal-500 mb-4")
                ui.label("Sessione scaduta").classes("text-2xl text-white font-bold")
                ui.label("Effettua il login per accedere all'admin panel.").classes("text-gray-400 mt-2")
                ui.button("Vai al Login", on_click=lambda: ui.navigate.to("/login")).classes("mt-4 bg-teal-600")
            return

        if role != "sysadmin":
            with ui.column().classes("w-full h-screen items-center justify-center"):
                ui.icon("lock").classes("text-6xl text-red-500 mb-4")
                ui.label("Accesso negato").classes("text-2xl text-white font-bold")
                ui.label("Questa pagina è riservata agli amministratori di sistema.").classes("text-gray-400 mt-2")
                ui.button("Torna alla Home", on_click=lambda: ui.navigate.to("/")).classes("mt-4 bg-teal-600")
            return

        # Header
        with ui.row().classes("w-full px-6 py-4 bg-[#202c33] items-center"):
            with ui.element("div").classes(
                "w-10 h-10 rounded-full bg-gradient-to-br from-red-400 to-orange-600 flex items-center justify-center"
            ):
                ui.icon("admin_panel_settings").classes("text-white")

            ui.label("Admin Dashboard").classes("text-xl font-bold text-white ml-3")

            ui.element("div").classes("flex-grow")

            # User info
            username = app.storage.user.get("username", "Admin")
            ui.label(f"👤 {username}").classes("text-gray-300 mr-4")

            ui.button("Logout", on_click=self._logout).classes("bg-red-600 hover:bg-red-700")
            ui.button("Chat", on_click=lambda: ui.navigate.to("/")).classes("bg-teal-600 hover:bg-teal-700 ml-2")
            ui.button("Profilo", on_click=lambda: ui.navigate.to("/profile")).classes(
                "bg-blue-600 hover:bg-blue-700 ml-2"
            )

        # Main content with tabs
        with ui.tabs().classes("w-full bg-[#1a2730]") as tabs:
            stats_tab = ui.tab("Statistiche", icon="analytics")
            users_tab = ui.tab("Gestione Utenti", icon="people")
            audit_tab = ui.tab("Audit Log", icon="history")
            db_tab = ui.tab("Database", icon="storage")
            query_tab = ui.tab("Query SQL", icon="code")

        with ui.tab_panels(tabs, value=stats_tab).classes("w-full flex-grow bg-[#0b141a]"):
            # Statistics Panel
            with ui.tab_panel(stats_tab).classes("p-6"):
                await self._render_stats_panel()

            # Users Management Panel
            with ui.tab_panel(users_tab).classes("p-6"):
                await self._render_users_panel()

            # Audit Log Panel
            with ui.tab_panel(audit_tab).classes("p-6"):
                await self._render_audit_panel()

            # Database Panel
            with ui.tab_panel(db_tab).classes("p-6"):
                await self._render_database_panel()

            # Query Panel
            with ui.tab_panel(query_tab).classes("p-6"):
                await self._render_query_panel()

    async def _render_stats_panel(self):
        """Render statistics panel."""
        import httpx

        ui.label("Statistiche Sistema").classes("text-2xl font-bold text-white mb-6")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/admin/dashboard/stats",
                    headers=self._get_auth_headers(),
                )

                if response.status_code == 200:
                    self.stats = response.json()

                    with ui.row().classes("w-full gap-6 flex-wrap"):
                        # Stats cards
                        self._stat_card(
                            "Utenti Totali",
                            self.stats["total_users"],
                            "people",
                            "from-blue-500 to-blue-700",
                        )
                        self._stat_card(
                            "Utenti Attivi",
                            self.stats["active_users"],
                            "check_circle",
                            "from-green-500 to-green-700",
                        )
                        self._stat_card(
                            "Conversazioni",
                            self.stats["total_conversations"],
                            "chat",
                            "from-purple-500 to-purple-700",
                        )
                        self._stat_card(
                            "Messaggi",
                            self.stats["total_messages"],
                            "message",
                            "from-orange-500 to-orange-700",
                        )

                    # Users by role
                    ui.label("Utenti per Ruolo").classes("text-xl font-bold text-white mt-8 mb-4")
                    with ui.row().classes("gap-4"):
                        for role, count in self.stats.get("users_by_role", {}).items():
                            with ui.card().classes("bg-[#202c33] p-4"):
                                ui.label(role.upper()).classes("text-gray-400 text-sm")
                                ui.label(str(count)).classes("text-2xl font-bold text-white")

                else:
                    ui.label("Errore nel caricamento delle statistiche").classes("text-red-400")

        except Exception as e:
            ui.label(f"Errore: {str(e)}").classes("text-red-400")

    def _stat_card(self, title: str, value: int, icon: str, gradient: str):
        """Create a statistics card."""
        with ui.card().classes(f"w-48 p-4 bg-gradient-to-br {gradient} rounded-xl shadow-lg"):
            with ui.row().classes("items-center justify-between"):
                ui.icon(icon).classes("text-3xl text-white opacity-80")
                ui.label(str(value)).classes("text-3xl font-bold text-white")
            ui.label(title).classes("text-white text-sm mt-2 opacity-90")

    async def _render_users_panel(self):
        """Render users management panel."""

        ui.label("Gestione Utenti").classes("text-2xl font-bold text-white mb-6")

        # Search and add user row
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            self.search_input = (
                ui.input(label="🔍 Cerca utenti...", placeholder="Username, email o ruolo")
                .classes("flex-grow")
                .props("dark outlined color=teal dense")
            )
            ui.button("Cerca", on_click=self._load_users_table).classes("bg-teal-600 hover:bg-teal-700")
            ui.button("+ Nuovo Utente", on_click=self._show_add_user_dialog).classes("bg-teal-600 hover:bg-teal-700")

        # Users table container
        self.users_table_container = ui.column().classes("w-full")

        await self._load_users_table()

    async def _load_users_table(self):
        """Load and display users table."""
        import httpx

        self.users_table_container.clear()

        with self.users_table_container:
            try:
                # Build query params with search
                params = {"limit": 200}
                if self.search_input and self.search_input.value:
                    params["search"] = self.search_input.value

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "http://localhost:8000/api/v1/admin/users",
                        headers=self._get_auth_headers(),
                        params=params,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        users = data.get("users", data) if isinstance(data, dict) else data
                        total = data.get("total", len(users)) if isinstance(data, dict) else len(users)

                        ui.label(f"Totale: {total} utenti").classes("text-gray-400 text-sm mb-2")

                        columns = [
                            {"name": "id", "label": "ID", "field": "id", "align": "left"},
                            {"name": "username", "label": "Username", "field": "username", "align": "left"},
                            {"name": "email", "label": "Email", "field": "email", "align": "left"},
                            {"name": "role", "label": "Ruolo", "field": "role", "align": "left"},
                            {"name": "is_active", "label": "Attivo", "field": "is_active", "align": "center"},
                            {"name": "actions", "label": "Azioni", "field": "actions", "align": "center"},
                        ]

                        rows = [
                            {
                                "id": u["id"],
                                "username": u["username"],
                                "email": u["email"],
                                "role": u["role"],
                                "is_active": "✅" if u["is_active"] else "❌",
                            }
                            for u in users
                        ]

                        table = (
                            ui.table(columns=columns, rows=rows, row_key="id")
                            .classes("w-full bg-[#202c33]")
                            .props("dark flat")
                        )

                        # Add action buttons using slots
                        table.add_slot(
                            "body-cell-actions",
                            """
                            <q-td :props="props">
                                <q-btn flat round dense icon="edit" color="blue"
                                       @click="$parent.$emit('edit', props.row)" />
                                <q-btn flat round dense icon="delete" color="red"
                                       @click="$parent.$emit('delete', props.row)" />
                            </q-td>
                            """,
                        )

                        table.on("edit", lambda e: self._show_edit_user_dialog(e.args))
                        table.on("delete", lambda e: self._confirm_delete_user(e.args))

                    else:
                        ui.label("Errore nel caricamento degli utenti").classes("text-red-400")

            except Exception as e:
                ui.label(f"Errore: {str(e)}").classes("text-red-400")

    async def _show_add_user_dialog(self):
        """Show dialog to add a new user."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-6 bg-[#202c33]"):
            ui.label("Nuovo Utente").classes("text-xl font-bold text-white mb-4")

            username = ui.input("Username").classes("w-full mb-2").props("dark outlined")
            email = ui.input("Email").classes("w-full mb-2").props("dark outlined")
            password = ui.input("Password", password=True).classes("w-full mb-2").props("dark outlined")
            role = (
                ui.select(
                    ["user", "admin", "sysadmin"],
                    value="user",
                    label="Ruolo",
                )
                .classes("w-full mb-4")
                .props("dark outlined")
            )

            error_label = ui.label("").classes("text-red-400 text-sm")
            error_label.visible = False

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Annulla", on_click=dialog.close).classes("bg-gray-600")

                async def create_user():
                    import httpx

                    if not all([username.value, email.value, password.value]):
                        error_label.text = "Compila tutti i campi"
                        error_label.visible = True
                        return

                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                "http://localhost:8000/api/v1/admin/users",
                                headers=self._get_auth_headers(),
                                json={
                                    "username": username.value,
                                    "email": email.value,
                                    "password": password.value,
                                    "role": role.value,
                                },
                            )

                            if response.status_code == 201:
                                dialog.close()
                                await self._load_users_table()
                                ui.notify("Utente creato con successo", type="positive")
                            else:
                                try:
                                    error_data = response.json()
                                    if isinstance(error_data, dict):
                                        error = error_data.get("detail", error_data.get("message", str(error_data)))
                                        if isinstance(error, dict):
                                            error = error.get("message", str(error))
                                    else:
                                        error = str(error_data)
                                except Exception:
                                    error = f"Errore {response.status_code}"
                                error_label.text = str(error)
                                error_label.visible = True

                    except Exception as e:
                        error_label.text = str(e)
                        error_label.visible = True

                ui.button("Crea", on_click=create_user).classes("bg-teal-600")

        dialog.open()

    def _show_edit_user_dialog(self, user):
        """Show dialog to edit a user."""
        with ui.dialog() as dialog, ui.card().classes("w-96 p-6 bg-[#202c33]"):
            ui.label(f"Modifica Utente #{user['id']}").classes("text-xl font-bold text-white mb-4")

            username = ui.input("Username", value=user["username"]).classes("w-full mb-2").props("dark outlined")
            email = ui.input("Email", value=user["email"]).classes("w-full mb-2").props("dark outlined")
            password = (
                ui.input("Nuova Password (lascia vuoto per non cambiare)", password=True)
                .classes("w-full mb-2")
                .props("dark outlined")
            )
            role = (
                ui.select(
                    ["user", "admin", "sysadmin"],
                    value=user["role"],
                    label="Ruolo",
                )
                .classes("w-full mb-2")
                .props("dark outlined")
            )
            is_active = ui.checkbox("Attivo", value=user["is_active"] == "✅").classes("text-white mb-4")

            error_label = ui.label("").classes("text-red-400 text-sm")
            error_label.visible = False

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Annulla", on_click=dialog.close).classes("bg-gray-600")

                async def update_user():
                    import httpx

                    data = {
                        "username": username.value,
                        "email": email.value,
                        "role": role.value,
                        "is_active": is_active.value,
                    }
                    if password.value:
                        data["password"] = password.value

                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.put(
                                f"http://localhost:8000/api/v1/admin/users/{user['id']}",
                                headers=self._get_auth_headers(),
                                json=data,
                            )

                            if response.status_code == 200:
                                dialog.close()
                                await self._load_users_table()
                                ui.notify("Utente aggiornato con successo", type="positive")
                            else:
                                error = response.json().get("detail", "Errore")
                                error_label.text = error
                                error_label.visible = True

                    except Exception as e:
                        error_label.text = str(e)
                        error_label.visible = True

                ui.button("Salva", on_click=update_user).classes("bg-teal-600")

        dialog.open()

    def _confirm_delete_user(self, user):
        """Show confirmation dialog before deleting a user."""
        with ui.dialog() as dialog, ui.card().classes("p-6 bg-[#202c33]"):
            ui.label("Conferma Eliminazione").classes("text-xl font-bold text-white mb-4")
            ui.label(f"Sei sicuro di voler eliminare l'utente '{user['username']}'?").classes("text-gray-300 mb-4")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Annulla", on_click=dialog.close).classes("bg-gray-600")

                async def delete_user():
                    import httpx

                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.delete(
                                f"http://localhost:8000/api/v1/admin/users/{user['id']}",
                                headers=self._get_auth_headers(),
                            )

                            if response.status_code == 204:
                                dialog.close()
                                await self._load_users_table()
                                ui.notify("Utente eliminato", type="positive")
                            else:
                                error = response.json().get("detail", "Errore")
                                ui.notify(error, type="negative")

                    except Exception as e:
                        ui.notify(str(e), type="negative")

                ui.button("Elimina", on_click=delete_user).classes("bg-red-600")

        dialog.open()

    async def _render_audit_panel(self):
        """Render audit log panel."""
        import httpx

        ui.label("Audit Log").classes("text-2xl font-bold text-white mb-6")

        self.audit_container = ui.column().classes("w-full")

        with self.audit_container:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "http://localhost:8000/api/v1/admin/audit-logs",
                        headers=self._get_auth_headers(),
                        params={"limit": 100},
                    )

                    if response.status_code == 200:
                        data = response.json()
                        logs = data.get("logs", [])
                        total = data.get("total", 0)

                        ui.label(f"Totale: {total} eventi").classes("text-gray-400 text-sm mb-4")

                        if logs:
                            columns = [
                                {"name": "created_at", "label": "Data/Ora", "field": "created_at", "align": "left"},
                                {"name": "action", "label": "Azione", "field": "action", "align": "left"},
                                {"name": "username", "label": "Utente", "field": "username", "align": "left"},
                                {"name": "target_type", "label": "Tipo Target", "field": "target_type", "align": "left"},
                                {"name": "target_id", "label": "ID Target", "field": "target_id", "align": "center"},
                                {"name": "ip_address", "label": "IP", "field": "ip_address", "align": "left"},
                                {"name": "details", "label": "Dettagli", "field": "details", "align": "left"},
                            ]

                            rows = [
                                {
                                    "created_at": log["created_at"][:19].replace("T", " ") if log.get("created_at") else "",
                                    "action": log.get("action", ""),
                                    "username": log.get("username", "-"),
                                    "target_type": log.get("target_type", "-"),
                                    "target_id": str(log.get("target_id", "-")),
                                    "ip_address": log.get("ip_address", "-"),
                                    "details": (log.get("details", "") or "")[:80],
                                }
                                for log in logs
                            ]

                            ui.table(columns=columns, rows=rows).classes("w-full bg-[#202c33]").props(
                                "dark flat dense"
                            )
                        else:
                            ui.label("Nessun evento nel log").classes("text-gray-400")

                    else:
                        ui.label("Errore nel caricamento dei log").classes("text-red-400")

            except Exception as e:
                ui.label(f"Errore: {str(e)}").classes("text-red-400")

    async def _render_database_panel(self):
        """Render database explorer panel."""
        import httpx

        ui.label("Esplora Database").classes("text-2xl font-bold text-white mb-6")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/admin/database/tables",
                    headers=self._get_auth_headers(),
                )

                if response.status_code == 200:
                    tables = response.json()

                    with ui.row().classes("w-full gap-6"):
                        # Tables list
                        with ui.column().classes("w-64"):
                            ui.label("Tabelle").classes("text-lg font-bold text-white mb-4")

                            for table in tables:
                                with (
                                    ui.card()
                                    .classes("w-full p-4 bg-[#202c33] cursor-pointer hover:bg-[#2a3942] mb-2")
                                    .on("click", lambda t=table: self._show_table_data(t["name"]))
                                ):
                                    with ui.row().classes("items-center justify-between"):
                                        ui.icon("table_chart").classes("text-teal-400")
                                        ui.label(table["name"]).classes("text-white font-medium")
                                    ui.label(f"{table['row_count']} righe").classes("text-gray-400 text-sm")

                        # Table data container
                        self.table_data_container = ui.column().classes("flex-grow")
                        with self.table_data_container:
                            ui.label("Seleziona una tabella per visualizzare i dati").classes("text-gray-400")

                else:
                    ui.label("Errore nel caricamento delle tabelle").classes("text-red-400")

        except Exception as e:
            ui.label(f"Errore: {str(e)}").classes("text-red-400")

    async def _show_table_data(self, table_name: str):
        """Show data for a selected table."""
        import httpx

        self.table_data_container.clear()

        with self.table_data_container:
            ui.label(f"Tabella: {table_name}").classes("text-xl font-bold text-white mb-4")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:8000/api/v1/admin/database/tables/{table_name}",
                        headers=self._get_auth_headers(),
                        params={"limit": 100},
                    )

                    if response.status_code == 200:
                        result = response.json()
                        columns = result["columns"]
                        data = result["data"]

                        if data:
                            table_columns = [
                                {"name": col, "label": col, "field": col, "align": "left"} for col in columns
                            ]

                            # Convert data for display
                            rows = []
                            for row in data:
                                display_row = {}
                                for key, value in row.items():
                                    if isinstance(value, (dict, list)):
                                        display_row[key] = str(value)[:50] + "..."
                                    else:
                                        display_row[key] = str(value) if value is not None else "NULL"
                                rows.append(display_row)

                            ui.table(columns=table_columns, rows=rows).classes("w-full bg-[#202c33]").props(
                                "dark flat dense"
                            )
                        else:
                            ui.label("Nessun dato nella tabella").classes("text-gray-400")

                    else:
                        ui.label("Errore nel caricamento dei dati").classes("text-red-400")

            except Exception as e:
                ui.label(f"Errore: {str(e)}").classes("text-red-400")

    async def _render_query_panel(self):
        """Render SQL query panel."""
        ui.label("Query SQL").classes("text-2xl font-bold text-white mb-2")
        ui.label("⚠️ Attenzione: le query vengono eseguite direttamente sul database").classes(
            "text-orange-400 text-sm mb-6"
        )

        self.query_input = (
            ui.textarea(
                label="Query SQL",
                placeholder="SELECT * FROM users LIMIT 10;",
            )
            .classes("w-full mb-4")
            .props("dark outlined rows=6")
        )

        ui.button("Esegui Query", on_click=self._execute_query).classes("bg-teal-600 hover:bg-teal-700 mb-4")

        self.query_result_container = ui.column().classes("w-full")

    async def _execute_query(self):
        """Execute SQL query."""
        import httpx

        query = self.query_input.value.strip()
        if not query:
            ui.notify("Inserisci una query", type="warning")
            return

        self.query_result_container.clear()

        with self.query_result_container:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8000/api/v1/admin/database/query",
                        headers=self._get_auth_headers(),
                        json={"query": query},
                    )

                    result = response.json()

                    if result["success"]:
                        if result.get("data") is not None:
                            data = result["data"]
                            if data:
                                columns = list(data[0].keys())
                                table_columns = [
                                    {"name": col, "label": col, "field": col, "align": "left"} for col in columns
                                ]

                                rows = []
                                for row in data:
                                    display_row = {}
                                    for key, value in row.items():
                                        display_row[key] = str(value) if value is not None else "NULL"
                                    rows.append(display_row)

                                ui.label(f"Risultato: {len(data)} righe").classes("text-green-400 mb-2")
                                ui.table(columns=table_columns, rows=rows).classes("w-full bg-[#202c33]").props(
                                    "dark flat dense"
                                )
                            else:
                                ui.label("Query eseguita, nessun risultato").classes("text-green-400")
                        else:
                            ui.label(
                                f"Query eseguita con successo. Righe modificate: {result.get('affected_rows', 0)}"
                            ).classes("text-green-400")
                    else:
                        ui.label(f"Errore: {result.get('error')}").classes("text-red-400")

            except Exception as e:
                ui.label(f"Errore: {str(e)}").classes("text-red-400")

    async def _logout(self):
        """Logout user with server-side token blacklisting."""
        import httpx

        try:
            token = app.storage.user.get("access_token", "")
            if token:
                async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                    await client.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": f"Bearer {token}"},
                    )
        except Exception:
            pass
        app.storage.user.clear()
        ui.navigate.to("/login")
