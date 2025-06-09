import flet as ft
from flet_core import *
from flet_core.icons import *
import os
from models.database import Database
from views.rooms.rooms_view import RoomsView
from views.tenants.tenants_view import TenantsView

class BoardingHouseApp:
    def __init__(self):
        self.db = Database()
        self.rooms_view = None
        self.tenants_view = None
        
    def main(self, page: ft.Page):
        page.title = "Boarding House Management System"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1200
        page.window_height = 800
        page.padding = 20
        
        # Navigation Rail
        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            extended=True,
            width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=HOME_OUTLINED,
                    selected_icon=HOME,
                    label="Dashboard"
                ),
                ft.NavigationRailDestination(
                    icon=BED_OUTLINED,
                    selected_icon=BED,
                    label="Rooms"
                ),
                ft.NavigationRailDestination(
                    icon=PERSON_OUTLINE,
                    selected_icon=PERSON,
                    label="Tenants"
                ),
                ft.NavigationRailDestination(
                    icon=PAYMENTS_OUTLINED,
                    selected_icon=PAYMENTS,
                    label="Payments"
                ),
                ft.NavigationRailDestination(
                    icon=BUILD_OUTLINED,
                    selected_icon=BUILD,
                    label="Maintenance"
                ),
                ft.NavigationRailDestination(
                    icon=CHAT_OUTLINED,
                    selected_icon=CHAT,
                    label="Chatbot"
                ),
            ],
            on_change=self.change_view
        )
        
        # Main content area
        self.content = ft.Container(
            content=ft.Column([
                ft.Text("Welcome to Boarding House Management System", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Select a section from the navigation menu to get started.", size=16)
            ]),
            expand=True
        )
        
        # Layout
        page.add(
            ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    self.content,
                ],
                expand=True
            )
        )
    
    def change_view(self, e):
        index = e.control.selected_index
        if index == 0:  # Dashboard
            self.content.content = ft.Column([
                ft.Text("Dashboard", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Overview of the boarding house management system", size=16)
            ])
        elif index == 1:  # Rooms
            if self.rooms_view is None:
                self.rooms_view = RoomsView(self.db.get_connection())
            self.content.content = self.rooms_view.build()
        elif index == 2:  # Tenants
            if self.tenants_view is None:
                self.tenants_view = TenantsView(self.db.get_connection())
            self.content.content = self.tenants_view.build()
        elif index == 3:  # Payments
            self.content.content = ft.Text("Payments Management", size=30)
        elif index == 4:  # Maintenance
            self.content.content = ft.Text("Maintenance Management", size=30)
        elif index == 5:  # Chatbot
            self.content.content = ft.Text("Chatbot Assistant", size=30)
        self.content.update()

if __name__ == "__main__":
    app = BoardingHouseApp()
    ft.app(target=app.main) 