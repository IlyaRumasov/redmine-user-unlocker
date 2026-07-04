# =====================================================================
# СТАРА ВЕРСІЯ (main.py)
# Базова утиліта: тільки розблокування, без логування та прогрес-бару
# =====================================================================

import sys
import os
import datetime
import tkinter as tk
from tkinter import messagebox
from redminelib import Redmine

# Безпечно завантажуємо ключ із системи
REDMINE_API_URL = 'https://test-redmine.mindysupport.com'
REDMINE_API_KEY = os.environ.get('REDMINE_API_KEY')

if not REDMINE_API_KEY:
    messagebox.showerror("Помилка конфігурації", "Не знайдено змінну оточення REDMINE_API_KEY!\nБудь ласка, налаштуйте файл .env.")
    sys.exit(1)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

cancelled = False

def set_ui_message(text=None):
    loaded_decision_label.config(text=text)
    root.update()

def change_status(users=None):
    try:
        redmine = Redmine(REDMINE_API_URL, key=REDMINE_API_KEY, requests={'verify': True})
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося підключитися: {e}")
        return

    for idx, login in enumerate(users):
        if cancelled:
            set_ui_message("Процес зупинено.")
            break

        set_ui_message(f'Обробляю логін: {login}...')
        root.update_idletasks()

        try:
            users_redmine = list(redmine.user.filter(status=3, login=login))

            if not users_redmine:
                logins_listbox.insert(tk.END, f"[{login}] Не знайдено / Вже активний")
            else:
                user = users_redmine[0]
                redmine.user.update(user.id, status=1)
                logins_listbox.insert(tk.END, f"[{login}] РОЗБЛОКОВАНО ✅")

        except Exception as e:
            logins_listbox.insert(tk.END, f"[{login}] Помилка: {e}")

        logins_listbox.yview(tk.END)
        root.update()

def start_cycle():
    global cancelled
    cancelled = False

    logins_text = entry.get("1.0", tk.END).strip()
    if not logins_text:
        messagebox.showwarning("Увага", "Введіть або вставте логіни!")
        return

    users = [line.strip() for line in logins_text.split('\n') if line.strip()]
    start_button.config(state="disabled")

    change_status(users)

    if not cancelled:
        set_ui_message("Готово!")
    start_button.config(state="normal")

def paste():
    try:
        clipboard_data = root.clipboard_get()
        entry.insert(tk.END, clipboard_data + '\n')
    except tk.TclError:
        pass

def cancel_cycle():
    global cancelled
    cancelled = True
    messagebox.showinfo('Відміна', 'Цикл зупинено.')

def reset():
    global cancelled
    cancelled = True
    entry.config(state='normal')
    entry.delete('1.0', tk.END)
    logins_listbox.delete(0, tk.END)
    loaded_decision_label.config(text='')

def show_info():
    messagebox.showinfo('На лице собі нажми', 'Іди працюй.\n\n Кнопки воно тут жмакає.')

root = tk.Tk()
root.title('Розблокування користувачів Redmine')
root.resizable(False, False)
btn_width = 16

root.configure(padx=5, pady=5)
root.grid_rowconfigure(0, weight=2)
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=0)
root.grid_rowconfigure(4, weight=0)
root.grid_columnconfigure(0, weight=1)

top_frame = tk.Frame(root)
top_frame.grid(row=0, column=0, sticky='nsew')
top_frame.grid_rowconfigure(0, weight=0)
top_frame.grid_rowconfigure(1, weight=0)
top_frame.grid_rowconfigure(2, weight=0)
top_frame.grid_rowconfigure(3, weight=1)
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(1, weight=2)

entry_label = tk.Label(top_frame, text='Введіть логіни:')
entry_label.grid(row=2, column=0, sticky='nw', padx=(0, 5), pady=(0, 5))
entry = tk.Text(top_frame, height=10, width=40)
entry.grid(row=3, column=0, sticky='nsew', padx=(0, 5))

buttons_frame = tk.Frame(top_frame)
buttons_frame.grid(row=3, column=1, rowspan=2, sticky='nsew')

paste_button = tk.Button(buttons_frame, text='Вставити із буфера', width=btn_width, command=paste)
paste_button.pack(pady=5)
start_button = tk.Button(buttons_frame, text='Почати', width=btn_width, command=start_cycle)
start_button.pack(pady=5)
cancel_button = tk.Button(buttons_frame, text='Відміна', width=btn_width, command=cancel_cycle)
cancel_button.pack(pady=5)
reset_button = tk.Button(buttons_frame, text='Очистити', width=btn_width, command=reset)
reset_button.pack(pady=5)

logins_listbox = tk.Listbox(root)
logins_listbox.grid(row=1, column=0, sticky='nsew', pady=(5, 5))

loaded_decision_label = tk.Label(root, text='', fg='blue')
loaded_decision_label.grid(row=2, column=0, sticky='nsew', pady=(5, 5))

footer_frame = tk.Frame(root)
footer_frame.grid(row=4, column=0, sticky='nsew', pady=(5, 0))
footer_frame.grid_columnconfigure(0, weight=1)

current_year = datetime.datetime.now().year
copy_text = f'© {current_year} Mindy Support\nЛише для використання IT відділом.\nНе для поширення.'
copyright_label = tk.Label(footer_frame, text=copy_text, font=('Arial', 8), fg='gray')
copyright_label.grid(row=0, column=0, sticky='n', padx=5)

info_button = tk.Button(footer_frame, text='Інформація', width=10, command=show_info)
info_button.grid(row=1, column=0, sticky='n', pady=5)

root.mainloop()
