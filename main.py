import flet as ft
from flet_core import *
from flet_core.icons import *
from src.models.database import Database
from src.views.rooms.rooms_view import RoomsView
from src.views.tenants.tenants_view import TenantsView
from src.views.payments.payments_view import PaymentsView
from src.views.settings.settings_view import SettingsView
from src.views.chatbot.chatbot_view import get_chatbot_view
from src.auth import LoginPage, SignupPage

def main(page: ft.Page):
    print("Starting application...")
    
    # Initialize database
    db = Database()
    print("Database connection established successfully")
    db.create_tables()
    print("Tables created successfully")
    
    # Page setup
    page.title = "Boarding House Management System"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=colors.BLUE,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed=colors.BLUE,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    page.padding = 0
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.window_maximizable = True
    page.window_minimizable = True
    print("Page setup completed")
    
    # Initialize views
    print("Initializing views")
    rooms_view = RoomsView(page)
    tenants_view = TenantsView(page)
    payments_view = PaymentsView(page)
    settings_view = SettingsView(page)
    print("Views initialized")
    
    def handle_nav_change(index):
        print(f"Changing view to index: {index}")
        if index == 0:  # Rooms
            page.go("/rooms")
        elif index == 1:  # Tenants
            page.go("/tenants")
        elif index == 2:  # Payments
            page.go("/payments")
        elif index == 3:  # Chatbot
            page.go("/chatbot")
        elif index == 4:  # Settings
            page.go("/settings")
    
    # Create navigation rail
    print("Creating navigation rail")
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME,
                label="Rooms"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                label="Tenants"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PAYMENTS_OUTLINED,
                selected_icon=ft.Icons.PAYMENTS,
                label="Payments"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CHAT_OUTLINED,
                selected_icon=ft.Icons.CHAT,
                label="Chatbot"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.BUILD_OUTLINED,
                selected_icon=ft.Icons.BUILD,
                label="Settings"
            ),
        ],
        on_change=lambda e: handle_nav_change(e.control.selected_index)
    )
    print("Navigation rail created")
    
    # Create main layout
    main_layout = ft.Row(
        [
            nav_rail,
            ft.VerticalDivider(width=1),
            ft.Container(
                content=rooms_view.build(),
                expand=True
            )
        ],
        expand=True
    )
    print("Main layout created")
    
    def show_main_app():
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [main_layout]
            )
        )
        page.go("/rooms")
        page.update()
    
    def route_change(e):
        print(f"Route changed to: {e.route}")
        page.views.clear()
        
        if e.route == "/login":
            login_page = LoginPage(page)
            page.views.append(
                ft.View(
                    "/login",
                    [login_page.get_content()]
                )
            )
        elif e.route == "/signup":
            signup_page = SignupPage(page)
            page.views.append(
                ft.View(
                    "/signup",
                    [signup_page.get_content()]
                )
            )
        elif e.route == "/rooms":
            nav_rail.selected_index = 0
            page.views.append(
                ft.View(
                    "/rooms",
                    [main_layout]
                )
            )
        elif e.route == "/tenants":
            nav_rail.selected_index = 1
            page.views.append(
                ft.View(
                    "/tenants",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=tenants_view.build(),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        elif e.route == "/payments":
            nav_rail.selected_index = 2
            page.views.append(
                ft.View(
                    "/payments",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=payments_view.build(),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        elif e.route == "/chatbot":
            nav_rail.selected_index = 3
            page.views.append(
                ft.View(
                    "/chatbot",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=get_chatbot_view(page),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        elif e.route == "/settings":
            nav_rail.selected_index = 4
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=settings_view.build(),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        elif "/rooms/add" in e.route:
            page.views.append(
                ft.View(
                    "/rooms",
                    [main_layout]
                )
            )
        elif "/rooms/edit" in e.route:
            page.views.append(
                ft.View(
                    "/rooms",
                    [main_layout]
                )
            )
        elif "/tenants/add" in e.route:
            page.views.append(
                ft.View(
                    "/tenants",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=tenants_view.build(),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        elif "/tenants/edit" in e.route:
            page.views.append(
                ft.View(
                    "/tenants",
                    [
                        ft.Row(
                            [
                                nav_rail,
                                ft.VerticalDivider(width=1),
                                ft.Container(
                                    content=tenants_view.build(),
                                    expand=True
                                )
                            ],
                            expand=True
                        )
                    ]
                )
            )
        
        page.update()
    
    def view_pop(view):
        print("View popped")
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    # Set up routing
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Start with login page
    page.go("/login")
    
    print("Initial page update completed")

if __name__ == "__main__":
    ft.app(target=main) 