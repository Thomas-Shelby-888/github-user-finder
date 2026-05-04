import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests

DEFAULT_FILE = "favorites.json"
API_URL = "https://api.github.com/search/users"

class GitHubUserFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("980x680")
        self.root.minsize(900, 600)
        self.results = []
        self.favorites = []
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Готово к работе")
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        top = ttk.LabelFrame(main, text="Поиск пользователя GitHub", padding=10)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Entry(top, textvariable=self.search_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(top, text="Искать", command=self.search_users).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(top, text="Сохранить избранное", command=self.save_favorites).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(top, text="Загрузить избранное", command=self.load_favorites).grid(row=0, column=3)

        left = ttk.LabelFrame(main, text="Результаты поиска", padding=10)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=12)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.results_list = tk.Listbox(left, height=18)
        self.results_list.grid(row=0, column=0, sticky="nsew")
        res_scroll = ttk.Scrollbar(left, orient="vertical", command=self.results_list.yview)
        self.results_list.configure(yscrollcommand=res_scroll.set)
        res_scroll.grid(row=0, column=1, sticky="ns")
        ttk.Button(left, text="Добавить в избранное", command=self.add_favorite).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        right = ttk.LabelFrame(main, text="Избранные пользователи", padding=10)
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=12)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.fav_list = tk.Listbox(right, height=18)
        self.fav_list.grid(row=0, column=0, sticky="nsew")
        fav_scroll = ttk.Scrollbar(right, orient="vertical", command=self.fav_list.yview)
        self.fav_list.configure(yscrollcommand=fav_scroll.set)
        fav_scroll.grid(row=0, column=1, sticky="ns")
        btns = ttk.Frame(right)
        btns.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        ttk.Button(btns, text="Удалить из избранного", command=self.remove_favorite).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(btns, text="Очистить избранное", command=self.clear_favorites).grid(row=0, column=1, sticky="ew")

        status = ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w", padding=6)
        status.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _validate_search(self, text):
        text = text.strip()
        if not text:
            raise ValueError("Поле поиска не должно быть пустым.")
        return text

    def search_users(self):
        try:
            query = self._validate_search(self.search_var.get())
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        try:
            resp = requests.get(API_URL, params={"q": query, "per_page": 20}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self.results = data.get("items", [])
            self.results_list.delete(0, tk.END)
            for user in self.results:
                self.results_list.insert(tk.END, f"{user.get('login', '')} | {user.get('html_url', '')}")
            self.status_var.set(f"Найдено пользователей: {len(self.results)}")
        except requests.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось выполнить поиск: {e}")

    def add_favorite(self):
        idx = self.results_list.curselection()
        if not idx:
            messagebox.showwarning("Избранное", "Выберите пользователя из результатов поиска.")
            return
        user = self.results[idx[0]]
        fav = {"login": user.get("login", ""), "html_url": user.get("html_url", ""), "avatar_url": user.get("avatar_url", "")}
        if fav not in self.favorites:
            self.favorites.append(fav)
            self.refresh_favorites()
            self.status_var.set(f"Добавлен в избранное: {fav['login']}")
        else:
            messagebox.showinfo("Избранное", "Этот пользователь уже есть в избранном.")

    def refresh_favorites(self):
        self.fav_list.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_list.insert(tk.END, f"{fav['login']} | {fav['html_url']}")

    def remove_favorite(self):
        idx = self.fav_list.curselection()
        if not idx:
            messagebox.showwarning("Удаление", "Выберите пользователя в избранном.")
            return
        fav = self.favorites.pop(idx[0])
        self.refresh_favorites()
        self.status_var.set(f"Удалён из избранного: {fav['login']}")

    def clear_favorites(self):
        if not self.favorites:
            return
        if not messagebox.askyesno("Очистка", "Очистить избранное?"):
            return
        self.favorites = []
        self.refresh_favorites()
        self.status_var.set("Избранное очищено")

    def save_favorites(self):
        path = filedialog.asksaveasfilename(title="Сохранить избранное", defaultextension=".json", initialfile=DEFAULT_FILE, filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=4)
        self.status_var.set(f"Избранное сохранено: {os.path.basename(path)}")
        messagebox.showinfo("Сохранение", "Избранные пользователи сохранены в JSON.")

    def load_favorites(self):
        path = filedialog.askopenfilename(title="Загрузить избранное", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded = []
            for item in data:
                login = str(item.get("login", "")).strip()
                url = str(item.get("html_url", "")).strip()
                if not login:
                    continue
                loaded.append({"login": login, "html_url": url, "avatar_url": str(item.get("avatar_url", ""))})
            self.favorites = loaded
            self.refresh_favorites()
            self.status_var.set(f"Загружено избранных: {len(self.favorites)}")
            messagebox.showinfo("Загрузка", "Избранное загружено из JSON.")
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить файл: {e}")


def main():
    root = tk.Tk()
    GitHubUserFinderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
