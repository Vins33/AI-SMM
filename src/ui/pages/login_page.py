# src/ui/pages/login_page.py
"""Login page for user authentication."""

from nicegui import app, ui


class LoginPage:
    """Login page component."""

    def __init__(self, on_login_success=None, is_dark: bool = True):
        self.on_login_success = on_login_success
        self.is_dark = is_dark
        self.username_input = None
        self.password_input = None
        self.error_label = None

    async def render(self):
        """Render the login page."""
        if self.is_dark:
            ui.dark_mode(True)

        ui.add_head_html(
            """
            <style>
                body { margin: 0; padding: 0; background-color: #0b141a; }
                .nicegui-content { height: 100vh; display: flex; justify-content: center; align-items: center; }
            </style>
            """
        )

        with ui.card().classes("w-96 p-8 bg-[#202c33] rounded-2xl shadow-2xl"):
            # Logo/Title
            with ui.row().classes("w-full justify-center mb-6"):
                with ui.element("div").classes(
                    "w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-teal-600 "
                    "flex items-center justify-center"
                ):
                    ui.icon("smart_toy").classes("text-white text-3xl")

            ui.label("Financial Agent").classes(
                "text-2xl font-bold text-white text-center w-full mb-2"
            )
            ui.label("Accedi al tuo account").classes(
                "text-gray-400 text-center w-full mb-6"
            )

            # Error message
            self.error_label = ui.label("").classes(
                "text-red-400 text-sm text-center w-full mb-4"
            )
            self.error_label.visible = False

            # Username
            self.username_input = (
                ui.input(label="Username", placeholder="Inserisci username")
                .classes("w-full mb-4")
                .props("dark outlined color=teal")
            )

            # Password
            self.password_input = (
                ui.input(
                    label="Password", placeholder="Inserisci password", password=True
                )
                .classes("w-full mb-6")
                .props("dark outlined color=teal")
            )

            # Login button
            ui.button("Accedi", on_click=self._on_login).classes(
                "w-full bg-gradient-to-r from-green-500 to-teal-600 text-white py-3 "
                "rounded-lg font-semibold hover:from-green-600 hover:to-teal-700"
            )

            # Register link
            with ui.row().classes("w-full justify-center mt-4"):
                ui.label("Non hai un account?").classes("text-gray-400 text-sm")
                ui.link("Registrati", "/register").classes(
                    "text-teal-400 text-sm ml-1 hover:underline"
                )

    async def _on_login(self):
        """Handle login attempt."""
        import httpx

        username = self.username_input.value
        password = self.password_input.value

        if not username or not password:
            self.error_label.text = "Inserisci username e password"
            self.error_label.visible = True
            return

        try:
            async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                response = await client.post(
                    "/api/v1/auth/login",
                    data={"username": username, "password": password},
                )

                if response.status_code == 200:
                    data = response.json()
                    # Store tokens in app storage
                    app.storage.user["access_token"] = data["access_token"]
                    app.storage.user["refresh_token"] = data["refresh_token"]
                    app.storage.user["username"] = username

                    # Get user info
                    user_response = await client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        app.storage.user["role"] = user_data["role"]
                        app.storage.user["user_id"] = user_data["id"]

                    if self.on_login_success:
                        await self.on_login_success()
                    else:
                        # Redirect based on role with small delay to ensure storage sync
                        role = app.storage.user.get("role", "user")
                        if role == "sysadmin":
                            await ui.run_javascript('setTimeout(() => { window.location.href = "/admin"; }, 100);')
                        else:
                            await ui.run_javascript('setTimeout(() => { window.location.href = "/"; }, 100);')
                else:
                    self.error_label.text = "Username o password errati"
                    self.error_label.visible = True

        except Exception as e:
            self.error_label.text = f"Errore di connessione: {str(e)}"
            self.error_label.visible = True


class RegisterPage:
    """Registration page component."""

    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.username_input = None
        self.email_input = None
        self.password_input = None
        self.password_confirm_input = None
        self.error_label = None
        self.success_label = None

    async def render(self):
        """Render the registration page."""
        if self.is_dark:
            ui.dark_mode(True)

        ui.add_head_html(
            """
            <style>
                body { margin: 0; padding: 0; background-color: #0b141a; }
                .nicegui-content { height: 100vh; display: flex; justify-content: center; align-items: center; }
            </style>
            """
        )

        with ui.card().classes("w-96 p-8 bg-[#202c33] rounded-2xl shadow-2xl"):
            # Logo/Title
            with ui.row().classes("w-full justify-center mb-6"):
                with ui.element("div").classes(
                    "w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-teal-600 "
                    "flex items-center justify-center"
                ):
                    ui.icon("person_add").classes("text-white text-3xl")

            ui.label("Registrazione").classes(
                "text-2xl font-bold text-white text-center w-full mb-2"
            )
            ui.label("Crea un nuovo account").classes(
                "text-gray-400 text-center w-full mb-6"
            )

            # Error message
            self.error_label = ui.label("").classes(
                "text-red-400 text-sm text-center w-full mb-4"
            )
            self.error_label.visible = False

            # Success message
            self.success_label = ui.label("").classes(
                "text-green-400 text-sm text-center w-full mb-4"
            )
            self.success_label.visible = False

            # Username
            self.username_input = (
                ui.input(label="Username", placeholder="Scegli un username")
                .classes("w-full mb-4")
                .props("dark outlined color=teal")
            )

            # Email
            self.email_input = (
                ui.input(label="Email", placeholder="La tua email")
                .classes("w-full mb-4")
                .props("dark outlined color=teal")
            )

            # Password
            self.password_input = (
                ui.input(
                    label="Password", placeholder="Scegli una password", password=True
                )
                .classes("w-full mb-4")
                .props("dark outlined color=teal")
            )

            # Confirm Password
            self.password_confirm_input = (
                ui.input(
                    label="Conferma Password",
                    placeholder="Ripeti la password",
                    password=True,
                )
                .classes("w-full mb-6")
                .props("dark outlined color=teal")
            )

            # Register button
            ui.button("Registrati", on_click=self._on_register).classes(
                "w-full bg-gradient-to-r from-green-500 to-teal-600 text-white py-3 "
                "rounded-lg font-semibold hover:from-green-600 hover:to-teal-700"
            )

            # Login link
            with ui.row().classes("w-full justify-center mt-4"):
                ui.label("Hai già un account?").classes("text-gray-400 text-sm")
                ui.link("Accedi", "/login").classes(
                    "text-teal-400 text-sm ml-1 hover:underline"
                )

    async def _on_register(self):
        """Handle registration attempt."""
        import httpx

        username = self.username_input.value
        email = self.email_input.value
        password = self.password_input.value
        password_confirm = self.password_confirm_input.value

        self.error_label.visible = False
        self.success_label.visible = False

        if not all([username, email, password, password_confirm]):
            self.error_label.text = "Compila tutti i campi"
            self.error_label.visible = True
            return

        if password != password_confirm:
            self.error_label.text = "Le password non corrispondono"
            self.error_label.visible = True
            return

        if len(password) < 8:
            self.error_label.text = "La password deve avere almeno 8 caratteri"
            self.error_label.visible = True
            return

        try:
            async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                response = await client.post(
                    "/api/v1/auth/register",
                    json={"username": username, "email": email, "password": password},
                )

                if response.status_code == 200:
                    self.success_label.text = "Registrazione completata! Ora puoi accedere."
                    self.success_label.visible = True
                    # Clear inputs
                    self.username_input.value = ""
                    self.email_input.value = ""
                    self.password_input.value = ""
                    self.password_confirm_input.value = ""
                else:
                    error_data = response.json()
                    self.error_label.text = error_data.get("detail", "Errore durante la registrazione")
                    self.error_label.visible = True

        except Exception as e:
            self.error_label.text = f"Errore di connessione: {str(e)}"
            self.error_label.visible = True
