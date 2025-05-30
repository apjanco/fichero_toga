import traceback
from pathlib import Path

import toga
from toga.constants import COLUMN
from toga.style import Pack
from .process import process_directory

models_config = [
    {"name": "qwen-vl-max-latest", "provider": "dashscope"},
    {"name": "llama", "provider": "ollama"},
    {"name": "gpt-4o", "provider": "openai"},
]


provider_config = {
    "dashscope:": {
        "api_key": "YOUR_DASHSCOPE_API_KEY",
        "url": "https://api.dashscope.com/v1/vlm",
    },
    "ollama": {
        "api_key": "YOUR_OLLAMA_API_KEY",
        "url": "http://localhost:11434/api/v1/chat/completions",
    },
    "openai": {
        "api_key": "YOUR_OPENAI_API_KEY",
        "url": "https://api.openai.com/v1/chat/completions",
    }
}

class Fichero(toga.App):
    # Button callback functions
    def do_clear(self, widget, **kwargs):
        self.folders = []
        self.label.text = "📁 Folders selected:\n"

    async def action_select_folders(self, widget):
        try:
            path_names = await self.main_window.dialog(
                toga.SelectFolderDialog(
                    "Select multiple folders with Toga",
                    multiple_select=True,
                )
            )
            if path_names is not None:
                self.label.text = (
                    f"📁 Folders selected:\n {'\n'.join([str(p) for p in path_names])}"
                )
                self.folders = [Path(p) for p in path_names]
            else:
                self.label.text = "No folders selected!"
        except ValueError:
            self.label.text = "Folders select dialog was canceled"

    async def action_select_output_folder(self, widget):
        try:
            path_name = await self.main_window.dialog(
                toga.SelectFolderDialog(
                    "Select single folder with Toga",
                    multiple_select=False,
                )
            )
            if path_name is not None:
                self.right_label.text = (
                    f"💾 Output Folder:\n {path_name}"
                )
                self.output_folder = path_name
                print(f"💾 Output Folder:\n {self.output_folder}")
            else:
                self.label.text = "No folders selected!"
        except ValueError:
            self.label.text = "Folders select dialog was canceled"

    async def window_close_handler(self, window):
        # This handler is called before the window is closed, so there
        # still are 1 more windows than the number of secondary windows
        # after it is closed
        # Return False if the window should stay open

        # Check to see if there has been a previous close attempt.
        if window in self.close_attempts:
            # If there has, update the window label and allow
            # the close to proceed. The count is -2 (rather than -1)
            # because *this* window hasn't been removed from
            # the window list.
            self.set_window_label_text(len(self.windows) - 2)
            return True
        else:
            await window.dialog(
                toga.InfoDialog(f"Abort {window.title}!", "Maybe try that again...")
            )
            self.close_attempts.add(window)
            return False

    def action_open_secondary_window(self, widget):
        self.window_counter += 1
        window = toga.Window(title=f"New Window {self.window_counter}")

        self.set_window_label_text(len(self.windows) - 1)
        secondary_label = toga.Label(text="You are in a secondary window!")
        window.content = toga.Box(
            children=[secondary_label], style=Pack(flex=1, direction=COLUMN, margin=10)
        )
        window.on_close = self.window_close_handler
        window.show()

    def action_close_secondary_windows(self, widget):
        # Close all windows that aren't the main window.
        for window in list(self.windows):
            if not isinstance(window, toga.MainWindow):
                window.close()

    def action_select_model(self, widget):
        # get the selected model from the selection widget
        self.center_label.text = f"✨ Model: {self.model_selection.value.name}\n  Provider: {self.model_selection.value.provider}"

    def action_select_output_format(self, widget):
        self.right_label.text = "💾 Output Format:\n Markdown?"

    def action_open_models_config_editor(self, widget):
        # Create a window for editing models_config
        editor_window = toga.Window(title="Edit Models Config")

        # Store entry widgets for later access
        self.model_entries = []

        # Create a box for each model entry
        entry_boxes = []
        for model in models_config:
            name_entry = toga.TextInput()
            name_entry.value = model["name"]
            provider_entry = toga.TextInput()
            provider_entry.value = model["provider"]
            self.model_entries.append((name_entry, provider_entry))
            entry_box = toga.Box(
                children=[
                    toga.Label("Name:", style=Pack(width=60)),
                    name_entry,
                    toga.Label("Provider:", style=Pack(width=70)),
                    provider_entry,
                ],
                style=Pack(direction="row", margin_bottom=5),
            )
            entry_boxes.append(entry_box)

        # Add button to add a new model
        def add_model(widget):
            name_entry = toga.TextInput()
            provider_entry = toga.TextInput()
            self.model_entries.append((name_entry, provider_entry))
            new_box = toga.Box(
                children=[
                    toga.Label("Name:", style=Pack(width=60)),
                    name_entry,
                    toga.Label("Provider:", style=Pack(width=70)),
                    provider_entry,
                ],
                style=Pack(direction="row", margin_bottom=5),
            )
            models_box.children.insert(-2, new_box)  # Insert before buttons
            editor_window.content.refresh()

        # Save button callback
        def save_models(widget):
            # Update models_config with new values
            models_config.clear()
            for name_entry, provider_entry in self.model_entries:
                name = name_entry.value.strip()
                provider = provider_entry.value.strip()
                if name and provider:
                    models_config.append({"name": name, "provider": provider})
            editor_window.close()
            # Refresh model_selection items
            self.model_selection.items = models_config

        # Cancel button callback
        def cancel_edit(widget):
            editor_window.close()

        add_btn = toga.Button("Add Model", on_press=add_model, style=Pack(width=100))
        save_btn = toga.Button("Save", on_press=save_models, style=Pack(width=80))
        cancel_btn = toga.Button("Cancel", on_press=cancel_edit, style=Pack(width=80))

        models_box = toga.Box(
            children=entry_boxes + [add_btn, toga.Box(children=[save_btn, cancel_btn], style=Pack(direction="row", padding_top=10))],
            style=Pack(direction="column", padding=10),
        )

        editor_window.content = models_box
        editor_window.show()

    async def exit_handler(self, app):
        # Return True if app should close, and False if it should remain open
        if await self.dialog(
            toga.ConfirmDialog("Toga", "Are you sure you want to quit?")
        ):
            print(f"Label text was '{self.label.text}' when you quit the app")
            return True
        else:
            self.label.text = "Exit canceled"
            return False




    def startup(self):
        # Set up main window
        self.main_window = toga.MainWindow()
        self.on_exit = self.exit_handler
        self.folders = []
        # Label to show responses.
        self.label = toga.Label("📁 Folders selected:\n", style=Pack(margin_top=20))
        self.center_label = toga.Label(
            "✨ Model:", style=Pack(margin_top=20)
        )
        self.right_label = toga.Label(
            "💾 Output Folder:\n", style=Pack(margin_top=20)
        )
        self.info_label = toga.Label("", style=Pack(margin_top=20))
        self.window_counter = 0
        self.close_attempts = set()

        # Buttons
        btn_style = Pack(flex=1)
        
        btn_select_folders = toga.Button(
            "Select Folders",
            on_press=self.action_select_folders,
            style=btn_style,
        )
        btn_select_model = toga.Button(
            "Select Model",
            on_press=self.action_select_model,
            style=btn_style,
        )
        btn_select_output_folders = toga.Button(
            "Select Output Folder",
            on_press=self.action_select_output_folder,
            style=btn_style,
        )
        btn_clear = toga.Button("Clear", on_press=self.do_clear, style=btn_style)
        model_selection = toga.Selection(
            items=models_config,
            accessor="name",
        )
        self.model_selection = model_selection
        
        btn_models_config = toga.Button(
            "Edit Models Config",
            on_press=self.action_open_models_config_editor,
            style=btn_style,
        )
        # Start button
        def on_start_pressed(widget):
            if self.folders and self.model_selection.value:
                self.info_label.text = ""
                process_directory(self.folders, self.model_selection.value.provider, self.model_selection.value.name)
            else:
                self.info_label.text = "Please select folders\n and a model before starting."

        btn_start = toga.Button(
            "Start / Iniciar",
            on_press=on_start_pressed,
            # green button 
            style=Pack(
                background_color="green",
                color="white",
                flex=1,
                margin_top=20,
                margin_bottom=20,
            ),
        )
        my_image = toga.Image(self.paths.app / "resources"/ "icons" / "fichero-512.png")
        logo = toga.ImageView(
            my_image,
            style=Pack(
            width=200,
            height=200,
            margin_bottom=20,
            margin_top=20,
            alignment="center",
            )
        )

        # Containers
        info_container = toga.Box(
            children=[
               logo,
               btn_start,
               self.info_label
            ],
            #make the container only as wide as the logo
            style=Pack(flex=1, direction=COLUMN, margin=10, width=220),
        )
        left_container = toga.Box(
            children=[
                btn_select_folders,
                btn_clear,
                self.label

            ],
            #make the container only as wide as the logo
            style=Pack(flex=1, direction=COLUMN, margin=10, width=220),
        )
        
        center_container = toga.Box(
            children=[
                model_selection,
                btn_select_model,
                btn_models_config,
                self.center_label
            ],
            style=Pack(flex=1, direction=COLUMN, margin=10),
        )
        # Outermost box
        right_container = toga.Box(
            children=[
                btn_select_output_folders,
                toga.Button(
                    "Output Format",
                    on_press=self.action_select_output_format,
                    style=btn_style,
                ),
                self.right_label,
            ],
            style=Pack(flex=1, direction=COLUMN, margin=10),
        )
        left_split = toga.SplitContainer(content=[info_container, left_container])
        right_split = toga.SplitContainer(content=[center_container, right_container])
        main = toga.SplitContainer(content=[left_split, right_split])
        # Add the content on the main window
        self.main_window.content = main

        # Show the main window
        self.main_window.show()


def main():
    return Fichero("Fichero", "co.apjan.fichero")


if __name__ == "__main__":
    app = main()
    app.main_loop()
