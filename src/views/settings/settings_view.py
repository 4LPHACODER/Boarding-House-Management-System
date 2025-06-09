import flet as ft
from flet_core import colors
import mysql.connector
from mysql.connector import Error
import bcrypt

class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        self.setup_ui()
        
        # Load user data if logged in
        current_user = self.page.client_storage.get("current_user")
        if current_user:
            self.load_user_data(current_user)
        else:
            self.page.go("/login")

    def setup_ui(self):
        # Create form fields
        self.username_field = ft.TextField(
            label="Username",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            prefix_icon=ft.Icons.PERSON,
            read_only=True
        )
        self.email_field = ft.TextField(
            label="Email",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            prefix_icon=ft.Icons.EMAIL
        )
        self.first_name_field = ft.TextField(
            label="First Name",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            prefix_icon=ft.Icons.PERSON_OUTLINE
        )
        self.last_name_field = ft.TextField(
            label="Last Name",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            prefix_icon=ft.Icons.PERSON_OUTLINE
        )
        self.phone_field = ft.TextField(
            label="Phone Number",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            prefix_icon=ft.Icons.PHONE
        )
        self.current_password_field = ft.TextField(
            label="Current Password",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )
        self.new_password_field = ft.TextField(
            label="New Password",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )
        self.confirm_password_field = ft.TextField(
            label="Confirm New Password",
            border=ft.InputBorder.UNDERLINE,
            width=400,
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK
        )

        # Create buttons
        self.save_button = ft.ElevatedButton(
            "Save Changes",
            width=400,
            height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE,
            ),
            on_click=self.save_changes
        )
        
        self.logout_button = ft.ElevatedButton(
            "Logout",
            width=400,
            height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED,
            ),
            on_click=self.handle_logout
        )

        # Create the main container with scrolling
        self.main_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Settings", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Manage your account settings", size=16, color=ft.Colors.GREY_700),
                    ft.Divider(),
                    ft.Text("Profile Information", size=20, weight=ft.FontWeight.BOLD),
                    self.username_field,
                    self.email_field,
                    self.first_name_field,
                    self.last_name_field,
                    self.phone_field,
                    ft.Divider(),
                    ft.Text("Change Password", size=20, weight=ft.FontWeight.BOLD),
                    self.current_password_field,
                    self.new_password_field,
                    self.confirm_password_field,
                    self.save_button,
                    ft.Divider(),
                    self.logout_button
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.all(50),
            expand=True
        )

    def get_db_connection(self):
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="H4ckm3!_",
            database="boarding_house"
        )

    def load_user_data(self, username):
        connection = None
        cursor = None
        try:
            connection = self.get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT username, email, first_name, last_name, phone_number FROM landlords WHERE username = %s",
                (username,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                self.current_user = username
                self.username_field.value = user_data[0]
                self.email_field.value = user_data[1]
                self.first_name_field.value = user_data[2]
                self.last_name_field.value = user_data[3]
                self.phone_field.value = user_data[4] if user_data[4] else ""
                self.page.update()
            
        except Error as e:
            self.show_error(f"Error loading user data: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def save_changes(self, e):
        connection = None
        cursor = None
        try:
            if not self.current_user:
                self.show_error("No user is currently logged in")
                return

            # Get form values
            email = self.email_field.value
            first_name = self.first_name_field.value
            last_name = self.last_name_field.value
            phone = self.phone_field.value
            current_password = self.current_password_field.value
            new_password = self.new_password_field.value
            confirm_password = self.confirm_password_field.value

            # Validate required fields
            if not all([email, first_name, last_name]):
                self.show_error("Email, first name, and last name are required")
                return

            connection = self.get_db_connection()
            cursor = connection.cursor()

            # If changing password
            if current_password and new_password:
                if new_password != confirm_password:
                    self.show_error("New passwords do not match")
                    return

                # Verify current password
                cursor.execute(
                    "SELECT password_hash FROM landlords WHERE username = %s",
                    (self.current_user,)
                )
                result = cursor.fetchone()
                
                if not result or not bcrypt.checkpw(current_password.encode('utf-8'), result[0].encode('utf-8')):
                    self.show_error("Current password is incorrect")
                    return

                # Update password
                password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    """
                    UPDATE landlords 
                    SET email = %s, first_name = %s, last_name = %s, phone_number = %s, password_hash = %s
                    WHERE username = %s
                    """,
                    (email, first_name, last_name, phone, password_hash, self.current_user)
                )
            else:
                # Update without changing password
                cursor.execute(
                    """
                    UPDATE landlords 
                    SET email = %s, first_name = %s, last_name = %s, phone_number = %s
                    WHERE username = %s
                    """,
                    (email, first_name, last_name, phone, self.current_user)
                )

            connection.commit()
            self.show_success("Profile updated successfully")
            
            # Clear password fields
            self.current_password_field.value = ""
            self.new_password_field.value = ""
            self.confirm_password_field.value = ""
            self.page.update()

        except Error as e:
            self.show_error(f"Error updating profile: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def handle_logout(self, e):
        # Clear user data from client storage
        self.page.client_storage.remove("current_user")
        self.current_user = None
        self.page.go("/login")

    def show_error(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_success(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()

    def build(self):
        return self.main_container 