import traceback
from pathlib import Path

import toga
from toga.constants import COLUMN
from toga.style import Pack
from .process import process_directory


class Fichero(toga.App):
    # Button callback functions
    def do_clear(self, widget, **kwargs):
        self.label.text = "Ready."

    async def action_select_folder_dialog_multi(self, widget):
        try:
            path_names = await self.main_window.dialog(
                toga.SelectFolderDialog(
                    "Select multiple folders with Toga",
                    multiple_select=True,
                )
            )
            if path_names is not None:
                self.label.text = (
                    f"📁 Folders selected: {','.join([str(p) for p in path_names])}"
                )
                #process_directory
                self.folders = [Path(p) for p in path_names]
                print(f"Processing folders: {self.folders}")
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
        # check if self has attribute folders
        if not hasattr(self, 'folders'):
            self.label.text = "Please select folders first!"
            return
        

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

        # Label to show responses.
        self.label = toga.Label("Ready.", style=Pack(margin_top=20))
        self.window_label = toga.Label("", style=Pack(margin_top=20))
        self.window_counter = 0
        self.close_attempts = set()

        # Buttons
        btn_style = Pack(flex=1)
        
        btn_select_multi = toga.Button(
            "Select Folders",
            on_press=self.action_select_folder_dialog_multi,
            style=btn_style,
        )
        btn_select_model = toga.Button(
            "Select Model",
            on_press=self.action_select_model,
            style=btn_style,
        )
        btn_clear = toga.Button("Clear", on_press=self.do_clear, style=btn_style)

        model_selection = toga.Selection(
            items=["Alice", "Bob", "Charlie"],
            #on_select=self.action_select_model,
        )
        
        my_image = toga.Image(self.paths.app / "resources"/ "fichero.webp")
        logo = toga.ImageView(my_image,
                              style=Pack(
                                  width=200,
                                  height=200,
                                  margin_bottom=20,
                                  margin_top=20,
                              ))
        left_container = toga.Box(
            children=[
               logo
            ],
            style=Pack(
                flex=1, width=200, direction=COLUMN, margin=10
            ),
        )
        
        # Outermost box
        right_container = toga.Box(
            children=[
                btn_select_multi,
                btn_select_model,
                model_selection,
                self.label,
                self.window_label,
            ],
            style=Pack(flex=1, direction=COLUMN, margin=10),
        )
        split = toga.SplitContainer(content=[left_container, right_container])
        # Add the content on the main window
        self.main_window.content = split

        # Show the main window
        self.main_window.show()


def main():
    return Fichero("Fichero", "co.apjan.fichero")


if __name__ == "__main__":
    app = main()
    app.main_loop()
