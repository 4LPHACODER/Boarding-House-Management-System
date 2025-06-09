import flet as ft
from flet_core import *
from flet_core.icons import *
import sqlite3
from datetime import datetime

class TenantsView:
    def __init__(self, db_connection):
        self.db = db_connection
        self.tenants_list = ft.ListView(expand=True, spacing=10, padding=20)
        
    def build(self):
        view = ft.Container(
            content=ft.Column([
                ft.Text("Tenant Management", size=30, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton(
                        "Add New Tenant",
                        icon=ADD,
                        on_click=self.show_add_tenant_dialog
                    ),
                ]),
                self.tenants_list
            ])
        )
        
        self.refresh_tenants()
        return view
    
    def get_available_rooms(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT r.room_id, r.room_number, r.capacity, 
                   (SELECT COUNT(*) FROM tenants t WHERE t.room_id = r.room_id) as current_tenants
            FROM rooms r
            WHERE r.status = 'Available'
            AND (SELECT COUNT(*) FROM tenants t WHERE t.room_id = r.room_id) < r.capacity
        """)
        return cursor.fetchall()
    
    def refresh_tenants(self):
        self.tenants_list.controls.clear()
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT t.*, r.room_number, 
                   (SELECT SUM(amount) FROM payments WHERE tenant_id = t.tenant_id) as total_payments
            FROM tenants t
            LEFT JOIN rooms r ON t.room_id = r.room_id
            ORDER BY t.check_in_date DESC
        """)
        tenants = cursor.fetchall()
        
        for tenant in tenants:
            total_payments = tenant[6] if tenant[6] is not None else 0
            self.tenants_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(PERSON),
                                title=ft.Text(f"{tenant[1]}"),
                                subtitle=ft.Text(
                                    f"Room: {tenant[5]}\n"
                                    f"Contact: {tenant[2]}\n"
                                    f"Check-in: {tenant[4]}\n"
                                    f"Total Payments: ${total_payments}"
                                )
                            ),
                            ft.Row([
                                ft.TextButton("Edit", on_click=lambda e, t=tenant: self.show_edit_tenant_dialog(t)),
                                ft.TextButton("Delete", on_click=lambda e, t=tenant: self.delete_tenant(t[0])),
                                ft.TextButton("Add Payment", on_click=lambda e, t=tenant: self.show_add_payment_dialog(t)),
                            ], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )
            )
        if hasattr(self.tenants_list, 'page') and self.tenants_list.page is not None:
            self.tenants_list.update()
    
    def show_add_tenant_dialog(self, e):
        def save_tenant(e):
            try:
                if not room_id.value:
                    raise ValueError("Please select a room")
                
                cursor = self.db.cursor()
                # Check room capacity
                cursor.execute("""
                    SELECT r.capacity, 
                           (SELECT COUNT(*) FROM tenants t WHERE t.room_id = r.room_id) as current_tenants
                    FROM rooms r
                    WHERE r.room_id = ?
                """, (room_id.value,))
                room_info = cursor.fetchone()
                
                if room_info[1] >= room_info[0]:
                    raise ValueError("Selected room is at full capacity")
                
                cursor.execute(
                    "INSERT INTO tenants (name, contact, room_id, check_in_date) VALUES (?, ?, ?, ?)",
                    (name.value, contact.value, room_id.value, check_in_date.value)
                )
                self.db.commit()
                dialog.open = False
                self.refresh_tenants()
                page.update()
            except Exception as ex:
                print(f"Error adding tenant: {ex}")
        
        name = ft.TextField(label="Full Name", autofocus=True)
        contact = ft.TextField(label="Contact Number")
        check_in_date = ft.TextField(label="Check-in Date (YYYY-MM-DD)")
        
        # Get available rooms
        available_rooms = self.get_available_rooms()
        room_options = [
            ft.dropdown.Option(str(room[0]), f"Room {room[1]} ({room[2] - room[3]} spots available)")
            for room in available_rooms
        ]
        room_id = ft.Dropdown(
            label="Select Room",
            options=room_options
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Tenant"),
            content=ft.Column([
                name,
                contact,
                room_id,
                check_in_date
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Save", on_click=save_tenant)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page = e.page
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def show_edit_tenant_dialog(self, tenant):
        def save_changes(e):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "UPDATE tenants SET name=?, contact=?, room_id=?, check_in_date=? WHERE tenant_id=?",
                    (name.value, contact.value, room_id.value, check_in_date.value, tenant[0])
                )
                self.db.commit()
                dialog.open = False
                self.refresh_tenants()
                page.update()
            except Exception as ex:
                print(f"Error updating tenant: {ex}")
        
        name = ft.TextField(label="Full Name", value=tenant[1])
        contact = ft.TextField(label="Contact Number", value=tenant[2])
        check_in_date = ft.TextField(label="Check-in Date", value=tenant[4])
        
        # Get available rooms including current room
        available_rooms = self.get_available_rooms()
        room_options = [
            ft.dropdown.Option(str(room[0]), f"Room {room[1]} ({room[2] - room[3]} spots available)")
            for room in available_rooms
        ]
        room_id = ft.Dropdown(
            label="Select Room",
            value=str(tenant[3]),
            options=room_options
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("Edit Tenant"),
            content=ft.Column([
                name,
                contact,
                room_id,
                check_in_date
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
    
    def show_add_payment_dialog(self, tenant):
        def save_payment(e):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "INSERT INTO payments (tenant_id, amount, payment_date, payment_type) VALUES (?, ?, ?, ?)",
                    (tenant[0], float(amount.value), payment_date.value, payment_type.value)
                )
                self.db.commit()
                dialog.open = False
                self.refresh_tenants()
                page.update()
            except Exception as ex:
                print(f"Error adding payment: {ex}")
        
        amount = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER)
        payment_date = ft.TextField(label="Payment Date (YYYY-MM-DD)")
        payment_type = ft.Dropdown(
            label="Payment Type",
            options=[
                ft.dropdown.Option("Rent"),
                ft.dropdown.Option("Utility"),
                ft.dropdown.Option("Other")
            ]
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Add Payment for {tenant[1]}"),
            content=ft.Column([
                amount,
                payment_date,
                payment_type
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Save", on_click=save_payment)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page = ft.Page()
        page.dialog = dialog
        dialog.open = True
        page.update()
    
    def delete_tenant(self, tenant_id):
        def confirm_delete(e):
            try:
                cursor = self.db.cursor()
                cursor.execute("DELETE FROM tenants WHERE tenant_id=?", (tenant_id,))
                self.db.commit()
                dialog.open = False
                self.refresh_tenants()
                page.update()
            except Exception as ex:
                print(f"Error deleting tenant: {ex}")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text("Are you sure you want to delete this tenant?"),
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