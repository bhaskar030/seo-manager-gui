# importing libraries
from tkinter import ttk, messagebox, simpledialog, filedialog   # to create the GUI
import tkinter as tk                                            # to create the GUI
import model                                                    # to get the response and analyse the same with the help of model
import threading                                                # to create multi threading
import requests                                                 # to get the user id authenticated
from openpyxl import Workbook                                   # to export the sentiment and NER analysis
from datetime import datetime                                   # to get the date time while saving the analysis


API_URL = "http://localhost:8000"                               # Flask API URL to get the user id authenticated

# Creation a class for Login window and its realted task
class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System")
        self.root.geometry("640x480")
        self.token = None
        self.current_user = None
        self.login_screen()

    # Crating a login screen
    def login_screen(self):
        self.clear_window()

        # Creating a field for user name and getting its input
        tk.Label(self.root, text="Username").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        
        # Creating a field for password and getting its input
        tk.Label(self.root, text="Password").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        # Creating a check box to toggle password character between asterics and character
        self.show_pass = tk.IntVar()
        tk.Checkbutton(self.root, text="Show Password", variable=self.show_pass, command=self.toggle_password).pack()

        # Creating a button for login
        tk.Button(self.root, text="Login", command=self.authenticate).pack(pady=10)

    # Creating a function to toggle password character between asterics and character
    def toggle_password(self):
        self.password_entry.config(show="" if self.show_pass.get() else "*")

    # Creating a function to authentication for user management
    def authenticate(self):
        username = self.username_entry.get().strip()                                   # getting username
        password = self.password_entry.get().strip()                                   # getting password

        # if username and password - both are blank - through message 
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        # getting the response as json from the API which can be translated to User name, Password and access
        try:
            response = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                access = data.get("access")
                if not self.token or not access:
                    messagebox.showerror("Error", "Invalid login response from server.")
                    return

                self.current_user = {"username": username, "access": access}
                self.main_screen()
            else:
                messagebox.showerror("Login Failed", response.json().get("message", "Invalid username or password."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")

    # Creating a function for main screen
    def main_screen(self):
        self.clear_window()
        # Creating a lable for Welcome message
        tk.Label(self.root, text=f"Welcome, {self.current_user['username']}").pack(pady=5)
        # Creating a lable for access level
        tk.Label(self.root, text=f"Access Level: {self.current_user['access']}").pack(pady=5)
        # Creating a button for View info
        tk.Button(self.root, text="View Info", command=self.view_info).pack(pady=5)
        # Creating a admin specific access
        if self.current_user['access'].lower() == 'admin':
            tk.Label(self.root, text="--- Admin Panel ---").pack(pady=5)
            tk.Button(self.root, text="Create New User", command=self.create_user).pack(pady=2)
            tk.Button(self.root, text="Delete User", command=self.delete_user).pack(pady=2)
            tk.Button(self.root, text="Change User Access", command=self.change_user_access).pack(pady=2)

        # Creating a general access
        tk.Button(self.root, text="Open Task Manager", command=self.open_task_manager).pack(pady=5)
        tk.Button(self.root, text="Change Password", command=self.change_password).pack(pady=2)
        tk.Button(self.root, text="Logout", command=self.logout).pack(pady=10)

    # Creating a function to open Taskmanager
    def open_task_manager(self):
        TaskManagerWindow(self.root)

    # Creating a function to view info
    def view_info(self):
        messagebox.showinfo("Info", f"User: {self.current_user['username']}\nAccess: {self.current_user['access']}")

    # Creating a function to create user
    def create_user(self):
        username = simpledialog.askstring("New User", "Enter new username:")
        if not username:
            return

        password = simpledialog.askstring("New User", "Enter password:", show="*")
        if not password:
            return

        access = simpledialog.askstring("New User", "Access level (User/Admin):")
        if access not in ["User", "Admin"]:
            messagebox.showerror("Error", "Access must be 'User' or 'Admin'")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.post(
                f"{API_URL}/users",
                json={"username": username, "password": password, "access": access},
                headers=headers
            )
            if response.status_code == 201:
                messagebox.showinfo("Success", f"User '{username}' created.")
            else:
                messagebox.showerror("Error", response.json().get("message", "Failed to create user."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")

    # Creating a function to delete user
    def delete_user(self):
        username = simpledialog.askstring("Delete User", "Enter username to delete:")
        if not username:
            return

        if username == self.current_user['username']:
            messagebox.showerror("Error", "You cannot delete yourself.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.delete(f"{API_URL}/users/{username}", headers=headers)
            if response.status_code == 200:
                messagebox.showinfo("Deleted", f"User '{username}' has been deleted.")
            else:
                messagebox.showerror("Error", response.json().get("message", "Failed to delete user."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")

    # Creating a function to change user access
    def change_user_access(self):
        username = simpledialog.askstring("Change Access", "Enter username:")
        if not username:
            return

        new_access = simpledialog.askstring("Change Access", "New access level (User/Admin):")
        if new_access not in ["User", "Admin"]:
            messagebox.showerror("Error", "Access must be 'User' or 'Admin'")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.put(
                f"{API_URL}/users/{username}/access",
                json={"access": new_access},
                headers=headers
            )
            if response.status_code == 200:
                messagebox.showinfo("Updated", f"User '{username}' access changed to '{new_access}'.")
            else:
                messagebox.showerror("Error", response.json().get("message", "Failed to update access."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")
    
    # Creating a function to change password
    def change_password(self):
        old_password = simpledialog.askstring("Change Password", "Enter current password:", show="*")
        if not old_password:
            return

        new_password = simpledialog.askstring("Change Password", "Enter new password:", show="*")
        if not new_password:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "old_password": old_password,
            "new_password": new_password
        }
        try:
            response = requests.put(
                f"{API_URL}/users/{self.current_user['username']}/password",
                json=payload,
                headers=headers
            )
            if response.status_code == 200:
                messagebox.showinfo("Success", "Password updated successfully.")
            else:
                messagebox.showerror("Error", response.json().get("message", "Failed to update password."))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to connect to server: {e}")

    # Creating a function to logout
    def logout(self):
        self.token = None
        self.current_user = None
        self.login_screen()
    
    # Creating a function to clear window
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

# Creating a class for Taskmanager
class TaskManagerWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("SEO Manager")
        self.window.geometry("1980x1600")

        self.create_widgets()

    # Creating fucntion for creating widgets
    def create_widgets(self):
        # Outer frame
        outer_frame = tk.Frame(self.window)
        outer_frame.pack(fill="both", expand=True)

        # Canvas + Scrollbars
        canvas = tk.Canvas(outer_frame)
        v_scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        h_scrollbar = tk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        outer_frame.grid_rowconfigure(0, weight=1)
        outer_frame.grid_columnconfigure(0, weight=1)

        # Creating a field for Title
        title = tk.Label(self.scrollable_frame, text="SEO Manager", font=("Arial", 20, "bold"))
        title.grid(row=0, column=2, columnspan=5, pady=10, sticky="nsew")

        # Creating a field for getiing prompt as an input and it lebal
        tk.Label(self.scrollable_frame, text="Your Promt: ").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.message_entry = tk.Text(self.scrollable_frame, wrap='word',height=3)
        self.message_entry.grid(row=1, column=1, rowspan= 3, columnspan=8, padx=5, pady=5, sticky="nsew")
        
        # Creating a button for sending the prompt to model
        send_button = tk.Button(self.scrollable_frame, text="Send", command=self.get_response)
        send_button.grid(row=4, column=2, padx=5, pady=5)

        # Creating a button for analysisng the text with model
        analysis_button = tk.Button(self.scrollable_frame, text="Analyse", command=self.get_response)
        analysis_button.grid(row=4, column=4, padx=5, pady=5)

        # Creating a field for chat
        tk.Label(self.scrollable_frame, text="Chat: ").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        self.chat_entry = tk.Text(self.scrollable_frame, wrap='word',height=10)
        self.chat_entry.grid(row=5, column=1, rowspan=5, columnspan=8, padx=5, pady=5, sticky="nsew")


        # Treeview with scrollbars for sentiment analysis
        tk.Label(self.scrollable_frame, text="Sentiment").grid(row=10, column=0, padx=5, pady=5, sticky="e")
        tree_frame_sentiment = tk.Frame(self.scrollable_frame)
        tree_frame_sentiment.grid(row=10, column=1, rowspan=5, columnspan=2, padx=5, pady=5, sticky="nsew")

        tree_sentiment_scroll_y = tk.Scrollbar(tree_frame_sentiment, orient="vertical")
        tree_sentiment_scroll_x = tk.Scrollbar(tree_frame_sentiment, orient="horizontal")
        self.tree_sentiment = ttk.Treeview(tree_frame_sentiment, columns=("Sentences","Sentiment", "Magnitude"),
                                 show="headings", yscrollcommand=tree_sentiment_scroll_y.set,
                                 xscrollcommand=tree_sentiment_scroll_x.set)
        self.tree_sentiment.pack(side="top", fill="both", expand=True)

        tree_sentiment_scroll_y.config(command=self.tree_sentiment.yview)
        tree_sentiment_scroll_x.pack(side="right", fill="y")

        tree_sentiment_scroll_x.config(command=self.tree_sentiment.xview)
        tree_sentiment_scroll_x.pack(side="bottom", fill="x")

        self.tree_sentiment.heading("Sentences", text="Sentences")
        self.tree_sentiment.heading("Sentiment", text="Sentiment")
        self.tree_sentiment.heading("Magnitude", text="Magnitude")

        # Download Button
        # Button to download sentiment data to Excel
        sentiment_download_btn = tk.Button(self.scrollable_frame, text="Export", command=self.download_sentiment_to_excel)
        sentiment_download_btn.grid(row=11, column=0, padx=5, pady=(10, 5), sticky="w")


        # # Treeview with scrollbars for sentiment analysis Entity
        tk.Label(self.scrollable_frame, text="Entity").grid(row=16, column=0, padx=5, pady=5, sticky="e")
        tree_frame = tk.Frame(self.scrollable_frame)
        tree_frame.grid(row=16, column=1, rowspan=5, columnspan=2, padx=5, pady=5, sticky="nsew")

        tree_scroll_y = tk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = tk.Scrollbar(tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(tree_frame, columns=("NER", "Class"),
                                 show="headings", yscrollcommand=tree_scroll_y.set,
                                 xscrollcommand=tree_scroll_x.set)
        self.tree.pack(side="top", fill="both", expand=True)

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_y.pack(side="right", fill="y")

        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_x.pack(side="bottom", fill="x")

        self.tree.heading("NER", text="NER")
        self.tree.heading("Class", text="Class")

        ner_download_btn = tk.Button(self.scrollable_frame, text="Export", command=self.download_ner_to_excel)
        ner_download_btn.grid(row=17, column=0, padx=5, pady=(10, 5), sticky="w")

        # Creating a field for getiing Grade and it lebal
        tk.Label(self.scrollable_frame, text="Grade").grid(row=10, column=6, padx=5, pady=5, sticky="e")
        self.grade_entry = tk.Entry(self.scrollable_frame)
        self.grade_entry.grid(row=10, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Genre 1 and it lebal
        tk.Label(self.scrollable_frame, text="Genre 1:").grid(row=11, column=6, padx=5, pady=5, sticky="e")
        self.genre_entry_1 = tk.Entry(self.scrollable_frame)
        self.genre_entry_1.grid(row=11, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Genre 1 scrore and it lebal
        tk.Label(self.scrollable_frame, text="Genre 1 Score:").grid(row=12, column=6, padx=5, pady=5, sticky="e")
        self.genre_score_1 = tk.Entry(self.scrollable_frame)
        self.genre_score_1.grid(row=12, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Genre 2 and it lebal
        tk.Label(self.scrollable_frame, text="Genre 2:").grid(row=13, column=6, padx=5, pady=5, sticky="e")
        self.genre_entry_2 = tk.Entry(self.scrollable_frame)
        self.genre_entry_2.grid(row=13, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Genre 2 score and it lebal
        tk.Label(self.scrollable_frame, text="Genre 2 Score:").grid(row=14, column=6, padx=5, pady=5, sticky="e")
        self.genre_score_2 = tk.Entry(self.scrollable_frame)
        self.genre_score_2.grid(row=14, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Overall sentiment and it lebal
        tk.Label(self.scrollable_frame, text="Overall Sentiment:").grid(row=15, column=6, padx=5, pady=5, sticky="e")
        self.overall_sentiment = tk.Entry(self.scrollable_frame)
        self.overall_sentiment.grid(row=15, column=7, padx=5, pady=5, sticky="nsew")

        # Creating a field for getiing Overall magnitude and it lebal
        tk.Label(self.scrollable_frame, text="Overall Magnitude:").grid(row=16, column=6, padx=5, pady=5, sticky="e")
        self.overall_magnitude = tk.Entry(self.scrollable_frame)
        self.overall_magnitude.grid(row=16, column=7, padx=1, pady=5, sticky="nsew")
        
        # Creating a field for about
        tk.Label(self.scrollable_frame, text="Developer:").grid(row=17, column=6, padx=5, pady=5, sticky="e")
        tk.Label(self.scrollable_frame, text="Bhaskar Mukhopadhyay").grid(row=17, column=7, padx=5, pady=5, sticky="e")
        tk.Label(self.scrollable_frame, text="About").grid(row=18, column=6, padx=5, pady=5, sticky="e")
        tk.Label(self.scrollable_frame, text="It will use mistralai/mistral-7b-instruct:free \nnmodel to generate the response \nand Google Natural API for getting \nNER-Sentiment and Classification Analysis.").grid(row=18, column=7, padx=5, pady=5, sticky="e")


        # Configure weight for responsiveness
        for col in range(8):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
        for row in range(10):
            self.scrollable_frame.grid_rowconfigure(row, weight=1)

    
    # Creating a function for getting response from model
    def get_response(self):
        # Checking if prompt and chat both are blank then show messgae
        prompt = self.message_entry.get("1.0", "end-1c")
        chat = self.chat_entry.get("1.0", "end-1c")
        if not (prompt.strip() or chat.strip()):
            messagebox.showwarning("Warning", "Prompt cannot be empty.")
            return

        # Disable UI while processing
        self.message_entry.config(state='disabled')
        if prompt:
            self.chat_entry.config(state='normal')
            self.chat_entry.delete('1.0', tk.END)
            self.chat_entry.insert(tk.END, "Processing...\n")
            self.chat_entry.config(state='disabled')

        # Creating a function for analysis
        def run_analysis(chat,prompt):
            try:
                ''' 
                if prompt is not null then it will take the prompt and with help of llm_app class, generates
                the llm response then it will pass the response to ReadabilityAnalyzer as a parameter to
                check sentiment - overall and sentencewise, grade, Named Entity Representation 

                '''
                if prompt:
                    llm = model.llm_app(prompt)
                    chat = llm.chat()
                    analysis = model.ReadabilityAnalyzer(chat)
                else:    
                    analysis = model.ReadabilityAnalyzer(chat)
                sentiment = analysis.get_sentiment()
                genre = analysis.detect_genre()
                grade = analysis.get_grade()
                ner = analysis.get_ner()

                # Update UI on the main thread
                self.window.after(0, self.update_ui, prompt, chat, sentiment, genre, grade,ner)
            except Exception as e:
                self.window.after(0, lambda e=e: messagebox.showerror("Error", str(e)))
            finally:
                self.window.after(0, lambda: self.message_entry.config(state='normal'))

        threading.Thread(target=run_analysis(chat,prompt), daemon=True).start()

    # Creating a fucntion to update the UI with llm response, sentiment, grde, ner
    def update_ui(self, prompt, chat, sentiment, genre, grade, ner):
        self.chat_entry.config(state='normal')
        self.chat_entry.delete('1.0', tk.END)
        self.chat_entry.insert(tk.END, f'User: {prompt} \n\n AI: {chat}')
        self.chat_entry.config(state='disabled')

        self.overall_sentiment.delete(0, tk.END)
        self.overall_sentiment.insert(tk.END, sentiment[0][0]['score'])
        self.overall_magnitude.delete(0, tk.END)
        self.overall_magnitude.insert(tk.END, sentiment[0][0]['magnitude'])

        self.grade_entry.delete(0, tk.END)
        self.grade_entry.insert(tk.END, grade[0])

        self.genre_entry_1.delete(0, tk.END)
        self.genre_score_1.delete(0, tk.END)
        #self.genre_entry.insert(tk.END, genre['label'])
        if len(genre)<=1:
            self.genre_entry_1.insert(tk.END, genre[0][0])
            self.genre_score_1.insert(tk.END, genre[0][1])
        else:
            self.genre_entry_1.insert(tk.END, genre[0][0])

            self.genre_score_1.delete(0, tk.END)
            self.genre_score_1.insert(tk.END, genre[0][1])


            self.genre_entry_2.delete(0, tk.END)
            #self.genre_score_entry.insert(tk.END, genre['score'])
            self.genre_entry_2.insert(tk.END, genre[1][0])

            self.genre_score_2.delete(0, tk.END)
            self.genre_score_2.insert(tk.END, genre[1][1])



        # Clear previous Treeview items of sentiment table
        for item in self.tree_sentiment.get_children():
            self.tree_sentiment.delete(item)

        # Populate Treeview with sentiment data
        for element in sentiment[1]:
            if 'part' in element and 'scores' in element:
                part = element['part']
                score = element['scores'].get('score', None)
                magnitude = element['scores'].get('magnitude', None)
                self.tree_sentiment.insert('', 'end', values=(part, score, magnitude))


        # Clear previous Treeview items of ner table
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate Treeview with ner data
        for element in ner:
            self.tree.insert('', 'end', values=(element[0], element[1]))

    # creating a method to download the sentiment table as a workbook
    def download_sentiment_to_excel(self):
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Sentiment Data"

        # Write headers
        ws.append(["Sentences", "Sentiment", "Magnitude"])

        # Write Treeview data
        for row_id in self.tree_sentiment.get_children():
            values = self.tree_sentiment.item(row_id)["values"]
            ws.append(values)

        # Save file
        filename = f"sentiment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)

        # Inform the user
        messagebox.showinfo("Export Successful", f"Data saved to {filename}")
    
    # creating a method to download the ner table as a workbook
    def download_ner_to_excel(self):
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "NER Data"

        # Write headers
        ws.append(["NER", "Class"])

        # Write Treeview data
        for row_id in self.tree.get_children():
            values = self.tree.item(row_id)["values"]
            ws.append(values)

        # Save file
        filename = f"NER Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)

        # Inform the user
        messagebox.showinfo("Export Successful", f"Data saved to {filename}")


if __name__ == "__main__":
     root = tk.Tk()
     app = TaskManagerWindow(root)
     root.mainloop()