import flet as ft
from flet_core import colors
from src.models.database import Database
from decimal import Decimal

class RoomsView:
    def __init__(self, page: ft.Page):
        print("Initializing RoomsView")
        self.page = page
        self.db = Database()
        
        # Add search field
        self.search_field = ft.TextField(
            label="Search rooms",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.filter_rooms,
            expand=True,
            color=colors.WHITE
        )
        
        # Add status filter
        self.status_filter = ft.Dropdown(
            label="Filter by Status",
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance")
            ],
            value="All",
            on_change=self.filter_rooms,
            width=200,
            color=colors.WHITE
        )
        
        self.rooms_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Room Number", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Capacity", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Price", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD, color=colors.WHITE)),
            ],
            rows=[],
            border=ft.border.all(1, colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.all(1, colors.OUTLINE),
            horizontal_lines=ft.border.all(1, colors.OUTLINE),
            column_spacing=50,
            heading_row_color=colors.SURFACE_VARIANT,
            heading_row_height=70,
            data_row_color={"hovered": "0x30FF0000"},
            show_checkbox_column=False,
        )
        print("RoomsView initialized")
        self.refresh_rooms()

    def show_error(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=colors.ERROR,
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()

    def filter_rooms(self, e=None):
        search_term = self.search_field.value.lower() if self.search_field.value else ""
        status_filter = self.status_filter.value
        
        for row in self.rooms_table.rows:
            room_number = row.cells[0].content.value.lower()
            status = row.cells[3].content.value
            
            show_by_search = search_term in room_number
            show_by_status = status_filter == "All" or status == status_filter
            
            row.visible = show_by_search and show_by_status
        
        self.page.update()

    def refresh_rooms(self):
        print("Refreshing rooms")
        try:
            self.rooms_table.rows.clear()
            rooms = self.db.fetch_all("SELECT * FROM rooms")
            print(f"Fetched rooms: {rooms}")
            for room in rooms:
                # Create status badge with appropriate color
                status_color = {
                    "Available": colors.GREEN,
                    "Occupied": colors.RED,
                    "Maintenance": colors.ORANGE
                }.get(room[4], colors.GREY)
                
                status_badge = ft.Container(
                    content=ft.Text(
                        room[4] or "",
                        color=colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=status_color,
                    padding=ft.padding.all(8),
                    border_radius=20,
                )
                
                # Create buttons with proper event binding
                edit_button = ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=colors.BLUE,
                    tooltip="Edit",
                    data=room,
                    on_click=lambda e: self.edit_room(e.control.data)
                )
                
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=colors.RED,
                    tooltip="Delete",
                    data=room,
                    on_click=lambda e: self.delete_room(e.control.data)
                )
                
                self.rooms_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(room[1] or "", size=16)),
                            ft.DataCell(ft.Text(str(room[2] or ""), size=16)),
                            ft.DataCell(ft.Text(f"₱{room[3]:,.2f}" if room[3] else "", size=16)),
                            ft.DataCell(status_badge),
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
                print("Updating page after room refresh")
                self.page.update()
        except Exception as e:
            print(f"Error refreshing rooms: {e}")
            self.show_error(f"Error refreshing rooms: {str(e)}")

    def add_room(self, e):
        print("Opening add room page")
        # Create form fields
        room_number_field = ft.TextField(label="Room Number", autofocus=True)
        capacity_field = ft.TextField(label="Capacity", keyboard_type=ft.KeyboardType.NUMBER)
        price_field = ft.TextField(label="Price", keyboard_type=ft.KeyboardType.NUMBER)
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance")
            ],
            value="Available"
        )

        def save_room(e):
            try:
                room_number = room_number_field.value
                capacity = capacity_field.value
                price = price_field.value
                status = status_dropdown.value

                print(f"Adding room: {room_number}, {capacity}, {price}, {status}")

                if not room_number:
                    self.show_error("Room number is required")
                    return

                # Check if room number already exists
                existing_room = self.db.fetch_one(
                    "SELECT room_id FROM rooms WHERE room_number = %s",
                    (room_number,)
                )
                if existing_room:
                    self.show_error("Room number already exists")
                    return

                # Convert capacity to integer
                try:
                    capacity = int(capacity) if capacity else None
                except ValueError:
                    self.show_error("Capacity must be a valid number")
                    return

                # Convert price to Decimal
                try:
                    price = Decimal(price) if price else None
                except (ValueError, TypeError):
                    self.show_error("Price must be a valid number")
                    return

                self.db.insert(
                    """
                    INSERT INTO rooms (room_number, capacity, price, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (room_number, capacity, price, status)
                )
                
                # Return to rooms list
                self.page.go("/rooms")
                self.refresh_rooms()
            except Exception as e:
                print(f"Error adding room: {e}")
                self.show_error(f"Error adding room: {str(e)}")

        # Create the add room page
        add_room_page = ft.View(
            "/rooms/add",
            [
                ft.AppBar(
                    title=ft.Text("Add New Room"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/rooms")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Add New Room", size=30, weight=ft.FontWeight.BOLD),
                            room_number_field,
                            capacity_field,
                            price_field,
                            status_dropdown,
                            ft.ElevatedButton(
                                "Save Room",
                                icon=ft.Icons.SAVE,
                                on_click=save_room
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
        self.page.views.append(add_room_page)
        self.page.go("/rooms/add")

    def edit_room(self, room):
        print(f"Opening edit room page for room: {room[1]}")
        # Create form fields
        room_number_field = ft.TextField(label="Room Number", value=room[1] or "")
        capacity_field = ft.TextField(
            label="Capacity",
            value=str(room[2] or ""),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        price_field = ft.TextField(
            label="Price",
            value=str(room[3] or ""),
            keyboard_type=ft.KeyboardType.NUMBER
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance")
            ],
            value=room[4] or "Available"
        )

        def save_changes(e):
            try:
                room_number = room_number_field.value
                capacity = capacity_field.value
                price = price_field.value
                status = status_dropdown.value

                print(f"Updating room: {room_number}, {capacity}, {price}, {status}")

                if not room_number:
                    self.show_error("Room number is required")
                    return

                # Check if room number already exists (excluding current room)
                existing_room = self.db.fetch_one(
                    "SELECT room_id FROM rooms WHERE room_number = %s AND room_id != %s",
                    (room_number, room[0])
                )
                if existing_room:
                    self.show_error("Room number already exists")
                    return

                # Convert capacity to integer
                try:
                    capacity = int(capacity) if capacity else None
                except ValueError:
                    self.show_error("Capacity must be a valid number")
                    return

                # Convert price to Decimal
                try:
                    price = Decimal(price) if price else None
                except (ValueError, TypeError):
                    self.show_error("Price must be a valid number")
                    return

                self.db.update(
                    """
                    UPDATE rooms 
                    SET room_number = %s, capacity = %s, price = %s, status = %s 
                    WHERE room_id = %s
                    """,
                    (room_number, capacity, price, status, room[0])
                )
                
                # Return to rooms list
                self.page.go("/rooms")
                self.refresh_rooms()
            except Exception as e:
                print(f"Error updating room: {e}")
                self.show_error(f"Error updating room: {str(e)}")

        # Create the edit room page
        edit_room_page = ft.View(
            f"/rooms/edit/{room[0]}",
            [
                ft.AppBar(
                    title=ft.Text("Edit Room"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/rooms")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Edit Room", size=30, weight=ft.FontWeight.BOLD),
                            room_number_field,
                            capacity_field,
                            price_field,
                            status_dropdown,
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
        self.page.views.append(edit_room_page)
        self.page.go(f"/rooms/edit/{room[0]}")

    def delete_room(self, room):
        print(f"Opening delete room page for room: {room[1]}")
        
        def confirm_delete(e):
            try:
                print(f"Deleting room: {room[0]}")
                # Check if room has tenants
                tenants = self.db.fetch_one(
                    "SELECT COUNT(*) FROM tenants WHERE room_id = %s",
                    (room[0],)
                )
                if tenants and tenants[0] > 0:
                    self.show_error("Cannot delete room with active tenants")
                    self.page.go("/rooms")
                    return
                
                self.db.delete("DELETE FROM rooms WHERE room_id = %s", (room[0],))
                self.page.go("/rooms")
                self.refresh_rooms()
            except Exception as e:
                print(f"Error deleting room: {e}")
                self.show_error(f"Error deleting room: {str(e)}")
                self.page.go("/rooms")

        # Create the delete confirmation page
        delete_page = ft.View(
            f"/rooms/delete/{room[0]}",
            [
                ft.AppBar(
                    title=ft.Text("Delete Room"),
                    bgcolor=colors.SURFACE_VARIANT,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/rooms")
                    )
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Delete Room", size=30, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Are you sure you want to delete Room {room[1]}?", size=16),
                            ft.Text("This action cannot be undone.", color=colors.RED),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Cancel",
                                        icon=ft.Icons.CANCEL,
                                        on_click=lambda _: self.page.go("/rooms")
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
        self.page.go(f"/rooms/delete/{room[0]}")

    def build(self):
        print("Building RoomsView")
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Rooms Management", size=30, weight=ft.FontWeight.BOLD),
                                ft.ElevatedButton(
                                    "Add Room",
                                    icon=ft.Icons.ADD,
                                    on_click=self.add_room,
                                    style=ft.ButtonStyle(
                                        color=colors.BLACK,
                                        bgcolor=colors.PRIMARY,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    )
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=ft.padding.only(bottom=20)
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.search_field,
                                self.status_filter
                            ],
                            spacing=20,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        padding=ft.padding.only(bottom=20)
                    ),
                    ft.Container(
                        content=self.rooms_table,
                        padding=ft.padding.all(20),
                        border_radius=10,
                        bgcolor=colors.SURFACE,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=colors.BLACK12,
                        ),
                        expand=True,
                        width=self.page.window_width - 40  # Full width minus padding
                    )
                ],
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                alignment=ft.MainAxisAlignment.START
            ),
            padding=20,
            expand=True,
            alignment=ft.alignment.top_center
        ) 