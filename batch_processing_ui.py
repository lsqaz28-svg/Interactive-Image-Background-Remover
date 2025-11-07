# batch_processing_ui.py
# Adds batch-processing UI and worker functions to the existing BackgroundRemoverGUI instance.
import threading
import queue
import time
import os
import tkinter as tk
import tkinter.ttk as ttk
import processing as batch_processing
import modes

def attach(gui):
    """Attach batch-processing UI and methods to a BackgroundRemoverGUI instance.
    This function mutates the gui by adding widgets and binding methods.
    """

    # state
    gui.batch_thread = None
    gui.batch_stop_event = threading.Event()
    gui.batch_queue = queue.Queue()
    gui.batch_progress = 0
    gui.batch_total = 0
    gui.selected_batch_mode = None
    gui.batch_output_prefix = "batch_"
    gui.batch_output_format = "PNG"

    # UI
    BatchFrame = tk.LabelFrame(gui.Controls, text="Batch processing", name="batch_frame")
    BatchFrame.pack(fill="x", padx=2, pady=4, side="top")

    tk.Label(BatchFrame, text="Output prefix:").pack(anchor="w", padx=6)
    gui.batch_prefix_entry = ttk.Entry(BatchFrame)
    gui.batch_prefix_entry.insert(0, gui.batch_output_prefix)
    gui.batch_prefix_entry.pack(fill="x", padx=6, pady=2)

    tk.Label(BatchFrame, text="Save format:").pack(anchor="w", padx=6)
    gui.batch_format_var = tk.StringVar(value=gui.batch_output_format)
    gui.batch_format_combo = ttk.Combobox(BatchFrame, textvariable=gui.batch_format_var, state="readonly", values=["PNG","JPEG","WEBP"], width=10)
    gui.batch_format_combo.pack(anchor="w", padx=6, pady=2)

    gui.preset_black_btn = ttk.Button(BatchFrame, text="Використати пресет: Чорний", command=lambda: gui.batch_use_preset('preset_black'))
    gui.preset_black_btn.pack(fill="x", padx=6, pady=(4,2))

    btn_frame = tk.Frame(BatchFrame)
    btn_frame.pack(fill="x", padx=6, pady=6)
    gui.start_batch_btn = ttk.Button(btn_frame, text="Start Batch", command=lambda: gui.batch_start())
    gui.start_batch_btn.pack(side="left", padx=6)
    gui.stop_batch_btn = ttk.Button(btn_frame, text="Stop Batch", command=lambda: gui.batch_stop(), state=tk.DISABLED)
    gui.stop_batch_btn.pack(side="left", padx=6)

    gui.batch_progress_label = ttk.Label(BatchFrame, text="Progress: 0/0")
    gui.batch_progress_label.pack(anchor="w", padx=6, pady=(4,0))

    gui.batch_log_text = tk.Text(BatchFrame, height=6)
    gui.batch_log_text.pack(fill="x", padx=6, pady=(4,6))
    gui.batch_log_text.configure(state=tk.DISABLED)

    # methods to attach
    def append_batch_log(text):
        try:
            gui.batch_log_text.configure(state=tk.NORMAL)
            gui.batch_log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {text}\n")
            gui.batch_log_text.see(tk.END)
            gui.batch_log_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def batch_use_preset(preset_name):
        entry = modes.MODES.get(preset_name)
        if entry:
            gui.selected_batch_mode = entry['module']
            append_batch_log(f"Preset selected: {entry.get('label', preset_name)}")
        else:
            gui.selected_batch_mode = None
            append_batch_log(f"Preset {preset_name} not found")

    def batch_start():
        if not getattr(gui, 'image_paths', None):
            tk.messagebox.showinfo("Batch", "No images to process.")
            return
        gui.batch_output_prefix = gui.batch_prefix_entry.get().strip() or "batch_"
        gui.batch_output_format = gui.batch_format_var.get() or "PNG"
        # prepare queue
        gui.batch_queue = queue.Queue()
        for p in gui.image_paths:
            gui.batch_queue.put(p)
        gui.batch_total = gui.batch_queue.qsize()
        gui.batch_progress = 0
        gui.batch_stop_event.clear()
        gui.start_batch_btn.configure(state=tk.DISABLED)
        gui.stop_batch_btn.configure(state=tk.NORMAL)
        append_batch_log(f"Starting batch ({gui.batch_total} files) format={gui.batch_output_format}")
        gui.batch_thread = threading.Thread(target=_batch_worker, daemon=True)
        gui.batch_thread.start()
        gui.after(200, _batch_ui_update)

    def batch_stop():
        gui.batch_stop_event.set()
        append_batch_log("Stop requested...")

    def _batch_worker():
        while not gui.batch_queue.empty() and not gui.batch_stop_event.is_set():
            input_path = gui.batch_queue.get()
            base = os.path.basename(input_path)
            name = os.path.splitext(base)[0]
            out_ext = ".png" if gui.batch_output_format == "PNG" else (".jpg" if gui.batch_output_format=="JPEG" else ".webp")
            out_name = f"{gui.batch_output_prefix}{name}{out_ext}"
            out_path = os.path.join(os.path.dirname(input_path), out_name)
            try:
                # determine bg_option from UI selection (map bg_color.get())
                bg_opt = None
                try:
                    bg_choice = gui.bg_color.get() if hasattr(gui, 'bg_color') else "Transparent"
                except Exception:
                    bg_choice = "Transparent"
                if bg_choice == "Transparent":
                    bg_opt = None
                elif bg_choice == "Blurred_(Slow)":
                    bg_opt = {'type':'color','value':(255,255,255)}
                else:
                    named = bg_choice.lower()
                    map_colors = {"white":(255,255,255),"black":(0,0,0)}
                    bg_opt = {'type':'color','value':map_colors.get(named,(255,255,255))}

                mode_mod = getattr(gui, 'selected_batch_mode', None)
                params = {}
                batch_processing.process_image(input_path, out_path, mode_module=mode_mod, params=params, bg_option=bg_opt, save_format=gui.batch_output_format)
                gui.batch_progress += 1
                append_batch_log(f"Processed: {input_path} -> {out_name}")
            except Exception as e:
                append_batch_log(f"ERROR processing {input_path}: {e}")
            time.sleep(0.01)
        append_batch_log("Batch finished" if not gui.batch_stop_event.is_set() else "Batch stopped")
        gui.batch_stop_event.clear()

    def _batch_ui_update():
        total = getattr(gui, 'batch_total', 0)
        try:
            gui.batch_progress_label.config(text=f"Progress: {gui.batch_progress}/{total}")
        except Exception:
            pass
        if gui.batch_thread and gui.batch_thread.is_alive():
            gui.after(200, _batch_ui_update)
        else:
            try:
                gui.start_batch_btn.configure(state=tk.NORMAL)
                gui.stop_batch_btn.configure(state=tk.DISABLED)
            except Exception:
                pass

    # attach methods to gui so they can be called from other code or bound in the instance
    gui.append_batch_log = append_batch_log
    gui.batch_use_preset = batch_use_preset
    gui.batch_start = batch_start
    gui.batch_stop = batch_stop
    gui._batch_worker = _batch_worker
    gui._batch_ui_update = _batch_ui_update

    # initial log entry
    append_batch_log("Batch UI attached.")