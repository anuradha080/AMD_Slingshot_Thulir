import tkinter as tk
from tkinter import scrolledtext
import requests
import threading
import json

def generate_response():
    user_problem = input_text.get("1.0", tk.END).strip()

    if not user_problem:
        output_text.insert(tk.END, "Please enter a timing issue.\n")
        return

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, " Generating solution...\n")
    window.update()

    def run_model():
        prompt = f"""
You are an ASIC timing engineer.

Problem:
{user_problem}

Return ONLY valid JSON in this exact format:

{{
  "input_delay": number,
  "output_delay": number,
  "clock_uncertainty": number,
  "optimizations": [
    "suggestion1",
    "suggestion2",
    "suggestion3"
  ]
}}

Rules:
- Do NOT explain.
- Do NOT add text outside JSON.
- Only return JSON.
"""

        url = "http://localhost:11434/api/generate"

        payload = {
            "model": "phi",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 120,
                "temperature": 0.2
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=300)

            if response.status_code == 200:
                result = response.json()
                model_output = result["response"].strip()

                if model_output.startswith("```"):
                    parts = model_output.split("```")
                    if len(parts) >= 2:
                        model_output = parts[1]

                model_output = model_output.replace("json", "").strip()

                start = model_output.find("{")
                end = model_output.rfind("}") + 1

                if start != -1 and end != -1:
                    clean_json = model_output[start:end]
                else:
                    clean_json = model_output

                try:
                    data = json.loads(clean_json)

                    input_delay = data.get("input_delay", 0.2)
                    output_delay = data.get("output_delay", 0.2)
                    clock_uncertainty = data.get("clock_uncertainty", 0.05)
                    optimizations = data.get("optimizations", [])

                    sdc_output = f"""
SDC:
create_clock -name clk -period 1.0 [get_ports clk]
set_input_delay {input_delay} -clock clk [all_inputs]
set_output_delay {output_delay} -clock clk [all_outputs]
set_clock_uncertainty {clock_uncertainty} [get_clocks clk]

Optimizations:
"""

                    if optimizations and len(optimizations) >= 3:
                        for opt in optimizations[:3]:
                            sdc_output += f"- {opt}\n"
                    else:
                        sdc_output += "- Insert pipeline register\n"
                        sdc_output += "- Reduce logic depth\n"
                        sdc_output += "- Upsize critical cells\n"

                    output_text.delete("1.0", tk.END)
                    output_text.insert(tk.END, sdc_output)

                except Exception:
                    output_text.delete("1.0", tk.END)
                    output_text.insert(tk.END, "⚠ Model returned invalid JSON.\n\n")
                    output_text.insert(tk.END, model_output)

            else:
                output_text.insert(tk.END, f"Error: {response.status_code}")

        except Exception as e:
            output_text.insert(tk.END, f"Connection Error: {e}")

    threading.Thread(target=run_model).start()



window = tk.Tk()
window.title("AI-Powered ASIC Design Optimization Assistant")
window.geometry("780x520")
window.configure(bg="#0f0f0f")
window.resizable(False, False)


header_frame = tk.Frame(window, bg="#0f0f0f")
header_frame.pack(fill="x", pady=(15, 5))

title_label = tk.Label(
    header_frame,
    text="AI-Powered ASIC Timing Assistant",
    font=("Bahnschrift", 16, "bold"),
    fg="white",
    bg="#0f0f0f"
)
title_label.pack()

creator_label = tk.Label(
    header_frame,
    text="Developed by Yugi • Anu • Raj",
    font=("Bahnschrift", 10),
    fg="#cccccc",
    bg="#0f0f0f"
)
creator_label.pack(pady=(2, 5))


accent_line = tk.Frame(window, bg="#ED1C24", height=3)
accent_line.pack(fill="x", padx=40, pady=(0, 15))


input_label = tk.Label(
    window,
    text="Timing Issue",
    font=("Bahnschrift", 11),
    fg="white",
    bg="#0f0f0f"
)
input_label.pack(anchor="w", padx=40)

input_text = scrolledtext.ScrolledText(
    window,
    height=4,
    font=("Consolas", 10),
    bg="#1c1c1c",
    fg="white",
    insertbackground="white",
    bd=0
)
input_text.pack(fill="x", padx=40, pady=(5, 15))

button_frame = tk.Frame(window, bg="#0f0f0f")
button_frame.pack()

generate_button = tk.Button(
    button_frame,
    text="Generate",
    command=generate_response,
    bg="#ED1C24",
    fg="white",
    font=("Bahnschrift", 10, "bold"),
    width=12,
    bd=0,
    activebackground="#c4171c"
)
generate_button.grid(row=0, column=0, padx=10)

def clear_output():
    output_text.delete("1.0", tk.END)

clear_button = tk.Button(
    button_frame,
    text="Clear",
    command=clear_output,
    bg="#2b2b2b",
    fg="white",
    font=("Bahnschrift", 10),
    width=10,
    bd=0
)
clear_button.grid(row=0, column=1, padx=10)

def copy_output():
    window.clipboard_clear()
    window.clipboard_append(output_text.get("1.0", tk.END))

copy_button = tk.Button(
    button_frame,
    text="Copy",
    command=copy_output,
    bg="#2b2b2b",
    fg="white",
    font=("Bahnschrift", 10),
    width=10,
    bd=0
)
copy_button.grid(row=0, column=2, padx=10)

output_label = tk.Label(
    window,
    text="Generated SDC & Optimizations",
    font=("Bahnschrift", 11),
    fg="white",
    bg="#0f0f0f"
)
output_label.pack(anchor="w", padx=40, pady=(20, 0))

output_text = scrolledtext.ScrolledText(
    window,
    font=("Consolas", 10),
    bg="#1c1c1c",
    fg="#e6e6e6",
    insertbackground="white",
    bd=0
)
output_text.pack(fill="both", expand=True, padx=40, pady=(5, 20))

window.mainloop()
