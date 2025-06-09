import flet as ft
from flet_core import *
from flet_core.icons import *
import sqlite3
from datetime import datetime

class RoomsView:
    def __init__(self, db_connection):
        self.db = db_connection
        self.rooms_list = ft.ListView(expand=True, spacing=10, padding=20)
        
    def build(self):
        # Create the view structure
        view = ft.Container(
            content=ft.Column([
                ft.Text("Room Management", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton(
                        "Add New Room",
                        icon=ADD,
                        on_click=self.show_add_room_dialog
                    ),
                ]),
                self.rooms_list
            ])
        )
        
        # Refresh rooms after the view is built
        self.refresh_rooms()
        return view
    
    def refresh_rooms(self):
        self.rooms_list.controls.clear()
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM rooms")
        rooms = cursor.fetchall()
        
        for room in rooms:
            self.rooms_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(BED),
                                title=ft.Text(f"Room {room[1]}"),
                                subtitle=ft.Text(f"Capacity: {room[2]} | Price: ${room[3]} | Status: {room[4]}")
                            ),
                            ft.Row([
                                ft.TextButton("Edit", on_click=lambda e, r=room: self.show_edit_room_dialog(r)),
                                ft.TextButton("Delete", on_click=lambda e, r=room: self.delete_room(r[0])),
                            ], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )
            )
        if hasattr(self.rooms_list, 'page') and self.rooms_list.page is not None:
            self.rooms_list.update()
    
    def show_add_room_dialog(self, e):
        def save_room(e):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "INSERT INTO rooms (room_number, capacity, price, status) VALUES (?, ?, ?, ?)",
                    (room_number.value, int(capacity.value), float(price.value), status.value)
                )
                self.db.commit()
                dialog.open = False
                self.refresh_rooms()
                page.update()
            except Exception as ex:
                print(f"Error adding room: {ex}")
        
        room_number = ft.TextField(label="Room Number", autofocus=True)
        capacity = ft.TextField(label="Capacity", keyboard_type=ft.KeyboardType.NUMBER)
        price = ft.TextField(label="Price", keyboard_type=ft.KeyboardType.NUMBER)
        status = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance")
            ]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Room"),
            content=ft.Column([
                room_number,
                capacity,
                price,
                status
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Save", on_click=save_room)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page = e.page
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def show_edit_room_dialog(self, room):
        def save_changes(e):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "UPDATE rooms SET room_number=?, capacity=?, price=?, status=? WHERE room_id=?",
                    (room_number.value, int(capacity.value), float(price.value), status.value, room[0])
                )
                self.db.commit()
                dialog.open = False
                self.refresh_rooms()
                page.update()
            except Exception as ex:
                print(f"Error updating room: {ex}")
        
        room_number = ft.TextField(label="Room Number", value=room[1])
        capacity = ft.TextField(label="Capacity", value=str(room[2]), keyboard_type=ft.KeyboardType.NUMBER)
        price = ft.TextField(label="Price", value=str(room[3]), keyboard_type=ft.KeyboardType.NUMBER)
        status = ft.Dropdown(
            label="Status",
            value=room[4],
            options=[
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("Occupied"),
                ft.dropdown.Option("Maintenance")
            ]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Edit Room"),
            content=ft.Column([
                room_number,
                capacity,
                price,
                status
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Save", on_click=save_changes)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page = ft.Page()
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def delete_room(self, room_id):
        def confirm_delete(e):
            try:
                cursor = self.db.cursor()
                cursor.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
                self.db.commit()
                dialog.open = False
                self.refresh_rooms()
                page.update()
            except Exception as ex:
                print(f"Error deleting room: {ex}")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this room?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Delete", on_click=confirm_delete)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page = ft.Page()
        page.dialog = dialog
        dialog.open = True
        page.update() 