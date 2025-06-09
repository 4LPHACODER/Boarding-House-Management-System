import flet as ft
import bcrypt
import mysql.connector
from mysql.connector import Error
from pathlib import Path

class SignupPage:
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
                    # Right side - Signup form
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Create Account", size=32, weight=ft.FontWeight.BOLD),
                                ft.Text("Please fill in the details to create your account", size=16, color=ft.Colors.GREY_700),
                                ft.TextField(
                                    label="Username",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.PERSON,
                                ),
                                ft.TextField(
                                    label="Email",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.EMAIL,
                                ),
                                ft.TextField(
                                    label="First Name",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.PERSON_OUTLINE,
                                ),
                                ft.TextField(
                                    label="Last Name",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.PERSON_OUTLINE,
                                ),
                                ft.TextField(
                                    label="Phone Number",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    prefix_icon=ft.Icons.PHONE,
                                ),
                                ft.TextField(
                                    label="Password",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    password=True,
                                    can_reveal_password=True,
                                    prefix_icon=ft.Icons.LOCK,
                                ),
                                ft.TextField(
                                    label="Confirm Password",
                                    border=ft.InputBorder.UNDERLINE,
                                    width=400,
                                    password=True,
                                    can_reveal_password=True,
                                    prefix_icon=ft.Icons.LOCK,
                                ),
                                ft.ElevatedButton(
                                    "Sign Up",
                                    width=400,
                                    height=50,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.BLUE,
                                    ),
                                    on_click=self.handle_signup,
                                ),
                                ft.TextButton(
                                    "Already have an account? Login",
                                    on_click=lambda _: self.page.go("/login"),
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

    def handle_signup(self, e):
        # Get all the form fields
        form = self.main_container.content.controls[1].content.controls
        username = form[2].value
        email = form[3].value
        first_name = form[4].value
        last_name = form[5].value
        phone_number = form[6].value
        password = form[7].value
        confirm_password = form[8].value

        # Validate form
        if not all([username, email, first_name, last_name, password, confirm_password]):
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please fill in all required fields"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        if password != confirm_password:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Passwords do not match"))
            self.page.snack_bar.open = True
            self.page.update()
            return

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
                
                # Check if username or email already exists
                cursor.execute("SELECT id FROM landlords WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    self.page.snack_bar = ft.SnackBar(content=ft.Text("Username or email already exists"))
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                # Hash the password
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # Insert the new landlord
                cursor.execute("""
                    INSERT INTO landlords (username, email, password_hash, first_name, last_name, phone_number)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, email, password_hash, first_name, last_name, phone_number))
                
                connection.commit()
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Account created successfully!"))
                self.page.snack_bar.open = True
                self.page.update()
                self.page.go("/login")  # Redirect to login page

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