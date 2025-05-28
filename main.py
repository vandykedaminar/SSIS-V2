import sqlite3 as sql
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import re
import os

DATABASE_NAME = 'students_ssis_pure_sqlite_v3.db' # New DB name for this version with full CRUD

# --- Default Data (to be inserted if DB is empty) ---
DEFAULT_COLLEGES_DATA = [
    ("College of Engineering and Technology", "COET"),
    ("College of Education", "CED"),
    ("College of Arts and Science", "CASS"),
    ("College of Business Administration & Accountancy", "CBAA"),
    ("College of Nursing", "CHS"), 
    ("College of Science and Mathematics", "CSM"),
    ("College of Computer Studies", "CCS")
]

DEFAULT_PROGRAM_LISTS_DATA = {
    "COET": "DIPLOMA IN CHEMICAL ENGINEERING TECHNOLOGY,BS IN CIVIL ENGINEERING,BS IN CERAMICS ENGINEERING,BS IN CHEMICAL ENGINEERING,BS IN COMPUTER ENGINEERING,BS IN ELECTRONICS & COMMUNICATIONS ENGINEERING,BS IN ELECTRICAL ENGINEERING,BS IN MINING ENG'G.,BS IN ENVIRONMENTAL ENGINEERING TECHNOLOGY,BS IN MECHANICAL ENGINEERING,BS IN METALLURGICAL ENGINEERING",
    "CED": "BACHELOR OF SECONDARY EDUCATION (BIOLOGY),BS IN INDUSTRIAL EDUCATION (DRAFTING),BACHELOR OF SECONDARY EDUCATION (CHEMISTRY),BACHELOR OF SECONDARY EDUCATION (PHYSICS),BACHELOR OF SECONDARY EDUCATION (MATHEMATICS),BACHELOR OF SECONDARY EDUCATION (MAPEH),Certificate Program for Teachers,BACHELOR OF SECONDARY EDUCATION (TLE),BACHELOR OF SECONDARY EDUCATION (GENERAL SCIENCE),BACHELOR OF ELEMENTARY EDUCATION (ENGLISH),BACHELOR OF ELEMENTARY EDUCATION (SCIENCE AND HEALTH),BS IN TECHNOLOGY TEACHER EDUCATION (INDUSTRIAL TECH),BS IN TECHNOLOGY TEACHER EDUCATION (DRAFTING TECH)",
    "CASS": "GENERAL EDUCATION PROGRAM,BA IN ENGLISH,BS IN PSYCHOLOGY,BA IN FILIPINO,BA IN HISTORY,BA IN POLITICAL SCIENCE",
    "CBAA": "BS IN BUSINESS ADMINISTRATION (BUSINESS ECONOMICS),BS IN BUSINESS ADMINISTRATION (ECONOMICS),BS IN BUSINESS ADMINISTRATION (ENTREPRENEURIAL MARKETING),BS IN HOTEL AND RESTAURANT MANAGEMENT,BS IN ACCOUNTANCY",
    "CHS": "BS IN NURSING",
    "CSM": "BS IN BIOLOGY (GENERAL),BS IN STATISTICS,BS IN BIOLOGY (BOTANY),BS IN BIOLOGY (ZOOLOGY),BS IN BIOLOGY (MARINE),BS IN CHEMISTRY,BS IN MATHEMATICS,BS IN PHYSICS",
    "CCS": "BS IN COMPUTER SCIENCE,BS IN INFORMATION TECHNOLOGY,BS IN INFORMATION SYSTEMS,BS IN ELECTRONICS AND COMPUTER TECHNOLOGY (EMBEDDED SYSTEMS),BS IN ELECTRONICS AND COMPUTER TECHNOLOGY (COMMUNICATIONS SYSTEM),DIPLOMA IN ELECTRONICS TECHNOLOGY,DIPLOMA IN ELECTRONICS ENGINEERING TECH (Communication Electronics),DIPLOMA IN ELECTRONICS ENGINEERING TECH (Computer Electronics)"
}

# --- Database Initialization and Connection ---
def get_db_connection():
    conn = sql.connect(DATABASE_NAME)
    conn.row_factory = sql.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Colleges (
            CollegeCode TEXT PRIMARY KEY,
            CollegeName TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CollegeProgramLists (
            CollegeCode TEXT PRIMARY KEY,
            ProgramNames TEXT,
            FOREIGN KEY (CollegeCode) REFERENCES Colleges(CollegeCode) ON DELETE CASCADE ON UPDATE CASCADE
        )
    ''') # Added ON UPDATE CASCADE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            idnum TEXT PRIMARY KEY,
            fname TEXT,
            lname TEXT,
            sex TEXT,
            pcode TEXT,
            yrlvl INTEGER,
            cname TEXT,
            ccode TEXT,
            FOREIGN KEY (ccode) REFERENCES Colleges(CollegeCode) ON DELETE CASCADE ON UPDATE CASCADE
        )
    ''') # Added ON UPDATE CASCADE
    conn.commit()
    conn.close()

def seed_default_data_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Colleges")
    college_count = cursor.fetchone()[0]

    if college_count == 0:
        print("Database is empty. Seeding default college and program data...")
        try:
            for cname, ccode in DEFAULT_COLLEGES_DATA:
                try:
                    cursor.execute("INSERT INTO Colleges (CollegeName, CollegeCode) VALUES (?, ?)", (cname, ccode))
                except sql.IntegrityError: pass # Skip if already exists somehow
            conn.commit()
            for ccode, programs_str in DEFAULT_PROGRAM_LISTS_DATA.items():
                cursor.execute("SELECT CollegeCode FROM Colleges WHERE CollegeCode = ?", (ccode,))
                if cursor.fetchone():
                    try:
                        cursor.execute("INSERT INTO CollegeProgramLists (CollegeCode, ProgramNames) VALUES (?, ?)", (ccode, programs_str))
                    except sql.IntegrityError: pass # Skip
            conn.commit()
            print("Default data seeded.")
        except sql.Error as e:
            messagebox.showerror("DB Seeding Error", f"Error seeding default data: {e}")
    conn.close()

# --- Load data into Python dictionaries from DB ---
def load_college_programs_from_db():
    programs = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT CollegeCode, ProgramNames FROM CollegeProgramLists")
        rows = cursor.fetchall()
        for row in rows:
            program_list = [p.strip() for p in row['ProgramNames'].split(',') if p.strip()] if row['ProgramNames'] else []
            programs[row['CollegeCode']] = program_list
    except sql.Error as e: messagebox.showerror("DB Error", f"Error loading college programs: {e}")
    finally: conn.close()
    return programs

def load_college_mapping_from_db():
    mapping = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT CollegeName, CollegeCode FROM Colleges ORDER BY CollegeName")
        rows = cursor.fetchall()
        for row in rows: mapping[row['CollegeName']] = row['CollegeCode']
    except sql.Error as e: messagebox.showerror("DB Error", f"Error loading college mapping: {e}")
    finally: conn.close()
    return mapping

initialize_database()
seed_default_data_if_empty()
college_programs_dict = load_college_programs_from_db()
college_mapping_dict = load_college_mapping_from_db()

# --- GUI Functions ---
def autofill_code(event):
    selected_college_name = CollName_entry.get()
    if selected_college_name in college_mapping_dict:
        college_code = college_mapping_dict[selected_college_name]
        CollCode_entry.config(state='normal'); CollCode_entry.delete(0, END); CollCode_entry.insert(0, college_code); CollCode_entry.config(state='readonly')
        programs_list = college_programs_dict.get(college_code, [])
        program_combobox['values'] = programs_list
        if programs_list: program_combobox.current(0); autofill_program_code_display(None)
        else: program_combobox.set(''); autofill_program_code_display(None)
    else:
        CollCode_entry.config(state='normal'); CollCode_entry.delete(0, END); CollCode_entry.config(state='readonly')
        program_combobox['values'] = []; program_combobox.set(''); autofill_program_code_display(None)

def autofill_program_code_display(event):
    selected_program = progcode_var.get() # progcode_var is tied to program_combobox
    ProgCode_entry.config(state='normal'); ProgCode_entry.delete(0, END)
    if selected_program: ProgCode_entry.insert(0, selected_program)
    ProgCode_entry.config(state='readonly')

def save_student_to_db():
    idnum, fname, lname, sex = idnum_var.get(), fname_var.get(), lname_var.get(), sex_var.get()
    program_name_selected, year_str = progcode_var.get(), year_var.get()
    collname, collcode = collname_var.get(), collcode_var.get()
    if not all([idnum, fname, lname, sex, program_name_selected, year_str, collname, collcode]):
        messagebox.showwarning("Input Error", "All fields must be filled out"); return
    try: year = int(year_str)
    except ValueError: messagebox.showwarning("Input Error", "Year level must be a number."); return
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Students VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (idnum, fname, lname, sex, program_name_selected, year, collname, collcode))
        conn.commit(); messagebox.showinfo("Success", "Student saved successfully!"); refresh_student_treeview(); clear_input_fields()
    except sql.IntegrityError: messagebox.showerror("Save Error", f"Student ID '{idnum}' already exists.")
    except sql.Error as e: messagebox.showerror("Database Error", f"Error saving student: {e}")
    finally: conn.close()

def clear_input_fields():
    idnum_var.set(""); fname_var.set(""); lname_var.set(""); sex_var.set(""); progcode_var.set(""); year_var.set("1"); collname_var.set("")
    CollCode_entry.config(state='normal'); CollCode_entry.delete(0, END); CollCode_entry.config(state='readonly')
    ProgCode_entry.config(state='normal'); ProgCode_entry.delete(0, END); ProgCode_entry.config(state='readonly')
    program_combobox['values'] = []
    if CollName_entry['values']: CollName_entry.current(0); autofill_code(None)
    else: pass # No colleges, fields remain clear

def refresh_ui_data():
    """Reloads global dictionaries and updates relevant UI elements."""
    global college_mapping_dict, college_programs_dict
    college_mapping_dict = load_college_mapping_from_db()
    college_programs_dict = load_college_programs_from_db()
    
    CollName_entry['values'] = list(college_mapping_dict.keys())
    if list(college_mapping_dict.keys()):
        current_selection = collname_var.get()
        if current_selection in college_mapping_dict:
            CollName_entry.set(current_selection) # Keep current selection if still valid
        else:
            CollName_entry.current(0) # Default to first
        autofill_code(None)
    else: # No colleges left
        collname_var.set('')
        CollCode_entry.config(state='normal'); CollCode_entry.delete(0, END); CollCode_entry.config(state='readonly')
        program_combobox['values'] = []; progcode_var.set('')
        ProgCode_entry.config(state='normal'); ProgCode_entry.delete(0, END); ProgCode_entry.config(state='readonly')

    refresh_student_treeview()


# --- CRUD for Colleges ---
def open_add_college_window():
    add_college_win = Toplevel(root)
    add_college_win.title("Add New College")
    add_college_win.geometry("400x300")
    add_college_win.grab_set() # Modal behavior

    Label(add_college_win, text="College Name:").pack(pady=5)
    new_cname_var = StringVar()
    Entry(add_college_win, textvariable=new_cname_var, width=40).pack(pady=2)

    Label(add_college_win, text="College Code (e.g., CCS):").pack(pady=5)
    new_ccode_var = StringVar()
    Entry(add_college_win, textvariable=new_ccode_var, width=15).pack(pady=2)

    Label(add_college_win, text="Programs (comma-separated):").pack(pady=5)
    new_progs_var = StringVar()
    Entry(add_college_win, textvariable=new_progs_var, width=50).pack(pady=2)

    def save_new_college():
        cname, ccode = new_cname_var.get().strip(), new_ccode_var.get().strip().upper()
        progs_str = new_progs_var.get().strip()
        if not cname or not ccode:
            messagebox.showerror("Input Error", "College Name and Code are required!", parent=add_college_win); return
        
        conn = get_db_connection(); cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Colleges (CollegeName, CollegeCode) VALUES (?, ?)", (cname, ccode))
            if progs_str: # Only insert if programs are provided
                cursor.execute("INSERT INTO CollegeProgramLists (CollegeCode, ProgramNames) VALUES (?, ?)", (ccode, progs_str))
            conn.commit()
            messagebox.showinfo("Success", "College added successfully!", parent=add_college_win)
            refresh_ui_data()
            add_college_win.destroy()
        except sql.IntegrityError: messagebox.showerror("Save Error", f"College Code '{ccode}' or Name '{cname}' already exists.", parent=add_college_win)
        except sql.Error as e: messagebox.showerror("Database Error", f"Error saving college: {e}", parent=add_college_win)
        finally: conn.close()

    Button(add_college_win, text="Save College", command=save_new_college).pack(pady=15)

def open_edit_college_window():
    edit_college_win = Toplevel(root)
    edit_college_win.title("Edit College")
    edit_college_win.geometry("450x380")
    edit_college_win.grab_set()

    Label(edit_college_win, text="Select College to Edit:").pack(pady=5)
    select_cname_var = StringVar()
    college_select_combo = ttk.Combobox(edit_college_win, textvariable=select_cname_var, 
                                        values=list(college_mapping_dict.keys()), state="readonly", width=40)
    college_select_combo.pack(pady=2)

    details_frame = LabelFrame(edit_college_win, text="Edit Details", padx=10, pady=10)
    details_frame.pack(pady=10, fill="x", padx=10)

    edit_cname_var, edit_ccode_var = StringVar(), StringVar()
    original_ccode_hidden = StringVar() # To store the PK for WHERE clause
    add_progs_var = StringVar()

    Label(details_frame, text="College Name:").grid(row=0, column=0, sticky="w", pady=3)
    Entry(details_frame, textvariable=edit_cname_var, width=30).grid(row=0, column=1, pady=3)
    Label(details_frame, text="College Code:").grid(row=1, column=0, sticky="w", pady=3)
    Entry(details_frame, textvariable=edit_ccode_var, width=15).grid(row=1, column=1, pady=3, sticky="w")
    Label(details_frame, text="Current Programs:").grid(row=2, column=0, sticky="nw", pady=3)
    current_progs_text = Text(details_frame, height=4, width=35, state="disabled", wrap="word")
    current_progs_text.grid(row=2, column=1, pady=3, sticky="w")
    Label(details_frame, text="Add New Programs (comma-sep):").grid(row=3, column=0, sticky="w", pady=3)
    Entry(details_frame, textvariable=add_progs_var, width=35).grid(row=3, column=1, pady=3, sticky="w")

    def populate_edit_fields(event=None):
        selected_name = select_cname_var.get()
        if selected_name in college_mapping_dict:
            original_code = college_mapping_dict[selected_name]
            original_ccode_hidden.set(original_code)
            edit_cname_var.set(selected_name)
            edit_ccode_var.set(original_code)
            add_progs_var.set("")
            
            current_progs_list = college_programs_dict.get(original_code, [])
            current_progs_text.config(state="normal")
            current_progs_text.delete(1.0, END)
            if current_progs_list: current_progs_text.insert(END, "\n".join(current_progs_list))
            else: current_progs_text.insert(END, "(No programs listed)")
            current_progs_text.config(state="disabled")
    
    college_select_combo.bind("<<ComboboxSelected>>", populate_edit_fields)
    if list(college_mapping_dict.keys()): college_select_combo.current(0); populate_edit_fields()

    def save_college_changes():
        orig_ccode = original_ccode_hidden.get()
        new_cname, new_ccode = edit_cname_var.get().strip(), edit_ccode_var.get().strip().upper()
        progs_to_add_str = add_progs_var.get().strip()

        if not orig_ccode: messagebox.showerror("Error", "No college selected or original code lost.", parent=edit_college_win); return
        if not new_cname or not new_ccode: messagebox.showerror("Input Error", "College Name and Code are required.", parent=edit_college_win); return

        conn = get_db_connection(); cursor = conn.cursor()
        try:
            # Update Colleges table. ON UPDATE CASCADE should handle FKs in Students and CollegeProgramLists if ccode changes
            cursor.execute("UPDATE Colleges SET CollegeName = ?, CollegeCode = ? WHERE CollegeCode = ?", 
                           (new_cname, new_ccode, orig_ccode))
            
            # Update programs in CollegeProgramLists
            # Fetch existing programs, append new ones, then update the string
            cursor.execute("SELECT ProgramNames FROM CollegeProgramLists WHERE CollegeCode = ?", (new_ccode,)) # Use new_ccode if it changed
            current_prog_row = cursor.fetchone()
            existing_progs_list = []
            if current_prog_row and current_prog_row['ProgramNames']:
                existing_progs_list = [p.strip() for p in current_prog_row['ProgramNames'].split(',') if p.strip()]
            
            if progs_to_add_str:
                newly_added_progs = [p.strip() for p in progs_to_add_str.split(',') if p.strip()]
                # Add only unique new programs
                for prog in newly_added_progs:
                    if prog not in existing_progs_list:
                        existing_progs_list.append(prog)
            
            updated_progs_str = ",".join(existing_progs_list)
            
            # If CollegeProgramLists entry exists, update it. If not (e.g., new college or ccode changed and no entry for new ccode), insert.
            cursor.execute("SELECT COUNT(*) FROM CollegeProgramLists WHERE CollegeCode = ?", (new_ccode,))
            if cursor.fetchone()[0] > 0 :
                 cursor.execute("UPDATE CollegeProgramLists SET ProgramNames = ? WHERE CollegeCode = ?", 
                               (updated_progs_str, new_ccode))
            else: # This handles case where CollegeCode was changed and old entry was cascade deleted
                 cursor.execute("INSERT INTO CollegeProgramLists (CollegeCode, ProgramNames) VALUES (?,?)", (new_ccode, updated_progs_str))


            conn.commit()
            messagebox.showinfo("Success", "College updated successfully!", parent=edit_college_win)
            refresh_ui_data()
            edit_college_win.destroy()
        except sql.IntegrityError as ie: messagebox.showerror("Save Error", f"New College Code '{new_ccode}' or Name '{new_cname}' might conflict. {ie}", parent=edit_college_win)
        except sql.Error as e: messagebox.showerror("Database Error", f"Error updating college: {e}", parent=edit_college_win)
        finally: conn.close()

    Button(edit_college_win, text="Save Changes", command=save_college_changes).pack(pady=10)

def open_edit_student_window():
    selected_item_iid = student_info.selection()
    if not selected_item_iid: messagebox.showwarning("Selection Error", "No student selected!"); return
    
    stud_values = student_info.item(selected_item_iid[0], 'values')
    # (IDNum, FName, LName, Sex, PCode, YrLvl, CName, CCode)

    edit_stud_win = Toplevel(root)
    edit_stud_win.title("Edit Student Information")
    edit_stud_win.geometry("400x450")
    edit_stud_win.grab_set()

    # Vars for student fields
    edit_id_var = StringVar(value=stud_values[0])
    edit_fname_var = StringVar(value=stud_values[1])
    edit_lname_var = StringVar(value=stud_values[2])
    edit_sex_var = StringVar(value=stud_values[3])
    edit_pcode_var = StringVar(value=stud_values[4]) # Selected Program Name
    edit_yrlvl_var = StringVar(value=str(stud_values[5]))
    edit_cname_var = StringVar(value=stud_values[6])
    edit_ccode_var = StringVar(value=stud_values[7])

    Label(edit_stud_win, text="ID Number (Read-only):").pack(pady=2)
    Entry(edit_stud_win, textvariable=edit_id_var, state="readonly").pack(pady=2)
    Label(edit_stud_win, text="First Name:").pack(pady=2)
    Entry(edit_stud_win, textvariable=edit_fname_var).pack(pady=2)
    Label(edit_stud_win, text="Last Name:").pack(pady=2)
    Entry(edit_stud_win, textvariable=edit_lname_var).pack(pady=2)
    Label(edit_stud_win, text="Sex:").pack(pady=2)
    ttk.Combobox(edit_stud_win, textvariable=edit_sex_var, values=["F","M"], state="readonly").pack(pady=2)
    
    Label(edit_stud_win, text="College Name:").pack(pady=2)
    edit_cname_combo = ttk.Combobox(edit_stud_win, textvariable=edit_cname_var, 
                                     values=list(college_mapping_dict.keys()), state="readonly")
    edit_cname_combo.pack(pady=2)
    
    Label(edit_stud_win, text="College Code (Read-only):").pack(pady=2)
    edit_ccode_entry = Entry(edit_stud_win, textvariable=edit_ccode_var, state="readonly")
    edit_ccode_entry.pack(pady=2)

    Label(edit_stud_win, text="Program Name:").pack(pady=2)
    edit_pcode_combo = ttk.Combobox(edit_stud_win, textvariable=edit_pcode_var, state="readonly")
    edit_pcode_combo.pack(pady=2)

    Label(edit_stud_win, text="Year Level:").pack(pady=2)
    ttk.Combobox(edit_stud_win, textvariable=edit_yrlvl_var, values=[str(i) for i in range(1,6)], state="readonly").pack(pady=2)

    def update_edit_student_college_fields(event=None):
        sel_cname = edit_cname_var.get()
        if sel_cname in college_mapping_dict:
            sel_ccode = college_mapping_dict[sel_cname]
            edit_ccode_var.set(sel_ccode)
            progs = college_programs_dict.get(sel_ccode, [])
            edit_pcode_combo['values'] = progs
            current_pcode = edit_pcode_var.get()
            if progs:
                if current_pcode in progs: edit_pcode_combo.set(current_pcode)
                else: edit_pcode_combo.current(0) # Default to first if current not in list
            else: edit_pcode_combo.set('') # No programs for this college
        else: # Should not happen with readonly combobox
            edit_ccode_var.set('')
            edit_pcode_combo['values'] = []
            edit_pcode_combo.set('')
            
    edit_cname_combo.bind("<<ComboboxSelected>>", update_edit_student_college_fields)
    update_edit_student_college_fields() # Initial population of program list for current college

    def save_student_changes():
        idnum, fname, lname, sex = edit_id_var.get(), edit_fname_var.get(), edit_lname_var.get(), edit_sex_var.get()
        pcode, yrlvl_str = edit_pcode_var.get(), edit_yrlvl_var.get()
        cname, ccode = edit_cname_var.get(), edit_ccode_var.get()

        if not all([fname, lname, sex, pcode, yrlvl_str, cname, ccode]):
            messagebox.showerror("Input Error", "All fields (except ID) must be filled.", parent=edit_stud_win); return
        try: yrlvl = int(yrlvl_str)
        except ValueError: messagebox.showerror("Input Error", "Year level must be a number.", parent=edit_stud_win); return

        conn = get_db_connection(); cursor = conn.cursor()
        try:
            cursor.execute("""UPDATE Students SET fname=?, lname=?, sex=?, pcode=?, yrlvl=?, cname=?, ccode=?
                              WHERE idnum = ?""", 
                           (fname, lname, sex, pcode, yrlvl, cname, ccode, idnum))
            conn.commit()
            if cursor.rowcount > 0:
                messagebox.showinfo("Success", "Student updated successfully!", parent=edit_stud_win)
                refresh_student_treeview()
                edit_stud_win.destroy()
            else: messagebox.showerror("Update Error", "No student found with that ID or no changes made.", parent=edit_stud_win)
        except sql.Error as e: messagebox.showerror("Database Error", f"Error updating student: {e}", parent=edit_stud_win)
        finally: conn.close()

    Button(edit_stud_win, text="Save Changes", command=save_student_changes).pack(pady=15)


# --- Other GUI Functions (Delete College, Refresh TreeView, etc. - mostly same) ---
def open_delete_college_window():
    delete_college_window = Toplevel(root); delete_college_window.title("Delete College"); delete_college_window.geometry("400x200"); delete_college_window.grab_set()
    Label(delete_college_window, text="Select College to Delete:", font=("Arial", 12)).pack(pady=10)
    current_college_names = list(college_mapping_dict.keys()) # Use current in-memory map
    college_combobox_del = ttk.Combobox(delete_college_window, values=current_college_names, state="readonly", font=("Arial", 10))
    college_combobox_del.pack(pady=10)
    if current_college_names: college_combobox_del.current(0)
    def delete_college_from_db():
        selected_college_name = college_combobox_del.get()
        if not selected_college_name: messagebox.showwarning("Selection Error", "No college selected!", parent=delete_college_window); return
        college_code_to_delete = college_mapping_dict.get(selected_college_name)
        if not college_code_to_delete: messagebox.showerror("Error", "Could not find code for selected college.", parent=delete_college_window); return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{selected_college_name}' ({college_code_to_delete})?\nThis also deletes its programs and students.", parent=delete_college_window)
        if not confirm: return
        conn = get_db_connection(); cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Colleges WHERE CollegeCode = ?", (college_code_to_delete,))
            conn.commit()
            if cursor.rowcount > 0:
                messagebox.showinfo("Success", f"College '{selected_college_name}' deleted.", parent=delete_college_window)
                refresh_ui_data() # This will reload maps and update UI
                delete_college_window.destroy()
            else: messagebox.showerror("Delete Error", "College not found or could not be deleted.", parent=delete_college_window)
        except sql.Error as e: messagebox.showerror("Database Error", f"Error deleting college: {e}", parent=delete_college_window)
        finally: conn.close()
    Button(delete_college_window, text="Delete College", command=delete_college_from_db).pack(pady=20)

def refresh_student_treeview(search_query=None, sort_col_name=None):
    for item in student_info.get_children(): student_info.delete(item)
    conn = get_db_connection(); cursor = conn.cursor()
    query = "SELECT idnum, fname, lname, sex, pcode, yrlvl, cname, ccode FROM Students"
    params = []
    if search_query:
        search_like = f"%{search_query}%"
        query += " WHERE idnum LIKE ? OR fname LIKE ? OR lname LIKE ? OR sex LIKE ? OR pcode LIKE ? OR cname LIKE ? OR ccode LIKE ?"
        params = [search_like] * 7
    if sort_col_name:
        db_column_map = {"ID Number": "idnum", "First Name": "fname", "Last Name": "lname", "Sex": "sex", 
                         "Program Code": "pcode", "Year Level": "yrlvl", "College Name": "cname", "College Code": "ccode"}
        actual_db_col = db_column_map.get(sort_col_name)
        if actual_db_col: query += f" ORDER BY {actual_db_col}"
    try:
        cursor.execute(query, params)
        for stud_row in cursor.fetchall(): student_info.insert('', 'end', values=tuple(stud_row))
    except sql.Error as e: messagebox.showerror("DB Error", f"Error loading students: {e}")
    finally: conn.close()

def delete_selected_students():
    selected_items_iids = student_info.selection()
    if not selected_items_iids: messagebox.showwarning("Selection Error", "No student selected"); return
    id_nums_to_delete = [student_info.item(iid, 'values')[0] for iid in selected_items_iids]
    confirm = messagebox.askyesno("Confirm Delete", f"Delete {len(id_nums_to_delete)} student(s)?")
    if not confirm: return
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        placeholders = ','.join(['?'] * len(id_nums_to_delete))
        cursor.execute(f"DELETE FROM Students WHERE idnum IN ({placeholders})", id_nums_to_delete)
        conn.commit()
        if cursor.rowcount > 0: messagebox.showinfo("Success", f"{cursor.rowcount} student(s) deleted."); refresh_student_treeview()
        else: messagebox.showerror("Delete Error", "No students were deleted.")
    except sql.Error as e: messagebox.showerror("Database Error", f"Error deleting students: {e}")
    finally: conn.close()

def update_search_suggestions(event=None): refresh_student_treeview(search_query=search_var.get())
def sort_by_column_action(column_display_name): refresh_student_treeview(search_query=search_var.get(), sort_col_name=column_display_name)
def validate_idnum_format(new_value): return re.match(r'^\d{0,4}(-\d{0,4})?$', new_value) is not None

# --- UI Setup (Main Window) ---
root = Tk()
root.title("Student System Information (SSIS - Pure SQLite v3)")
root.geometry("1450x550")
frame = Frame(root, bg="#f0f0f0", bd=5, relief=RIDGE); frame.place(relwidth=1, relheight=1)
idnum_var, fname_var, lname_var, sex_var = StringVar(), StringVar(), StringVar(), StringVar()
progcode_var, year_var, collname_var, collcode_var, search_var = StringVar(), StringVar(), StringVar(), StringVar(), StringVar()
year_var.set("1")

# Student Info Input Section
StuInfo = LabelFrame(frame, text="Student Information", font=("Arial", 12, "bold"), bg="#e0e0e0", bd=5, relief=RIDGE)
StuInfo.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
# ... (Labels and Entries for ID, FName, LName, Sex - same as before)
Label(StuInfo, text="ID Number:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
vcmd_id = (root.register(validate_idnum_format), '%P')
Entry(StuInfo, textvariable=idnum_var, font=("Arial", 10), validate='key', validatecommand=vcmd_id, width=25).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
Label(StuInfo, text="First Name:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
Entry(StuInfo, textvariable=fname_var, font=("Arial", 10), width=25).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
Label(StuInfo, text="Last Name:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
Entry(StuInfo, textvariable=lname_var, font=("Arial", 10), width=25).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
Label(StuInfo, text="Sex:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
Gender_entry = ttk.Combobox(StuInfo, values=["F", "M"], textvariable=sex_var, font=("Arial", 10), state='readonly', width=22)
Gender_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew"); Gender_entry.current(0) if Gender_entry['values'] else None
StuInfo.grid_columnconfigure(1, weight=1)

# College Info Input Section
StuColl = LabelFrame(frame, text="College Information", font=("Arial", 12, "bold"), bg="#e0e0e0", bd=5, relief=RIDGE)
StuColl.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
# ... (Labels, Combobox for College Name, Entry for College Code - same as before)
Label(StuColl, text="College Name:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
CollName_entry = ttk.Combobox(StuColl, values=list(college_mapping_dict.keys()), textvariable=collname_var, font=("Arial", 10), state='readonly', width=40)
CollName_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew"); CollName_entry.bind("<<ComboboxSelected>>", autofill_code)
Label(StuColl, text="College Code:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
CollCode_entry = Entry(StuColl, textvariable=collcode_var, font=("Arial", 10), state='readonly', width=15)
CollCode_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
StuColl.grid_columnconfigure(1, weight=1)

# Program Info Input Section
StuProg = LabelFrame(frame, text="Program Information", font=("Arial", 12, "bold"), bg="#e0e0e0", bd=5, relief=RIDGE)
StuProg.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
# ... (Labels, Combobox for Program Name, Entry for Program Code, Combobox for Year Level - same as before)
Label(StuProg, text="Program Name:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
program_combobox = ttk.Combobox(StuProg, values=[], textvariable=progcode_var, font=("Arial", 10), state='readonly', width=40)
program_combobox.grid(row=0, column=1, padx=5, pady=2, sticky="ew"); program_combobox.bind("<<ComboboxSelected>>", autofill_program_code_display)
Label(StuProg, text="Program Code:").grid(row=1, column=0, padx=5, pady=2, sticky="w") # Display only
ProgCode_entry = Entry(StuProg, font=("Arial", 10), state='readonly', width=40)
ProgCode_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
Label(StuProg, text="Year Level:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
Year_entry = ttk.Combobox(StuProg, values=[str(i) for i in range(1,6)], textvariable=year_var, font=("Arial", 10), state='readonly', width=5)
Year_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w"); Year_entry.set("1")
StuProg.grid_columnconfigure(1, weight=1)

# Save Student Button
button_save = ttk.Button(frame, text="Save Student", command=save_student_to_db)
button_save.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

# Student Display Section (Right side)
Saved_student_lf = LabelFrame(frame, text="Saved Students", font=("Arial", 12, "bold"), bg="#e0e0e0", bd=5, relief=RIDGE)
Saved_student_lf.grid(row=0, column=1, rowspan=4, padx=10, pady=5, sticky="nsew")
frame.grid_columnconfigure(0, weight=1); frame.grid_columnconfigure(1, weight=3) # Adjusted weight for display
frame.grid_rowconfigure(0, weight=0);frame.grid_rowconfigure(1, weight=0);frame.grid_rowconfigure(2, weight=0); frame.grid_rowconfigure(3, weight=1) # Allow last input row to expand a bit

# Search and Action Buttons Bar
Search_frame_top = Frame(Saved_student_lf, bg="#e0e0e0")
Search_frame_top.pack(side=TOP, fill=X, padx=5, pady=5)
# ... (Search Entry and Menubuttons for Edit, Delete, Sort - same as before)
Label(Search_frame_top, text="Search:", font=("Arial", 10), bg="#e0e0e0").pack(side=LEFT, padx=(0,5))
search_entry = Entry(Search_frame_top, textvariable=search_var, font=("Arial", 10), width=25)
search_entry.pack(side=LEFT, padx=5); search_entry.bind('<KeyRelease>', update_search_suggestions)
edit_menu_button = Menubutton(Search_frame_top, text="Edit", relief=RAISED, font=("Arial", 10)); edit_menu_button.pack(side=LEFT, padx=5)
edit_menu = Menu(edit_menu_button, tearoff=0); edit_menu_button.config(menu=edit_menu)
edit_menu.add_command(label="Edit Selected Student", command=open_edit_student_window)
edit_menu.add_command(label="Edit College Info", command=open_edit_college_window)
edit_menu.add_command(label="Add New College", command=open_add_college_window)
delete_menu_button = Menubutton(Search_frame_top, text="Delete", relief=RAISED, font=("Arial", 10)); delete_menu_button.pack(side=LEFT, padx=5)
delete_menu = Menu(delete_menu_button, tearoff=0); delete_menu_button.config(menu=delete_menu)
delete_menu.add_command(label="Delete Selected Student(s)", command=delete_selected_students)
delete_menu.add_command(label="Delete College", command=open_delete_college_window)
sort_menu_button = Menubutton(Search_frame_top, text="Sort By", relief=RAISED, font=("Arial", 10)); sort_menu_button.pack(side=LEFT, padx=5)
sort_menu = Menu(sort_menu_button, tearoff=0); sort_menu_button.config(menu=sort_menu)
sort_menu.add_command(label="ID Number", command=lambda: sort_by_column_action("ID Number"))
sort_menu.add_command(label="First Name", command=lambda: sort_by_column_action("First Name"))
sort_menu.add_command(label="Last Name", command=lambda: sort_by_column_action("Last Name"))

# Treeview for Student Data
Data_display_frame = Frame(Saved_student_lf, bg="#f0f0f0", bd=2, relief=SUNKEN)
Data_display_frame.pack(side=TOP, fill=BOTH, expand=True, padx=5, pady=5)
# ... (Scrollbars and Treeview setup - same as before)
yscroll_tree = Scrollbar(Data_display_frame, orient=VERTICAL); xscroll_tree = Scrollbar(Data_display_frame, orient=HORIZONTAL)
student_info_cols = ("ID Number", "First Name", "Last Name", "Sex", "Program Code", "Year Level", "College Name", "College Code")
student_info = ttk.Treeview(Data_display_frame, columns=student_info_cols, yscrollcommand=yscroll_tree.set, xscrollcommand=xscroll_tree.set)
yscroll_tree.config(command=student_info.yview); xscroll_tree.config(command=student_info.xview)
yscroll_tree.pack(side=RIGHT, fill=Y); xscroll_tree.pack(side=BOTTOM, fill=X); student_info.pack(fill=BOTH, expand=True)
for col_name in student_info_cols: student_info.heading(col_name, text=col_name); student_info.column(col_name, width=120, anchor='w')
student_info['show'] = 'headings'

# Initial UI population
if list(college_mapping_dict.keys()): CollName_entry.current(0); autofill_code(None)
refresh_student_treeview()

root.mainloop()