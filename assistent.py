import customtkinter as ctk
import speech_recognition as sr
from langchain_ollama import OllamaLLM
from openai import OpenAI
import threading
import tkinter as tk

# Set the appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

model_name = ""
base_url = "https://models.inference.ai.azure.com"
api_key = "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"
provider = "OpenAI"

class ChatGPTAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("AI Assistant")
        self.geometry("800x600")
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main chat frame
        self.frame_chat = ctk.CTkFrame(self, corner_radius=10)
        self.frame_chat.pack(padx=20, pady=(10, 20), fill="both", expand=True)

        # Chat output field
        self.entry_user_prompt = ctk.CTkTextbox(self.frame_chat, height=200, corner_radius=10)
        self.entry_user_prompt.pack(padx=10, pady=10, fill="both", expand=True, side="top")
        self.entry_user_prompt.insert('0.0', "User: ")

        # Assistant's response field
        self.entry_assistant_character = ctk.CTkTextbox(self.frame_chat, height=100, corner_radius=10)
        self.entry_assistant_character.pack(padx=10, pady=(10, 20), fill="x", side="top")
        self.entry_assistant_character.insert('0.0', """###System prompt###""")

        # Frame for buttons at the bottom
        self.frame_buttons = ctk.CTkFrame(self, corner_radius=10)
        self.frame_buttons.pack(padx=20, pady=(0, 20), side="bottom")

        # Listen button
        self.button_listen = ctk.CTkButton(self.frame_buttons, text="Listen", command=self.handle_listen, corner_radius=10)
        self.button_listen.grid(row=0, column=0, padx=10, pady=10)

        # Get Answer button
        self.button_get_answer = ctk.CTkButton(self.frame_buttons, text="Get Answer", command=self.handle_get_answer, corner_radius=10)
        self.button_get_answer.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.settings_button = ctk.CTkButton(self.frame_buttons, text="Settings", command=self.open_settings, corner_radius=10)
        self.settings_button.grid(row=0, column=2, padx=10, pady=10)

        self.toplevel_window = None


    def handle_listen(self):
        r = sr.Recognizer()
        r.energy_threshold = 400
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5) #Added timeout and phrase_time_limit
                text = r.recognize_google(audio, language="ru-RU")
                self.entry_user_prompt.insert(tk.END, text)
            except sr.UnknownValueError:
                self.entry_user_prompt.insert(tk.END, "Could not understand audio. Please try again.\n")
            except sr.RequestError as e:
                self.entry_user_prompt.insert(tk.END, f"Could not request results from Google Speech Recognition service; {e}\n")
            except sr.WaitTimeoutError:
                self.entry_user_prompt.insert(tk.END, "Timeout occurred. Please try again.\n")
            except Exception as e:
                self.entry_user_prompt.insert(tk.END, f"An unexpected error occurred: {e}\n")


    def handle_get_answer(self):
        global llm
        try:
            if provider == "Ollama":
                llm = OllamaLLM(model=model_name)
                user_message = self.entry_user_prompt.get("1.0", tk.END).strip()
                character = self.entry_assistant_character.get(1.0, tk.END).strip()
                if user_message:
                    def process_response():
                        try:
                            prompt = f"Agent Character: {character}\nUser: {user_message}\nAssistant:"
                            response = llm.invoke(prompt)
                            self.entry_user_prompt.insert(tk.END, f"\nAssistent: {response}\nUser: ")
                            self.entry_user_prompt.see(tk.END)
                        except Exception as e:
                            self.entry_user_prompt.insert(tk.END, f"Error: {e}\n")

                    thread = threading.Thread(target=process_response)
                    thread.start()
            elif provider == "OpenAI":
                client = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                )
                user_message = self.entry_user_prompt.get("1.0", tk.END).strip()
                character = self.entry_assistant_character.get(1.0, tk.END).strip()
                if user_message:
                    def process_response():
                        try:
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": character},
                                    {"role": "user", "content": user_message}
                                ]
                            )
                            self.entry_user_prompt.insert(tk.END, f"\nAssistent: {response.choices[0].message.content}\nUser: ")
                            self.entry_user_prompt.see(tk.END)
                        except Exception as e:
                            self.entry_user_prompt.insert(tk.END, f"Error: {e}\n")

                    thread = threading.Thread(target=process_response)
                    thread.start()
            else:
                self.entry_user_prompt.insert(tk.END, "Error: Invalid provider selected.\n")
                return
        except Exception as e:
            self.entry_user_prompt.insert(tk.END, f"Error: {e}\n")

    def open_settings(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it


class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, *args, width=345, height=300, **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

        # Window settings
        self.title("Settings")
        self.width = width
        self.height = height
        self.geometry(f"{self.width}x{self.height}")
        self.update_model_choices(provider)  # Initialize with OpenAI models

        self.provider_label = ctk.CTkLabel(self, text="Choose a provider:")
        self.provider_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.provider_choice = ctk.CTkComboBox(self, values=["OpenAI", "Ollama"], command=self.update_model_choices)
        self.provider_choice.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.provider_choice.set(provider)  # Set the initial value

        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def update_model_choices(self, choice):
        if choice == "Ollama":
            try:
                self.model_base_url.grid_remove()
                self.model_base_url_entry.grid_remove()
                self.model_api.grid_remove()
                self.model_api_entry.grid_remove()
                self.model_choice_label.grid_remove()
                self.model_choice_entry.grid_remove()
            except Exception as e:
                pass

            self.model_choice_label = ctk.CTkLabel(self, text="Choose a model:")
            self.model_choice_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

            self.model_choice_entry = ctk.CTkEntry(self, placeholder_text="Enter model name here", width=200)
            self.model_choice_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.model_choice_entry.insert(0, model_name)  # Set the default value

        if choice == "OpenAI":
            self.model_base_url = ctk.CTkLabel(self, text="Base URL:")
            self.model_base_url.grid(row=1, column=0, padx=10, pady=10, sticky="w")

            self.model_base_url_entry = ctk.CTkEntry(self, placeholder_text="Enter base URL here")
            self.model_base_url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
            self.model_base_url_entry.insert(0, base_url)  # Set the default value

            self.model_api = ctk.CTkLabel(self, text="API Key:")
            self.model_api.grid(row=2, column=0, padx=10, pady=10, sticky="w")

            self.model_api_entry = ctk.CTkEntry(self, placeholder_text="Enter API Key here", show="*")
            self.model_api_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
            self.model_api_entry.insert(0, api_key)  # Set the default value

            self.model_choice_label = ctk.CTkLabel(self, text="Choose a model:")
            self.model_choice_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

            self.model_choice_entry = ctk.CTkEntry(self, placeholder_text="Enter model name here", width=200)
            self.model_choice_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.model_choice_entry.insert(0, model_name)  # Set the default value

    def save_settings(self):
        global model_name, base_url, api_key, provider
        try:
            provider = self.provider_choice.get()
            model_name = self.model_choice_entry.get()
            base_url = self.model_base_url_entry.get()
            api_key = self.model_api_entry.get()
            self.destroy()
        except AttributeError as e:
            pass


if __name__ == "__main__":
    app = ChatGPTAssistant()
    app.mainloop()
