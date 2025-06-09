import flet as ft
from flet_core.colors import (
    WHITE, BLACK, BLUE, GREEN, RED, ORANGE, GREY_400, BLUE_GREY_50, BLUE_GREY_100,
    ORANGE_700, GREEN_700, RED_700, GREY_700, BLUE_700
)
from flet_core.icons import (
    SEARCH, REFRESH, PAYMENT, EDIT, DELETE
)
from datetime import datetime, date
from src.models.database import Database

class PaymentsView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = Database()
        self.payments_table = None
        self.summary_cards = None
        
        # Set page background color
        self.page.bgcolor = BLUE_GREY_50
        
        # Initialize search field
        self.search_field = ft.TextField(
            label="Search payments...",
            prefix_icon=SEARCH,
            on_change=self.filter_payments,
            expand=True,
            color=BLACK
        )
        
        # Initialize payments table
        self.payments_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tenant", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Room", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Amount Rent", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Amount Paid", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Balance", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD, color=BLACK, size=14))
            ],
            rows=[],
            border=ft.border.all(1, GREY_400),
            border_radius=15,
            vertical_lines=ft.border.all(1, GREY_400),
            horizontal_lines=ft.border.all(1, GREY_400),
            column_spacing=50,
            heading_row_color=BLUE_GREY_100,
            heading_row_height=70,
            data_row_color={"hovered": "0x30FF0000"},
            show_checkbox_column=False,
        )
        
    def show_error(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=BLACK),
            bgcolor=RED
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def show_success(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=BLACK),
            bgcolor=GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def calculate_rent(self, check_in_date, check_out_date, room_price):
        if not check_out_date:
            check_out_date = date.today()
        
        # Calculate months between dates
        months = (check_out_date.year - check_in_date.year) * 12 + check_out_date.month - check_in_date.month
        if check_out_date.day > check_in_date.day:
            months += 1
            
        return months * room_price
        
    def refresh_payments(self):
        try:
            print("Fetching tenants for payments view...")
            # Get all active tenants with their room and payment information
            query = """
                SELECT 
                    t.tenant_id, 
                    t.first_name, 
                    t.last_name, 
                    t.check_in_date, 
                    t.check_out_date,
                    r.price as room_price, 
                    r.room_number,
                    COALESCE(p.amount_rent, 0) as amount_rent,
                    COALESCE(p.amount_paid, 0) as amount_paid,
                    COALESCE(p.balance, 0) as balance,
                    COALESCE(p.status, 'Pending') as status,
                    p.payment_id
                FROM tenants t
                JOIN rooms r ON t.room_id = r.room_id
                LEFT JOIN payments p ON t.tenant_id = p.tenant_id
                WHERE (t.check_out_date IS NULL OR t.check_out_date > CURRENT_DATE)
                ORDER BY t.last_name, t.first_name
            """
            tenants = self.db.fetch_all(query)
            
            print(f"Found {len(tenants) if tenants else 0} tenants")
            
            if not self.payments_table:
                print("Payments table not initialized")
                return
                
            # Clear existing rows
            self.payments_table.rows.clear()
            
            # Initialize totals
            total_rent = 0
            total_paid = 0
            total_balance = 0
            
            # Add tenant rows
            for tenant in tenants:
                print(f"Processing tenant: {tenant[1]} {tenant[2]}")
                # Calculate current rent if no payment record exists
                if not tenant[11]:  # payment_id is NULL
                    current_rent = self.calculate_rent(
                        tenant[3],  # check_in_date
                        tenant[4],  # check_out_date
                        tenant[5]   # room_price
                    )
                    amount_rent = current_rent
                    amount_paid = 0
                    balance = current_rent
                    status = "Pending"
                else:
                    amount_rent = float(tenant[7])
                    amount_paid = float(tenant[8])
                    balance = float(tenant[9])
                    status = tenant[10]
                
                # Update totals
                total_rent += amount_rent
                total_paid += amount_paid
                total_balance += balance
                
                print(f"Adding row for tenant: {tenant[1]} {tenant[2]}, Room: {tenant[6]}, Balance: {balance}")
                print(f"Current totals - Rent: {total_rent}, Paid: {total_paid}, Balance: {total_balance}")
                
                # Create action buttons with enhanced styling
                action_buttons = ft.Row([
                    ft.ElevatedButton(
                        "Pay Now",
                        icon=PAYMENT,
                        style=ft.ButtonStyle(
                            color=WHITE,
                            bgcolor=GREEN,
                            shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                        on_click=lambda e, id=tenant[0]: self.add_payment(id)
                    ) if status == "Pending" else ft.Container(),
                    ft.IconButton(
                        icon=EDIT,
                        icon_color=BLUE,
                        tooltip="Edit Payment",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                        on_click=lambda e, id=tenant[11]: self.edit_payment(id) if tenant[11] else None
                    ) if tenant[11] else ft.Container(),
                    ft.IconButton(
                        icon=DELETE,
                        icon_color=RED,
                        tooltip="Delete Payment",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                        on_click=lambda e, id=tenant[11]: self.delete_payment(id) if tenant[11] else None
                    ) if tenant[11] else ft.Container()
                ], spacing=5)
                
                # Create status badge with enhanced styling
                status_badge = ft.Container(
                    content=ft.Text(
                        status,
                        color=WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=self.get_status_color(status),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=3,
                        color="0x4D000000"  # 30% opacity black
                    )
                )
                
                self.payments_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{tenant[1]} {tenant[2]}", weight=ft.FontWeight.W_500, color=BLACK)),
                            ft.DataCell(ft.Text(f"Room {tenant[6]}", weight=ft.FontWeight.W_500, color=BLACK)),
                            ft.DataCell(ft.Text(f"₱{amount_rent:,.2f}", weight=ft.FontWeight.W_500, color=BLACK)),
                            ft.DataCell(ft.Text(f"₱{amount_paid:,.2f}", weight=ft.FontWeight.W_500, color=BLACK)),
                            ft.DataCell(ft.Text(f"₱{balance:,.2f}", weight=ft.FontWeight.W_500, color=BLACK)),
                            ft.DataCell(status_badge),
                            ft.DataCell(action_buttons)
                        ]
                    )
                )
            
            print(f"Final totals - Rent: {total_rent}, Paid: {total_paid}, Balance: {total_balance}")
            # Update summary cards
            self.update_summary_cards(total_rent, total_paid, total_balance)
            
            print("Updating payments table...")
            self.page.update()
            print("Payments table updated")
            
        except Exception as e:
            print(f"Error in refresh_payments: {str(e)}")
            self.show_error(f"Error refreshing payments: {e}")
            
    def get_status_color(self, status: str) -> str:
        colors = {
            "Pending": ORANGE_700,
            "Paid": GREEN_700,
            "Overdue": RED_700,
            "Cancelled": GREY_700
        }
        return colors.get(status, BLUE_700)
        
    def add_payment(self, tenant_id):
        try:
            print(f"Adding payment for tenant ID: {tenant_id}")
            # Get tenant information
            query = """
                SELECT 
                    t.tenant_id, 
                    t.first_name, 
                    t.last_name, 
                    t.check_in_date, 
                    t.check_out_date,
                    r.price as room_price,
                    r.room_number,
                    COALESCE(p.amount_rent, 0) as amount_rent,
                    COALESCE(p.amount_paid, 0) as amount_paid,
                    COALESCE(p.balance, 0) as balance,
                    COALESCE(p.status, 'Pending') as status,
                    p.payment_id
                FROM tenants t
                JOIN rooms r ON t.room_id = r.room_id
                LEFT JOIN payments p ON t.tenant_id = p.tenant_id
                WHERE t.tenant_id = %s
            """
            tenant = self.db.fetch_one(query, (tenant_id,))
            
            if not tenant:
                self.show_error("Tenant not found")
                return
                
            print(f"Found tenant: {tenant[1]} {tenant[2]}")
            
            # Calculate current rent if no payment record exists
            if not tenant[11]:  # payment_id is NULL
                current_rent = self.calculate_rent(
                    tenant[3],  # check_in_date
                    tenant[4],  # check_out_date
                    tenant[5]   # room_price
                )
                amount_rent = current_rent
                amount_paid = 0
                balance = current_rent
                status = "Pending"
            else:
                amount_rent = float(tenant[7])
                amount_paid = float(tenant[8])
                balance = float(tenant[9])
                status = tenant[10]
            
            # Create payment form
            amount_field = ft.TextField(
                label="Amount",
                value=str(balance),
                prefix_text="₱",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=200,
                color=BLACK
            )
            
            payment_method = ft.Dropdown(
                label="Payment Method",
                options=[
                    ft.dropdown.Option("Cash"),
                    ft.dropdown.Option("Bank Transfer"),
                    ft.dropdown.Option("GCash"),
                    ft.dropdown.Option("Maya")
                ],
                width=200,
                color=BLACK
            )
            
            description = ft.TextField(
                label="Description",
                multiline=True,
                min_lines=3,
                max_lines=5,
                width=400,
                color=BLACK
            )
            
            def save_payment(e):
                try:
                    amount = float(amount_field.value)
                    if amount <= 0:
                        self.show_error("Amount must be greater than 0")
                        return
                        
                    if not payment_method.value:
                        self.show_error("Please select a payment method")
                        return
                        
                    # Insert payment record
                    query = """
                        INSERT INTO payments (
                            tenant_id, amount_rent, amount_paid, balance,
                            payment_date, payment_method, status, description
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        tenant_id,
                        amount_rent,
                        amount,
                        balance - amount,
                        datetime.now().date(),
                        payment_method.value,
                        "Paid" if amount >= balance else "Pending",
                        description.value
                    )
                    
                    self.db.execute(query, values)
                    self.show_success("Payment added successfully")
                    self.page.go("/payments")
                    self.refresh_payments()
                    
                except Exception as e:
                    print(f"Error saving payment: {str(e)}")
                    self.show_error(f"Error saving payment: {e}")
            
            def cancel_payment(e):
                self.page.go("/payments")
            
            # Create the add payment page
            add_payment_page = ft.View(
                f"/payments/add/{tenant_id}",
                [
                    ft.AppBar(
                        title=ft.Text("Add Payment", color=WHITE),
                        bgcolor=BLUE_GREY_100,
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda _: self.page.go("/payments")
                        )
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Add Payment", size=30, weight=ft.FontWeight.BOLD, color=BLACK),
                                ft.Text(f"Tenant: {tenant[1]} {tenant[2]}", size=16, color=BLACK),
                                ft.Text(f"Room: {tenant[6]}", size=16, color=BLACK),
                                ft.Text(f"Amount Due: ₱{balance:,.2f}", size=16, color=BLACK),
                                amount_field,
                                payment_method,
                                description,
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            "Save",
                                            icon=ft.Icons.SAVE,
                                            on_click=save_payment,
                                            style=ft.ButtonStyle(
                                                color=WHITE,
                                                bgcolor=GREEN,
                                            )
                                        ),
                                        ft.ElevatedButton(
                                            "Cancel",
                                            icon=ft.Icons.CANCEL,
                                            on_click=cancel_payment,
                                            style=ft.ButtonStyle(
                                                color=WHITE,
                                                bgcolor=RED,
                                            )
                                        )
                                    ],
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
            self.page.views.append(add_payment_page)
            self.page.go(f"/payments/add/{tenant_id}")
            
        except Exception as e:
            print(f"Error adding payment: {str(e)}")
            self.show_error(f"Error adding payment: {e}")
            
    def build(self):
        print("Building PaymentsView")
        try:
            # Create search field
            search_field = ft.TextField(
                label="Search tenants...",
                label_style=ft.TextStyle(color=BLACK, size=14),
                prefix_icon=SEARCH,
                width=300,
                height=45,
                border_radius=10,
                filled=True,
                bgcolor=WHITE,
                on_change=lambda e: self.filter_payments(e.control.value),
                color=BLACK
            )

            # Create data table
            self.payments_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Tenant", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Room", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Amount Rent", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Amount Paid", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Balance", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=BLACK, size=14)),
                    ft.DataColumn(ft.Text("Actions", weight=ft.FontWeight.BOLD, color=BLACK, size=14))
                ],
                rows=[],
                border=ft.border.all(1, GREY_400),
                border_radius=15,
                vertical_lines=ft.border.all(1, GREY_400),
                horizontal_lines=ft.border.all(1, GREY_400),
                column_spacing=50,
                heading_row_color=BLUE_GREY_100,
                heading_row_height=70,
                data_row_color={"hovered": "0x30FF0000"},
                show_checkbox_column=False,
            )

            # Create summary cards with enhanced styling
            self.summary_cards = ft.Row([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Rent", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("₱0.00", size=24, weight=ft.FontWeight.BOLD, color=BLUE)
                        ]),
                        padding=20
                    ),
                    width=200,
                    elevation=5,
                    shadow_color=BLUE_GREY_100
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Paid", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("₱0.00", size=24, weight=ft.FontWeight.BOLD, color=GREEN)
                        ]),
                        padding=20
                    ),
                    width=200,
                    elevation=5,
                    shadow_color=BLUE_GREY_100
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Total Balance", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("₱0.00", size=24, weight=ft.FontWeight.BOLD, color=ORANGE)
                        ]),
                        padding=20
                    ),
                    width=200,
                    elevation=5,
                    shadow_color=BLUE_GREY_100
                )
            ], spacing=20)

            # Create refresh button with enhanced styling
            refresh_button = ft.ElevatedButton(
                "Refresh",
                icon=REFRESH,
                style=ft.ButtonStyle(
                    color=WHITE,
                    bgcolor=BLUE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                ),
                on_click=lambda e: self.refresh_payments()
            )

            # Create header with enhanced styling
            header = ft.Container(
                content=ft.Row(
                    [
                        ft.Text("Tenant Payments", size=32, weight=ft.FontWeight.BOLD, color=BLACK),
                        ft.Row([search_field, refresh_button], spacing=15)
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=ft.padding.symmetric(horizontal=25, vertical=20),
                bgcolor=BLUE_GREY_50,
                border_radius=15,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=BLUE_GREY_100,
                )
            )

            # Create main content with enhanced layout
            main_content = ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Container(
                            content=self.summary_cards,
                            padding=ft.padding.only(bottom=20)
                        ),
                        ft.Container(
                            content=self.payments_table,
                            padding=25,
                            border_radius=15,
                            bgcolor=WHITE,
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=15,
                                color=BLUE_GREY_100,
                            )
                        )
                    ],
                    spacing=25
                ),
                padding=25,
                expand=True,
                bgcolor=BLUE_GREY_50
            )

            print("Loading initial data...")
            # Load initial data
            self.refresh_payments()
            print("Initial data loaded")

            return main_content

        except Exception as e:
            print(f"Error in build: {str(e)}")
            self.show_error(f"Error building payments view: {e}")
            return ft.Text("Error loading payments", color=BLACK)

    def filter_payments(self, search_text: str):
        """Filter payments table based on search text"""
        try:
            if not self.payments_table:
                return

            search_text = search_text.lower()
            for row in self.payments_table.rows:
                tenant_name = row.cells[0].content.value.lower()
                room_number = row.cells[1].content.value.lower()
                
                # Show row if search text matches tenant name or room number
                row.visible = search_text in tenant_name or search_text in room_number

            self.page.update()
        except Exception as e:
            print(f"Error filtering payments: {str(e)}")
            self.show_error(f"Error filtering payments: {e}")

    def update_summary_cards(self, total_rent: float, total_paid: float, total_balance: float):
        """Update the summary cards with current totals"""
        try:
            print("\nUpdating summary cards...")
            print(f"Totals to update - Rent: {total_rent}, Paid: {total_paid}, Balance: {total_balance}")
            
            if not self.summary_cards:
                self.summary_cards = ft.Row([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Total Rent", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"₱{total_rent:,.2f}", size=24, weight=ft.FontWeight.BOLD, color=BLUE)
                            ]),
                            padding=20
                        ),
                        width=200
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Total Paid", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"₱{total_paid:,.2f}", size=24, weight=ft.FontWeight.BOLD, color=GREEN)
                            ]),
                            padding=20
                        ),
                        width=200
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Total Balance", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"₱{total_balance:,.2f}", size=24, weight=ft.FontWeight.BOLD, color=ORANGE)
                            ]),
                            padding=20
                        ),
                        width=200
                    )
                ], spacing=20)
            else:
                # Update existing cards
                self.summary_cards.controls[0].content.content.controls[1].value = f"₱{total_rent:,.2f}"
                self.summary_cards.controls[1].content.content.controls[1].value = f"₱{total_paid:,.2f}"
                self.summary_cards.controls[2].content.content.controls[1].value = f"₱{total_balance:,.2f}"
            
            # Update the page to reflect changes
            self.page.update()
            print("Summary cards update complete\n")
            
        except Exception as e:
            print(f"Error updating summary cards: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            self.show_error(f"Error updating summary cards: {e}")

    def edit_payment(self, payment_id: int):
        try:
            # Get payment details
            payment = self.db.fetch_one("""
                SELECT p.*, t.first_name, t.last_name, r.room_number
                FROM payments p
                JOIN tenants t ON p.tenant_id = t.tenant_id
                JOIN rooms r ON t.room_id = r.room_id
                WHERE p.payment_id = %s
            """, (payment_id,))
            
            if not payment:
                self.show_error("Payment not found")
                return
                
            # Create form fields
            amount_field = ft.TextField(
                label="Amount Paid",
                value=str(payment[3]),  # amount_paid
                prefix_text="₱",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=200
            )
            
            method_dropdown = ft.Dropdown(
                label="Payment Method",
                options=[
                    ft.dropdown.Option("Cash"),
                    ft.dropdown.Option("GCash"),
                    ft.dropdown.Option("Bank Transfer")
                ],
                value=payment[4],  # payment_method
                width=200
            )
            
            status_dropdown = ft.Dropdown(
                label="Status",
                options=[
                    ft.dropdown.Option("Pending"),
                    ft.dropdown.Option("Paid"),
                    ft.dropdown.Option("Overdue"),
                    ft.dropdown.Option("Cancelled")
                ],
                value=payment[6],  # status
                width=200
            )
            
            description_field = ft.TextField(
                label="Description",
                value=payment[7] or "",  # description
                multiline=True,
                min_lines=2,
                max_lines=3,
                width=400
            )
            
            def save_changes(e):
                try:
                    if not amount_field.value:
                        self.show_error("Please enter payment amount")
                        return
                        
                    amount = float(amount_field.value)
                    if amount <= 0:
                        self.show_error("Amount must be greater than 0")
                        return
                    
                    # Update payment
                    self.db.execute("""
                        UPDATE payments 
                        SET amount_paid = %s,
                            payment_method = %s,
                            status = %s,
                            description = %s
                        WHERE payment_id = %s
                    """, (
                        amount,
                        method_dropdown.value,
                        status_dropdown.value,
                        description_field.value,
                        payment_id
                    ))
                    
                    self.show_success("Payment updated successfully")
                    self.refresh_payments()
                    self.page.go("/payments")
                    
                except Exception as e:
                    print(f"Error saving changes: {str(e)}")
                    self.show_error(f"Error saving changes: {e}")
            
            def cancel_edit(e):
                self.page.go("/payments")
            
            # Create edit window content
            edit_content = ft.Container(
                content=ft.Column([
                    ft.Text(f"Edit Payment for {payment[8]} {payment[9]}", size=20, weight=ft.FontWeight.BOLD, color=BLACK),
                    ft.Text(f"Room {payment[10]}", size=16, color=BLACK),
                    ft.Divider(),
                    amount_field,
                    method_dropdown,
                    status_dropdown,
                    description_field,
                    ft.Row([
                        ft.ElevatedButton("Save Changes", on_click=save_changes),
                        ft.ElevatedButton("Cancel", on_click=cancel_edit)
                    ])
                ]),
                padding=20
            )
            
            # Create a new view for the edit window
            edit_view = ft.View(
                f"/payments/edit/{payment_id}",
                [edit_content],
                appbar=ft.AppBar(
                    title=ft.Text("Edit Payment"),
                    center_title=True,
                    bgcolor=BLUE
                )
            )
            
            # Add the edit view to the page
            self.page.views.append(edit_view)
            self.page.go(f"/payments/edit/{payment_id}")
            
        except Exception as e:
            print(f"Error in edit_payment: {str(e)}")
            self.show_error(f"Error editing payment: {e}")
            self.page.go("/payments")
            
    def delete_payment(self, payment_id: int):
        try:
            # Get payment details for confirmation
            payment = self.db.fetch_one("""
                SELECT p.*, t.first_name, t.last_name, r.room_number
                FROM payments p
                JOIN tenants t ON p.tenant_id = t.tenant_id
                JOIN rooms r ON t.room_id = r.room_id
                WHERE p.payment_id = %s
            """, (payment_id,))
            
            if not payment:
                self.show_error("Payment not found")
                return
            
            def confirm_delete(e):
                try:
                    # Delete payment
                    self.db.execute("""
                        DELETE FROM payments
                        WHERE payment_id = %s
                    """, (payment_id,))
                    
                    self.show_success("Payment deleted successfully")
                    self.refresh_payments()
                    self.page.go("/payments")
                    
                except Exception as e:
                    print(f"Error deleting payment: {str(e)}")
                    self.show_error(f"Error deleting payment: {e}")
            
            def cancel_delete(e):
                self.page.go("/payments")
            
            # Create delete window content
            delete_content = ft.Container(
                content=ft.Column([
                    ft.Text("Delete Payment", size=20, weight=ft.FontWeight.BOLD, color=BLACK),
                    ft.Text(f"Are you sure you want to delete the payment for:", size=16, color=BLACK),
                    ft.Text(f"Tenant: {payment[8]} {payment[9]}", size=16, color=BLACK),
                    ft.Text(f"Room: {payment[10]}", size=16, color=BLACK),
                    ft.Text(f"Amount Paid: ₱{float(payment[3]):,.2f}", size=16, color=BLACK),
                    ft.Text(f"Status: {payment[6]}", size=16, color=BLACK),
                    ft.Divider(),
                    ft.Row([
                        ft.ElevatedButton(
                            "Delete",
                            icon=DELETE,
                            color=WHITE,
                            bgcolor=RED,
                            on_click=confirm_delete
                        ),
                        ft.ElevatedButton(
                            "Cancel",
                            on_click=cancel_delete
                        )
                    ])
                ]),
                padding=20
            )
            
            # Create a new view for the delete window
            delete_view = ft.View(
                f"/payments/delete/{payment_id}",
                [delete_content],
                appbar=ft.AppBar(
                    title=ft.Text("Delete Payment"),
                    center_title=True,
                    bgcolor=RED
                )
            )
            
            # Add the delete view to the page
            self.page.views.append(delete_view)
            self.page.go(f"/payments/delete/{payment_id}")
            
        except Exception as e:
            print(f"Error in delete_payment: {str(e)}")
            self.show_error(f"Error deleting payment: {e}")
            self.page.go("/payments") 
            