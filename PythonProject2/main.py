from tkinter import *
from tkinter import ttk, messagebox
import os
import sqlite3 as sql
from datetime import datetime
from Style import style_defaults, color


class Window(Tk):
    def __init__(self):
        super().__init__()
        self.button = None
        self.order_items = []  # Store order items
        self.order_counter = 1  # For order ID
        self.current_frame = None  # Track current active frame
        self.category_frames = {}  # Store all category frames
        self.db_conn = None  # Database connection

        with open('theme_name.txt', 'r') as f:
            file_read =f.read()
            print(file_read)

        self.theme_name = file_read
        self.active_toplevels = []  # Track all active toplevel windows

        # Initialize database
        self.initialize_database()

        self.title('Snack Lebanese Fast Food...')
        self.geometry('1200x700+50+50')
        self.configure(background=color(self.theme_name, 'bg'))

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        style_defaults(self, self.style, self.theme_name)

        # Bind window close event to handle cleanup
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Top Frame [Title, Clock, Staff name, etc.]
        self.TopFrame = ttk.Frame(self, width=1150, height=50, style='TFrame')
        self.TopFrame.pack(expand=True, fill='x')
        self.TopFrame.pack_propagate(False)

        # Add title and current time to top frame
        self.setup_top_frame()

        # Center Frame
        self.CenterFrame = ttk.Frame(self, width=1150, height=700)
        self.CenterFrame.pack(expand=True, fill='x')
        self.CenterFrame.pack_propagate(False)

        # Center Frame 1 - Food Items (Container for all category frames)
        self.CenterFrame1 = ttk.Frame(self.CenterFrame, width=700, height=450)
        self.CenterFrame1.grid(row=0, column=0, rowspan=2, sticky='news')
        self.CenterFrame1.grid_propagate(False)

        # Create all category frames
        self.create_category_frames()

        # Center Frame 2 - Order Display
        self.CenterFrame2 = ttk.Frame(self.CenterFrame, width=500, height=250)
        self.CenterFrame2.grid(row=0, column=1, sticky='news')
        self.CenterFrame2.grid_propagate(False)

        self.treeView(self.CenterFrame2)

        # Center Frame 3 - Order Summary
        self.CenterFrame3 = ttk.Frame(self.CenterFrame, width=500, height=200)
        self.CenterFrame3.grid(row=1, column=1, sticky='news')
        self.CenterFrame3.grid_propagate(False)

        self.setup_order_summary()

        # Bottom Frame - Categories
        self.BottomFrame = ttk.Frame(self, width=1150, height=75, style='Top.TFrame')
        self.BottomFrame.pack(anchor='w', expand=True)
        self.BottomFrame.pack_propagate(False)

        self.bottom_main(self.BottomFrame)

        # Show default frame
        default_category = self.get_default_category()
        self.show_category_frame(default_category)

    def on_close(self):
        """Handle application close event"""
        # Close all toplevel windows first
        for toplevel in self.active_toplevels:
            try:
                toplevel.destroy()
            except:
                pass

        # Close database connection
        if self.db_conn:
            self.db_conn.close()

        # Destroy main window
        self.destroy()

    def initialize_database(self):
        """Initialize the SQLite database and create tables if they don't exist"""
        self.db_conn = sql.connect('pos_database.db')
        cursor = self.db_conn.cursor()

        # Create menu items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            barcode TEXT UNIQUE,
            is_active INTEGER DEFAULT 1
        )
        ''')

        # Create orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            payment_method TEXT,
            customer_name TEXT,
            notes TEXT
        )
        ''')

        # Create order_items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (item_id) REFERENCES menu_items(id)
        )
        ''')

        # Create settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            default_category TEXT,
            theme_name TEXT,
            tax_rate REAL DEFAULT 0.0,
            receipt_header TEXT,
            receipt_footer TEXT
        )
        ''')

        # Insert default settings if not exists
        cursor.execute('''
        INSERT OR IGNORE INTO settings (id, default_category, theme_name, tax_rate, receipt_header, receipt_footer)
        VALUES (1, 'Snacks', 'superhero', 0.0, 'Snack Lebanese Fast Food', 'Thank you for your visit!')
        ''')

        # Check if we have menu items, if not insert default ones
        cursor.execute("SELECT COUNT(*) FROM menu_items")
        if cursor.fetchone()[0] == 0:
            self.insert_default_menu_items()

        self.db_conn.commit()

    def insert_default_menu_items(self):
        """Insert default menu items into the database"""
        cursor = self.db_conn.cursor()

        default_items = [
            # Snacks
            ('Snacks', 'Fajita Small', 8.50, '1001'),
            ('Snacks', 'Philadelphia Small', 9.00, '1002'),
            ('Snacks', 'Kafta Small', 7.50, '1003'),
            ('Snacks', 'Hamburger Small', 6.50, '1004'),
            ('Snacks', 'Chicken Burger Small', 7.00, '1005'),
            ('Snacks', 'Tawook Small', 8.00, '1006'),
            ('Snacks', 'Liver Small', 7.50, '1007'),
            ('Snacks', 'Shawarma Small', 7.00, '1008'),

            # Drinks
            ('Drinks', 'Coca Cola', 2.50, '2001'),
            ('Drinks', 'Pepsi', 2.50, '2002'),
            ('Drinks', 'Orange Juice', 3.00, '2003'),
            ('Drinks', 'Apple Juice', 3.00, '2004'),

            # Desserts
            ('Desserts', 'Baklava', 4.50, '3001'),
            ('Desserts', 'Muhallabia', 3.50, '3002'),
            ('Desserts', 'Knafeh', 5.00, '3003'),
            ('Desserts', 'Ma\'amoul', 3.00, '3004'),

            # Combos
            ('Combos', 'Fajita Combo', 12.00, '4001'),
            ('Combos', 'Burger Combo', 10.50, '4002'),
            ('Combos', 'Chicken Combo', 11.50, '4003'),
            ('Combos', 'Kafta Combo', 11.00, '4004'),

            # Specials
            ('Specials', 'Chef Special', 18.00, '5001'),
            ('Specials', 'Daily Special', 15.00, '5002'),
            ('Specials', 'Weekend Special', 20.00, '5003'),
            ('Specials', 'Lebanese Platter', 22.00, '5004'),
        ]

        cursor.executemany('''
        INSERT INTO menu_items (category, name, price, barcode)
        VALUES (?, ?, ?, ?)
        ''', default_items)

        self.db_conn.commit()

    def get_default_category(self):
        """Get the default category from settings"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT default_category FROM settings WHERE id = 1")
        result = cursor.fetchone()
        return result[0] if result else 'Snacks'

    def setup_top_frame(self):
        """Setup the top frame with title and time"""
        title_label = ttk.Label(self.TopFrame, text="Snack Lebanese Fast Food",
                                font=('Arial', 16, 'bold'))
        title_label.pack(side='left', padx=20, pady=10)

        # Current time
        self.time_label = ttk.Label(self.TopFrame, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    font=('Arial', 12))
        self.time_label.pack(side='right', padx=20, pady=10)

        # Update time every second
        self.update_time()

    def update_time(self):
        """Update the time display every second"""
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self.update_time)

    def setup_order_summary(self):
        """Setup order summary section"""
        summary_label = ttk.Label(self.CenterFrame3, text="Order Summary",
                                  font=('Arial', 14, 'bold'))
        summary_label.pack(pady=10)

        # Total display
        self.total_frame = ttk.Frame(self.CenterFrame3)
        self.total_frame.pack(pady=10)

        ttk.Label(self.total_frame, text="Total: $", font=('Arial', 12, 'bold')).pack(side='left')
        self.total_label = ttk.Label(self.total_frame, text="0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(side='left')

        # Action buttons
        button_frame = ttk.Frame(self.CenterFrame3)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Clear Order",
                   command=self.clear_order, style='border.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Process Payment",
                   command=self.process_payment, style='border.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="View Orders",
                   command=self.view_orders, style='border.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Print Receipt",
                   command=self.print_receipt, style='border.TButton').pack(side='left', padx=5)

    def create_category_frames(self):
        """Create separate frames for each category with items from database"""
        cursor = self.db_conn.cursor()

        # Get all distinct categories from database
        cursor.execute("SELECT DISTINCT category FROM menu_items WHERE is_active = 1")
        categories = [row[0] for row in cursor.fetchall()]

        if not categories:
            categories = ['Snacks', 'Drinks', 'Desserts', 'Combos', 'Specials']

        # Create frame for each category
        for category in categories:
            frame = ttk.Frame(self.CenterFrame1, width=700, height=450)
            frame.grid(row=0, column=0, sticky='news')
            frame.grid_propagate(False)

            # Get items for this category from database
            cursor.execute("SELECT id, name, price FROM menu_items WHERE category = ? AND is_active = 1", (category,))
            items = cursor.fetchall()

            # Create buttons for this category
            cols = 4  # Number of columns
            category_buttons = []

            for i, (item_id, name, price) in enumerate(items):
                button = ttk.Button(frame, text=f"{name}\n${price:.2f}", width=20,
                                    padding=(0, 15), style='border.TButton',
                                    command=lambda n=name, p=price: self.add_to_order(n, p))
                button.grid(row=i // cols, column=i % cols, padx=2, pady=2, sticky='ew')

                # Add right-click context menu for item management
                button.bind("<Button-3>", lambda e, item_id = item_id: self.show_item_context_menu(e, item_id))

                category_buttons.append(button)

            # Configure column weights for better layout
            for col in range(cols):
                frame.columnconfigure(col, weight=1)

            # Store frame and hide it initially
            self.category_frames[category] = frame
            frame.grid_remove()  # Hide frame initially

    def show_item_context_menu(self, event, item_id):
        """Show context menu for item management"""
        menu = Menu(self, tearoff=0)
        menu.add_command(label="Edit Item", command=lambda: self.edit_item_from_context(item_id))
        menu.add_command(label="Toggle Active", command=lambda: self.toggle_item_active(item_id))
        menu.add_command(label="Delete Item", command=lambda: self.delete_item_from_context(item_id))
        menu.tk_popup(event.x_root, event.y_root)

    def edit_item_from_context(self, item_id):
        """Edit item from context menu"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, category, name, price, barcode FROM menu_items WHERE id = ?", (item_id,))
        item_data = cursor.fetchone()

        if item_data:
            self.edit_menu_item_dialog(item_data)

    def toggle_item_active(self, item_id):
        """Toggle item active status"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT is_active FROM menu_items WHERE id = ?", (item_id,))
        current_status = cursor.fetchone()[0]

        new_status = 0 if current_status else 1

        try:
            cursor.execute("UPDATE menu_items SET is_active = ? WHERE id = ?", (new_status, item_id))
            self.db_conn.commit()

            # Refresh the display
            self.create_category_frames()
            default_category = self.get_default_category()
            self.show_category_frame(default_category)

            messagebox.showinfo("Success", f"Item status updated to {'active' if new_status else 'inactive'}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update item status: {str(e)}")
            self.db_conn.rollback()

    def delete_item_from_context(self, item_id):
        """Delete item from context menu"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name FROM menu_items WHERE id = ?", (item_id,))
        item_name = cursor.fetchone()[0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item_name}'?")
        if confirm:
            try:
                cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
                self.db_conn.commit()

                # Refresh the display
                self.create_category_frames()
                default_category = self.get_default_category()
                self.show_category_frame(default_category)

                messagebox.showinfo("Success", "Item deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item: {str(e)}")
                self.db_conn.rollback()

    def show_category_frame(self, category):
        """Show the selected category frame and hide others"""
        # Hide current frame if exists
        if self.current_frame and self.current_frame in self.category_frames.values():
            self.current_frame.grid_remove()

        # Show selected category frame
        if category in self.category_frames:
            self.category_frames[category].grid()
            self.current_frame = self.category_frames[category]

    def add_to_order(self, item_name, price, quantity=1):
        """Add item to order"""
        # Insert into treeview
        total_price = price * quantity
        self.tree.insert('', 'end', values=(self.order_counter, item_name, f"${price:.2f}", f"${total_price:.2f}"))

        # Add to order list
        self.order_items.append({'id': self.order_counter, 'name': item_name, 'price': price, 'quantity': quantity})
        self.order_counter += 1

        # Update total
        self.update_total()

    def update_total(self):
        """Update the total price display"""
        total = sum(item['price'] * item['quantity'] for item in self.order_items)
        self.total_label.config(text=f"{total:.2f}")

    def clear_order(self):
        """Clear the current order"""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear order list
        self.order_items.clear()
        self.order_counter = 1

        # Update total
        self.update_total()

        messagebox.showinfo("Order Cleared", "Order has been cleared successfully!")

    def process_payment(self):
        """Process the payment and save to database"""
        if not self.order_items:
            messagebox.showwarning("Empty Order", "Please add items to the order first!")
            return

        total = sum(item['price'] * item['quantity'] for item in self.order_items)

        # Create payment dialog
        payment_window = Toplevel(self)
        payment_window.title("Process Payment")
        payment_window.geometry("400x300")
        self.active_toplevels.append(payment_window)

        # Payment method selection
        ttk.Label(payment_window, text="Payment Method:").pack(pady=(20, 5))
        payment_method = ttk.Combobox(payment_window, values=["Cash", "Credit Card", "Debit Card", "Mobile Payment"])
        payment_method.pack(pady=5)
        payment_method.set("Cash")

        # Customer name
        ttk.Label(payment_window, text="Customer Name (Optional):").pack(pady=(10, 5))
        customer_name = ttk.Entry(payment_window)
        customer_name.pack(pady=5)

        # Notes
        ttk.Label(payment_window, text="Notes (Optional):").pack(pady=(10, 5))
        notes = ttk.Entry(payment_window)
        notes.pack(pady=5)

        # Total display
        ttk.Label(payment_window, text=f"Total: ${total:.2f}", font=('Arial', 12, 'bold')).pack(pady=10)

        def process():
            """Process the payment"""
            try:
                cursor = self.db_conn.cursor()

                # Insert order into database
                order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                INSERT INTO orders (order_date, total_amount, payment_method, customer_name, notes)
                VALUES (?, ?, ?, ?, ?)
                ''', (order_date, total, payment_method.get(), customer_name.get(), notes.get()))

                order_id = cursor.lastrowid

                # Insert order items
                for item in self.order_items:
                    # Get item ID from database
                    cursor.execute("SELECT id FROM menu_items WHERE name = ?", (item['name'],))
                    item_id = cursor.fetchone()[0]

                    cursor.execute('''
                    INSERT INTO order_items (order_id, item_id, item_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (order_id, item_id, item['name'], item['quantity'], item['price']))

                self.db_conn.commit()

                messagebox.showinfo("Payment Processed",
                                    f"Payment of ${total:.2f} processed successfully!\nOrder ID: {order_id}")

                # Print receipt if needed
                if messagebox.askyesno("Print Receipt", "Would you like to print a receipt?"):
                    self.print_receipt(order_id)

                payment_window.destroy()
                self.active_toplevels.remove(payment_window)
                self.clear_order()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to save order: {str(e)}")
                self.db_conn.rollback()

        ttk.Button(payment_window, text="Confirm Payment", command=process).pack(pady=10)

    def view_orders(self):
        """Open a window to view past orders"""
        orders_window = Toplevel(self)
        orders_window.title("Order History")
        orders_window.geometry("1000x700")
        self.active_toplevels.append(orders_window)

        # Add filter options
        filter_frame = ttk.Frame(orders_window)
        filter_frame.pack(fill='x', padx=10, pady=10)

        # Date range filter
        ttk.Label(filter_frame, text="From:").pack(side='left')
        self.from_date = ttk.Entry(filter_frame)
        self.from_date.pack(side='left', padx=5)
        self.from_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(filter_frame, text="To:").pack(side='left')
        self.to_date = ttk.Entry(filter_frame)
        self.to_date.pack(side='left', padx=5)
        self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side='left', padx=(10, 0))
        self.status_filter = ttk.Combobox(filter_frame, values=["All", "completed", "cancelled", "refunded"])
        self.status_filter.pack(side='left', padx=5)
        self.status_filter.set("All")

        # Filter button
        ttk.Button(filter_frame, text="Filter", command=lambda: self.load_orders(tree)).pack(side='left', padx=10)

        # Create treeview to display orders
        columns = ['ID', 'Date', 'Total', 'Status', 'Payment', 'Customer']
        tree = ttk.Treeview(orders_window, columns=columns, show='headings', height=20)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Configure columns
        tree.column('ID', width=50, anchor='center')
        tree.column('Date', width=150)
        tree.column('Total', width=100, anchor='center')
        tree.column('Status', width=100, anchor='center')
        tree.column('Payment', width=100)
        tree.column('Customer', width=150)

        # Set headings
        for col in columns:
            tree.heading(col, text=col)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(orders_window, orient="vertical", command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        # Load orders from database
        self.load_orders(tree)

        # Add button to view order details
        def view_order_details():
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select an order first!")
                return

            order_id = tree.item(selected_item)['values'][0]
            self.show_order_details(order_id)

        # Add button to cancel/refund order
        def cancel_order():
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select an order first!")
                return

            order_id = tree.item(selected_item)['values'][0]
            current_status = tree.item(selected_item)['values'][3]

            if current_status == 'completed':
                new_status = 'cancelled'
            elif current_status == 'cancelled':
                new_status = 'completed'
            else:
                messagebox.showwarning("Invalid Action", "Cannot modify this order status")
                return

            confirm = messagebox.askyesno("Confirm", f"Change order status to {new_status}?")
            if confirm:
                try:
                    cursor = self.db_conn.cursor()
                    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
                    self.db_conn.commit()

                    # Refresh the order list
                    self.load_orders(tree)
                    messagebox.showinfo("Success", f"Order status updated to {new_status}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update order: {str(e)}")
                    self.db_conn.rollback()

        button_frame = ttk.Frame(orders_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="View Details", command=view_order_details).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Toggle Status", command=cancel_order).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Print Receipt",
                   command=lambda: self.print_receipt(
                       tree.item(tree.focus())['values'][0] if tree.focus() else None)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", command=lambda: self.close_toplevel(orders_window)).pack(side='left',
                                                                                                        padx=5)

    def load_orders(self, tree):
        """Load orders into the treeview based on filters"""
        # Clear current items
        for item in tree.get_children():
            tree.delete(item)

        # Get filter values
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        status = self.status_filter.get()

        # Build query
        query = "SELECT id, order_date, total_amount, status, payment_method, customer_name FROM orders WHERE 1=1"
        params = []

        if from_date:
            query += " AND date(order_date) >= ?"
            params.append(from_date)

        if to_date:
            query += " AND date(order_date) <= ?"
            params.append(to_date)

        if status != "All":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY order_date DESC"

        # Execute query
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        orders = cursor.fetchall()

        for order in orders:
            tree.insert('', 'end', values=order)

    def show_order_details(self, order_id):
        """Show details of a specific order"""
        details_window = Toplevel(self)
        details_window.title(f"Order Details - #{order_id}")
        details_window.geometry("800x700")
        self.active_toplevels.append(details_window)

        # Create treeview to display order items
        columns = ['Item', 'Quantity', 'Price', 'Total']
        tree = ttk.Treeview(details_window, columns=columns, show='headings', height=15)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Configure columns
        tree.column('Item', width=400)
        tree.column('Quantity', width=100, anchor='center')
        tree.column('Price', width=100, anchor='center')
        tree.column('Total', width=100, anchor='center')

        # Set headings
        for col in columns:
            tree.heading(col, text=col)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        # Load order details from database
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT item_name, quantity, price 
        FROM order_items 
        WHERE order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()

        for item in items:
            name, quantity, price = item
            total = quantity * price
            tree.insert('', 'end', values=(name, quantity, f"${price:.2f}", f"${total:.2f}"))

        # Get order info
        cursor.execute('''
        SELECT order_date, total_amount, status, payment_method, customer_name, notes 
        FROM orders WHERE id = ?
        ''', (order_id,))
        order_info = cursor.fetchone()

        # Display order info
        info_frame = ttk.Frame(details_window)
        info_frame.pack(fill='x', padx=10, pady=10)

        # Left side info
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side='left', fill='y')

        ttk.Label(left_frame, text=f"Order ID: {order_id}").pack(anchor='w')
        ttk.Label(left_frame, text=f"Date: {order_info[0]}").pack(anchor='w')
        ttk.Label(left_frame, text=f"Status: {order_info[2]}").pack(anchor='w')

        # Right side info
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side='right', fill='y')

        ttk.Label(right_frame, text=f"Customer: {order_info[4] or 'N/A'}").pack(anchor='e')
        ttk.Label(right_frame, text=f"Payment: {order_info[3]}").pack(anchor='e')
        ttk.Label(right_frame, text=f"Notes: {order_info[5] or 'N/A'}").pack(anchor='e')

        # Display total
        total_frame = ttk.Frame(details_window)
        total_frame.pack(pady=10)

        ttk.Label(total_frame, text="Total:", font=('Arial', 12, 'bold')).pack(side='left')
        ttk.Label(total_frame, text=f"${order_info[1]:.2f}", font=('Arial', 12, 'bold')).pack(side='left', padx=10)

        button_frame = ttk.Frame(details_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Print Receipt",
                   command=lambda: self.print_receipt(order_id)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close",
                   command=lambda: self.close_toplevel(details_window)).pack(side='left', padx=5)

    def treeView(self, frame):
        """Setup the order display treeview"""
        self.frame1 = ttk.Frame(frame, width=500, height=50)
        self.frame1.pack()

        ttk.Label(self.frame1, text='Barcode:').pack(side='left', pady=(0, 10))

        self.ETN1 = ttk.Entry(self.frame1, font=('Arial', 12), width=30)
        self.ETN1.pack(side='left', pady=(0, 10), padx=(5, 0))

        # Add barcode search button
        ttk.Button(self.frame1, text="Search", style='border.TButton',
                   command=self.search_barcode).pack(side='left', padx=(5, 0))

        # Add manual quantity entry
        ttk.Label(self.frame1, text="Qty:").pack(side='left', padx=(10, 0))
        self.quantity_entry = ttk.Entry(self.frame1, font=('Arial', 12), width=5)
        self.quantity_entry.pack(side='left', pady=(0, 10))
        self.quantity_entry.insert(0, "1")

        columns = [1, 2, 3, 4]
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
        self.tree.pack(anchor='nw', fill='both', expand=True)

        self.tree.column(1, width=40, anchor='center')
        self.tree.column(2, width=250)
        self.tree.column(3, width=100, anchor='center')
        self.tree.column(4, width=100, anchor='center')

        self.tree.heading(1, text='ID')
        self.tree.heading(2, text='DESCRIPTION')
        self.tree.heading(3, text='UNIT PRICE')
        self.tree.heading(4, text='TOTAL PRICE')

        # Add double-click to remove item
        self.tree.bind('<Double-1>', self.remove_item)

        # Bind Enter key to barcode search
        self.ETN1.bind('<Return>', lambda e: self.search_barcode())

    def search_barcode(self):
        """Search for item by barcode"""
        barcode = self.ETN1.get().strip()
        if not barcode:
            messagebox.showwarning("Empty Barcode", "Please enter a barcode to search!")
            return

        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, price FROM menu_items WHERE barcode = ?", (barcode,))
        item = cursor.fetchone()

        if item:
            name, price = item
            try:
                quantity = int(self.quantity_entry.get())
                if quantity < 1:
                    raise ValueError
            except ValueError:
                quantity = 1
                self.quantity_entry.delete(0, 'end')
                self.quantity_entry.insert(0, "1")

            self.add_to_order(name, price, quantity)
            self.ETN1.delete(0, 'end')
        else:
            messagebox.showwarning("Not Found", f"No item found with barcode: {barcode}")

    def remove_item(self, event):
        """Remove selected item from order"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            item_id = int(item['values'][0])

            # Remove from treeview
            self.tree.delete(selection[0])

            # Remove from order list
            self.order_items = [item for item in self.order_items if item['id'] != item_id]

            # Update total
            self.update_total()

    def bottom_main(self, frame):
        """Create category buttons and settings button"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM menu_items WHERE is_active = 1")
        categories = [row[0] for row in cursor.fetchall()]

        if not categories:
            categories = ['Snacks', 'Drinks', 'Desserts', 'Combos', 'Specials']

        self.buttons_2 = []

        for i, name in enumerate(categories):
            button = ttk.Button(frame, text=name, width=15, padding=(0, 22),
                                style='border.TButton',
                                command=lambda n=name: self.show_category_frame(n))
            button.grid(row=0, column=i, padx=2, pady=2)
            self.buttons_2.append(button)

        # Add Settings button
        settings_button = ttk.Button(frame, text="Settings", width=15, padding=(0, 22),
                                     style='border.TButton',
                                     command=self.open_settings)
        settings_button.grid(row=0, column=len(categories), padx=2, pady=2)

        # Add Admin button for advanced controls
        admin_button = ttk.Button(frame, text="Admin", width=15, padding=(0, 22),
                                  style='border.TButton',
                                  command=self.open_admin_panel)
        admin_button.grid(row=0, column=len(categories) + 1, padx=2, pady=2)

    def open_admin_panel(self):
        """Open the admin panel with advanced controls"""
        admin_window = Toplevel(self)
        admin_window.title("Admin Panel")
        admin_window.geometry("800x800")
        self.active_toplevels.append(admin_window)

        # Create notebook for different admin tabs
        notebook = ttk.Notebook(admin_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Database Management Tab
        db_frame = ttk.Frame(notebook)
        notebook.add(db_frame, text="Database")

        # Backup and restore buttons
        ttk.Button(db_frame, text="Backup Database",
                   command=self.backup_database).pack(pady=10)
        ttk.Button(db_frame, text="Restore Database",
                   command=self.restore_database).pack(pady=10)

        # Reports Tab
        reports_frame = ttk.Frame(notebook)
        notebook.add(reports_frame, text="Reports")

        ttk.Button(reports_frame, text="Sales Report",
                   command=self.generate_sales_report).pack(pady=10)
        ttk.Button(reports_frame, text="Inventory Report",
                   command=self.generate_inventory_report).pack(pady=10)

        # System Tab
        system_frame = ttk.Frame(notebook)
        notebook.add(system_frame, text="System")

        ttk.Button(system_frame, text="Clear All Orders",
                   command=self.clear_all_orders).pack(pady=10)
        ttk.Button(system_frame, text="Reset Menu Items",
                   command=self.reset_menu_items).pack(pady=10)

        # Close button
        ttk.Button(admin_window, text="Close",
                   command=lambda: self.close_toplevel(admin_window)).pack(pady=10)

    def backup_database(self):
        """Backup the database to a file"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"pos_backup_{timestamp}.db")

            # Close current connection
            if self.db_conn:
                self.db_conn.close()

            # Copy the database file
            import shutil
            shutil.copy2('pos_database.db', backup_file)

            # Reopen connection
            self.db_conn = sql.connect('pos_database.db')

            messagebox.showinfo("Success", f"Database backed up to:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {str(e)}")
            # Reopen connection if something went wrong
            self.db_conn = sql.connect('pos_database.db')

    def restore_database(self):
        """Restore database from backup"""
        backup_window = Toplevel(self)
        backup_window.title("Restore Database")
        backup_window.geometry("600x400")
        self.active_toplevels.append(backup_window)

        # List available backups
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]

        if not backups:
            ttk.Label(backup_window, text="No backup files found").pack(pady=20)
            return

        # Create listbox with backups
        listbox = Listbox(backup_window)
        for backup in backups:
            listbox.insert('end', backup)
        listbox.pack(fill='both', expand=True, padx=10, pady=10)

        def restore_selected():
            """Restore the selected backup"""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup file")
                return

            backup_file = os.path.join(backup_dir, listbox.get(selection[0]))

            confirm = messagebox.askyesno("Confirm Restore",
                                          "This will overwrite the current database.\nContinue?")
            if confirm:
                try:
                    # Close current connection
                    if self.db_conn:
                        self.db_conn.close()

                    # Copy the backup file
                    import shutil
                    shutil.copy2(backup_file, 'pos_database.db')

                    # Reopen connection
                    self.db_conn = sql.connect('pos_database.db')

                    messagebox.showinfo("Success", "Database restored successfully!\nPlease restart the application.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to restore database: {str(e)}")
                    # Reopen connection if something went wrong
                    self.db_conn = sql.connect('pos_database.db')

        ttk.Button(backup_window, text="Restore Selected",
                   command=restore_selected).pack(pady=10)
        ttk.Button(backup_window, text="Close",
                   command=lambda: self.close_toplevel(backup_window)).pack(pady=10)

    def generate_sales_report(self):
        """Generate and display a sales report"""
        report_window = Toplevel(self)
        report_window.title("Sales Report")
        report_window.geometry("800x600")
        self.active_toplevels.append(report_window)

        # Date range selection
        filter_frame = ttk.Frame(report_window)
        filter_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(filter_frame, text="From:").pack(side='left')
        from_date = ttk.Entry(filter_frame)
        from_date.pack(side='left', padx=5)
        from_date.insert(0, datetime.now().strftime("%Y-%m-01"))  # First day of current month

        ttk.Label(filter_frame, text="To:").pack(side='left')
        to_date = ttk.Entry(filter_frame)
        to_date.pack(side='left', padx=5)
        to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Group by options
        ttk.Label(filter_frame, text="Group by:").pack(side='left', padx=(10, 0))
        group_by = ttk.Combobox(filter_frame, values=["Day", "Week", "Month", "Category", "Item"])
        group_by.pack(side='left', padx=5)
        group_by.set("Day")

        # Generate button
        def generate_report():
            """Generate the report based on selected filters"""
            # Clear previous results
            for widget in results_frame.winfo_children():
                widget.destroy()

            # Get filter values
            date_from = from_date.get()
            date_to = to_date.get()
            group_option = group_by.get().lower()

            # Build query
            if group_option in ['day', 'week', 'month']:
                if group_option == 'day':
                    date_format = "date(order_date)"
                elif group_option == 'week':
                    date_format = "strftime('%Y-%W', order_date)"
                else:  # month
                    date_format = "strftime('%Y-%m', order_date)"

                query = f"""
                SELECT {date_format} as period, 
                       COUNT(*) as orders, 
                       SUM(total_amount) as total_sales
                FROM orders
                WHERE date(order_date) BETWEEN ? AND ?
                GROUP BY period
                ORDER BY period
                """

                cursor = self.db_conn.cursor()
                cursor.execute(query, (date_from, date_to))
                results = cursor.fetchall()

                # Display results
                if not results:
                    ttk.Label(results_frame, text="No data found for selected period").pack(pady=20)
                    return

                # Create treeview
                columns = ['Period', 'Orders', 'Total Sales']
                tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
                tree.pack(fill='both', expand=True, padx=10, pady=10)

                for col in columns:
                    tree.column(col, width=100, anchor='center')
                    tree.heading(col, text=col)

                for row in results:
                    period, orders, total = row
                    tree.insert('', 'end', values=(period, orders, f"${total:.2f}"))

                # Add summary
                total_sales = sum(row[2] for row in results)
                avg_sales = total_sales / len(results) if results else 0

                summary_frame = ttk.Frame(results_frame)
                summary_frame.pack(fill='x', pady=10)

                ttk.Label(summary_frame, text=f"Total Sales: ${total_sales:.2f}",
                          font=('Arial', 12, 'bold')).pack(side='left', padx=10)
                ttk.Label(summary_frame, text=f"Average per {group_option}: ${avg_sales:.2f}",
                          font=('Arial', 12, 'bold')).pack(side='left', padx=10)

            elif group_option in ['category', 'item']:
                if group_option == 'category':
                    join_clause = "JOIN menu_items mi ON oi.item_id = mi.id"
                    group_clause = "mi.category"
                else:  # item
                    join_clause = "JOIN menu_items mi ON oi.item_id = mi.id"
                    group_clause = "oi.item_name"

                query = f"""
                SELECT {group_clause} as name,
                       SUM(oi.quantity) as quantity,
                       SUM(oi.price * oi.quantity) as total_sales
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                {join_clause}
                WHERE date(o.order_date) BETWEEN ? AND ?
                GROUP BY name
                ORDER BY total_sales DESC
                """

                cursor = self.db_conn.cursor()
                cursor.execute(query, (date_from, date_to))
                results = cursor.fetchall()

                # Display results
                if not results:
                    ttk.Label(results_frame, text="No data found for selected period").pack(pady=20)
                    return

                # Create treeview
                columns = ['Name', 'Quantity', 'Total Sales']
                tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
                tree.pack(fill='both', expand=True, padx=10, pady=10)

                for col in columns:
                    tree.column(col, width=100, anchor='center')
                    tree.heading(col, text=col)

                for row in results:
                    name, quantity, total = row
                    tree.insert('', 'end', values=(name, quantity, f"${total:.2f}"))

                # Add summary
                total_sales = sum(row[2] for row in results)
                total_quantity = sum(row[1] for row in results)

                summary_frame = ttk.Frame(results_frame)
                summary_frame.pack(fill='x', pady=10)

                ttk.Label(summary_frame, text=f"Total Sales: ${total_sales:.2f}",
                          font=('Arial', 12, 'bold')).pack(side='left', padx=10)
                ttk.Label(summary_frame, text=f"Total Items Sold: {total_quantity}",
                          font=('Arial', 12, 'bold')).pack(side='left', padx=10)

        ttk.Button(filter_frame, text="Generate", command=generate_report).pack(side='left', padx=10)

        # Export button
        def export_report():
            """Export the report to CSV"""
            # TODO: Implement CSV export functionality
            messagebox.showinfo("Export", "Export functionality will be implemented here")

        ttk.Button(filter_frame, text="Export", command=export_report).pack(side='left', padx=5)

        # Results frame
        results_frame = ttk.Frame(report_window)
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Close button
        ttk.Button(report_window, text="Close",
                   command=lambda: self.close_toplevel(report_window)).pack(pady=10)

    def generate_inventory_report(self):
        """Generate and display an inventory report"""
        report_window = Toplevel(self)
        report_window.title("Inventory Report")
        report_window.geometry("800x600")
        self.active_toplevels.append(report_window)

        # Create treeview
        columns = ['ID', 'Category', 'Name', 'Price', 'Barcode', 'Status']
        tree = ttk.Treeview(report_window, columns=columns, show='headings', height=25)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Configure columns
        tree.column('ID', width=50, anchor='center')
        tree.column('Category', width=100)
        tree.column('Name', width=200)
        tree.column('Price', width=80, anchor='center')
        tree.column('Barcode', width=100)
        tree.column('Status', width=80, anchor='center')

        # Set headings
        for col in columns:
            tree.heading(col, text=col)

        # Load data
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, category, name, price, barcode, is_active FROM menu_items")
        items = cursor.fetchall()

        for item in items:
            item_id, category, name, price, barcode, is_active = item
            status = "Active" if is_active else "Inactive"
            tree.insert('', 'end', values=(item_id, category, name, f"${price:.2f}", barcode or '', status))

        # Add summary
        summary_frame = ttk.Frame(report_window)
        summary_frame.pack(fill='x', pady=10)

        active_count = sum(1 for item in items if item[5])
        inactive_count = len(items) - active_count

        ttk.Label(summary_frame, text=f"Total Items: {len(items)}",
                  font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        ttk.Label(summary_frame, text=f"Active: {active_count}",
                  font=('Arial', 12, 'bold')).pack(side='left', padx=10)
        ttk.Label(summary_frame, text=f"Inactive: {inactive_count}",
                  font=('Arial', 12, 'bold')).pack(side='left', padx=10)

        # Close button
        ttk.Button(report_window, text="Close",
                   command=lambda: self.close_toplevel(report_window)).pack(pady=10)

    def clear_all_orders(self):
        """Clear all orders from the database"""
        confirm = messagebox.askyesno("Confirm",
                                      "This will delete ALL order history.\nAre you sure?")
        if confirm:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM order_items")
                cursor.execute("DELETE FROM orders")
                cursor.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='order_items'")
                cursor.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='orders'")
                self.db_conn.commit()

                messagebox.showinfo("Success", "All orders have been cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear orders: {str(e)}")
                self.db_conn.rollback()

    def reset_menu_items(self):
        """Reset menu items to default"""
        confirm = messagebox.askyesno("Confirm",
                                      "This will reset ALL menu items to defaults.\nAre you sure?")
        if confirm:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM menu_items")
                cursor.execute("UPDATE sqlite_sequence SET seq=0 WHERE name='menu_items'")
                self.insert_default_menu_items()

                # Refresh the display
                self.create_category_frames()
                default_category = self.get_default_category()
                self.show_category_frame(default_category)

                messagebox.showinfo("Success", "Menu items reset to defaults")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset menu items: {str(e)}")
                self.db_conn.rollback()

    def open_settings(self):
        """Open the settings window"""
        settings_window = Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("600x700")
        self.active_toplevels.append(settings_window)

        # Create notebook for different settings tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Menu Items Tab
        menu_frame = ttk.Frame(notebook)
        notebook.add(menu_frame, text="Menu Items")

        # Add treeview for menu items
        columns = ['ID', 'Category', 'Name', 'Price', 'Barcode', 'Status']
        tree = ttk.Treeview(menu_frame, columns=columns, show='headings', height=15)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Configure columns
        tree.column('ID', width=50, anchor='center')
        tree.column('Category', width=100)
        tree.column('Name', width=150)
        tree.column('Price', width=80, anchor='center')
        tree.column('Barcode', width=100)
        tree.column('Status', width=80, anchor='center')

        # Set headings
        for col in columns:
            tree.heading(col, text=col)

        # Load menu items from database
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, category, name, price, barcode, is_active FROM menu_items")
        items = cursor.fetchall()

        for item in items:
            item_id, category, name, price, barcode, is_active = item
            status = "Active" if is_active else "Inactive"
            tree.insert('', 'end', values=(item_id, category, name, f"${price:.2f}", barcode or '', status))

        # Add buttons for menu management
        button_frame = ttk.Frame(menu_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Add Item", command=lambda: self.add_menu_item_dialog(tree)).pack(side='left',
                                                                                                        padx=5)
        ttk.Button(button_frame, text="Edit Item", command=lambda: self.edit_menu_item_dialog(tree)).pack(side='left',
                                                                                                          padx=5)
        ttk.Button(button_frame, text="Delete Item", command=lambda: self.delete_menu_item_dialog(tree)).pack(
            side='left', padx=5)

        # Application Settings Tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Application Settings")

        # Get current settings

        cursor.execute(
            "SELECT default_category, theme_name, tax_rate, receipt_header, receipt_footer FROM settings WHERE id = 1")
        default_category, theme_name, tax_rate, receipt_header, receipt_footer = cursor.fetchone()


        cursor.execute("SELECT DISTINCT theme_name FROM settings")
        theme_name_get = cursor.fetchall()

        combo_value = [row[0] for row in theme_name_get]

        # Default category setting
        ttk.Label(settings_frame, text="Default Category:").pack(pady=(20, 5))

        cursor.execute("SELECT DISTINCT category FROM menu_items")
        categories = [row[0] for row in cursor.fetchall()]

        self.default_category_var = StringVar(value=default_category)
        category_combo = ttk.Combobox(settings_frame, textvariable=self.default_category_var,
                                      values=categories, state='readonly')
        category_combo.pack(pady=5)

        # Theme setting
        ttk.Label(settings_frame, text="Theme:").pack(pady=(20, 5))

        themes = ['cosmo', 'flatly', 'litera', 'minty', 'lumen', 'sandstone', 'yeti', 'pulse', 'united',
                  'morph', 'journal', 'darkly', 'superhero', 'solar', 'cyborg', 'vapor', 'simplex',
                  'cerculean']  # Add more themes as needed
        self.theme_var = StringVar(value=theme_name)
        theme_combo = ttk.Combobox(settings_frame, textvariable=self.theme_var,
                                   values=themes, state='readonly')
        theme_combo.pack(pady=5)

        # with open('theme_name.txt', 'w') as f:
        #     f.write(self.theme_var.get())
        #
        # with open('theme_name.txt', 'r') as f:
        #     file = f.read()

        # Tax rate setting
        ttk.Label(settings_frame, text="Tax Rate (%):").pack(pady=(20, 5))
        self.tax_rate_var = StringVar(value=str(tax_rate))
        tax_rate_entry = ttk.Entry(settings_frame, textvariable=self.tax_rate_var)
        tax_rate_entry.pack(pady=5)

        # Receipt header
        ttk.Label(settings_frame, text="Receipt Header:").pack(pady=(20, 5))
        self.receipt_header_var = StringVar(value=receipt_header)
        receipt_header_entry = ttk.Entry(settings_frame, textvariable=self.receipt_header_var)
        receipt_header_entry.pack(pady=5)

        # Receipt footer
        ttk.Label(settings_frame, text="Receipt Footer:").pack(pady=(20, 5))
        self.receipt_footer_var = StringVar(value=receipt_footer)
        receipt_footer_entry = ttk.Entry(settings_frame, textvariable=self.receipt_footer_var)
        receipt_footer_entry.pack(pady=5)

        # Save settings button
        ttk.Button(settings_frame, text="Save Settings",
                   command=lambda: self.save_settings(settings_window)).pack(pady=20)

    def add_menu_item_dialog(self, tree):
        """Open dialog to add new menu item"""
        add_window = Toplevel(self)
        add_window.title("Add Menu Item")
        add_window.geometry("400x500")
        self.active_toplevels.append(add_window)

        # Form fields
        ttk.Label(add_window, text="Category:").pack(pady=(20, 5))
        category_entry = ttk.Entry(add_window)
        category_entry.pack(pady=5)

        ttk.Label(add_window, text="Name:").pack(pady=(10, 5))
        name_entry = ttk.Entry(add_window)
        name_entry.pack(pady=5)

        ttk.Label(add_window, text="Price:").pack(pady=(10, 5))
        price_entry = ttk.Entry(add_window)
        price_entry.pack(pady=5)

        ttk.Label(add_window, text="Barcode:").pack(pady=(10, 5))
        barcode_entry = ttk.Entry(add_window)
        barcode_entry.pack(pady=5)

        ttk.Label(add_window, text="Status:").pack(pady=(10, 5))
        status_var = IntVar(value=1)
        ttk.Checkbutton(add_window, text="Active", variable=status_var).pack(pady=5)

        def save_item():
            """Save the new menu item to database"""
            category = category_entry.get().strip()
            name = name_entry.get().strip()
            price = price_entry.get().strip()
            barcode = barcode_entry.get().strip()
            is_active = status_var.get()

            if not all([category, name, price]):
                messagebox.showwarning("Missing Fields", "Please fill in all required fields!")
                return

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid Price", "Please enter a valid positive price!")
                return

            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                INSERT INTO menu_items (category, name, price, barcode, is_active)
                VALUES (?, ?, ?, ?, ?)
                ''', (category, name, price, barcode if barcode else None, is_active))

                self.db_conn.commit()

                # Refresh the treeview
                self.refresh_menu_items_tree(tree)

                # Also refresh category frames if needed
                if category not in self.category_frames:
                    self.create_category_frames()
                    self.bottom_main(self.BottomFrame)

                messagebox.showinfo("Success", "Menu item added successfully!")
                add_window.destroy()
                self.active_toplevels.remove(add_window)
            except sql.IntegrityError:
                messagebox.showerror("Error", "Barcode must be unique!")
                self.db_conn.rollback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add menu item: {str(e)}")
                self.db_conn.rollback()

        ttk.Button(add_window, text="Save", command=save_item).pack(pady=20)

    def edit_menu_item_dialog(self, tree, item_data=None):
        """Open dialog to edit menu item"""
        if not item_data:
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("No Selection", "Please select a menu item first!")
                return

            item_data = tree.item(selected_item)['values']
            item_id, category, name, price_str, barcode, status = item_data
            price = float(price_str.replace('$', ''))
            is_active = 1 if status == "Active" else 0
        else:
            item_id, category, name, price, barcode = item_data
            is_active = 1

        edit_window = Toplevel(self)
        edit_window.title("Edit Menu Item")
        edit_window.geometry("400x400")
        self.active_toplevels.append(edit_window)

        # Form fields with current values
        ttk.Label(edit_window, text="Category:").pack(pady=(20, 5))
        category_entry = ttk.Entry(edit_window)
        category_entry.insert(0, category)
        category_entry.pack(pady=5)

        ttk.Label(edit_window, text="Name:").pack(pady=(10, 5))
        name_entry = ttk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.pack(pady=5)

        ttk.Label(edit_window, text="Price:").pack(pady=(10, 5))
        price_entry = ttk.Entry(edit_window)
        price_entry.insert(0, str(price))
        price_entry.pack(pady=5)

        ttk.Label(edit_window, text="Barcode:").pack(pady=(10, 5))
        barcode_entry = ttk.Entry(edit_window)
        barcode_entry.insert(0, barcode if barcode else '')
        barcode_entry.pack(pady=5)

        ttk.Label(edit_window, text="Status:").pack(pady=(10, 5))
        status_var = IntVar(value=is_active)
        ttk.Checkbutton(edit_window, text="Active", variable=status_var).pack(pady=5)

        def save_changes():
            """Save the edited menu item to database"""
            new_category = category_entry.get().strip()
            new_name = name_entry.get().strip()
            new_price = price_entry.get().strip()
            new_barcode = barcode_entry.get().strip()
            new_active = status_var.get()

            if not all([new_category, new_name, new_price]):
                messagebox.showwarning("Missing Fields", "Please fill in all required fields!")
                return

            try:
                new_price = float(new_price)
                if new_price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid Price", "Please enter a valid positive price!")
                return

            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                UPDATE menu_items
                SET category = ?, name = ?, price = ?, barcode = ?, is_active = ?
                WHERE id = ?
                ''', (new_category, new_name, new_price, new_barcode if new_barcode else None, new_active, item_id))

                self.db_conn.commit()

                # Refresh the treeview
                self.refresh_menu_items_tree(tree)

                # Also refresh category frames if needed
                if new_category != category:
                    self.create_category_frames()
                    self.bottom_main(self.BottomFrame)

                messagebox.showinfo("Success", "Menu item updated successfully!")
                edit_window.destroy()
                self.active_toplevels.remove(edit_window)
            except sql.IntegrityError:
                messagebox.showerror("Error", "Barcode must be unique!")
                self.db_conn.rollback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update menu item: {str(e)}")
                self.db_conn.rollback()

        ttk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=20)

    def delete_menu_item_dialog(self, tree):
        """Delete selected menu item from database"""
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a menu item first!")
            return

        item_data = tree.item(selected_item)['values']
        item_id, category, name, price, barcode, status = item_data

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete '{name}' from the menu?")
        if confirm:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
                self.db_conn.commit()

                # Refresh the treeview
                self.refresh_menu_items_tree(tree)

                # Also refresh category frames
                self.create_category_frames()
                self.bottom_main(self.BottomFrame)

                messagebox.showinfo("Success", "Menu item deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete menu item: {str(e)}")
                self.db_conn.rollback()

    def refresh_menu_items_tree(self, tree):
        """Refresh the menu items treeview with current data"""
        # Clear current items
        for item in tree.get_children():
            tree.delete(item)

        # Load fresh data
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, category, name, price, barcode, is_active FROM menu_items")
        items = cursor.fetchall()

        for item in items:
            item_id, category, name, price, barcode, is_active = item
            status = "Active" if is_active else "Inactive"
            tree.insert('', 'end', values=(item_id, category, name, f"${price:.2f}", barcode or '', status))

    def save_settings(self, settings_window):
        """Save application settings to database"""
        default_category = self.default_category_var.get()
        theme_name = self.theme_var.get()

        try:
            tax_rate = float(self.tax_rate_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for tax rate")
            return

        receipt_header = self.receipt_header_var.get()
        receipt_footer = self.receipt_footer_var.get()

        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            UPDATE settings
            SET default_category = ?, theme_name = ?, tax_rate = ?, receipt_header = ?, receipt_footer = ?
            WHERE id = 1
            ''', (default_category, theme_name, tax_rate, receipt_header, receipt_footer))

            self.db_conn.commit()

            # Update theme if changed
            if theme_name != self.theme_name:
                self.theme_name = theme_name
                self.configure(background=color(self.theme_name, 'bg'))
                style_defaults(self, self.style, self.theme_name)
                messagebox.showinfo("Theme Changed", "Application theme has been updated.")

            messagebox.showinfo("Success", "Settings saved successfully!")
            settings_window.destroy()
            self.active_toplevels.remove(settings_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            self.db_conn.rollback()

        with open('theme_name.txt', 'w') as f:
            f.write(self.theme_var.get())

    def print_receipt(self, order_id=None):
        """Print or preview a receipt for an order"""
        if order_id is None and not self.order_items:
            messagebox.showwarning("Empty Order", "No order to print receipt for!")
            return

        # Create receipt window
        receipt_window = Toplevel(self)
        receipt_window.title("Receipt Preview")
        receipt_window.geometry("400x600")
        self.active_toplevels.append(receipt_window)

        # Get receipt settings
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT receipt_header, receipt_footer, tax_rate FROM settings WHERE id = 1")
        header, footer, tax_rate = cursor.fetchone()

        # Create text widget for receipt
        receipt_text = Text(receipt_window, font=('Courier New', 12), width=40, height=30)
        receipt_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Add header
        receipt_text.insert('end', f"{header.center(40)}\n\n", 'center')
        receipt_text.insert('end', f"{'=' * 40}\n")

        # Add order info
        if order_id:
            # Existing order
            cursor.execute("SELECT order_date, total_amount, payment_method FROM orders WHERE id = ?", (order_id,))
            order_date, total_amount, payment_method = cursor.fetchone()

            cursor.execute("""
            SELECT item_name, quantity, price 
            FROM order_items 
            WHERE order_id = ?
            """, (order_id,))
            items = cursor.fetchall()

            receipt_text.insert('end', f"Order #: {order_id}\n")
            receipt_text.insert('end', f"Date: {order_date}\n")
        else:
            # Current order
            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_amount = sum(item['price'] * item['quantity'] for item in self.order_items)
            payment_method = "Cash"  # Default

            items = [(item['name'], item['quantity'], item['price']) for item in self.order_items]

            receipt_text.insert('end', "NEW ORDER\n")
            receipt_text.insert('end', f"Date: {order_date}\n")

        receipt_text.insert('end', f"{'-' * 40}\n")

        # Add items
        for name, quantity, price in items:
            line = f"{quantity}x {name[:20]:20} ${price * quantity:7.2f}\n"
            receipt_text.insert('end', line)

        receipt_text.insert('end', f"{'-' * 40}\n")

        # Calculate totals
        subtotal = total_amount / (1 + tax_rate / 100)
        tax = subtotal * (tax_rate / 100)

        receipt_text.insert('end', f"Subtotal: ${subtotal:27.2f}\n")
        receipt_text.insert('end', f"Tax ({tax_rate}%): ${tax:25.2f}\n")
        receipt_text.insert('end', f"Total: ${total_amount:29.2f}\n")
        receipt_text.insert('end', f"{'-' * 40}\n")
        receipt_text.insert('end', f"Payment: {payment_method}\n")
        receipt_text.insert('end', f"{'=' * 40}\n")

        # Add footer
        receipt_text.insert('end', f"\n{footer.center(40)}\n", 'center')

        # Configure tags for centering
        receipt_text.tag_configure('center', justify='center')

        # Add print button
        button_frame = ttk.Frame(receipt_window)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Print", command=lambda: self.do_print(receipt_text)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", command=lambda: self.close_toplevel(receipt_window)).pack(side='left',
                                                                                                         padx=5)

    def do_print(self, text_widget):
        """Print the receipt"""
        # TODO: Implement actual printing functionality
        messagebox.showinfo("Print", "Print functionality will be implemented here")

    def close_toplevel(self, toplevel):
        """Close a toplevel window and remove from active list"""
        toplevel.destroy()
        if toplevel in self.active_toplevels:
            self.active_toplevels.remove(toplevel)


def root():
    app = Window()
    app.mainloop()


if __name__ == '__main__':
    root()