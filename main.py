"""
main.py
Interfaz gráfica moderna de escritorio para la gestión y manipulación integral de documentos PDF y Word.
Desarrollada con CustomTkinter en modo oscuro, con procesamiento asíncrono (multihilo).

Módulos incluidos:
1. Unir PDFs
2. Dividir PDF (por rangos o individual)
3. Organizar y Rotar páginas
4. Comprimir PDF (reducción de metadatos y flujos)
5. Imágenes a PDF (JPG, PNG, WEBP, BMP)
6. Word a PDF (individual y por lotes)
7. Seguridad (Proteger con AES-128/AES-256 y Desproteger)
"""

import os
import threading
from typing import List, Dict, Any, Optional
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from pdf_tools import (
    merge_pdfs,
    split_pdf_ranges,
    split_pdf_all,
    get_pdf_page_count,
    reorganize_pdf,
    compress_pdf,
    images_to_pdf,
    is_pdf_encrypted,
    encrypt_pdf,
    decrypt_pdf,
    convert_docx_batch,
    PDFToolError
)

# Configuración de apariencia global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def format_bytes(num_bytes: int) -> str:
    """Convierte bytes a representación amigable (KB, MB)."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


class PDFMasterApp(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()

        self.title("PDF Master Suite - Gestor Integral de Documentos")
        self.geometry("1040x740")
        self.minsize(920, 660)

        # Estado global
        self._is_processing = False

        # Datos - Pestaña 1: Unir
        self.merge_files: List[str] = []
        self.merge_selected_index: Optional[int] = None

        # Datos - Pestaña 2: Dividir
        self.split_source_file: str = ""
        self.split_total_pages: int = 0
        self.split_mode_var = tk.StringVar(value="ranges")

        # Datos - Pestaña 3: Organizar / Rotar
        self.reorg_source_file: str = ""
        self.reorg_pages: List[Dict[str, int]] = []
        self.reorg_selected_index: Optional[int] = None

        # Datos - Pestaña 4: Comprimir
        self.comp_source_file: str = ""

        # Datos - Pestaña 5: Imágenes a PDF
        self.img_files: List[str] = []
        self.img_selected_index: Optional[int] = None

        # Datos - Pestaña 6: Word a PDF (Lotes)
        self.word_files: List[str] = []
        self.word_selected_index: Optional[int] = None
        self.word_dest_mode_var = tk.StringVar(value="same_folder")
        self.word_custom_output_dir: str = ""

        # Datos - Pestaña 7: Seguridad
        self.sec_mode_var = tk.StringVar(value="encrypt")
        self.sec_source_file: str = ""
        self.sec_algo_var = tk.StringVar(value="AES-256")

        # Construir interfaz
        self._create_header()
        self._create_tabs()
        self._create_status_bar()

    # -------------------------------------------------------------------------
    # HEADER Y BARRA DE ESTADO
    # -------------------------------------------------------------------------
    def _create_header(self):
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray20", "gray13"))
        header_frame.pack(fill="x", padx=0, pady=0)

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="PDF Master Suite",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("gray10", "white")
        )
        title_lbl.pack(anchor="w", padx=20, pady=(10, 2))

        subtitle_lbl = ctk.CTkLabel(
            header_frame,
            text="Suite completa local: Unir, Dividir, Rotar, Comprimir, Imágenes, Word por lotes y Seguridad AES",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65")
        )
        subtitle_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    def _create_status_bar(self):
        status_frame = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color=("gray22", "gray12"))
        status_frame.pack(side="bottom", fill="x")

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Estado: Listo",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color=("gray30", "gray70")
        )
        self.status_label.pack(side="left", padx=16, pady=6, fill="x", expand=True)

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=180, mode="indeterminate")
        self.progress_bar.pack(side="right", padx=16, pady=8)
        self.progress_bar.set(0)

    def set_status(self, text: str, state_type: str = "info"):
        colors = {
            "info": ("gray30", "gray70"),
            "success": ("#2e7d32", "#4caf50"),
            "warning": ("#f57f17", "#ffb74d"),
            "error": ("#c62828", "#ef5350"),
            "processing": ("#0288d1", "#29b6f6")
        }
        color = colors.get(state_type, colors["info"])
        self.status_label.configure(text=f"Estado: {text}", text_color=color)

        if state_type == "processing":
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.set(0)

    # -------------------------------------------------------------------------
    # EJECUCIÓN ASÍNCRONA (THREADING)
    # -------------------------------------------------------------------------
    def run_async(self, task_func, on_success=None, on_error=None, initial_msg="Procesando..."):
        """Ejecuta una función en segundo plano para evitar bloqueos en la interfaz."""
        if self._is_processing:
            messagebox.showwarning("Operación en curso", "Ya hay un proceso en ejecución. Espera a que termine.")
            return

        self._is_processing = True
        self.set_status(initial_msg, "processing")

        def worker():
            try:
                result = task_func()
                self.after(0, lambda: self._on_worker_success(result, on_success))
            except Exception as exc:
                self.after(0, lambda: self._on_worker_error(exc, on_error))

        threading.Thread(target=worker, daemon=True).start()

    def _on_worker_success(self, result, callback):
        self._is_processing = False
        if callback:
            callback(result)

    def _on_worker_error(self, exc, callback):
        self._is_processing = False
        msg = str(exc)
        self.set_status(f"Error: {msg}", "error")
        if callback:
            callback(exc)
        else:
            messagebox.showerror("Error", msg)

    # -------------------------------------------------------------------------
    # PESTAÑAS PRINCIPALES
    # -------------------------------------------------------------------------
    def _create_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=14, pady=10)

        self.tab_merge = self.tabview.add("1. Unir PDFs")
        self.tab_split = self.tabview.add("2. Dividir PDF")
        self.tab_reorg = self.tabview.add("3. Organizar / Rotar")
        self.tab_comp = self.tabview.add("4. Comprimir")
        self.tab_img = self.tabview.add("5. Imágenes a PDF")
        self.tab_word = self.tabview.add("6. Word a PDF")
        self.tab_sec = self.tabview.add("7. Seguridad")

        self._build_merge_tab()
        self._build_split_tab()
        self._build_reorg_tab()
        self._build_comp_tab()
        self._build_img_tab()
        self._build_word_tab()
        self._build_sec_tab()

    # =========================================================================
    # PESTAÑA 1: UNIR PDFs
    # =========================================================================
    def _build_merge_tab(self):
        toolbar = ctk.CTkFrame(self.tab_merge, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(6, 8))

        ctk.CTkButton(toolbar, text="+ Agregar PDFs", command=self._on_merge_add_files, width=130, fg_color="#1f538d").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="▲ Subir", width=85, command=self._on_merge_move_up).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="▼ Bajar", width=85, command=self._on_merge_move_down).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Eliminar", width=85, fg_color="#992222", hover_color="#771111", command=self._on_merge_remove).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Limpiar Todo", width=95, fg_color="gray30", hover_color="gray25", command=self._on_merge_clear).pack(side="left", padx=4)

        self.merge_count_label = ctk.CTkLabel(toolbar, text="0 archivos", text_color="gray60")
        self.merge_count_label.pack(side="right", padx=8)

        self.merge_scroll_frame = ctk.CTkScrollableFrame(self.tab_merge, label_text="Archivos a Unir (Orden de arriba a abajo)")
        self.merge_scroll_frame.pack(fill="both", expand=True, padx=8, pady=4)

        btn_save = ctk.CTkButton(
            self.tab_merge,
            text="✔ Unir PDFs y Guardar Como...",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_merge_process
        )
        btn_save.pack(fill="x", padx=8, pady=8)

    def _render_merge_list(self):
        for widget in self.merge_scroll_frame.winfo_children():
            widget.destroy()

        self.merge_count_label.configure(text=f"{len(self.merge_files)} archivo(s)")

        if not self.merge_files:
            empty_lbl = ctk.CTkLabel(
                self.merge_scroll_frame,
                text="No hay archivos agregados.\nHaz clic en '+ Agregar PDFs' para comenzar.",
                text_color="gray50"
            )
            empty_lbl.pack(pady=40)
            return

        for idx, file_path in enumerate(self.merge_files):
            is_selected = (idx == self.merge_selected_index)
            bg_color = "#1f538d" if is_selected else ("gray25", "gray18")

            item_frame = ctk.CTkFrame(self.merge_scroll_frame, fg_color=bg_color, corner_radius=6)
            item_frame.pack(fill="x", pady=2, padx=4)

            btn = ctk.CTkButton(
                item_frame,
                text=f"[{idx + 1}]  {os.path.basename(file_path)}",
                anchor="w",
                fg_color="transparent",
                hover_color=("gray35", "gray28"),
                text_color="white",
                command=lambda i=idx: self._select_merge_item(i)
            )
            btn.pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkLabel(
                item_frame,
                text=os.path.dirname(file_path),
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            ).pack(side="right", padx=12)

    def _select_merge_item(self, idx: int):
        self.merge_selected_index = idx
        self._render_merge_list()

    def _on_merge_add_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF para unir",
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
        )
        if files:
            for f in files:
                norm_f = os.path.normpath(f)
                if norm_f not in self.merge_files:
                    self.merge_files.append(norm_f)
            self._render_merge_list()
            self.set_status(f"Se agregaron {len(files)} archivo(s).", "info")

    def _on_merge_move_up(self):
        if self.merge_selected_index is not None and self.merge_selected_index > 0:
            idx = self.merge_selected_index
            self.merge_files[idx - 1], self.merge_files[idx] = self.merge_files[idx], self.merge_files[idx - 1]
            self.merge_selected_index = idx - 1
            self._render_merge_list()

    def _on_merge_move_down(self):
        if self.merge_selected_index is not None and self.merge_selected_index < len(self.merge_files) - 1:
            idx = self.merge_selected_index
            self.merge_files[idx + 1], self.merge_files[idx] = self.merge_files[idx], self.merge_files[idx + 1]
            self.merge_selected_index = idx + 1
            self._render_merge_list()

    def _on_merge_remove(self):
        if self.merge_selected_index is not None and 0 <= self.merge_selected_index < len(self.merge_files):
            del self.merge_files[self.merge_selected_index]
            if not self.merge_files:
                self.merge_selected_index = None
            elif self.merge_selected_index >= len(self.merge_files):
                self.merge_selected_index = len(self.merge_files) - 1
            self._render_merge_list()

    def _on_merge_clear(self):
        self.merge_files.clear()
        self.merge_selected_index = None
        self._render_merge_list()
        self.set_status("Lista de PDFs limpiada.", "info")

    def _on_merge_process(self):
        if len(self.merge_files) < 2:
            messagebox.showwarning("Archivos insuficientes", "Debes agregar al menos 2 archivos PDF para unirlos.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Guardar PDF combinado como",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
        )
        if not out_path:
            return

        files = list(self.merge_files)

        def task():
            merge_pdfs(files, out_path)
            return out_path

        def on_done(res):
            self.set_status(f"PDFs combinados guardados en: {os.path.basename(res)}", "success")
            messagebox.showinfo("Éxito", f"PDF combinado guardado exitosamente en:\n{res}")

        self.run_async(task, on_success=on_done, initial_msg="Uniendo archivos PDF...")

    # =========================================================================
    # PESTAÑA 2: DIVIDIR PDF
    # =========================================================================
    def _build_split_tab(self):
        sel_frame = ctk.CTkFrame(self.tab_split, fg_color=("gray22", "gray17"))
        sel_frame.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(sel_frame, text="1. Selecciona el archivo PDF a dividir:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        input_row = ctk.CTkFrame(sel_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=(0, 8))

        self.split_path_entry = ctk.CTkEntry(input_row, placeholder_text="Ningún archivo seleccionado...")
        self.split_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(input_row, text="Examinar...", width=120, command=self._on_split_browse).pack(side="right")

        self.split_info_label = ctk.CTkLabel(sel_frame, text="Páginas detectadas: -", text_color="gray60")
        self.split_info_label.pack(anchor="w", padx=12, pady=(0, 10))

        opt_frame = ctk.CTkFrame(self.tab_split, fg_color=("gray22", "gray17"))
        opt_frame.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(opt_frame, text="2. Modalidad de división:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(10, 8))

        ctk.CTkRadioButton(
            opt_frame,
            text="Extraer páginas seleccionadas o rangos en un nuevo PDF",
            variable=self.split_mode_var,
            value="ranges",
            command=self._on_split_mode_change
        ).pack(anchor="w", padx=20, pady=4)

        range_inner = ctk.CTkFrame(opt_frame, fg_color="transparent")
        range_inner.pack(fill="x", padx=40, pady=(2, 10))

        ctk.CTkLabel(range_inner, text="Rangos de páginas:").pack(side="left", padx=(0, 8))
        self.split_range_entry = ctk.CTkEntry(range_inner, placeholder_text="Ejemplo: 1-3, 5, 8-10", width=240)
        self.split_range_entry.pack(side="left")
        ctk.CTkLabel(range_inner, text="(Valores basados en 1, separados por comas)", text_color="gray50", font=ctk.CTkFont(size=11)).pack(side="left", padx=8)

        ctk.CTkRadioButton(
            opt_frame,
            text="Extraer todas las páginas individualmente (1 archivo PDF por página)",
            variable=self.split_mode_var,
            value="all",
            command=self._on_split_mode_change
        ).pack(anchor="w", padx=20, pady=(4, 12))

        btn_split_process = ctk.CTkButton(
            self.tab_split,
            text="✔ Procesar y Extraer Páginas",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_split_process
        )
        btn_split_process.pack(fill="x", padx=12, pady=12)

    def _on_split_mode_change(self):
        is_ranges = (self.split_mode_var.get() == "ranges")
        self.split_range_entry.configure(state="normal" if is_ranges else "disabled")

    def _on_split_browse(self):
        file = filedialog.askopenfilename(title="Seleccionar PDF para dividir", filetypes=[("Archivos PDF (*.pdf)", "*.pdf")])
        if file:
            self.split_source_file = os.path.normpath(file)
            self.split_path_entry.delete(0, tk.END)
            self.split_path_entry.insert(0, self.split_source_file)

            try:
                self.split_total_pages = get_pdf_page_count(self.split_source_file)
                self.split_info_label.configure(
                    text=f"Total de páginas detectadas: {self.split_total_pages} páginas.",
                    text_color="#4caf50"
                )
                self.set_status(f"PDF cargado: {os.path.basename(self.split_source_file)} ({self.split_total_pages} págs.)", "info")
            except Exception as e:
                self.split_total_pages = 0
                self.split_info_label.configure(text=f"Error: {str(e)}", text_color="#ef5350")

    def _on_split_process(self):
        if not self.split_source_file or not os.path.exists(self.split_source_file):
            messagebox.showwarning("Archivo no seleccionado", "Selecciona un archivo PDF válido primero.")
            return

        mode = self.split_mode_var.get()

        if mode == "ranges":
            ranges_str = self.split_range_entry.get().strip()
            if not ranges_str:
                messagebox.showwarning("Rango requerido", "Introduce los rangos de páginas (ej. 1-3, 5).")
                return

            out_path = filedialog.asksaveasfilename(
                title="Guardar páginas extraídas como",
                defaultextension=".pdf",
                filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
            )
            if not out_path:
                return

            def task():
                return split_pdf_ranges(self.split_source_file, ranges_str, out_path)

            def on_done(count):
                self.set_status(f"Se guardaron {count} página(s) en {os.path.basename(out_path)}", "success")
                messagebox.showinfo("División Exitosa", f"Se extrajeron {count} páginas correctamente en:\n{out_path}")

            self.run_async(task, on_success=on_done, initial_msg="Extrayendo páginas...")

        elif mode == "all":
            out_folder = filedialog.askdirectory(title="Carpeta destino para las páginas")
            if not out_folder:
                return

            def task():
                return split_pdf_all(self.split_source_file, out_folder)

            def on_done(files):
                self.set_status(f"Se generaron {len(files)} archivos en la carpeta.", "success")
                messagebox.showinfo("División Exitosa", f"Se han generado {len(files)} archivos individuales en:\n{out_folder}")

            self.run_async(task, on_success=on_done, initial_msg="Extrayendo páginas individuales...")

    # =========================================================================
    # PESTAÑA 3: ORGANIZAR Y ROTAR
    # =========================================================================
    def _build_reorg_tab(self):
        top_frame = ctk.CTkFrame(self.tab_reorg, fg_color="transparent")
        top_frame.pack(fill="x", padx=8, pady=(6, 6))

        ctk.CTkButton(top_frame, text="Cargar PDF...", command=self._on_reorg_browse, width=130, fg_color="#1f538d").pack(side="left", padx=4)
        self.reorg_file_label = ctk.CTkLabel(top_frame, text="Ningún archivo cargado", text_color="gray60")
        self.reorg_file_label.pack(side="left", padx=8)

        toolbar = ctk.CTkFrame(self.tab_reorg, fg_color=("gray22", "gray17"))
        toolbar.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(toolbar, text="↻ Rotar +90°", width=105, command=lambda: self._on_reorg_rotate(90)).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="↺ Rotar -90°", width=105, command=lambda: self._on_reorg_rotate(-90)).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="↕ Rotar 180°", width=105, command=lambda: self._on_reorg_rotate(180)).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="▲ Subir", width=80, command=self._on_reorg_move_up).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="▼ Bajar", width=80, command=self._on_reorg_move_down).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="Eliminar Página", width=110, fg_color="#992222", hover_color="#771111", command=self._on_reorg_delete_page).pack(side="left", padx=4, pady=6)
        ctk.CTkButton(toolbar, text="Restablecer", width=95, fg_color="gray30", hover_color="gray25", command=self._on_reorg_reset).pack(side="left", padx=4, pady=6)

        self.reorg_scroll_frame = ctk.CTkScrollableFrame(self.tab_reorg, label_text="Lista de Páginas del Documento")
        self.reorg_scroll_frame.pack(fill="both", expand=True, padx=8, pady=4)

        btn_export = ctk.CTkButton(
            self.tab_reorg,
            text="✔ Guardar PDF Reorganizado y Rotado...",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_reorg_export
        )
        btn_export.pack(fill="x", padx=8, pady=8)

    def _on_reorg_browse(self):
        file = filedialog.askopenfilename(title="Seleccionar PDF para organizar", filetypes=[("Archivos PDF (*.pdf)", "*.pdf")])
        if file:
            self.reorg_source_file = os.path.normpath(file)
            self._load_reorg_pages()

    def _load_reorg_pages(self):
        try:
            total = get_pdf_page_count(self.reorg_source_file)
            self.reorg_pages = [{"orig_idx": i, "rotation": 0} for i in range(total)]
            self.reorg_selected_index = 0 if total > 0 else None
            self.reorg_file_label.configure(
                text=f"{os.path.basename(self.reorg_source_file)} ({total} páginas)",
                text_color="#4caf50"
            )
            self._render_reorg_list()
            self.set_status(f"PDF cargado: {os.path.basename(self.reorg_source_file)}", "info")
        except Exception as e:
            self.reorg_file_label.configure(text="Error al cargar archivo", text_color="#ef5350")
            messagebox.showerror("Error", f"No se pudo cargar el PDF: {str(e)}")

    def _render_reorg_list(self):
        for widget in self.reorg_scroll_frame.winfo_children():
            widget.destroy()

        if not self.reorg_pages:
            ctk.CTkLabel(
                self.reorg_scroll_frame,
                text="No hay páginas cargadas.\nHaz clic en 'Cargar PDF...' para ver las páginas.",
                text_color="gray50"
            ).pack(pady=40)
            return

        for pos, item in enumerate(self.reorg_pages):
            is_selected = (pos == self.reorg_selected_index)
            bg_color = "#1f538d" if is_selected else ("gray25", "gray18")

            card = ctk.CTkFrame(self.reorg_scroll_frame, fg_color=bg_color, corner_radius=6)
            card.pack(fill="x", pady=2, padx=4)

            btn = ctk.CTkButton(
                card,
                text=f"Orden #{pos + 1}  ⟶  Página original {item['orig_idx'] + 1}",
                anchor="w",
                fg_color="transparent",
                hover_color=("gray35", "gray28"),
                text_color="white",
                command=lambda p=pos: self._select_reorg_item(p)
            )
            btn.pack(side="left", fill="x", expand=True, padx=8, pady=4)

            rot_val = item["rotation"] % 360
            rot_color = "#ffb74d" if rot_val != 0 else "gray60"
            ctk.CTkLabel(
                card,
                text=f"Rotación: {rot_val}°",
                font=ctk.CTkFont(size=11, weight="bold" if rot_val != 0 else "normal"),
                text_color=rot_color
            ).pack(side="right", padx=12)

    def _select_reorg_item(self, pos: int):
        self.reorg_selected_index = pos
        self._render_reorg_list()

    def _on_reorg_rotate(self, degrees: int):
        if self.reorg_selected_index is not None and 0 <= self.reorg_selected_index < len(self.reorg_pages):
            item = self.reorg_pages[self.reorg_selected_index]
            item["rotation"] = (item["rotation"] + degrees) % 360
            self._render_reorg_list()
        else:
            messagebox.showinfo("Aviso", "Selecciona una página de la lista para rotarla.")

    def _on_reorg_move_up(self):
        if self.reorg_selected_index is not None and self.reorg_selected_index > 0:
            idx = self.reorg_selected_index
            self.reorg_pages[idx - 1], self.reorg_pages[idx] = self.reorg_pages[idx], self.reorg_pages[idx - 1]
            self.reorg_selected_index = idx - 1
            self._render_reorg_list()

    def _on_reorg_move_down(self):
        if self.reorg_selected_index is not None and self.reorg_selected_index < len(self.reorg_pages) - 1:
            idx = self.reorg_selected_index
            self.reorg_pages[idx + 1], self.reorg_pages[idx] = self.reorg_pages[idx], self.reorg_pages[idx + 1]
            self.reorg_selected_index = idx + 1
            self._render_reorg_list()

    def _on_reorg_delete_page(self):
        if self.reorg_selected_index is not None and 0 <= self.reorg_selected_index < len(self.reorg_pages):
            del self.reorg_pages[self.reorg_selected_index]
            if not self.reorg_pages:
                self.reorg_selected_index = None
            elif self.reorg_selected_index >= len(self.reorg_pages):
                self.reorg_selected_index = len(self.reorg_pages) - 1
            self._render_reorg_list()

    def _on_reorg_reset(self):
        if self.reorg_source_file:
            self._load_reorg_pages()

    def _on_reorg_export(self):
        if not self.reorg_source_file or not os.path.exists(self.reorg_source_file):
            messagebox.showwarning("Sin archivo", "Carga un archivo PDF primero.")
            return

        if not self.reorg_pages:
            messagebox.showwarning("Sin páginas", "No hay páginas para exportar.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Guardar PDF reorganizado como",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
        )
        if not out_path:
            return

        config = [{"original_index": it["orig_idx"], "rotation": it["rotation"]} for it in self.reorg_pages]

        def task():
            return reorganize_pdf(self.reorg_source_file, config, out_path)

        def on_done(count):
            self.set_status(f"Guardado exitosamente: {count} páginas en {os.path.basename(out_path)}", "success")
            messagebox.showinfo("Exportación Exitosa", f"Archivo generado con {count} páginas en:\n{out_path}")

        self.run_async(task, on_success=on_done, initial_msg="Generando PDF reorganizado...")

    # =========================================================================
    # PESTAÑA 4: COMPRIMIR PDF
    # =========================================================================
    def _build_comp_tab(self):
        card = ctk.CTkFrame(self.tab_comp, fg_color=("gray22", "gray17"))
        card.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(card, text="Optimización y Compresión de PDF", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            card,
            text="Reduce el peso del PDF eliminando metadatos redundantes, removiendo objetos duplicados y recomprimiendo los flujos de contenido de cada página con pypdf.",
            text_color="gray60",
            wraplength=750,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        ctk.CTkLabel(card, text="1. Selecciona el archivo PDF a comprimir:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(0, 4))
        in_row = ctk.CTkFrame(card, fg_color="transparent")
        in_row.pack(fill="x", padx=16, pady=(0, 8))

        self.comp_input_entry = ctk.CTkEntry(in_row, placeholder_text="Ningún PDF seleccionado...")
        self.comp_input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(in_row, text="Examinar...", width=120, command=self._on_comp_browse).pack(side="right")

        self.comp_info_label = ctk.CTkLabel(card, text="Tamaño original: -", text_color="gray60")
        self.comp_info_label.pack(anchor="w", padx=16, pady=(0, 14))

        # Result box
        self.comp_result_card = ctk.CTkFrame(card, fg_color=("gray26", "gray14"), corner_radius=8)
        self.comp_result_card.pack(fill="x", padx=16, pady=(0, 14))

        self.comp_result_lbl = ctk.CTkLabel(
            self.comp_result_card,
            text="Selecciona un archivo y haz clic en 'Comprimir PDF y Guardar Como...'",
            text_color="gray50",
            pady=16
        )
        self.comp_result_lbl.pack()

        btn_comp = ctk.CTkButton(
            card,
            text="✔ Comprimir PDF y Guardar Como...",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_comp_process
        )
        btn_comp.pack(fill="x", padx=16, pady=(0, 16))

    def _on_comp_browse(self):
        file = filedialog.askopenfilename(title="Seleccionar PDF a comprimir", filetypes=[("Archivos PDF (*.pdf)", "*.pdf")])
        if file:
            self.comp_source_file = os.path.normpath(file)
            self.comp_input_entry.delete(0, tk.END)
            self.comp_input_entry.insert(0, self.comp_source_file)
            sz = os.path.getsize(self.comp_source_file)
            self.comp_info_label.configure(text=f"Tamaño original: {format_bytes(sz)}", text_color="#4caf50")
            self.comp_result_lbl.configure(text="Listo para comprimir. Haz clic en el botón inferior.", text_color="gray60")

    def _on_comp_process(self):
        if not self.comp_source_file or not os.path.exists(self.comp_source_file):
            messagebox.showwarning("Sin archivo", "Selecciona un archivo PDF válido primero.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Guardar PDF comprimido como",
            defaultextension=".pdf",
            initialfile="comprimido_" + os.path.basename(self.comp_source_file),
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
        )
        if not out_path:
            return

        in_file = self.comp_source_file

        def task():
            return compress_pdf(in_file, out_path)

        def on_done(stats):
            orig_str = format_bytes(stats["original_size"])
            new_str = format_bytes(stats["compressed_size"])
            pct = stats["reduction_percent"]
            saved_str = format_bytes(stats["saved_bytes"])

            res_text = (
                f"✔ Compresión finalizada con éxito:\n"
                f"• Tamaño original: {orig_str}\n"
                f"• Tamaño comprimido: {new_str}\n"
                f"• Ahorro de espacio: {saved_str} ({pct}%)\n\n"
                f"Guardado en: {os.path.basename(out_path)}"
            )
            self.comp_result_lbl.configure(text=res_text, text_color="#4caf50")
            self.set_status(f"Compresión lista: reducido en {pct}%", "success")
            messagebox.showinfo("Compresión Completada", res_text)

        self.run_async(task, on_success=on_done, initial_msg="Comprimiendo PDF...")

    # =========================================================================
    # PESTAÑA 5: IMÁGENES A PDF
    # =========================================================================
    def _build_img_tab(self):
        toolbar = ctk.CTkFrame(self.tab_img, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(6, 8))

        ctk.CTkButton(toolbar, text="+ Agregar Imágenes", command=self._on_img_add_files, width=150, fg_color="#1f538d").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="▲ Subir", width=85, command=self._on_img_move_up).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="▼ Bajar", width=85, command=self._on_img_move_down).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Eliminar", width=85, fg_color="#992222", hover_color="#771111", command=self._on_img_remove).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Limpiar Todo", width=95, fg_color="gray30", hover_color="gray25", command=self._on_img_clear).pack(side="left", padx=4)

        self.img_count_label = ctk.CTkLabel(toolbar, text="0 imágenes", text_color="gray60")
        self.img_count_label.pack(side="right", padx=8)

        self.img_scroll_frame = ctk.CTkScrollableFrame(self.tab_img, label_text="Imágenes a compilar en páginas PDF (Ordenadas)")
        self.img_scroll_frame.pack(fill="both", expand=True, padx=8, pady=4)

        btn_compile = ctk.CTkButton(
            self.tab_img,
            text="✔ Compilar Imágenes a PDF y Guardar Como...",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_img_process
        )
        btn_compile.pack(fill="x", padx=8, pady=8)

    def _render_img_list(self):
        for widget in self.img_scroll_frame.winfo_children():
            widget.destroy()

        self.img_count_label.configure(text=f"{len(self.img_files)} imagen(es)")

        if not self.img_files:
            ctk.CTkLabel(
                self.img_scroll_frame,
                text="No has seleccionado imágenes aún.\nHaz clic en '+ Agregar Imágenes' (JPG, PNG, WEBP, BMP).",
                text_color="gray50"
            ).pack(pady=40)
            return

        for idx, file_path in enumerate(self.img_files):
            is_selected = (idx == self.img_selected_index)
            bg_color = "#1f538d" if is_selected else ("gray25", "gray18")

            item_frame = ctk.CTkFrame(self.img_scroll_frame, fg_color=bg_color, corner_radius=6)
            item_frame.pack(fill="x", pady=2, padx=4)

            btn = ctk.CTkButton(
                item_frame,
                text=f"Página {idx + 1}:  {os.path.basename(file_path)}",
                anchor="w",
                fg_color="transparent",
                hover_color=("gray35", "gray28"),
                text_color="white",
                command=lambda i=idx: self._select_img_item(i)
            )
            btn.pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkLabel(
                item_frame,
                text=os.path.dirname(file_path),
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            ).pack(side="right", padx=12)

    def _select_img_item(self, idx: int):
        self.img_selected_index = idx
        self._render_img_list()

    def _on_img_add_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=[("Imágenes (*.jpg;*.jpeg;*.png;*.webp;*.bmp)", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")]
        )
        if files:
            for f in files:
                norm_f = os.path.normpath(f)
                if norm_f not in self.img_files:
                    self.img_files.append(norm_f)
            self._render_img_list()
            self.set_status(f"Se agregaron {len(files)} imagen(es).", "info")

    def _on_img_move_up(self):
        if self.img_selected_index is not None and self.img_selected_index > 0:
            idx = self.img_selected_index
            self.img_files[idx - 1], self.img_files[idx] = self.img_files[idx], self.img_files[idx - 1]
            self.img_selected_index = idx - 1
            self._render_img_list()

    def _on_img_move_down(self):
        if self.img_selected_index is not None and self.img_selected_index < len(self.img_files) - 1:
            idx = self.img_selected_index
            self.img_files[idx + 1], self.img_files[idx] = self.img_files[idx], self.img_files[idx + 1]
            self.img_selected_index = idx + 1
            self._render_img_list()

    def _on_img_remove(self):
        if self.img_selected_index is not None and 0 <= self.img_selected_index < len(self.img_files):
            del self.img_files[self.img_selected_index]
            if not self.img_files:
                self.img_selected_index = None
            elif self.img_selected_index >= len(self.img_files):
                self.img_selected_index = len(self.img_files) - 1
            self._render_img_list()

    def _on_img_clear(self):
        self.img_files.clear()
        self.img_selected_index = None
        self._render_img_list()

    def _on_img_process(self):
        if not self.img_files:
            messagebox.showwarning("Sin imágenes", "Agrega al menos una imagen para crear el PDF.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Guardar PDF compilado como",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
        )
        if not out_path:
            return

        imgs = list(self.img_files)

        def task():
            return images_to_pdf(imgs, out_path)

        def on_done(count):
            self.set_status(f"PDF generado exitosamente con {count} página(s) de imágenes.", "success")
            messagebox.showinfo("Éxito", f"Se compilaron {count} imágenes en el PDF:\n{out_path}")

        self.run_async(task, on_success=on_done, initial_msg="Compilando imágenes a PDF con Pillow...")

    # =========================================================================
    # PESTAÑA 6: WORD A PDF (INDIVIDUAL Y LOTES)
    # =========================================================================
    def _build_word_tab(self):
        card = ctk.CTkFrame(self.tab_word, fg_color=("gray22", "gray17"))
        card.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(card, text="Conversión de Microsoft Word (.docx) a PDF (Soporte Lotes)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            card,
            text="Convierte uno o múltiples documentos de Word preservando fuentes, formatos y tablas mediante la API COM nativa de Office en Windows sin enviar datos a internet.",
            text_color="gray60",
            wraplength=750,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        toolbar = ctk.CTkFrame(self.tab_word, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(toolbar, text="+ Agregar Archivo(s) Word (.docx)", command=self._on_word_add_files, width=220, fg_color="#1f538d").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Eliminar", width=90, fg_color="#992222", hover_color="#771111", command=self._on_word_remove).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Limpiar Todo", width=100, fg_color="gray30", hover_color="gray25", command=self._on_word_clear).pack(side="left", padx=4)

        self.word_count_label = ctk.CTkLabel(toolbar, text="0 documento(s)", text_color="gray60")
        self.word_count_label.pack(side="right", padx=8)

        self.word_scroll_frame = ctk.CTkScrollableFrame(self.tab_word, label_text="Documentos de Word a Convertir")
        self.word_scroll_frame.pack(fill="both", expand=True, padx=12, pady=4)

        dest_frame = ctk.CTkFrame(self.tab_word, fg_color=("gray22", "gray17"))
        dest_frame.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(dest_frame, text="Destino de los PDFs generados:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(8, 4))

        ctk.CTkRadioButton(
            dest_frame,
            text="Guardar en la misma carpeta que cada archivo Word original",
            variable=self.word_dest_mode_var,
            value="same_folder"
        ).pack(anchor="w", padx=20, pady=2)

        custom_row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        custom_row.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkRadioButton(
            custom_row,
            text="Guardar todos en una carpeta específica:",
            variable=self.word_dest_mode_var,
            value="custom_folder"
        ).pack(side="left", padx=(0, 8))

        self.word_dir_entry = ctk.CTkEntry(custom_row, placeholder_text="Selecciona carpeta destino...")
        self.word_dir_entry.pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(custom_row, text="Examinar...", width=100, command=self._on_word_browse_dir).pack(side="right", padx=4)

        btn_convert = ctk.CTkButton(
            self.tab_word,
            text="✔ Iniciar Conversión a PDF",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_word_process
        )
        btn_convert.pack(fill="x", padx=12, pady=(4, 10))

    def _render_word_list(self):
        for widget in self.word_scroll_frame.winfo_children():
            widget.destroy()

        self.word_count_label.configure(text=f"{len(self.word_files)} documento(s)")

        if not self.word_files:
            ctk.CTkLabel(
                self.word_scroll_frame,
                text="No hay documentos de Word agregados.\nHaz clic en '+ Agregar Archivo(s) Word (.docx)'.",
                text_color="gray50"
            ).pack(pady=30)
            return

        for idx, file_path in enumerate(self.word_files):
            is_selected = (idx == self.word_selected_index)
            bg_color = "#1f538d" if is_selected else ("gray25", "gray18")

            item_frame = ctk.CTkFrame(self.word_scroll_frame, fg_color=bg_color, corner_radius=6)
            item_frame.pack(fill="x", pady=2, padx=4)

            btn = ctk.CTkButton(
                item_frame,
                text=f"[{idx + 1}]  {os.path.basename(file_path)}",
                anchor="w",
                fg_color="transparent",
                hover_color=("gray35", "gray28"),
                text_color="white",
                command=lambda i=idx: self._select_word_item(i)
            )
            btn.pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkLabel(
                item_frame,
                text=os.path.dirname(file_path),
                font=ctk.CTkFont(size=10),
                text_color="gray60"
            ).pack(side="right", padx=12)

    def _select_word_item(self, idx: int):
        self.word_selected_index = idx
        self._render_word_list()

    def _on_word_add_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar documentos de Word",
            filetypes=[("Documentos de Word (*.docx;*.doc)", "*.docx;*.doc")]
        )
        if files:
            for f in files:
                norm_f = os.path.normpath(f)
                if norm_f not in self.word_files:
                    self.word_files.append(norm_f)
            self._render_word_list()
            self.set_status(f"Se agregaron {len(files)} documento(s) Word.", "info")

    def _on_word_remove(self):
        if self.word_selected_index is not None and 0 <= self.word_selected_index < len(self.word_files):
            del self.word_files[self.word_selected_index]
            if not self.word_files:
                self.word_selected_index = None
            elif self.word_selected_index >= len(self.word_files):
                self.word_selected_index = len(self.word_files) - 1
            self._render_word_list()

    def _on_word_clear(self):
        self.word_files.clear()
        self.word_selected_index = None
        self._render_word_list()

    def _on_word_browse_dir(self):
        folder = filedialog.askdirectory(title="Carpeta destino para los PDFs convertidos")
        if folder:
            self.word_custom_output_dir = os.path.normpath(folder)
            self.word_dir_entry.delete(0, tk.END)
            self.word_dir_entry.insert(0, self.word_custom_output_dir)
            self.word_dest_mode_var.set("custom_folder")

    def _on_word_process(self):
        if not self.word_files:
            messagebox.showwarning("Sin archivos", "Agrega al menos un documento .docx para convertir.")
            return

        dest_mode = self.word_dest_mode_var.get()
        target_dir = None
        if dest_mode == "custom_folder":
            target_dir = self.word_dir_entry.get().strip()
            if not target_dir or not os.path.exists(target_dir):
                messagebox.showwarning("Carpeta no válida", "Selecciona una carpeta destino válida.")
                return

        docs = list(self.word_files)

        def progress(current, total, file_path):
            self.after(0, lambda: self.set_status(f"Convirtiendo [{current}/{total}]: {os.path.basename(file_path)}...", "processing"))

        def task():
            return convert_docx_batch(docs, output_dir=target_dir, progress_callback=progress)

        def on_done(results):
            self.set_status(f"Conversión completada: {len(results)} archivo(s) convertidos a PDF.", "success")
            messagebox.showinfo("Conversión Exitosa", f"Se convirtieron {len(results)} documento(s) Word a PDF correctamente.")

        self.run_async(task, on_success=on_done, initial_msg="Iniciando conversión con Microsoft Word...")

    # =========================================================================
    # PESTAÑA 7: SEGURIDAD (PROTEGER / DESPROTEGER)
    # =========================================================================
    def _build_sec_tab(self):
        card = ctk.CTkFrame(self.tab_sec, fg_color=("gray22", "gray17"))
        card.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(card, text="Seguridad de Documentos PDF (Cifrado AES)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            card,
            text="Protege tus archivos con contraseña usando cifrado robusto de estándar bancario (AES-256 o AES-128) o remueve la contraseña de un documento protegido si conoces su clave.",
            text_color="gray60",
            wraplength=750,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        # Mode selector
        mode_row = ctk.CTkFrame(card, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkRadioButton(
            mode_row,
            text="🔒 Proteger PDF con Contraseña",
            variable=self.sec_mode_var,
            value="encrypt",
            command=self._on_sec_mode_change
        ).pack(side="left", padx=(0, 20))

        ctk.CTkRadioButton(
            mode_row,
            text="🔓 Desproteger / Quitar Contraseña",
            variable=self.sec_mode_var,
            value="decrypt",
            command=self._on_sec_mode_change
        ).pack(side="left")

        # File selector
        ctk.CTkLabel(card, text="1. Archivo PDF:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(8, 4))
        f_row = ctk.CTkFrame(card, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=(0, 12))

        self.sec_file_entry = ctk.CTkEntry(f_row, placeholder_text="Ningún PDF seleccionado...")
        self.sec_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(f_row, text="Examinar...", width=120, command=self._on_sec_browse).pack(side="right")

        self.sec_file_info_lbl = ctk.CTkLabel(card, text="Estado del archivo: -", text_color="gray60")
        self.sec_file_info_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Password input
        ctk.CTkLabel(card, text="2. Contraseña:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(0, 4))
        pwd_row = ctk.CTkFrame(card, fg_color="transparent")
        pwd_row.pack(fill="x", padx=16, pady=(0, 12))

        self.sec_pwd_entry = ctk.CTkEntry(pwd_row, show="*", placeholder_text="Ingresa la contraseña...")
        self.sec_pwd_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.sec_show_pwd_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            pwd_row,
            text="Mostrar contraseña",
            variable=self.sec_show_pwd_var,
            command=self._toggle_sec_pwd_visibility
        ).pack(side="right")

        # Algorithm (only for encrypt mode)
        self.sec_algo_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.sec_algo_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(self.sec_algo_frame, text="Algoritmo de cifrado:").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(self.sec_algo_frame, text="AES-256 (Máxima seguridad)", variable=self.sec_algo_var, value="AES-256").pack(side="left", padx=(0, 14))
        ctk.CTkRadioButton(self.sec_algo_frame, text="AES-128 (Compatibilidad)", variable=self.sec_algo_var, value="AES-128").pack(side="left")

        # Action button
        self.sec_action_btn = ctk.CTkButton(
            card,
            text="🔒 Proteger PDF y Guardar Como...",
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            command=self._on_sec_process
        )
        self.sec_action_btn.pack(fill="x", padx=16, pady=(4, 16))

    def _toggle_sec_pwd_visibility(self):
        show_char = "" if self.sec_show_pwd_var.get() else "*"
        self.sec_pwd_entry.configure(show=show_char)

    def _on_sec_mode_change(self):
        mode = self.sec_mode_var.get()
        if mode == "encrypt":
            self.sec_algo_frame.pack(fill="x", padx=16, pady=(0, 16))
            self.sec_action_btn.configure(
                text="🔒 Proteger PDF y Guardar Como...",
                fg_color="#2e7d32",
                hover_color="#1b5e20"
            )
        else:
            self.sec_algo_frame.pack_forget()
            self.sec_action_btn.configure(
                text="🔓 Desproteger PDF y Guardar Como...",
                fg_color="#1f538d",
                hover_color="#163f6d"
            )
        self._update_sec_file_status()

    def _on_sec_browse(self):
        file = filedialog.askopenfilename(title="Seleccionar archivo PDF", filetypes=[("Archivos PDF (*.pdf)", "*.pdf")])
        if file:
            self.sec_source_file = os.path.normpath(file)
            self.sec_file_entry.delete(0, tk.END)
            self.sec_file_entry.insert(0, self.sec_source_file)
            self._update_sec_file_status()

    def _update_sec_file_status(self):
        if not self.sec_source_file or not os.path.exists(self.sec_source_file):
            self.sec_file_info_lbl.configure(text="Estado del archivo: Ningún archivo seleccionado", text_color="gray60")
            return

        try:
            encrypted = is_pdf_encrypted(self.sec_source_file)
            if encrypted:
                self.sec_file_info_lbl.configure(text="Estado del archivo: 🔒 El archivo está protegido con contraseña.", text_color="#ffb74d")
            else:
                self.sec_file_info_lbl.configure(text="Estado del archivo: 🔓 El archivo no está protegido.", text_color="#4caf50")
        except Exception as e:
            self.sec_file_info_lbl.configure(text=f"Error al analizar archivo: {str(e)}", text_color="#ef5350")

    def _on_sec_process(self):
        if not self.sec_source_file or not os.path.exists(self.sec_source_file):
            messagebox.showwarning("Sin archivo", "Selecciona un archivo PDF válido primero.")
            return

        pwd = self.sec_pwd_entry.get().strip()
        if not pwd:
            messagebox.showwarning("Contraseña requerida", "Introduce una contraseña para continuar.")
            return

        mode = self.sec_mode_var.get()
        in_file = self.sec_source_file

        if mode == "encrypt":
            algo = self.sec_algo_var.get()
            out_path = filedialog.asksaveasfilename(
                title="Guardar PDF protegido como",
                defaultextension=".pdf",
                initialfile="protegido_" + os.path.basename(in_file),
                filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
            )
            if not out_path:
                return

            def task():
                encrypt_pdf(in_file, out_path, password=pwd, algorithm=algo)
                return out_path

            def on_done(res):
                self.set_status(f"PDF encriptado exitosamente con {algo}: {os.path.basename(res)}", "success")
                messagebox.showinfo("Seguridad", f"PDF protegido exitosamente con {algo} en:\n{res}")

            self.run_async(task, on_success=on_done, initial_msg=f"Cifrando PDF con {algo}...")

        else:
            out_path = filedialog.asksaveasfilename(
                title="Guardar PDF desprotegido como",
                defaultextension=".pdf",
                initialfile="desprotegido_" + os.path.basename(in_file),
                filetypes=[("Archivos PDF (*.pdf)", "*.pdf")]
            )
            if not out_path:
                return

            def task():
                decrypt_pdf(in_file, out_path, password=pwd)
                return out_path

            def on_done(res):
                self.set_status(f"PDF desprotegido exitosamente: {os.path.basename(res)}", "success")
                messagebox.showinfo("Seguridad", f"Contraseña removida exitosamente. Archivo guardado en:\n{res}")

            self.run_async(task, on_success=on_done, initial_msg="Desbloqueando documento PDF...")


def main():
    app = PDFMasterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
