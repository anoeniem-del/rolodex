import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Database setup
conn = sqlite3.connect("rolodex.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        phone TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_name TEXT NOT NULL UNIQUE
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        field_id INTEGER NOT NULL,
        value TEXT,
        FOREIGN KEY (contact_id) REFERENCES contacts(id),
        FOREIGN KEY (field_id) REFERENCES fields(id)
    )
""")

conn.commit()

# ---- MAIN WINDOW ----

root = tk.Tk()
root.title("Rolodex")
root.geometry("900x600")
root.iconbitmap("rolodex.ico")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

contacts_frame = ttk.Frame(notebook)
fields_frame = ttk.Frame(notebook)

notebook.add(contacts_frame, text="Contacts")
notebook.add(fields_frame, text="Manage Fields")
# ---- ALL FUNCTIONS ----

def load_contacts(search_field=None, search_value=None):
    for row in contact_tree.get_children():
        contact_tree.delete(row)
    if search_field and search_value:
        if search_field == "Name":
            cursor.execute("SELECT id, name, description, phone FROM contacts WHERE name LIKE ?", (f"%{search_value}%",))
            rows = cursor.fetchall()
        elif search_field == "Phone":
            cursor.execute("SELECT id, name, description, phone FROM contacts WHERE phone LIKE ?", (f"%{search_value}%",))
            rows = cursor.fetchall()
        elif search_field == "Description":
            cursor.execute("SELECT id, name, description, phone FROM contacts WHERE description LIKE ?", (f"%{search_value}%",))
            rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT c.id, c.name, c.description, c.phone
                FROM contacts c
                JOIN contact_fields cf ON c.id = cf.contact_id
                JOIN fields f ON cf.field_id = f.id
                WHERE f.field_name = ? AND cf.value LIKE ?
            """, (search_field, f"%{search_value}%"))
            rows = cursor.fetchall()
    else:
        cursor.execute("SELECT id, name, description, phone FROM contacts ORDER BY name")
        rows = cursor.fetchall()
    if not rows:
        messagebox.showinfo("Not Found", "No contacts found.")
    else:
        for row in rows:
            contact_tree.insert("", "end", values=(row[0], row[1], row[2] or "", row[3]))

def search_contact():
    search_value = entry_search.get().strip()
    search_field = search_dropdown.get()
    if not search_value:
        load_contacts()
        return
    load_contacts(search_field, search_value)

def load_fields():
    for row in fields_tree.get_children():
        fields_tree.delete(row)
    cursor.execute("SELECT id, field_name FROM fields ORDER BY field_name")
    for row in cursor.fetchall():
        fields_tree.insert("", "end", values=(row[0], row[1]))
    update_search_dropdown()

def update_search_dropdown():
    cursor.execute("SELECT field_name FROM fields ORDER BY field_name")
    custom_fields = [row[0] for row in cursor.fetchall()]
    all_fields = ["Name", "Phone", "Description"] + custom_fields
    search_dropdown["values"] = all_fields
    if search_dropdown.get() not in all_fields:
        search_dropdown.set("Name")

def add_field():
    field_name = entry_field_name.get().strip()
    if not field_name:
        messagebox.showwarning("Missing Info", "Please enter a field name.")
        return
    cursor.execute("SELECT COUNT(*) FROM fields")
    count = cursor.fetchone()[0]
    if count >= 15:
        messagebox.showerror("Limit Reached", "You can only have 15 custom fields.")
        return
    try:
        cursor.execute("INSERT INTO fields (field_name) VALUES (?)", (field_name,))
        conn.commit()
        entry_field_name.delete(0, tk.END)
        load_fields()
    except sqlite3.IntegrityError:
        messagebox.showerror("Duplicate", f"'{field_name}' already exists.")

def delete_field():
    selected = fields_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a field to delete.")
        return
    item = fields_tree.item(selected[0])
    field_id = item["values"][0]
    field_name = item["values"][1]
    confirm = messagebox.askyesno("Confirm Delete", f"Delete field '{field_name}'?\nThis will remove this field from all contacts.")
    if confirm:
        cursor.execute("DELETE FROM contact_fields WHERE field_id = ?", (field_id,))
        cursor.execute("DELETE FROM fields WHERE id = ?", (field_id,))
        conn.commit()
        load_fields()

def open_add_contact():
    popup = tk.Toplevel(root)
    popup.title("Add New Contact")
    popup.geometry("400x500")
    popup.grab_set()

    ttk.Label(popup, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    entry_pop_name = ttk.Entry(popup, width=30)
    entry_pop_name.grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(popup, text="Description:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_pop_desc = ttk.Entry(popup, width=30)
    entry_pop_desc.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(popup, text="Phone:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry_pop_phone = ttk.Entry(popup, width=30)
    entry_pop_phone.grid(row=2, column=1, padx=10, pady=5)

    ttk.Separator(popup, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
    ttk.Label(popup, text="Custom Fields", font=("Helvetica", 9, "bold")).grid(row=4, column=0, columnspan=2, pady=2)

    cursor.execute("SELECT id, field_name FROM fields ORDER BY field_name")
    custom_fields = cursor.fetchall()
    field_entries = {}
    for i, (field_id, field_name) in enumerate(custom_fields):
        ttk.Label(popup, text=f"{field_name}:").grid(row=5+i, column=0, padx=10, pady=3, sticky="w")
        entry = ttk.Entry(popup, width=30)
        entry.grid(row=5+i, column=1, padx=10, pady=3)
        field_entries[field_id] = entry

    def confirm_add():
        name = entry_pop_name.get().strip()
        description = entry_pop_desc.get().strip()
        phone = entry_pop_phone.get().strip()
        if not name or not phone:
            messagebox.showwarning("Missing Info", "Name and Phone are required.", parent=popup)
            return
        cursor.execute("INSERT INTO contacts (name, description, phone) VALUES (?, ?, ?)", (name, description, phone))
        contact_id = cursor.lastrowid
        for field_id, entry in field_entries.items():
            value = entry.get().strip()
            if value:
                cursor.execute("INSERT INTO contact_fields (contact_id, field_id, value) VALUES (?, ?, ?)", (contact_id, field_id, value))
        conn.commit()
        load_contacts()
        popup.destroy()

    ttk.Button(popup, text="Save Contact", command=confirm_add).grid(row=5+len(custom_fields), column=0, columnspan=2, pady=15)

def open_modify_contact():
    selected = contact_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a contact to modify.")
        return
    item = contact_tree.item(selected[0])
    contact_id = item["values"][0]
    contact_name = item["values"][1]
    contact_desc = item["values"][2]
    contact_phone = item["values"][3]

    popup = tk.Toplevel(root)
    popup.title(f"Modify Contact - {contact_name}")
    popup.geometry("400x500")
    popup.grab_set()

    ttk.Label(popup, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    entry_pop_name = ttk.Entry(popup, width=30)
    entry_pop_name.insert(0, contact_name)
    entry_pop_name.grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(popup, text="Description:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_pop_desc = ttk.Entry(popup, width=30)
    entry_pop_desc.insert(0, contact_desc)
    entry_pop_desc.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(popup, text="Phone:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    entry_pop_phone = ttk.Entry(popup, width=30)
    entry_pop_phone.insert(0, contact_phone)
    entry_pop_phone.grid(row=2, column=1, padx=10, pady=5)

    ttk.Separator(popup, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
    ttk.Label(popup, text="Custom Fields", font=("Helvetica", 9, "bold")).grid(row=4, column=0, columnspan=2, pady=2)

    cursor.execute("SELECT id, field_name FROM fields ORDER BY field_name")
    custom_fields = cursor.fetchall()
    field_entries = {}
    for i, (field_id, field_name) in enumerate(custom_fields):
        ttk.Label(popup, text=f"{field_name}:").grid(row=5+i, column=0, padx=10, pady=3, sticky="w")
        entry = ttk.Entry(popup, width=30)
        cursor.execute("SELECT value FROM contact_fields WHERE contact_id = ? AND field_id = ?", (contact_id, field_id))
        existing = cursor.fetchone()
        if existing:
            entry.insert(0, existing[0])
        entry.grid(row=5+i, column=1, padx=10, pady=3)
        field_entries[field_id] = entry

    def confirm_modify():
        new_name = entry_pop_name.get().strip()
        new_desc = entry_pop_desc.get().strip()
        new_phone = entry_pop_phone.get().strip()
        if not new_name or not new_phone:
            messagebox.showwarning("Missing Info", "Name and Phone are required.", parent=popup)
            return
        cursor.execute("UPDATE contacts SET name = ?, description = ?, phone = ? WHERE id = ?", (new_name, new_desc, new_phone, contact_id))
        for field_id, entry in field_entries.items():
            value = entry.get().strip()
            cursor.execute("SELECT id FROM contact_fields WHERE contact_id = ? AND field_id = ?", (contact_id, field_id))
            existing = cursor.fetchone()
            if existing:
                if value:
                    cursor.execute("UPDATE contact_fields SET value = ? WHERE contact_id = ? AND field_id = ?", (value, contact_id, field_id))
                else:
                    cursor.execute("DELETE FROM contact_fields WHERE contact_id = ? AND field_id = ?", (contact_id, field_id))
            elif value:
                cursor.execute("INSERT INTO contact_fields (contact_id, field_id, value) VALUES (?, ?, ?)", (contact_id, field_id, value))
        conn.commit()
        load_contacts()
        popup.destroy()
        messagebox.showinfo("Updated", f"'{contact_name}' has been updated.")

    ttk.Button(popup, text="Save Changes", command=confirm_modify).grid(row=5+len(custom_fields), column=0, columnspan=2, pady=15)

def delete_contact():
    selected = contact_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a contact to delete.")
        return
    item = contact_tree.item(selected[0])
    contact_id = item["values"][0]
    contact_name = item["values"][1]
    confirm = messagebox.askyesno("Confirm Delete", f"Delete '{contact_name}'?")
    if confirm:
        cursor.execute("DELETE FROM contact_fields WHERE contact_id = ?", (contact_id,))
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        load_contacts()
        # ---- CONTACTS TAB LAYOUT ----

# Search bar
search_frame = ttk.Frame(contacts_frame)
search_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(search_frame, text="Search in:").grid(row=0, column=0, padx=5)
search_dropdown = ttk.Combobox(search_frame, width=15, state="readonly")
search_dropdown.grid(row=0, column=1, padx=5)

ttk.Label(search_frame, text="Search:").grid(row=0, column=2, padx=5)
entry_search = ttk.Entry(search_frame, width=25)
entry_search.grid(row=0, column=3, padx=5)

ttk.Button(search_frame, text="Search", command=search_contact).grid(row=0, column=4, padx=5)
ttk.Button(search_frame, text="Show All", command=lambda: load_contacts()).grid(row=0, column=5, padx=5)

# Contact list
list_frame = ttk.LabelFrame(contacts_frame, text="Contacts")
list_frame.pack(fill="both", expand=True, padx=10, pady=5)

contact_tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Description", "Phone"), show="headings")
contact_tree.heading("ID", text="ID")
contact_tree.heading("Name", text="Name")
contact_tree.heading("Description", text="Description/Reference")
contact_tree.heading("Phone", text="Phone Number")
contact_tree.column("ID", width=50)
contact_tree.column("Name", width=200)
contact_tree.column("Description", width=200)
contact_tree.column("Phone", width=150)
contact_tree.pack(fill="both", expand=True, padx=5, pady=5)

btn_frame = ttk.Frame(list_frame)
btn_frame.pack(pady=5)

ttk.Button(btn_frame, text="Add Contact", command=open_add_contact).grid(row=0, column=0, padx=5)
ttk.Button(btn_frame, text="Modify Contact", command=open_modify_contact).grid(row=0, column=1, padx=5)
ttk.Button(btn_frame, text="Delete Contact", command=delete_contact).grid(row=0, column=2, padx=5)

# ---- MANAGE FIELDS TAB LAYOUT ----

fields_form_frame = ttk.LabelFrame(fields_frame, text="Add New Field")
fields_form_frame.pack(fill="x", padx=10, pady=10)

ttk.Label(fields_form_frame, text="Field Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_field_name = ttk.Entry(fields_form_frame, width=25)
entry_field_name.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(fields_form_frame, text="Add Field", command=add_field).grid(row=0, column=2, padx=10, pady=5)

ttk.Label(fields_form_frame, text="(Maximum 15 custom fields)", foreground="gray").grid(row=1, column=0, columnspan=3, pady=2)

fields_list_frame = ttk.LabelFrame(fields_frame, text="Current Custom Fields")
fields_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

fields_tree = ttk.Treeview(fields_list_frame, columns=("ID", "Field Name"), show="headings")
fields_tree.heading("ID", text="ID")
fields_tree.heading("Field Name", text="Field Name")
fields_tree.column("ID", width=50)
fields_tree.column("Field Name", width=300)
fields_tree.pack(fill="both", expand=True, padx=5, pady=5)

ttk.Button(fields_list_frame, text="Delete Selected Field", command=delete_field).pack(pady=5)

# ---- START ----
load_fields()
load_contacts()
root.mainloop()