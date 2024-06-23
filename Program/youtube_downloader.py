import os
import regex as re
from pytube import YouTube
import pytube.exceptions as pte
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeAudioClip
import tkinter as tk
from tkinter import NORMAL, ttk, messagebox, filedialog
import sv_ttk
from proglog import ProgressBarLogger

# TODO finn en måte å slette temp filene hvis nedlastning blir avbrutt


class Youtube_DownloaderGUI:

    def __init__(self):
        # * Test url (vanlig video): https://www.youtube.com/watch?v=Ri7-vnrJD3k
        # * Test url (unike video formater): https://www.youtube.com/watch?v=WXwgZL4zx9o

        self.root = tk.Tk()
        sv_ttk.set_theme("dark")

        self.desktop_path = os.path.normpath(os.path.expanduser("~/Desktop"))
        self.program_folder_path = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )

        self.root.maxsize(800, 450)
        self.root.minsize(800, 250)

        self.root.title("YouTube Downloader - github.com/saleemtoure")
        self.label = ttk.Label(self.root, text="YouTube Downloader", font=("Arial", 19))
        self.label.pack(padx=10, pady=10)

        self.theme_button = ttk.Button(
            self.root, text="Toggle Dark Mode", command=sv_ttk.toggle_theme
        )
        self.theme_button.pack(padx=10, pady=10)

        self.url_box = ttk.Entry(self.root, width=60, font=("Arial", 16))
        self.url_box.insert(0, "Paste your URL here")
        self.clicked = self.url_box.bind("<Button-1>", self.click)
        self.url_box.pack(padx=10, pady=10)

        self.checkState = tk.StringVar(self.root, "Download Video")
        self.checkState.set("Video")

        self.get_resolution_btn = ttk.Button(
            self.root,
            text="Get available resolutions",
            command=lambda: self.get_resolutions(self.url_box.get()),
        )
        self.get_resolution_btn.pack(padx=10, pady=10)

        self.check_button_state = tk.IntVar()
        self.check_button = ttk.Checkbutton(
            text="Choose where to save file (Default: Desktop)",
            variable=self.check_button_state,
        )
        self.path_label = ttk.Label(self.root, text=f"Downloading to: Desktop")

        self.video = None
        self.audio = None

        self.progress = tk.IntVar(value=0)
        self.progress_label = ttk.Label(self.root, text=f"{0}%")

        self.progress2 = tk.IntVar(value=0)
        self.progress2_label = ttk.Label(self.root, text=f"{0}%")

        self.download_button = ttk.Button(
            self.root,
            text="Download File",
            command=lambda: self.download_media(
                self.url_box.get(),
                self.dropdown_select()[0],
                self.dropdown_select()[1],
            ),
        )

        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.root.mainloop()

    def get_resolutions(self, video_url):
        resolution_list = []
        yt = YouTube(video_url)
        self.video_title_label = ttk.Label(
            self.root,
            text=f"Tittel: {self.parse_title_regex(yt.title)}",
        )
        self.video_title_label.pack()
        for stream in yt.streams.filter(mime_type="video/mp4").order_by("resolution"):
            if not stream.resolution in resolution_list:
                resolution_list.append(stream.resolution.removesuffix("p"))

        resolution_list.reverse()
        for i in range(len(resolution_list)):
            resolution_list[i] += "p"

        list(set(resolution_list))
        resolution_list.append("Only Audio (Highest Quality available)")
        self.initDropDown(resolution_list)

        self.get_resolution_btn.destroy()

        self.check_button.pack(padx=10, pady=10)

        self.path_label.pack(padx=10, pady=10)

        self.progress_label.pack(padx=10, pady=10)

    def initDropDown(self, valueList):
        self.dropdown = ttk.Combobox(
            state="readOnly",
            values=valueList,
            width=35,
        )
        self.dropdown.current(0)
        self.dropdown.pack(padx=10, pady=10)

        self.download_button.pack(padx=10, pady=10)

    def dropdown_select(self):
        selection = self.dropdown.get()
        if selection == "Only Audio (Highest Quality available)":
            return "Audio", None
        else:
            return "Video", selection

    def download_media(self, video_url, media_type, video_quality):
        out_path = ""
        temp_path = ""
        if self.check_button_state.get() == 0:
            out_path = self.desktop_path
        else:
            self.check_button_state.set(1)
            temp_path = filedialog.askdirectory()
            if temp_path != "":  # Empty string
                out_path = temp_path
                self.path_label.configure(text=f"Downloading to: {out_path}")
            else:
                out_path = self.desktop_path
                self.path_label.configure(
                    text=f"No custom path chosen \n Downloading to: Desktop"
                )
        try:
            yt = YouTube(video_url)
            video_title = self.parse_title_regex(yt.title)

            if media_type == "Audio":
                yt = YouTube(video_url, on_progress_callback=self.on_progress)
                file = yt.streams.get_audio_only()
                if file is not None:
                    file.download(output_path=self.program_folder_path)

                    audio_mp4_file = AudioFileClip(
                        f"{self.program_folder_path}/{file.title}.mp4"
                    )
                    audio_mp4_file.write_audiofile(f"{out_path}/{file.title}.mp3")

                    if os.path.exists(f"{self.program_folder_path}/{file.title}.mp4"):
                        os.remove(f"{self.program_folder_path}/{file.title}.mp4")
                        self.on_finish()
                    else:
                        "Error when deleting converted files"

            else:

                if self.checkProgressive(video_url, video_quality):
                    yt = YouTube(video_url, on_progress_callback=self.on_progress)
                    file = (
                        yt.streams.filter(
                            res=video_quality, type="video", progressive=True
                        )
                        .order_by("resolution")
                        .desc()
                        .first()
                    )

                    if file is not None:

                        file.download(
                            filename=f"{video_title} ({video_quality}).mp4",
                            skip_existing=False,
                            output_path=out_path,
                        )
                        self.on_finish()
                    else:
                        print("Fil er none")

                else:  # Videoer som ikke er progressive (oftest over 720p) lastes ned annderledes
                    audiofile = yt.streams.get_audio_only()
                    if audiofile is not None:
                        audiofile.download(
                            filename="audio.mp3",
                            skip_existing=False,
                            output_path=self.program_folder_path,
                        )
                        self.audio = CompositeAudioClip(
                            [AudioFileClip(f"{self.program_folder_path}/audio.mp3")]
                        )

                    yt = YouTube(video_url, on_progress_callback=self.on_progress)
                    file = (
                        yt.streams.filter(res=video_quality, type="video")
                        .order_by("resolution")
                        .desc()
                        .first()
                    )

                    if file is not None:
                        file.download(
                            filename="video.mp4",
                            skip_existing=False,
                            output_path=self.program_folder_path,
                        )
                    else:
                        print("Fil er none")

                    self.video = VideoFileClip(f"{self.program_folder_path}/video.mp4")
                    self.video.audio = self.audio
                    self.progress2_label.pack(padx=10, pady=10)
                    self.video.write_videofile(
                        f"{out_path}/{video_title} ({video_quality}).mp4",
                        logger=self.MyLogger(self.progress2_label),
                    )

                    if os.path.exists(
                        f"{self.program_folder_path}/video.mp4"
                    ) and os.path.exists(f"{self.program_folder_path}/audio.mp3"):
                        os.remove(f"{self.program_folder_path}/video.mp4")
                        os.remove(f"{self.program_folder_path}/audio.mp3")
                        self.on_finish()
                    else:
                        "Error when deleting merged files"

        except pte.RegexMatchError:
            print("Regex match error. Invalid URL.")
        except pte.VideoPrivate:
            print("Video is private.")
        except pte.VideoRegionBlocked:
            print("Video is blocked in your region.")
        except pte.VideoUnavailable:
            print("Video is unavailable.")
        except pte.PytubeError as e:
            print(f"A Pytube error occurred: {e}")
        except InterruptedError:
            print("interrupted")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def checkProgressive(self, video_url, video_quality):
        yt = YouTube(video_url)
        for stream in yt.streams.filter(resolution=video_quality):
            if stream.is_progressive:
                return stream.is_progressive

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = bytes_downloaded / total_size * 100
        per = str(int(percentage))
        self.progress_label.configure(text=f"{per}%")
        if bytes_remaining == 0:
            self.progress_label.configure(text="Completed. Now converting")
        self.progress_label.update()

    def on_finish(self):
        self.progress_label.configure(text="Finished downloading and converting!")

    def click(self, event):
        self.url_box.configure(state=NORMAL)
        self.url_box.delete(0, tk.END)
        self.url_box.unbind("<Button-1>", self.clicked)

    def onClosing(self):
        if messagebox.askyesno(title="Quit?", message="Do you really want to quit"):
            self.root.destroy()

            # self.audio = None
            # os.remove(f"{self.program_folder_path}/audio.mp3")

    # *********************************************** Code mostly from Stack Overflow (with some modifications)

    class MyLogger(ProgressBarLogger):
        def __init__(self, outer_instance):
            super().__init__()
            self.prog_label = outer_instance

        def callback(self, **changes):
            # Every time the logger message is updated, this function is called with
            # the `changes` dictionary of the form `parameter: new value`.
            for parameter, value in changes.items():
                print("Parameter %s is now %s" % (parameter, value))

        def bars_callback(self, bar, attr, value, old_value=None):
            # Every time the logger progress is updated, this function is called
            percentage = value / self.bars[bar]["total"] * 100
            prog = str(int(percentage))
            self.prog_label.configure(text=f"{prog}%")
            self.prog_label.update()
            # print(percentage)

    # *********************************************** Code 99.9% from Stack Overflow

    def parse_title_regex(self, text):
        # Regular expression pattern to match emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )

        no_emojis = emoji_pattern.sub(r"", text)
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", "", no_emojis)
        return cleaned_text

    # ***************************************************


Youtube_DownloaderGUI()
