import flet as ft
from flet_core import colors
from flet_core.icons import PAYMENTS, SAVE, CANCEL
from datetime import datetime
from src.database import Database

class PaymentOperations:
    def __init__(self, page: ft.Page, db: Database):
        self.page = page
        self.db = db

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

    def calculate_rent(self, check_in_date, check_out_date, room_price):
        if not check_in_date:
            return 0
            
        if check_out_date:
            end_date = check_out_date
        else:
            end_date = datetime.now().date()
            
        months = (end_date.year - check_in_date.year) * 12 + end_date.month - check_in_date.month
        if end_date.day > check_in_date.day:
            months += 1
            
        return months * room_price

    def add_payment(self, tenant_id):
        try:
            print(f"Adding payment for tenant ID: {tenant_id}")
            # Get tenant information
            tenant = self.db.fetch_one("""
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
            """, (tenant_id,))
            
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
                amount_rent = tenant[7]
                amount_paid = tenant[8]
                balance = tenant[9]
                status = tenant[10]
            
            # Create payment form
            amount_field = ft.TextField(
                label="Amount",
                value=str(balance),
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
                value="Cash",
                width=200
            )
            
            description_field = ft.TextField(
                label="Description",
                multiline=True,
                min_lines=2,
                max_lines=3,
                width=400
            )
            
            def save_payment(e):
                try:
                    if not amount_field.value:
                        self.show_error("Please enter payment amount")
                        return
                        
                    amount = float(amount_field.value)
                    if amount <= 0:
                        self.show_error("Amount must be greater than 0")
                        return
                        
                    new_amount_paid = amount_paid + amount
                    new_balance = amount_rent - new_amount_paid
                    new_status = "Paid" if new_balance <= 0 else "Pending"
                    
                    if tenant[11]:  # Update existing payment
                        self.db.execute("""
                            UPDATE payments 
                            SET amount_paid = %s,
                                balance = %s,
                                status = %s,
                                payment_date = %s,
                                payment_method = %s,
                                description = %s
                            WHERE payment_id = %s
                        """, (
                            new_amount_paid,
                            new_balance,
                            new_status,
                            datetime.now().date(),
                            method_dropdown.value,
                            description_field.value,
                            tenant[11]
                        ))
                    else:  # Create new payment
                        self.db.execute("""
                            INSERT INTO payments (
                                tenant_id, amount_rent, amount_paid, balance,
                                payment_date, payment_method, status, description
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            tenant_id,
                            amount_rent,
                            amount,
                            new_balance,
                            datetime.now().date(),
                            method_dropdown.value,
                            new_status,
                            description_field.value
                        ))
                    
                    self.show_success("Payment saved successfully")
                    self.page.go("/payments")  # Navigate back to payments view
                    
                except Exception as e:
                    print(f"Error saving payment: {str(e)}")
                    self.show_error(f"Error saving payment: {e}")
            
            def cancel_payment(e):
                self.page.go("/payments")  # Navigate back to payments view
            
            # Create payment window content
            payment_content = ft.Container(
                content=ft.Column([
                    ft.Text(f"Payment for {tenant[1]} {tenant[2]}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Room {tenant[6]}", size=16),
                    ft.Text(f"Current Balance: ₱{balance:,.2f}", size=16),
                    ft.Divider(),
                    amount_field,
                    method_dropdown,
                    description_field,
                    ft.Row([
                        ft.ElevatedButton("Save", on_click=save_payment),
                        ft.ElevatedButton("Cancel", on_click=cancel_payment)
                    ])
                ]),
                padding=20
            )
            
            # Create a new view for the payment window
            payment_view = ft.View(
                "/payment",
                [payment_content],
                appbar=ft.AppBar(
                    title=ft.Text("Add Payment"),
                    center_title=True,
                    bgcolor=colors.BLUE
                )
            )
            
            # Add the payment view to the page
            self.page.views.append(payment_view)
            self.page.go("/payment")
            
        except Exception as e:
            print(f"Error in add_payment: {str(e)}")
            self.show_error(f"Error adding payment: {e}")
            self.page.go("/payments")  # Navigate back to payments view on error

    def delete_payment(self, payment_id):
        try:
            # Confirm deletion
            def confirm_delete(e):
                try:
                    self.db.execute("DELETE FROM payments WHERE payment_id = %s", (payment_id,))
                    self.show_success("Payment deleted successfully")
                    self.page.go("/payments")
                except Exception as e:
                    self.show_error(f"Error deleting payment: {e}")
                finally:
                    self.page.dialog.open = False
                    self.page.update()

            def cancel_delete(e):
                self.page.dialog.open = False
                self.page.update()

            # Create confirmation dialog
            self.page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirm Deletion"),
                content=ft.Text("Are you sure you want to delete this payment?"),
                actions=[
                    ft.TextButton("Yes", on_click=confirm_delete),
                    ft.TextButton("No", on_click=cancel_delete),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.dialog.open = True
            self.page.update()

        except Exception as e:
            self.show_error(f"Error showing delete confirmation: {e}") 