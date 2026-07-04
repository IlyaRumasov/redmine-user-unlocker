# =====================================================================
# НОВА ВЕРСІЯ (unlocker.py)
# Покращена утиліта: прогрес-бар, валідація, логування дій, експорт звітів
# =====================================================================

import sys
import os
import datetime
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk  # Для прогрес-бару
from redminelib import Redmine

# Спроба імпортувати модуль для системного звуку (тільки для Windows)
try:
    import winsound
except ImportError:
    winsound = None


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Налаштування локального логування (продуктивний файл)
log_file_path = os.path.join(os.path.abspath("."), "unlock_history.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

cancelled = False

# ПРОДУКТИВНІ дані
REDMINE_API_URL = 'https://redmine.mindysupport.com/'
REDMINE_API_KEY = '35ffa3eb3777e38bbb2613749be4b40338c6d5ea'


def set_ui_message(text=None):
    loaded_decision_label.config(text=text)
    root.update()


def change_status(users=None):
    try:
        redmine = Redmine(REDMINE_API_URL, key=REDMINE_API_KEY, requests={'verify': True})
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося підключитися: {e}")
        logging.error(f"Помилка підключення до API: {e}")
        return

    # Лічильники для статистики
    stats = {'success': 0, 'skipped': 0, 'errors': 0}
    total_users = len(users)
    progress_bar['maximum'] = total_users

    for idx, login in enumerate(users):
        if cancelled:
            set_ui_message("Процес зупинено користувачем.")
            logging.info("--- Процес зупинено користувачем ---")
            break

        set_ui_message(f'Обробляю логін ({idx + 1}/{total_users}): {login}...')
        progress_bar['value'] = idx + 1
        root.update_idletasks()

        try:
            users_redmine = list(redmine.user.filter(status=3, login=login))

            if not users_redmine:
                msg = f"[{login}] Не знайдено / Вже активний"
                logins_listbox.insert(tk.END, msg)
                logging.info(msg)
                stats['skipped'] += 1
            else:
                user = users_redmine[0]
                redmine.user.update(user.id, status=1)
                msg = f"[{login}] РОЗБЛОКОВАНО ✅"
                logins_listbox.insert(tk.END, msg)
                logging.info(msg)
                stats['success'] += 1

        except Exception as e:
            msg = f"[{login}] Помилка: {e}"
            logins_listbox.insert(tk.END, msg)
            logging.error(msg)
            stats['errors'] += 1

        logins_listbox.yview(tk.END)
        root.update()

    return stats


def start_cycle():
    global cancelled
    cancelled = False

    logins_text = entry.get("1.0", tk.END).strip()
    if not logins_text:
        messagebox.showwarning("Увага", "Введіть або вставте логіни!")
        return

    # ВАЛІДАЦІЯ: Очищення від пробілів та порожніх рядків
    raw_users = [line.strip() for line in logins_text.split('\n') if line.strip()]

    # ВАЛІДАЦІЯ: Видалення дублікатів зі збереженням порядку
    users = list(dict.fromkeys(raw_users))

    duplicates_removed = len(raw_users) - len(users)
    if duplicates_removed > 0:
        logins_listbox.insert(tk.END, f"--- Видалено дублікатів: {duplicates_removed} ---")

    logging.info(f"--- ЗАПУСК ЦИКЛУ: {len(users)} унікальних логінів ---")

    start_button.config(state="disabled")
    progress_bar['value'] = 0

    stats = change_status(users)

    if not cancelled and stats:
        # Звуковий сигнал завершення
        if winsound:
            winsound.MessageBeep(winsound.MB_OK)
        else:
            root.bell()

        final_msg = f"Готово! ✅\nРозблоковано: {stats['success']} | Пропущено: {stats['skipped']} | Помилок: {stats['errors']}"
        set_ui_message(final_msg)
        logging.info(f"--- ЦИКЛ ЗАВЕРШЕНО. {final_msg.replace(chr(10), ' ')} ---")

    start_button.config(state="normal")


def paste():
    try:
        clipboard_data = root.clipboard_get()
        entry.insert(tk.END, clipboard_data + '\n')
    except tk.TclError:
        pass


def save_report():
    items = logins_listbox.get(0, tk.END)
    if not items:
        messagebox.showinfo("Увага", "Немає даних для збереження.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Зберегти звіт"
    )

    if filepath:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(items))
            messagebox.showinfo("Успіх", "Звіт успішно збережено!")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл:\n{e}")


def cancel_cycle():
    global cancelled
    cancelled = True
    messagebox.showinfo('Відміна', 'Очікуйте завершення поточного запиту. Цикл зупиняється...')


def reset():
    global cancelled
    cancelled = True
    entry.config(state='normal')
    entry.delete('1.0', tk.END)
    logins_listbox.delete(0, tk.END)
    loaded_decision_label.config(text='')
    progress_bar['value'] = 0


def show_info():
    messagebox.showinfo('На лице собі нажми', 'Іди працюй.\n\n Кнопки воно тут жмакає.')


# --- Графічний інтерфейс ---
root = tk.Tk()
root.title('Розблокування користувачів Redmine')
root.resizable(False, False)
btn_width = 16

root.configure(padx=5, pady=5)
root.grid_rowconfigure(0, weight=2)
root.grid_rowconfigure(1, weight=0)  # Для прогрес-бару
root.grid_rowconfigure(2, weight=1)  # Для лістбоксу
root.grid_rowconfigure(3, weight=0)  # Для лейблу
root.grid_rowconfigure(4, weight=0)  # Для футера
root.grid_columnconfigure(0, weight=1)

top_frame = tk.Frame(root)
top_frame.grid(row=0, column=0, sticky='nsew')
top_frame.grid_rowconfigure(0, weight=0)
top_frame.grid_rowconfigure(1, weight=0)
top_frame.grid_rowconfigure(2, weight=0)
top_frame.grid_rowconfigure(3, weight=1)
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(1, weight=0)

entry_label = tk.Label(top_frame, text='Введіть логіни (кожен з нового рядка):')
entry_label.grid(row=2, column=0, sticky='nw', padx=(0, 5), pady=(0, 5))
entry = tk.Text(top_frame, height=10, width=40)
entry.grid(row=3, column=0, sticky='nsew', padx=(0, 5))

buttons_frame = tk.Frame(top_frame)
buttons_frame.grid(row=3, column=1, rowspan=2, sticky='nsew')

paste_button = tk.Button(buttons_frame, text='Вставити із буфера', width=btn_width, command=paste)
paste_button.pack(pady=2)
start_button = tk.Button(buttons_frame, text='Почати', width=btn_width, command=start_cycle, bg="#d4edda")
start_button.pack(pady=2)
cancel_button = tk.Button(buttons_frame, text='Відміна', width=btn_width, command=cancel_cycle, bg="#f8d7da")
cancel_button.pack(pady=2)
reset_button = tk.Button(buttons_frame, text='Очистити', width=btn_width, command=reset)
reset_button.pack(pady=2)
# Нова кнопка для експорту
save_button = tk.Button(buttons_frame, text='Зберегти звіт', width=btn_width, command=save_report)
save_button.pack(pady=2)

# Прогрес-бар
progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate')
progress_bar.grid(row=1, column=0, sticky='nsew', pady=(5, 0))

logins_listbox = tk.Listbox(root, height=10)
logins_listbox.grid(row=2, column=0, sticky='nsew', pady=(5, 5))

loaded_decision_label = tk.Label(root, text='', fg='blue', justify="left")
loaded_decision_label.grid(row=3, column=0, sticky='w', pady=(0, 5))

footer_frame = tk.Frame(root)
footer_frame.grid(row=4, column=0, sticky='nsew', pady=(5, 0))
footer_frame.grid_columnconfigure(0, weight=1)

current_year = datetime.datetime.now().year
copy_text = f'© {current_year} Mindy Support\nЛише для використання IT відділом.\nВсі дії логуються у файл.'
copyright_label = tk.Label(footer_frame, text=copy_text, font=('Arial', 8), fg='gray', justify="left")
copyright_label.grid(row=0, column=0, sticky='w', padx=5)

info_button = tk.Button(footer_frame, text='Інформація', width=10, command=show_info)
info_button.grid(row=0, column=1, sticky='e', pady=5)

root.mainloop()
