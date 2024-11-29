import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import tkinter
from tkinter import messagebox, filedialog
import customtkinter
import send2trash

directory = ""
cache = {}
cache_time = 300

def find_archives():
    global directory, cache

    loading_window = customtkinter.CTkToplevel(root)
    loading_window.title("Procurando arquivos...")
    loading_window.config(bg="#01011c")
    loading_window.resizable(False, False)

    def center_loading_window():
        window_width = 300
        window_height = 100
        screen_width = root.winfo_width()
        screen_height = root.winfo_height()
        position_top = root.winfo_y() + int(screen_height / 2 - window_height / 2)
        position_left = root.winfo_x() + int(screen_width / 2 - window_width / 2)
        loading_window.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")

    center_loading_window()

    def on_root_move(event):
        if loading_window.winfo_exists():
            center_loading_window()

    root.bind("<Configure>", on_root_move)

    loading_window.grab_set()
    loading_label = customtkinter.CTkLabel(loading_window, text="Procurando arquivos...", text_color="#ffffff", bg_color="#01011c")
    loading_label.pack(pady=20)

    spinner = customtkinter.CTkProgressBar(loading_window, mode='indeterminate')
    spinner.pack(pady=10)
    spinner.start()

    def search_files():
        try:
            global cache

            if directory in cache and time.time() - cache[directory]['time'] < cache_time:
                rar_files = cache[directory]['files']
            else:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future = executor.submit(collect_files, directory)
                    rar_files = future.result()
                cache[directory] = {'files': rar_files, 'time': time.time()}

            if rar_files:
                listbox.delete(0, tkinter.END)
                root.after(0, lambda: listbox.insert(tkinter.END, *rar_files))
                messagebox.showinfo("Arquivos .rar encontrados", f"Foram encontrados {len(rar_files)} arquivos .rar em {directory}.")
            else:
                listbox.delete(0, tkinter.END)
                messagebox.showinfo("Nenhum arquivo .rar encontrado", f"Nenhum arquivo .rar foi encontrado em {directory}.")
            if loading_window and loading_window.winfo_exists():
                root.after(100, loading_window.destroy)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante a busca: {e}")
            if loading_window and loading_window.winfo_exists():
                root.after(100, loading_window.destroy)

    threading.Thread(target=search_files, daemon=True).start()

def collect_files(directory):
    rar_files = []
    for root_dir, _, files in os.walk(directory):
        rar_files.extend(os.path.join(root_dir, file) for file in files if file.endswith(".rar"))
    return rar_files

def move_to_trash(file_path):
    send2trash.send2trash(file_path)

def delete_archive():
    selected_index = listbox.curselection()
    if selected_index:
        file_path = os.path.abspath(listbox.get(selected_index))
        try:
            move_to_trash(file_path)
            listbox.delete(selected_index)
            messagebox.showinfo("Arquivo movido para a lixeira", f"O arquivo {file_path} foi movido para a lixeira com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro ao mover arquivo", f"Ocorreu um erro ao mover o arquivo para a lixeira: {e}")
    else:
        messagebox.showinfo("Nenhum arquivo selecionado", "Nenhum arquivo .rar foi selecionado.")

def delete_all_archives(): 
    all_items = listbox.get(0, tkinter.END)
    if all_items:
        resposta = messagebox.askyesno("Confirmação", "Tem certeza de que deseja mover todos os arquivos para a lixeira?")
        if resposta:
            erros = []
            for item in all_items:
                file_path = os.path.abspath(item)
                try:
                    if os.path.exists(file_path):
                        move_to_trash(file_path)
                    else:
                        erros.append(f"O arquivo {file_path} não existe mais.")
                except Exception as e:
                    erros.append(str(e))

            listbox.delete(0, tkinter.END)
            if erros:
                messagebox.showwarning("Atenção", f"Alguns arquivos não puderam ser movidos:\n" + "\n".join(erros))
            else:
                messagebox.showinfo("Arquivos movidos para a lixeira", "Todos os arquivos foram movidos para a lixeira com sucesso.")
    else:
        messagebox.showinfo("Nenhum arquivo selecionado", "Nenhum arquivo .rar foi selecionado.")

def update_directory():
    global directory
    directory = filedialog.askdirectory()
    if directory:
        text_directory.configure(state="normal")
        text_directory.delete(1.0, tkinter.END)
        text_directory.insert(tkinter.END, directory)
        text_directory.configure(state="disabled")
        find_archives()

root = customtkinter.CTk()
root.title("Rar Cleaner")
root.config(bg="#01011c")
root.iconbitmap(os.path.join(os.path.dirname(__file__), "icons", "RarCleaner.ico"))

root.geometry("900x700")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=0)
root.columnconfigure(2, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)

text_directory = customtkinter.CTkTextbox(master=root, height=0, width=269, bg_color="#01011c", font=("Times", 10), border_spacing=0, corner_radius=5, border_width=2)
text_directory.insert(tkinter.END, directory if directory else "")
text_directory.configure(state="disabled")
text_directory.grid(row=0, column=1, sticky="SW", pady=(0, 10))

button4 = customtkinter.CTkButton(master=root, text="Browse Files", command=update_directory, height=10, width=0, bg_color="#01011c", border_width=2)
button4.grid(row=0, column=1, sticky="SE", pady=(0, 11))

listbox_frame = customtkinter.CTkFrame(root, width=500, height=300, fg_color="#1b1c42", corner_radius=10)
listbox_frame.grid(row=1, column=1, sticky="NS")

listbox = tkinter.Listbox(listbox_frame, width=75, height=30, bg="#1b1c42", fg="#ffffff")
listbox.pack(fill="both", expand=True, padx=10, pady=10)

button = customtkinter.CTkButton(master=root, text="Update directory", command=find_archives, width=0, height=10, bg_color="#01011c", border_width=2)
button.grid(sticky="E", row=1, column=0, padx=(0, 10))

button2 = customtkinter.CTkButton(master=root, text="Delete", command=delete_archive, width=80, height=10, bg_color="#01011c", border_width=2)
button2.grid(sticky="SW", row=1, column=2, pady=(150, 70), padx=(10, 0))

button3 = customtkinter.CTkButton(master=root, text="Delete All", command=delete_all_archives, width=80, height=10, bg_color="#01011c", border_width=2)
button3.grid(sticky="SW", row=1, column=2, padx=(10, 0))

root.mainloop()
