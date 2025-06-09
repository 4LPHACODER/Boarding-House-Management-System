import flet as ft
import bcrypt
import mysql.connector
from mysql.connector import Error
from pathlib import Path

class LoginPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_ui()

    def setup_ui(self):
        # Create the main container
        self.main_container = ft.Container(
            content=ft.Row(
                [
                    # Left side - Logo
                    ft.Container(
                        content=ft.Image(
                            src=f"src/assets/images/System_Logo.png",
                            width=600,
                            height=600,
                            fit=ft.ImageFit.CONTAIN,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                    # Right side - Login form
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Welcome Back!", size=32, weight=ft.FontWeight.BOLD),
                                ft.Text("Please login to your account", size=16, color=ft.Colors.GREY_700),
                                ft.TextField(
                                    label="Username",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.PERSON,
                                ),
                                ft.TextField(
                                    label="Password",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    password=True,
                                    can_reveal_password=True,
                                    prefix_icon=ft.Icons.LOCK,
                                ),
                                ft.ElevatedButton(
                                    "Login",
                                    width=400,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.BLUE,
                                    ),
                                    on_click=self.handle_login,
                                ),
                                ft.TextButton(
                                    "Don't have an account? Sign up",
                                    on_click=lambda _: self.page.go("/signup"),
                                ),
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(50),
                        expand=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
        )

    def handle_login(self, e):
        # Get the username and password from the text fields
        username = self.main_container.content.controls[1].content.controls[2].value
        password = self.main_container.content.controls[1].content.controls[3].value

        try:
            # Connect to the database
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="H4ckm3!_",
                database="boarding_house"
            )

            if connection.is_connected():
                cursor = connection.cursor()
                # Check if the user exists
                cursor.execute("SELECT id, password_hash FROM landlords WHERE username = %s", (username,))
                result = cursor.fetchone()

                if result and bcrypt.checkpw(password.encode('utf-8'), result[1].encode('utf-8')):
                    # Store username in page client storage
                    self.page.client_storage.set("current_user", username)
                    
                    # Login successful
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Login successful!"))
                    self.page.snack_bar.open = True
                    self.page.update()
                    self.page.go("/rooms")  # Redirect to dashboard
                else:
                    # Login failed
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Invalid username or password"))
                    self.page.snack_bar.open = True
                    self.page.update()

        except Error as e:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def get_content(self):
        return self.main_container 