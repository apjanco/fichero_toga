import traceback
from pathlib import Path
import os
import json
import srsly
import toga
from toga.constants import COLUMN
from toga.style import Pack
from .process import process_folders
from .store import test_chroma_client
from .secrets import get_models_config


class Fichero(toga.App):
    # Button callback functions
    def do_clear(self, widget, **kwargs):
        self.folders = []
        self.label.text = "📁 Folders selected:\n"

    async def action_open_logs(self, widget):
        #this will open a window that displays the logs
        logs = toga.Window(title="Logs")
        logs.content = toga.ScrollContainer(
            content=toga.MultilineTextInput(
                value="".join(traceback.format_stack()),
                style=Pack(flex=1, padding=10, font_size=14),
            ),
            style=Pack(flex=1, padding=10)
        )
        logs.show()

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
        self.right_label.text = "💾 Output Format:\n Markdown (that's all you get for now)"

    def action_open_model_config_editor(self, widget):
        # Create a window for editing models_config
        editor_window = toga.Window(title="Edit Model Config")

        # get currently selected model 
        current_model = self.model_selection.value.name
        # Create a box for each model entry
        current_model_data = [model for model in self.models_config if model["name"] == current_model]
        if current_model_data:
            current_model_data = current_model_data[0]
            # pop current model from the list to avoid duplication
            self.models_config.remove(current_model_data)
            # Create input fields for editing model fields
            name_label = toga.Label("Model Name:")
            name_input = toga.TextInput(value=current_model_data["name"], placeholder="Model Name")
            provider_label = toga.Label("Provider:")
            provider_input = toga.TextInput(value=current_model_data["provider"], placeholder="Provider")
            api_key_label = toga.Label("API Key:")
            api_key_input = toga.TextInput(
                value=current_model_data.get("api_key", ""),
                placeholder="API Key (optional)"
            )
            prompt_label = toga.Label("Prompt:")
            prompt_input = toga.MultilineTextInput(
                value=current_model_data.get("prompt", "Extract text to markdown!"),
                placeholder="Prompt (optional)"
            )
            url_label = toga.Label("API URL:")
            url_input = toga.TextInput(
                value=current_model_data.get("url", ""),
                placeholder="API URL (optional)"
            )

            def save_changes(widget):
                current_model_data["name"] = name_input.value
                current_model_data["provider"] = provider_input.value
                current_model_data["api_key"] = api_key_input.value
                current_model_data["prompt"] = prompt_input.value
                current_model_data["url"] = url_input.value
                # add updated model back to the list
                self.models_config.append(current_model_data)
                #save changes to disk 
                srsly.write_jsonl(self.paths.data / "models_config.jsonl", self.models_config)
                
                editor_window.close()

            save_button = toga.Button("Save", on_press=save_changes, style=Pack(margin_top=10))

            model_box = toga.Box(
                children=[name_label, name_input, 
                          provider_label, provider_input, 
                          api_key_label, api_key_input, 
                          prompt_label, prompt_input, 
                          url_label, url_input, 
                          save_button],
                style=Pack(direction=COLUMN, padding=10)
            )
             
            editor_window.content = model_box
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
        self.output_folder = self.paths.data
        # Text Labels to show responses.
        self.label = toga.Label("📁 Folders selected:\n", style=Pack(margin_top=20))
        
        self.right_label = toga.Label(
            f"💾 Output Folder:\n {self.paths.data}", style=Pack(margin_top=20)
        )
        self.info_label = toga.Label("", style=Pack(margin_top=20))
        self.window_counter = 0
        self.close_attempts = set()
        self.models_config = get_models_config(self)
        # Buttons
        btn_style = Pack(flex=1)
        btn_view_logs = toga.Button(
            "View Logs",
            on_press=self.action_open_logs,
            style=btn_style,
        )
        btn_select_folders = toga.Button(
            "Select Folders",
            on_press=self.action_select_folders,
            style=btn_style,
        )
        
        btn_select_output_folders = toga.Button(
            "Change Output Folder",
            on_press=self.action_select_output_folder,
            style=btn_style,
        )
        btn_clear = toga.Button("Clear", on_press=self.do_clear, style=btn_style)
        model_selection = toga.Selection(
            items=self.models_config,
            on_change=self.action_select_model,
            accessor="name",
        )
        self.model_selection = model_selection
        self.center_label = toga.Label(
            f"✨ Model: {self.model_selection.value.name if self.model_selection.value else 'None'}\n  Provider: {self.model_selection.value.provider if self.model_selection.value else 'None'}",
            style=Pack(margin_top=20, margin_bottom=20, flex=1),
        )
        btn_models_config = toga.Button(
            "Edit Model Config",
            on_press=self.action_open_model_config_editor,
            style=btn_style,
        )

        # confirmed that the Chroma is compatible with Toga in dev
        # btn_test_chroma = toga.Button(
        #     "Test Chroma Client",
        #     on_press=test_chroma_client,
        #     style=btn_style,
        # )

        # Start button
        def on_start_pressed(widget):
            if self.folders and self.model_selection.value:
                self.info_label.text = ""
                docs = process_folders(self)
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
               self.info_label,
               btn_view_logs
               #btn_test_chroma
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
