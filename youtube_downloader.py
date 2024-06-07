import os
from pytube import YouTube
import pytube.exceptions as pte
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeAudioClip
import tkinter as tk
from tkinter import NORMAL, DoubleVar, ttk, messagebox, filedialog
import sv_ttk
from proglog import ProgressBarLogger


desktop_path = os.path.normpath(os.path.expanduser("~/Desktop"))


# *********************************************** Code mostly from Stack Overflow (with small modifications)
class MyLogger(ProgressBarLogger):
    def callback(self, **changes):
        # Every time the logger message is updated, this function is called with
        # the `changes` dictionary of the form `parameter: new value`.
        for parameter, value in changes.items():
            print("Parameter %s is now %s" % (parameter, value))

    def bars_callback(self, bar, attr, value, old_value=None):
        # Every time the logger progress is updated, this function is called
        percentage = value / self.bars[bar]["total"] * 100
        prog = str(int(percentage))
        progress2_label.configure(text=f"{prog}%")
        progress2_label.update()
        # print(percentage)


# ***************************************************


def dropdown_select():
    selection = dropdown.get()
    if selection == "Video (Highest Quality available)":
        return "Video", "Highest"
    elif selection == "1080p":
        return "Video", "1080p"
    elif selection == "720p":
        return "Video", "720p"
    else:
        return "Audio", None


def download_media(video_url, media_type, video_quality):
    out_path = ""
    temp_path = ""
    if check_button_state.get() == 0:
        out_path = desktop_path
    else:
        check_button_state.set(1)
        temp_path = filedialog.askdirectory()
        if temp_path != "":  # Empty string
            out_path = temp_path
            path_label.configure(text=f"Downloading to: {out_path}")
        else:
            out_path = desktop_path
            path_label.configure(
                text=f"No custom path chosen \n Downloading to: Desktop"
            )
    try:
        yt = YouTube(video_url)
        video_title = yt.title

        if media_type == "Audio":
            yt = YouTube(video_url, on_progress_callback=on_progress)
            file = yt.streams.get_audio_only()
            file.download()

            audio_mp4_file = AudioFileClip(f"{file.title}.mp4")
            audio_mp4_file.write_audiofile(f"{out_path}/{file.title}.mp3")

            if os.path.exists(f"{file.title}.mp4"):
                os.remove(f"{file.title}.mp4")
                on_finish()
            else:
                "Error when deleting converted files"

        elif video_quality == "720p":
            yt = YouTube(video_url, on_progress_callback=on_progress)
            file = yt.streams.filter(
                res="720p", mime_type="video/mp4", progressive=True
            ).first()
            file.download(filename=f"{out_path}/{video_title}(720p).mp4")
            on_finish()

        else:
            yt.streams.get_audio_only().download(
                filename="audio.mp3", skip_existing=False
            )
            audio = CompositeAudioClip([AudioFileClip("audio.mp3")])

            if video_quality == "Highest":
                yt = YouTube(video_url, on_progress_callback=on_progress)
                file = (
                    yt.streams.filter(adaptive=True)
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                file.download(
                    filename="video.mp4", output_path=out_path, skip_existing=False
                )

                video = VideoFileClip("video.mp4")
                video.audio = audio
                progress2_label.pack(padx=10, pady=10)
                video.write_videofile(
                    f"{out_path}/{video_title}({yt.streams.filter(adaptive=True).order_by('resolution').desc().first().resolution}).mp4",
                    logger=MyLogger(),
                )

                if os.path.exists(f"video.mp4") and os.path.exists("audio.mp3"):
                    os.remove("video.mp4")
                    os.remove("audio.mp3")
                    on_finish()
                else:
                    "Error when deleting merged files"

            elif video_quality == "1080p":
                yt = YouTube(video_url, on_progress_callback=on_progress)
                file = (
                    yt.streams.filter(res="1080p", mime_type="video/mp4", adaptive=True)
                    .order_by("resolution")
                    .desc()
                    .first()
                )

                file.download(
                    filename="video.mp4", output_path=out_path, skip_existing=False
                )

                video = VideoFileClip("video.mp4")
                video.audio = audio
                progress2_label.pack(padx=10, pady=10)
                video.write_videofile(
                    f"{out_path}/{video_title}(1080p).mp4", logger=MyLogger()
                )

                if os.path.exists(f"video.mp4") and os.path.exists("audio.mp3"):
                    os.remove("video.mp4")
                    os.remove("audio.mp3")
                    on_finish()
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
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = bytes_downloaded / total_size * 100
    per = str(int(percentage))
    progress_label.configure(text=f"{per}%")
    if bytes_remaining == 0:
        progress_label.configure(text="Completed. Now converting")
    progress_label.update()


def on_finish():
    progress_label.configure(text="Finished downloading and converting!")


def click(event):
    url_box.configure(state=NORMAL)
    url_box.delete(0, tk.END)
    url_box.unbind("<Button-1>", clicked)


def onClosing():
    if messagebox.askyesno(title="Quit?", message="Do you really want to quit"):
        root.destroy()


root = tk.Tk()
sv_ttk.set_theme("dark")

root.maxsize(800, 450)
root.minsize(800, 250)


root.title("YouTube Downloader - github.com/saleemtoure")
label = ttk.Label(root, text="YouTube Downloader", font=("Arial", 19))
label.pack(padx=10, pady=10)

theme_button = ttk.Button(root, text="Toggle Dark Mode", command=sv_ttk.toggle_theme)
theme_button.pack(padx=10, pady=10)

url_box = ttk.Entry(root, width=60, font=("Arial", 16))
url_box.insert(0, "Paste your URL here")
clicked = url_box.bind("<Button-1>", click)
url_box.pack(padx=10, pady=10)

checkState = tk.StringVar(root, "Download Video")
checkState.set("Video")

dropdown = ttk.Combobox(
    state="readOnly",
    values=[
        "Video (Highest Quality available)",
        "1080p",
        "720p",
        "Only Audio (Highest Quality available)",
    ],
    width=35,
)
dropdown.current(1)
dropdown.pack(padx=10, pady=10)

check_button_state = tk.IntVar()
check_button = ttk.Checkbutton(
    text="Choose where to save file (Default: Desktop)",
    variable=check_button_state,
)
check_button.pack(padx=10, pady=10)

path_label = ttk.Label(root, text=f"Downloading to: Desktop")
path_label.pack(padx=10, pady=10)

download_button = ttk.Button(
    root,
    text="Download File",
    # font=("Arial", 18),
    command=lambda: download_media(
        url_box.get(), dropdown_select()[0], dropdown_select()[1]
    ),
)
download_button.pack(padx=10, pady=10)

progress = tk.IntVar(value=0)
progress_label = ttk.Label(root, text=f"{0}%")
progress_label.pack(padx=10, pady=10)

progress2 = tk.IntVar(value=0)
progress2_label = ttk.Label(root, text=f"{0}%")

root.protocol("WM_DELETE_WINDOW", onClosing)
root.mainloop()
