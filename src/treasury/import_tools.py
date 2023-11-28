from pathlib import Path
import subprocess
from typing import Literal

from PySide2 import QtCore, QtGui, QtWidgets
import yt_dlp

from src.model import Keep, Treasure
from src.settings import APPLICATIONS, PATHS, SIGNALS
from src.widgets import BackgroundProcess, Error, Icon, Information


class ClipboardAction(QtWidgets.QAction):

    def __init__(self, keep: Keep, format_filter: Literal['image', 'music'] | None = None, convert_youtube: bool = True,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.clipboard = QtGui.QClipboard()
        self.convert_youtube = convert_youtube
        self.format_filter = format_filter
        self.keep = keep
        self.treasure = Treasure.read_mime_data(keep, self.clipboard.mimeData())
        if self.treasure:
            self.setText(f'Create from Clipboard ({self.treasure["info"]})')
            self.setIcon(Icon('clipboard_paste'))
        self.triggered.connect(self.exec_)

    def __bool__(self) -> bool:
        return bool(self.treasure) and (not self.format_filter or self.treasure['type'] == self.format_filter)

    def exec_(self) -> int:
        if not self.treasure:
            return 0
        importer = Importer(self.treasure, convert_youtube=self.convert_youtube, parent=self.parent())
        result = importer.exec_()
        self.treasure = importer.treasure
        return result


class Downloader(BackgroundProcess):

    def __init__(self, treasure: Treasure):
        super().__init__(name=f'YouTube Downloader ("{treasure["info"]}")')
        self.treasure = treasure

    def target(self) -> tuple:
        downloaded_filename = self.download_youtube()
        converted_path = self.convert_to_mp3(downloaded_filename)
        downloaded_path = Path(downloaded_filename)
        uuid = Treasure.get_uuid_from_bytes(converted_path.read_bytes())
        self.treasure['name'] = downloaded_path.stem
        self.treasure['type'] = 'music'
        self.treasure['suffix'] = '.mp3'
        self.treasure['uuid'] = uuid
        try:
            converted_path.rename(PATHS['inventory'].joinpath(uuid))
        except FileExistsError:
            converted_path.unlink()
        downloaded_path.unlink(missing_ok=True)
        return ()

    def download_youtube(self) -> str:
        ydl_opts = {
            'outtmpl': PATHS['workbench'].joinpath('%(title)s.%(ext)s').as_posix(),
            'format': 'm4a/bestaudio/best',
            'quiet': True,
            'no-warnings': True
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = self.treasure['info']
            info = ydl.extract_info(url, download=True)
            self.treasure['text'] = info.get('description', '')
        return info['requested_downloads'][0]['filename']

    @staticmethod
    def convert_to_mp3(filename: str) -> Path:
        target = Path(filename).with_suffix('.mp3')
        commands = [APPLICATIONS['vlc'], '-I dummy', filename, '--no-sout-video',
                    f'--sout=#transcode{{acodec=mp3,ab=128,vcodec=dummy}}:'
                    f'std{{access="file",mux="raw",dst="{target.__str__()}"}}', 'vlc://quit']
        process = subprocess.run(commands, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if process.stderr and (not (target_path := Path(target)).exists() or target_path.stat().st_size < 10):
            raise TypeError(process.stderr.decode())
        return target


class Importer(QtCore.QObject):

    def __init__(self, treasure: Treasure, convert_youtube: bool = True, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.convert_youtube = convert_youtube
        self.downloader = None
        self.treasure = treasure

    def exec_(self) -> int:
        df = self.treasure.keep.buildings['treasure'].df
        duplicates = df[df['uuid'] == self.treasure.uuid]
        if not duplicates.empty:
            duplicate = duplicates.iloc[0]
            duplicate_name = duplicate['name']
            duplicate_box = QtWidgets.QMessageBox()
            duplicate_box.setIcon(duplicate_box.Question)
            duplicate_box.setWindowTitle('Duplicate Found')
            duplicate_box.setText(f'The file is already found in the database ("{duplicate_name}").')
            yes_button = QtWidgets.QPushButton(Icon('plus'), 'Add Treasure', self.parent())
            no_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self.parent())
            duplicate_box.addButton(yes_button, duplicate_box.AcceptRole)
            duplicate_box.addButton(no_button, duplicate_box.RejectRole)
            duplicate_box.exec_()
            if duplicate_box.clickedButton() == no_button:
                self.treasure = Treasure.read_keep(self.treasure.keep, db_index=int(duplicate.name))
                return 0
        if self.treasure['suffix'] == 'URL:youtube' and self.convert_youtube:
            message_box = QtWidgets.QMessageBox()
            message_box.setIcon(message_box.Question)
            message_box.setText('The Treasure is a link to a YouTube video. Shall I download that video as music? '
                                'This may take a few minutes.')
            message_box.setWindowIcon(Icon('earth_music'))
            message_box.setWindowTitle('YouTube URL')
            download_button = QtWidgets.QPushButton(Icon('download'), 'Download')
            decline_button = QtWidgets.QPushButton(Icon('earth_link'), 'Keep as URL')
            message_box.addButton(download_button, message_box.AcceptRole)
            message_box.addButton(decline_button, message_box.RejectRole)
            message_box.exec_()
            if message_box.clickedButton() == decline_button:
                self.treasure.commit()
                return 1
            Information('Download Started', 'The download has started. You will receive a notification when the '
                                            'download is complete.').exec_()
            self.downloader = Downloader(self.treasure)
            self.downloader.EXCEPTION.connect(self.on_exception)
            self.downloader.FINISHED.connect(self.on_finish)
            self.downloader.start()
            return 2
        self.treasure.commit()
        return 1

    def on_exception(self, name: str, message: str):
        text = f'An error occurred while downloading {self.treasure["info"]}:\n\n{message}'
        Error(title=name, text=text).exec_()

    def on_finish(self):
        if self.treasure.db_index:
            self.treasure.delete()
        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(message_box.Information)
        message_box.setWindowTitle('Download Finished')
        message_box.setText(f'The YouTube video {self.treasure["info"]} was successfully downloaded and converted.')
        self.treasure['info'] = 'Converted from YouTube'
        db_index = self.treasure.commit()
        ok_button = QtWidgets.QPushButton(Icon('ok'), 'Ok', message_box)
        inspect_button = QtWidgets.QPushButton(Icon('chest_open'), 'Inspect', message_box)
        message_box.addButton(ok_button, message_box.AcceptRole)
        message_box.addButton(inspect_button, message_box.ActionRole)
        message_box.exec_()
        if message_box.clickedButton() == inspect_button:
            SIGNALS.TREASURE_INSPECT.emit(db_index)


class OpenTreasureDialog(QtWidgets.QFileDialog):

    def __init__(self, keep: Keep, format_filter: Literal['image', 'music'] | None = None,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.setWindowIcon(Icon('chest'))
        self.setWindowTitle('Add Treasure')
        self.format_filter = format_filter
        self.setFileMode(self.ExistingFile)
        self.setViewMode(self.List)

    def get(self) -> Treasure | None:
        match self.format_filter:
            case 'image': self.setNameFilter(f'Images ({" ".join("*" + f for f in Treasure.IMAGE_FORMATS)})')
            case 'music': self.setNameFilter(f'Music ({" ".join("*" + f for f in Treasure.MUSIC_FORMATS)})')
            case _: self.setNameFilter('Any File (*)')
        if not self.exec_():
            return None
        try:
            treasure = Treasure.read_path(self.keep, Path(self.selectedFiles()[0]))
        except Exception as err:
            Error.read_exception(err).exec_()
            return None
        if self.format_filter and treasure['type'] != self.format_filter:
            Error('Invalid Type', f'The selected file is not a valid {self.format_filter} type.')
            return None
        return treasure
