import flet as ft
from flet_core import colors
from src.models.database import Database
import os
import shutil
from datetime import datetime

class TenantsView:
    def __init__(self, page: ft.Page):
        print("Initializing TenantsView")
        self.page = page
        self.db = Database()
        
        # Add search field
        self.search_field = ft.TextField(
            label="Search tenants...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filter_tenants,
            expand=True,
            color=colors.WHITE
        )
        
        # Add status filter
        self.status_filter = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Checked Out")
            ],
            value="All",
            on_change=self.filter_tenants,
            width=150,
            color=colors.WHITE
        )
        
        self.tenants_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Profile", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Contact", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Room", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Check-in", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Check-out", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
            ],
            rows=[],
            border=ft.border.all(1, colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.all(1, colors.OUTLINE),
            horizontal_lines=ft.border.all(1, colors.OUTLINE),
            sort_ascending=True,
            sort_column_index=1,
            heading_row_color=colors.SURFACE_VARIANT,
            heading_row_height=70,
            data_row_color={"hovered": "0x30FF0000"},
            show_checkbox_column=True,
        )
        
        # Initialize file picker
        self.file_picker = ft.FilePicker(
            on_result=self.handle_file_picker_result
        )
        self.page.overlay.append(self.file_picker)
        print("TenantsView initialized")
        self.refresh_tenants()

    def __del__(self):
        """Cleanup when the view is destroyed"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")

    def handle_file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            try:
                # Get the selected file
                selected_file = e.files[0]
                
                # Ensure the tenants directory exists
                os.makedirs("src/assets/images/tenants", exist_ok=True)
                
                # Create a new filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_image_path = f"src/assets/images/tenants/profile_{timestamp}.png"
                
                # Copy the selected file to our application directory
                shutil.copy(selected_file.path, new_image_path)
                
                # Update the current profile image
                if hasattr(self, 'current_profile_image'):
                    self.current_profile_image.src = new_image_path
                    self.current_profile_image_path = new_image_path
                    self.page.update()
            except Exception as e:
                print(f"Error handling file picker result: {e}")
                self.show_error("Error handling selected image")

    def show_error(self, message: str):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def filter_tenants(self, e):
        search_term = self.search_field.value.lower()
        status_filter = self.status_filter.value
        
        for row in self.tenants_table.rows:
            tenant_name = f"{row.cells[1].content.value}".lower()
            tenant_status = row.cells[7].content.value
            
            name_match = search_term in tenant_name
            status_match = status_filter == "All" or tenant_status == status_filter
            
            row.visible = name_match and status_match
        
        self.page.update()

    def refresh_tenants(self):
        print("Refreshing tenants")
        try:
            self.tenants_table.rows.clear()
            tenants = self.db.fetch_all("""
                SELECT t.*, r.room_number 
                FROM tenants t 
                LEFT JOIN rooms r ON t.room_id = r.room_id
            """)
            print(f"Fetched tenants: {tenants}")
            for tenant in tenants:
                # Create buttons with proper event binding
                edit_button = ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=colors.BLUE,
                    tooltip="Edit",
                    data=tenant,
                    on_click=lambda e: self.edit_tenant(e.control.data)
                )
                
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=colors.RED,
                    tooltip="Delete",
                    data=tenant,
                    on_click=lambda e: self.delete_tenant(e.control.data)
                )

                # Handle profile image
                profile_image = tenant[8] if tenant[8] else "src/assets/images/default_profile.png"
                if not os.path.exists(profile_image):
                    profile_image = "src/assets/images/default_profile.png"
                
                # Determine tenant status
                check_out_date = tenant[6]
                current_date = datetime.now().date()
                status = "Active"
                status_color = colors.GREEN
                
                if check_out_date:
                    check_out_date = datetime.strptime(str(check_out_date), "%Y-%m-%d").date()
                    if check_out_date < current_date:
                        status = "Checked Out"
                        status_color = colors.RED
                
                self.tenants_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Image(
                                    src=profile_image,
                                    width=40,
                                    height=40,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=20
                                )
                            ),
                            ft.DataCell(ft.Text(f"{tenant[1] or ''} {tenant[2] or ''}")),
                            ft.DataCell(ft.Text(tenant[3] or "")),
                            ft.DataCell(ft.Text(tenant[4] or "")),
                            ft.DataCell(ft.Text(tenant[9] or "")),
                            ft.DataCell(ft.Text(str(tenant[5] or ""))),
                            ft.DataCell(ft.Text(str(tenant[6] or ""))),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(status),
                                    bgcolor=status_color,
                                    padding=5,
                                    border_radius=5
                                )
                            ),
                            ft.DataCell(
                                ft.Row(
                                    controls=[edit_button, delete_button],
                                    spacing=0
                                )
                            )
                        ]
                    )
                )
            if hasattr(self, 'page') and self.page is not None:
                print("Updating page after tenant refresh")
                self.page.update()
        except Exception as e:
            print(f"Error refreshing tenants: {e}")
            self.show_error(f"Error refreshing tenants: {str(e)}")

    def add_tenant(self, e):
        print("Opening add tenant page")
        # Create form fields
        first_name_field = ft.TextField(label="First Name", autofocus=True)
        last_name_field = ft.TextField(label="Last Name")
        contact_field = ft.TextField(label="Contact Number")
        email_field = ft.TextField(label="Email")
        check_in_field = ft.TextField(label="Check-in Date (YYYY-MM-DD)")
        check_out_field = ft.TextField(label="Check-out Date (YYYY-MM-DD)")
        
        # Profile image picker
        self.current_profile_image_path = None
        self.current_profile_image = ft.Image(
            src="src/assets/images/default_profile.png",
            width=100,
            height=100,
            fit=ft.ImageFit.COVER,
            border_radius=50
        )

        def pick_image(e):
            self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["png", "jpg", "jpeg"],
                dialog_title="Select Profile Image"
            )

        # Get available rooms
        rooms = self.db.fetch_all("SELECT room_id, room_number FROM rooms WHERE status = 'Available'")
        room_dropdown = ft.Dropdown(
            label="Room",
            options=[ft.dropdown.Option(str(r[0]), r[1]) for r in rooms] if rooms else []
        )

        def save_tenant(e):
            try:
                first_name = first_name_field.value
                last_name = last_name_field.value
                contact_number = contact_field.value
                email = email_field.value
                room_id = room_dropdown.value
                check_in_date = check_in_field.value
                check_out_date = check_out_field.value

                print(f"Adding tenant: {first_name}, {last_name}, {contact_number}, {email}, {room_id}, {check_in_date}, {check_out_date}")

                if not first_name or not last_name:
                    self.show_error("First name and last name are required")
                    return

                # Check room capacity
                if room_id:
                    room = self.db.fetch_one("SELECT capacity FROM rooms WHERE room_id = %s", (room_id,))
                    current_tenants = self.db.fetch_one(
                        "SELECT COUNT(*) FROM tenants WHERE room_id = %s",
                        (room_id,)
                    )
                    if room and current_tenants and current_tenants[0] >= room[0]:
                        self.show_error("Room is at full capacity")
                        return

                self.db.insert(
                    """
                    INSERT INTO tenants 
                    (first_name, last_name, contact_number, email, room_id, check_in_date, check_out_date, profile_image) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (first_name, last_name, contact_number, email, room_id, check_in_date, check_out_date, self.current_profile_image_path)
                )
                
                # Return to tenants list
                self.page.go("/tenants")
                self.refresh_tenants()
            except Exception as e:
                print(f"Error adding tenant: {e}")
                self.show_error(f"Error adding tenant: {str(e)}")

        # Create the add tenant page
        add_tenant_page = ft.View(
            "/tenants/add",
            [
                ft.AppBar(
                    title=ft.Text("Add New Tenant"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/tenants")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Add New Tenant", size=30, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    self.current_profile_image,
                                    ft.ElevatedButton(
                                        "Pick Profile Image",
                                        icon=ft.Icons.IMAGE,
                                        on_click=pick_image
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=20
                            ),
                            first_name_field,
                            last_name_field,
                            contact_field,
                            email_field,
                            room_dropdown,
                            check_in_field,
                            check_out_field,
                            ft.ElevatedButton(
                                "Save Tenant",
                                icon=ft.Icons.SAVE,
                                on_click=save_tenant
                            )
                        ],
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=20,
                    expand=True
                )
            ]
        )

        # Add the route and navigate to it
        self.page.views.append(add_tenant_page)
        self.page.go("/tenants/add")

    def edit_tenant(self, tenant):
        print(f"Opening edit tenant page for tenant: {tenant[1]} {tenant[2]}")
        # Create form fields
        first_name_field = ft.TextField(label="First Name", value=tenant[1] or "")
        last_name_field = ft.TextField(label="Last Name", value=tenant[2] or "")
        contact_field = ft.TextField(label="Contact Number", value=tenant[3] or "")
        email_field = ft.TextField(label="Email", value=tenant[4] or "")
        check_in_field = ft.TextField(label="Check-in Date (YYYY-MM-DD)", value=str(tenant[5] or ""))
        check_out_field = ft.TextField(label="Check-out Date (YYYY-MM-DD)", value=str(tenant[6] or ""))

        # Profile image
        self.current_profile_image_path = tenant[8] if tenant[8] else "src/assets/images/default_profile.png"
        self.current_profile_image = ft.Image(
            src=self.current_profile_image_path,
            width=100,
            height=100,
            fit=ft.ImageFit.COVER,
            border_radius=50
        )

        def pick_image(e):
            self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["png", "jpg", "jpeg"],
                dialog_title="Select Profile Image"
            )

        # Get available rooms and current room
        rooms = self.db.fetch_all("""
            SELECT room_id, room_number 
            FROM rooms 
            WHERE status = 'Available' OR room_id = %s
        """, (tenant[5],))
        room_dropdown = ft.Dropdown(
            label="Room",
            options=[ft.dropdown.Option(str(r[0]), r[1]) for r in rooms] if rooms else [],
            value=str(tenant[5]) if tenant[5] else None
        )

        def save_changes(e):
            try:
                first_name = first_name_field.value
                last_name = last_name_field.value
                contact_number = contact_field.value
                email = email_field.value
                room_id = room_dropdown.value
                check_in_date = check_in_field.value
                check_out_date = check_out_field.value

                print(f"Updating tenant: {first_name}, {last_name}, {contact_number}, {email}, {room_id}, {check_in_date}, {check_out_date}")

                if not first_name or not last_name:
                    self.show_error("First name and last name are required")
                    return

                # Check room capacity if room is changed
                if room_id and room_id != tenant[5]:  # tenant[5] is the current room_id
                    room = self.db.fetch_one("SELECT capacity FROM rooms WHERE room_id = %s", (room_id,))
                    current_tenants = self.db.fetch_one(
                        "SELECT COUNT(*) FROM tenants WHERE room_id = %s",
                        (room_id,)
                    )
                    if room and current_tenants and current_tenants[0] >= room[0]:
                        self.show_error("Room is at full capacity")
                        return

                self.db.update(
                    """
                    UPDATE tenants 
                    SET first_name = %s, last_name = %s, contact_number = %s, 
                        email = %s, room_id = %s, check_in_date = %s, check_out_date = %s,
                        profile_image = %s
                    WHERE tenant_id = %s
                    """,
                    (first_name, last_name, contact_number, email, room_id, 
                     check_in_date, check_out_date, self.current_profile_image_path, tenant[0])
                )
                
                # Return to tenants list
                self.page.go("/tenants")
                self.refresh_tenants()
            except Exception as e:
                print(f"Error updating tenant: {e}")
                self.show_error(f"Error updating tenant: {str(e)}")

        # Create the edit tenant page
        edit_tenant_page = ft.View(
            f"/tenants/edit/{tenant[0]}",
            [
                ft.AppBar(
                    title=ft.Text("Edit Tenant"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/tenants")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Edit Tenant", size=30, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    self.current_profile_image,
                                    ft.ElevatedButton(
                                        "Change Profile Image",
                                        icon=ft.Icons.IMAGE,
                                        on_click=pick_image
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=20
                            ),
                            first_name_field,
                            last_name_field,
                            contact_field,
                            email_field,
                            room_dropdown,
                            check_in_field,
                            check_out_field,
                            ft.ElevatedButton(
                                "Save Changes",
                                icon=ft.Icons.SAVE,
                                on_click=save_changes
                            )
                        ],
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=20,
                    expand=True
                )
            ]
        )

        # Add the route and navigate to it
        self.page.views.append(edit_tenant_page)
        self.page.go(f"/tenants/edit/{tenant[0]}")

    def delete_tenant(self, tenant):
        print(f"Opening delete tenant page for tenant: {tenant[1]} {tenant[2]}")
        
        def confirm_delete(e):
            try:
                print(f"Deleting tenant: {tenant[0]}")
                # Delete profile image if it exists
                if tenant[8] and os.path.exists(tenant[8]):
                    os.remove(tenant[8])
                self.db.delete("DELETE FROM tenants WHERE tenant_id = %s", (tenant[0],))
                self.page.go("/tenants")
                self.refresh_tenants()
            except Exception as e:
                print(f"Error deleting tenant: {e}")
                self.show_error(f"Error deleting tenant: {str(e)}")
                self.page.go("/tenants")

        # Create the delete confirmation page
        delete_page = ft.View(
            f"/tenants/delete/{tenant[0]}",
            [
                ft.AppBar(
                    title=ft.Text("Delete Tenant"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/tenants")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Delete Tenant", size=30, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Are you sure you want to delete {tenant[1]} {tenant[2]}?", size=16),
                            ft.Text("This action cannot be undone.", color=colors.RED),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Cancel",
                                        icon=ft.Icons.CANCEL,
                                        on_click=lambda _: self.page.go("/tenants")
                                    ),
                                    ft.ElevatedButton(
                                        "Delete",
                                        icon=ft.Icons.DELETE,
                                        color=colors.RED,
                                        on_click=confirm_delete
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END,
                                spacing=20
                            )
                        ],
                        spacing=20,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=20,
                    expand=True
                )
            ]
        )

        # Add the route and navigate to it
        self.page.views.append(delete_page)
        self.page.go(f"/tenants/delete/{tenant[0]}")

    def build(self):
        print("Building TenantsView")
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Tenants Management", size=30, weight=ft.FontWeight.BOLD),
                                    ft.ElevatedButton(
                                        "Add Tenant",
                                        icon=ft.Icons.ADD,
                                        on_click=self.add_tenant,
                                        style=ft.ButtonStyle(
                                            color=colors.BLACK,
                                            bgcolor=colors.BLUE,
                                        )
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Row(
                                controls=[
                                    self.search_field,
                                    self.status_filter
                                ],
                                spacing=20
                            ),
                            ft.Container(
                                content=self.tenants_table,
                                padding=10,
                                border_radius=10,
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=15,
                                    color=colors.BLACK45,
                                )
                            )
                        ],
                        spacing=20
                    ),
                    padding=20,
                    expand=True
                )
            ],
            spacing=20,
            expand=True
        ) 