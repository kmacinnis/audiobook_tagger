from pathlib import Path
from collections import defaultdict

import mutagen
import toga
from toga.constants import (COLUMN, ROW, LEFT, RIGHT, TOP, BOTTOM, CENTER)
from toga.style import Pack, pack
from toga.sources import Source

from common import is_audiofile
from audiobooks import Audiobook


TABLE_COLUMNS = [
    'filename',
    'filetype',
    'author',
    'title',
    'narrator',
    'date',
    'path',
    
]

def table_info(startdir, columns=TABLE_COLUMNS, num_rows=20):
    
    def tagged_content(item, columns):
        tags = mutagen.File(item, easy=True)
        return [tags[column] for column in columns]
        
    content = filter(is_audiofile, Path(startdir).glob('**/*'))
    # return (tagged_content(item) for item in content)
    return content


class Row:
    def __init__(self, path):
        self.path = str(path)
        self.filename = path.name
        self.filetype = path.suffix.lstrip('.')
        tags = mutagen.File(path, easy=True)
        tags = defaultdict(lambda: [''], tags)
        self.author = tags['artist'][0]
        self.title = tags['title'][0]
        self.narrator = tags['composer'][0]
        self.series_info = tags['version'][0]
        self.date = tags['date'][0]

class TableSource(Source):
    def __init__(self, directory):
        super().__init__()
        self._rows = []

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, index):
        return self._rows[index]
    
    def add(self, entry):
        row = Row(entry)
        self._rows.append(row)
        # self._rows.sort()
        self._notify('insert', index=len(self._rows) - 1, item=row)
        
    def remove(self, index):
        item = self._rows[index]
        del self._rows[index]
        self._notify('remove', item=item)

    def clear(self):
        self._rows = []
        self._notify('clear')


class TagAudiobooksApp(toga.App):
    
    def show_table(self, widget, **kwargs):
        path = Path(self.pathbox.value)
        if path.exists():
            for entry in table_info(path):
                self.table.data.add(entry)            
            self.table_window.content = self.table_box
            self.table_window.show()
        else:
            self.main_window.info_dialog('Path', 'Please select a path that exists')
        
    def action_select_folder_dialog(self, widget):
        try:
            path_name = self.main_window.select_folder_dialog(
                title="Select folder with Toga"
            )[0]
            self.pathbox.value = path_name
            self.main_folder = path_name
        except ValueError:
            pass

    def startup(self):
        
        # Set up windows
        self.main_window = toga.MainWindow(title=self.name, size=(600, 100))
        self.table_window = toga.Window(title=self.name, size=(500, 500))

        # Widgets
        pathlabel = toga.Label('Path:')
        self.pathbox = toga.TextInput(placeholder='enter path here',
                                style=Pack(flex=5)
        )

        buttonstyle = Pack(flex=0)
        get_folder_button = toga.Button('Select Folder', 
                                 on_press=self.action_select_folder_dialog, 
                                 style=buttonstyle,
        )
        self.start_process_button = toga.Button('Start', 
                                 on_press=self.show_table, 
                                 style=buttonstyle,
        )
        labeling_box = toga.Box(
            children=[
                pathlabel,
                self.pathbox,
            ],
            style=Pack(
                flex=1,
                direction=COLUMN,
                # padding=(3,),
            )
        )
        select_folder_box = toga.Box(
            children=[
                labeling_box,
                toga.Box(style=Pack(width=10)),
                get_folder_button,
            ],
            style=Pack(
                flex=1,
                direction=ROW,
                alignment=BOTTOM,
                padding=(5,0),
            )
        )
        self.outer_box = toga.Box(
            children=[
                select_folder_box,
                toga.Box(style=Pack(height=20)),
                self.start_process_button,
            ],
            style=Pack(
                flex=1,
                direction=COLUMN,
                alignment=CENTER,
                padding=10,
            )
        )
        self.table = toga.Table(
            headings=TABLE_COLUMNS,
            data=TableSource(self.pathbox.value),
            style=Pack(flex=1),
        )
        self.table_box = toga.Box(
            children = [self.table],
            style = Pack(padding=10),
        )

        # Add the content on the windows
        self.main_window.content = self.outer_box

        # Show the main window
        self.main_window.show()




def main():
    return TagAudiobooksApp('Audiobook Tagger', 'dev.macinnis.audiobooktagger')


if __name__ == '__main__':
    app = main()
    app.main_loop()
