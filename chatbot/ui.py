import tkinter
from tkinter import ttk, PhotoImage, Text
import sv_ttk
import livewhisper

root = tkinter.Tk()
root.title("Chatbot")
root.geometry("1000x800+475+65")
root.attributes("-alpha", 0.95)
icon = PhotoImage(file = "chatbot/data/openai_fill.png")
root.iconphoto(True, icon)

personality = Text(wrap="word", width=50)

personality.insert('1.0', """
###Story here### 

Here is the story of the conversation: {context}

User: {user}

Model:
""")

personality.pack(anchor='w', padx=10, pady=10)

def listen():
    livewhisper.main(personality.get("1.0", "end"))

l_button = ttk.Button(root, text="Listen", command=listen)
l_button.pack(side="bottom", padx=10, pady=10)

sv_ttk.set_theme("dark")
root.mainloop()